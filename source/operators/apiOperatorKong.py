import kopf
import kubernetes.client
import logging
import json
from kubernetes.client.rest import ApiException
from kubernetes.client.api import CustomObjectsApi
import os
import yaml
import requests


logging_level = os.environ.get('LOGGING',logging.INFO)
print('Logging set to ',logging_level)

kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)

logger = logging.getLogger('APIOperator')
logger.setLevel(int(logging_level))


HTTP_SCHEME = "http://"
HTTP_K8s_LABELS = ['http', 'http2']
HTTP_STANDARD_PORTS = [80, 443]
GROUP = "oda.tmforum.org"
VERSION = "v1beta3"
APIS_PLURAL = "exposedapis"
httproute_uid = None

group = "gateway.networking.k8s.io"  # API group for Gateway API
version = "v1"  # Currently tested on v1 ,need to check with v1alpha1, v1alpha2, v1beta1, etc.
plural = "httproutes"  # The plural name of the kong route CRD - HTTPRoute resource 

 

@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def manage_api_lifecycle(spec, name, namespace, status, meta, logger, **kwargs):
    httproute_created = create_or_update_ingress(spec, name, namespace, meta, logger)
    if not httproute_created:
        logger.info("HTTPRoute creation/update failed. Skipping plugin/policy management.")
        return

    plugin_names = []

    if spec.get('rateLimit', {}).get('enabled', False):
        ratelimit_plugin = manage_ratelimit(spec, name, namespace, meta, logger)
        if ratelimit_plugin:
            plugin_names.append(ratelimit_plugin)

    if spec.get('apiKeyVerification', {}).get('enabled', False):
        apiauth_plugin = manage_apiauthentication(spec, name, namespace, meta, logger)
        if apiauth_plugin:
            plugin_names.append(apiauth_plugin)

    if spec.get('CORS', {}).get('enabled', False):
        cors_plugin = manage_cors(spec, name, namespace, meta, logger)
        if cors_plugin:
            plugin_names.append(cors_plugin)
    
    # Manage plugins from URL if provided  in template and collect their names generated after applying in cluster
    url_plugin_names = manage_plugins_from_url(spec, name, namespace, meta, logger)
    plugin_names.extend(url_plugin_names)

    # Update the HTTPRoute with annotations if any plugins were created or updated.
    if plugin_names:
        annotations = {'konghq.com/plugins': ','.join(plugin_names)}
        updated = update_httproute_annotations(name, namespace, annotations, logger)
        if updated:
            logger.info(f"HTTPRoute '{name}' updated with plugins: {plugin_names}")
        else:
            logger.error("Failed to update HTTPRoute with annotations.")


def create_or_update_ingress(spec, name, namespace, meta, logger, **kwargs):
    global httproute_uid
    # Check if 'implementation' is 'ready' this will be enabled once APIS_PLURAL = "exposedapis" will be used in components operator 
    """
    if not status.get('implementation', {}).get('ready', False):
        logger.info(f"Implementation not ready for '{name}'. Ingress creation or update skipped.")
        return
    """
    # Initialize Kubernetes  custom obecclient
    api_instance = kubernetes.client.CustomObjectsApi()
    ingress_name = f"kong-api-route-{name}"
    namespace = "istio-ingress" 
    service_name = "istio-ingress"
    service_namespace = "istio-ingress"
    strip_path = "false"
    kong_gateway_namespace = "istio-ingress"

    # Prepare ownerReference ,this will add owner refernece from exposedapis to http  route ,currently this will not work for cleanup as parent child in different ns 
    owner_references = [{
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": "ExposedAPIs",
        "name": name,
        "uid": meta.get('uid'),
        "controller": True,
        "blockOwnerDeletion": True,
    }]

    try:
        # Attempt to find if the path exists , if no path skip the configuration
        path = spec.get('path')
        print(path)
        if not path:
            logger.warning(f"Path not found   '{name}'. Ingress creation skipped.")
            return

        httproute_manifest = {
            "apiVersion": f"{group}/{version}",
            "kind": "HTTPRoute",
            "metadata": {
                "name": ingress_name,
                "namespace": namespace,
                "annotations": {
                    "konghq.com/strip-path": strip_path,
                },
                "ownerReferences": owner_references
            },
            "spec": {
                "parentRefs": [
                    {
                        "name": "kong",
                        "namespace": kong_gateway_namespace,
                    },
                ],
                "rules": [
                    {
                        "matches": [    
                            {
                                "path": {
                                    "type": "PathPrefix",
                                    "value": path,
                                },
                            },
                        ],
                        "backendRefs": [
                            {
                                "name": service_name,
                                "kind": "Service",
                                "port": 80,
                            },
                        ],
                    },
                ],
            },
        }

        try:
            # Check if the HTTPRoute already exists
            existing_route = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=ingress_name)
            resource_version = existing_route['metadata']['resourceVersion']
            httproute_manifest['metadata']['resourceVersion'] = resource_version
            response = api_instance.replace_namespaced_custom_object(group=group, version=version, namespace=namespace, name=ingress_name, plural=plural, body=httproute_manifest)
            logger.info(f"HTTPRoute '{ingress_name}' updated in namespace '{namespace}'.")
            httproute_uid = meta.get('uid')
            print(httproute_uid)
            return True
        except ApiException as e:
            if e.status == 404:
                response = api_instance.create_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, body=httproute_manifest)
                logger.info(f"HTTPRoute '{ingress_name}' created in namespace '{namespace}'.")
                httproute_uid = meta.get('uid')
                print(httproute_uid)
                return True 
            else:
                logger.error(f"API exception when accessing HTTPRoute: {e}")
                return False
    except ApiException as e:
        logger.error(f"Failed to create or update HTTPRoute '{ingress_name}': {e}")
        return False


def manage_ratelimit(spec, name, namespace, meta, logger, **kwargs):
    global httproute_uid
    #print(httproute_uid) httproute_uid will be used for cleanup 
    # Check condition will be removed from here as already in manage api lifecycle function
    rate_limit_config = spec.get('rateLimit', {})
    if not rate_limit_config.get('enabled', False):
        logger.info(f"Rate limiting not enabled for '{name}'. Plugin creation skipped.")
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"rate-limit-{name}"
    namespace = "istio-ingress" 
    group = "configuration.konghq.com"   
    version = "v1"  
    plural = "kongplugins"  
    rate_limit_config_interval = int(rate_limit_config['limit'])
    print(rate_limit_config_interval)

    rate_limit_plugin_manifest = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {
            "name": plugin_name,
            "namespace": namespace
        },
        "config": {
            "minute": rate_limit_config_interval,
            "policy": "local"
        },
        "plugin": "rate-limiting"
    }

    try:
        # Check if the plugin already exists
        existing_plugin = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=plugin_name)
        resource_version = existing_plugin['metadata']['resourceVersion']
        rate_limit_plugin_manifest['metadata']['resourceVersion'] = resource_version
        response = api_instance.replace_namespaced_custom_object(group=group, version=version, namespace=namespace, name=plugin_name, plural=plural, body=rate_limit_plugin_manifest)
        logger.info(f"Rate Limiting Plugin '{plugin_name}' updated in namespace '{namespace}'.")
        return plugin_name  # Return plugin name on success
    except ApiException as e:
        if e.status == 404:
            response = api_instance.create_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, body=rate_limit_plugin_manifest)
            logger.info(f"Rate Limiting Plugin '{plugin_name}' created in namespace '{namespace}'.")
            return plugin_name  # Return plugin name on success
        else:
            logger.error(f"API exception when accessing KongPlugin: {e}")
            raise


def manage_apiauthentication(spec, name, namespace, meta, logger, **kwargs):
    global httproute_uid
    #print(httproute_uid) httproute_uid will be used for cleanup 
    # Check condition will be removed from here as already in manage api lifecycle function
    apiauthentication_config = spec.get('apiKeyVerification', {})
    print(apiauthentication_config)
    if not apiauthentication_config.get('enabled', False):
        logger.info(f"Rate authentication not enabled for '{name}'. Plugin creation skipped.")
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"apiauthentication-{name}"
    namespace = "istio-ingress"  
    group = "configuration.konghq.com"   
    version = "v1"   
    plural = "kongplugins"   

    apiauthentication = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {
            "name": plugin_name,
            "namespace": namespace
        },
        "config": {
            #  static config values , change in crd will be required to make dynamic 
            "uri_param_names": ["jwt"],
            "cookie_names": ["token"],
            "claims_to_verify": ["exp"],
            "key_claim_name": "iss",
            "secret_is_base64": False,

        },
        "plugin": "jwt"
    }

    try:
        # Check if the plugin already exists
        existing_plugin = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=plugin_name)
        resource_version = existing_plugin['metadata']['resourceVersion']
        apiauthentication['metadata']['resourceVersion'] = resource_version
        response = api_instance.replace_namespaced_custom_object(group=group, version=version, namespace=namespace, name=plugin_name, plural=plural, body=apiauthentication)
        logger.info(f"api authentication '{plugin_name}' updated in namespace '{namespace}'.")
        return plugin_name  # Return plugin name on success
    except ApiException as e:
        if e.status == 404:
            response = api_instance.create_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, body=apiauthentication)
            logger.info(f"api authentication '{plugin_name}' created in namespace '{namespace}'.")
            return plugin_name  # Return plugin name on success
        else:
            logger.error(f"API exception when accessing KongPlugin: {e}")
            raise

def manage_cors(spec, name, namespace, meta, logger, **kwargs):
    global httproute_uid
    #print(httproute_uid) httproute_uid will be used for cleanup , cors config to be updated with new features
    # Check condition will be removed from here as already in manage api lifecycle function
    cors_config = spec.get('CORS', {})
    print(cors_config)
    if not cors_config.get('enabled', False):
        logger.info(f"CORS not enabled for '{name}'. Configuration skipped.")
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"cors-{name}"
    namespace = "istio-ingress"   
    group = "configuration.konghq.com"  
    version = "v1" 
    plural = "kongplugins"  # The plural name of the KongPlugin resource

    cors_plugin_manifest = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {
            "name": plugin_name,
            "namespace": namespace
        },
        "config": {
            "methods": cors_config.get('handlePreflightRequests', {}).get('allowMethods', ["GET", "POST", "HEAD", "OPTIONS"]).split(", "),
            "headers": cors_config.get('handlePreflightRequests', {}).get('allowHeaders', ["Origin", "Accept", "X-Requested-With", "Content-Type", "Access-Control-Request-Method", "Access-Control-Request-Headers"]).split(", "),
            "origins": [cors_config.get('allowOrigins', "*")],
            "credentials": cors_config.get('allowCredentials', False),
            "max_age": cors_config.get('handlePreflightRequests', {}).get('maxAge', 3600)
        },
        "plugin": "cors"
    }

    try:
        # Check if the plugin already exists
        existing_plugin = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=plugin_name)
        resource_version = existing_plugin['metadata']['resourceVersion']
        cors_plugin_manifest['metadata']['resourceVersion'] = resource_version
        response = api_instance.replace_namespaced_custom_object(group=group, version=version, namespace=namespace, name=plugin_name, plural=plural, body=cors_plugin_manifest)
        logger.info(f"CORS Plugin '{plugin_name}' updated in namespace '{namespace}'.")
        return plugin_name  # Return plugin name on success
    except ApiException as e:
        if e.status == 404:
            # If it doesn't exist, create it
            response = api_instance.create_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, body=cors_plugin_manifest)
            logger.info(f"CORS Plugin '{plugin_name}' created in namespace '{namespace}'.")
            return plugin_name  # Return plugin name on success
        else:
            logger.error(f"API exception when accessing CORS Plugin: {e}")
            raise


def update_httproute_annotations(name, namespace, annotations, logger):
    api_instance = kubernetes.client.CustomObjectsApi()
    ingress_name = f"kong-api-route-{name}"
    group = "gateway.networking.k8s.io"
    version = "v1"
    plural = "httproutes"
    namespace = "istio-ingress"

    try:
        # Fetch the current HTTPRoute to get the resourceVersion
        current_route = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=ingress_name)
        resource_version = current_route['metadata']['resourceVersion']

        # Update with  annotations ,using patch to update
        api_instance.patch_namespaced_custom_object(
            group=group, 
            version=version, 
            namespace=namespace, 
            plural=plural, 
            name=ingress_name, 
            body={
                "metadata": {
                    "annotations": annotations,
                    "resourceVersion": resource_version
                }
            }
        )
        logger.info(f"HTTPRoute '{ingress_name}' updated with annotations in namespace '{namespace}'.")
        return True
    except ApiException as e:
        logger.error(f"Failed to update annotations for HTTPRoute '{ingress_name}': {e}")
        return False









def check_url(url):
    #checking url access first
    try:
        response = requests.head(url)
        response.raise_for_status()  # Raise  HTTPError if the HTTP request returned an unsuccessful status code
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to reach the URL: {url}. Error: {e}")
        return False

def download_template(url):
    """ Download and parse the YAML or JSON template from the URL. """
    try:
        response = requests.get(url)
        response.raise_for_status()
        documents = yaml.safe_load_all(response.text)  # safe_load to handle one yaml and safe_load_all to handle multiple YAML documents
        return list(documents) 
    except requests.RequestException as e:
        logger.error(f"Failed to download the template from: {url}. Error: {e}")
        return None




def apply_plugins_from_template(templates, namespace):
    #Applying the configurations from the template to the Kubernetes cluster
    namespace = "istio-ingress"
    plugin_names = []
    api_instance = kubernetes.client.CustomObjectsApi()


    for template in templates:
        plugin_name = template['metadata']['name']
        group, version = template['apiVersion'].split('/')
        plural = 'kongplugins'

        try:
            # Attempt to get the existing plugin
            existing_plugin = api_instance.get_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=plugin_name)
            resource_version = existing_plugin['metadata']['resourceVersion']
            template['metadata']['resourceVersion'] = resource_version 
            response = api_instance.replace_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, name=plugin_name, body=template)
            logger.info(f"Plugin '{plugin_name}' updated in namespace '{namespace}'.")
        except ApiException as e:
            if e.status == 404:
                # If the plugin does not exist, creatring it
                response = api_instance.create_namespaced_custom_object(group=group, version=version, namespace=namespace, plural=plural, body=template)
                logger.info(f"Plugin '{plugin_name}' created in namespace '{namespace}'.")
            else:
                logger.error(f"Failed to apply plugin '{plugin_name}': {e}")
                continue  

        plugin_names.append(plugin_name)
    return plugin_names


def manage_plugins_from_url(spec, name, namespace, meta, logger):
    #Manages downloading and applying plugins from a URL specified
    plugin_names = []
    template_url = spec.get('template')
    if check_url(template_url):
        templates = download_template(template_url)
        if templates:
            plugin_names.extend(apply_plugins_from_template(templates, namespace))
            logger.info(f"Plugins applied from URL and their names collected here: {plugin_names}")
        else:
            logger.info("Template download failed or was empty.")
    else:
        logger.info("Template URL is not reachable.")
    return plugin_names








