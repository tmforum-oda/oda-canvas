"""
Kubernetes Kong API Lifecycle Management Operator for ODA API Custom Resources.

This module is part of the ODA Canvas, specifically tailored for environments adopting the Kong API Gateway. It utilizes the Kopf Kubernetes operator framework (https://kopf.readthedocs.io/) to manage API custom resources. 
The operator is designed to seamlessly integrate with the Kong API Gateway, facilitating the creation and management of HTTPRoute configurations to expose APIs.

Key Features:
* Automatically handles the lifecycle of ODA APIs including creation, update, and deletion of corresponding HTTPRoute resources to expose APIs through Kong.
* Manages KongPlugin resources to apply and enforce various plugins and policies on APIs routed through Kong.
* Configures an API gateway to act as a front aligning with recommended production architectures.

Usage:
This operator can be deployed as part of the ODA Canvas in Kubernetes clusters where the Kong API Gateway is used to expose APIs. It simplifies the management of API exposure and security by interfacing directly with Kong, 
providing a robust and scalable API management solution.
"""

import kopf
import kubernetes.client
import logging
from kubernetes.client.rest import ApiException
import os
import yaml
import requests

logging_level = os.environ.get("LOGGING", logging.INFO)
print("Logging set to ", logging_level)

kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)

logger = logging.getLogger("APIOperator")
logger.setLevel(int(logging_level))

GROUP = "oda.tmforum.org"
VERSION = "v1"
APIS_PLURAL = "exposedapis"

group = "gateway.networking.k8s.io"  # API group for Gateway API
version = "v1"  # Currently tested on v1 ,need to check with v1alpha1, v1alpha2, v1beta1, etc as well.
plural = "httproutes"  # The plural name of the kong route CRD - HTTPRoute resource


@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def manage_api_lifecycle(spec, name, namespace, status, meta, logger, **kwargs):
    """
    Handles the lifecycle events (creation and updates) for API resources.
    This function creates or updates HTTPRoute based on the provided spec, and manages associated
    plugins like rate limiting, API key verification, and CORS settings based on their enabled status
    along with check file path if plugin are provided in form on template.
    It also updates the HTTPRoute with annotations corresponding to the plugins applied.

    Parameters:
        spec (dict): The specification dictionary containing settings like path, plugins configuration etc.
        name (str): The name of the resource triggering this handler.
        namespace (str): The Kubernetes namespace where the resource resides.
        meta (dict): Metadata dictionary containing information eg. uid which is useful for managing resources.
        logger (logging.Logger): Logger instance for logging information or errors.
        kwargs: Arbitrary keyword arguments which might include additional context needed for plugins.

    Returns:
        Nothing
    """
    httproute_created = create_or_update_ingress(spec, name, namespace, meta)
    if not httproute_created:
        logger.info(
            "HTTPRoute creation/update failed. Skipping plugin/policy management."
        )
        return

    plugin_names = []

    if spec.get("rateLimit", {}).get("enabled", False):
        ratelimit_plugin = manage_ratelimit(spec, name, namespace, meta)
        if ratelimit_plugin:
            plugin_names.append(ratelimit_plugin)

    if spec.get("apiKeyVerification", {}).get("enabled", False):
        apiauth_plugin = manage_apiauthentication(spec, name, namespace, meta)
        if apiauth_plugin:
            plugin_names.append(apiauth_plugin)

    if spec.get("CORS", {}).get("enabled", False):
        cors_plugin = manage_cors(spec, name, namespace, meta)
        if cors_plugin:
            plugin_names.append(cors_plugin)

    # if provided  in template it ca manage plugins from URL and collect their names generated after applying in cluster
    url_plugin_names = manage_plugins_from_url(spec, name, namespace, meta)
    plugin_names.extend(url_plugin_names)

    # Updating the HTTPRoute with annotations if any plugins were created or updated.
    if plugin_names:
        annotations = {"konghq.com/plugins": ",".join(plugin_names)}
        updated = update_httproute_annotations(name, namespace, annotations)
        if updated:
            logger.info(f"HTTPRoute '{name}' updated with plugins: {plugin_names}")
        else:
            logger.error("Failed to update HTTPRoute with policies/plugins.")


def create_or_update_ingress(spec, name, namespace, meta, **kwargs):
    """
    Creates or updates an HTTPRoute for the given API resource. It configures the route based on the
    specified path and attaches it to defined service.
    The function also manages Kubernetes ownership metadata to ensure resources are cleaned up appropriately
    when the parent resource is deleted. see kopf.adopt()

    Parameters:
        spec (dict): The specification dictionary which should contain the path and other related settings.
        name (str): The name of the resource.
        namespace (str): The namespace where the HTTPRoute will be created or updated.
        meta (dict): Metadata about the resource, used to set ownership in Kubernetes.
        kwargs: Arbitrary keyword arguments, typically unused but available for future extensions.

    Returns:
        True if the HTTPRoute was successfully created or updated, False otherwise.
    """

    # Check if 'implementation' is 'ready' this will be enabled once APIS_PLURAL = "exposedapis" will be used in components operator,reference examples not available as on 25 April 2024
    """
    if not status.get('implementation', {}).get('ready', False):
        logger.info(f"Implementation not ready for '{name}'. Ingress creation or update skipped.")
        return
    """

    api_instance = kubernetes.client.CustomObjectsApi()
    ingress_name = f"kong-api-route-{name}"
    namespace = "components"
    service_name = "istio-ingress"
    service_namespace = "istio-ingress"
    strip_path = "false"
    kong_gateway_namespace = "components"

    try:
        # Attempt to find if the path exists or not , will skip if no path
        path = spec.get("path")
        if not path:
            logger.warning(f"Path not found   '{name}'. Httproute creation skipped.")
            return

        httproute_manifest = {
            "apiVersion": f"{group}/{version}",
            "kind": "HTTPRoute",
            "metadata": {
                "name": ingress_name,
                "namespace": namespace,
                "annotations": {
                    "konghq.com/strip-path": strip_path,
                    "konghq.com/protocols": "https",
                    "konghq.com/https-redirect-status-code": "301",
                },
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
                                "namespace": service_namespace,
                            },
                        ],
                    },
                ],
            },
        }
        # Make it child resource of exposedapis
        kopf.adopt(httproute_manifest)

        try:
            # Checking if the HTTPRoute already exists
            existing_route = api_instance.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=ingress_name,
            )
            resource_version = existing_route["metadata"]["resourceVersion"]
            httproute_manifest["metadata"]["resourceVersion"] = resource_version
            response = api_instance.replace_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                name=ingress_name,
                plural=plural,
                body=httproute_manifest,
            )
            logger.info(
                f"HTTPRoute '{ingress_name}' updated successfully in namespace '{namespace}'."
            )
            return True
        except ApiException as e:
            if e.status == 404:
                response = api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=httproute_manifest,
                )
                logger.info(
                    f"HTTPRoute '{ingress_name}' created successfully in namespace '{namespace}'."
                )
                return True
            else:
                logger.error(f"API exception when accessing HTTPRoute: {e}")
                return False
    except ApiException as e:
        logger.error(f"Failed to create or update HTTPRoute '{ingress_name}': {e}")
        return False


def manage_ratelimit(spec, name, namespace, meta, **kwargs):
    """
    Configures a rate limiting plugin for an API if rate limiting is enabled in the spec. It creates or updates
    the plugin configuration in the specified namespace.

    Parameters:
        spec (dict): The specification dictionary containing rate limiting configuration details.
        name (str): The name of the API resource.
        namespace (str): The Kubernetes namespace where the plugin will be configured.
        meta (dict): Metadata containing information eg. uid .
        kwargs: Arbitrary keyword arguments, used for logging or other contextual operations.

    Returns:
        str or None: The name of the authentication plugin on success, or None if the setup is skipped
    """

    # Check condition will be removed from here as already in manage api lifecycle function
    rate_limit_config = spec.get("rateLimit", {})
    if not rate_limit_config.get("enabled", False):
        logger.info(f"Rate limiting not enabled for '{name}'. Plugin creation skipped.")
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"rate-limit-{name}"
    namespace = "components"
    group = "configuration.konghq.com"
    version = "v1"
    plural = "kongplugins"
    rate_limit_config_interval = int(rate_limit_config["limit"])
    print(rate_limit_config_interval)

    rate_limit_plugin_manifest = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {"name": plugin_name, "namespace": namespace},
        "config": {"minute": rate_limit_config_interval, "policy": "local"},
        "plugin": "rate-limiting",
    }

    # Make it child resource of exposedapis
    kopf.adopt(rate_limit_plugin_manifest)

    try:
        # Checking if the plugin already exists
        existing_plugin = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=plugin_name,
        )
        resource_version = existing_plugin["metadata"]["resourceVersion"]
        rate_limit_plugin_manifest["metadata"]["resourceVersion"] = resource_version
        response = api_instance.replace_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            name=plugin_name,
            plural=plural,
            body=rate_limit_plugin_manifest,
        )
        logger.info(
            f"Rate Limiting Plugin '{plugin_name}' updated in namespace '{namespace}'."
        )
        return plugin_name  # Returning plugin name on success
    except ApiException as e:
        if e.status == 404:
            response = api_instance.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=rate_limit_plugin_manifest,
            )
            logger.info(
                f"Rate Limiting Plugin '{plugin_name}' created in namespace '{namespace}'."
            )
            return plugin_name  # Returning plugin name on success
        else:
            logger.error(f"API exception when accessing KongPlugin: {e}")
            raise


def manage_apiauthentication(spec, name, namespace, meta, **kwargs):
    """
    Configures or updates an API authentication plugin (JWT) , for the specified API resource based on its specification. This is configured and tested as per CE version of kong.
    If using paid version ,can use template option to pass authenication plugin yaml and authentication will be configured on route.

    This function checks if API key verification (authentication) is enabled and sets up or updates the JWT plugin
    accordingly. The function also handles the lifecycle of the plugin, ensuring it is properly adopted and managed within
    the Kubernetes environment.

    Parameters:
        spec (dict): The specification dictionary containing the API key verification settings.
        name (str): The name of the API resource.
        namespace (str): The Kubernetes namespace where the plugin will be configured.
        meta (dict): Metadata about the resource.
        kwargs: Arbitrary keyword arguments, primarily used for additional logging or context.

    Returns:
        str or None: The name of the authentication plugin on success, or None if the setup is skipped.

    Raises:
        ApiException: An error from the Kubernetes API if the plugin update or creation fails.
    """
    global httproute_uid
    # print(httproute_uid) httproute_uid will be used for cleanup
    # Check condition will be removed from here as already in manage api lifecycle function
    apiauthentication_config = spec.get("apiKeyVerification", {})
    print(apiauthentication_config)
    if not apiauthentication_config.get("enabled", False):
        logger.info(
            f"Rate authentication not enabled for '{name}'. Plugin creation skipped."
        )
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"apiauthentication-{name}"
    namespace = "components"
    group = "configuration.konghq.com"
    version = "v1"
    plural = "kongplugins"

    apiauthentication = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {"name": plugin_name, "namespace": namespace},
        "config": {
            #  static config values , change in crd will be required to make dynamic
            "uri_param_names": ["jwt"],
            "cookie_names": ["token"],
            "claims_to_verify": ["exp"],
            "key_claim_name": "iss",
            "secret_is_base64": False,
        },
        "plugin": "jwt",
    }

    kopf.adopt(apiauthentication)

    try:
        # Check if the plugin already exists
        existing_plugin = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=plugin_name,
        )
        resource_version = existing_plugin["metadata"]["resourceVersion"]
        apiauthentication["metadata"]["resourceVersion"] = resource_version
        response = api_instance.replace_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            name=plugin_name,
            plural=plural,
            body=apiauthentication,
        )
        logger.info(
            f"api authentication '{plugin_name}' updated in namespace '{namespace}'."
        )
        return plugin_name  # Return plugin name on success
    except ApiException as e:
        if e.status == 404:
            response = api_instance.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=apiauthentication,
            )
            logger.info(
                f"api authentication '{plugin_name}' created in namespace '{namespace}'."
            )
            return plugin_name  # Return plugin name on success
        else:
            logger.error(f"API exception when accessing KongPlugin: {e}")
            raise


def manage_cors(spec, name, namespace, meta, **kwargs):
    """
    Manages the creation or update of a CORS (Cross-Origin Resource Sharing) configuration for an API.

    This function sets up or updates a CORS plugin based on the CORS settings specified in the API resource's spec.
    It checks if CORS is enabled and configures the KongPlugin accordingly, handling its lifecycle within the Kubernetes environment.

    Parameters:
        spec (dict): The specification dictionary containing CORS configuration.
        name (str): The name of the API resource.
        namespace (str): The Kubernetes namespace where the plugin will be configured.
        meta (dict): Metadata about the resource, used for managing ownership in Kubernetes.
        kwargs: Arbitrary keyword arguments, primarily used for additional logging or context.

    Returns:
        str or None: The name of the CORS plugin on success, or None if CORS is not enabled.

    Raises:
        ApiException: An error from the Kubernetes API if the plugin update or creation fails.
    """

    cors_config = spec.get("CORS", {})
    if not cors_config.get("enabled", False):
        logger.info(f"CORS not enabled for '{name}'. Configuration skipped.")
        return

    api_instance = kubernetes.client.CustomObjectsApi()
    plugin_name = f"cors-{name}"
    namespace = "components"
    group = "configuration.konghq.com"
    version = "v1"
    plural = "kongplugins"

    cors_plugin_manifest = {
        "apiVersion": f"{group}/{version}",
        "kind": "KongPlugin",
        "metadata": {"name": plugin_name, "namespace": namespace},
        "config": {
            "methods": cors_config.get("handlePreflightRequests", {})
            .get("allowMethods", ["GET", "POST", "HEAD", "OPTIONS"])
            .split(", "),
            "headers": cors_config.get("handlePreflightRequests", {})
            .get(
                "allowHeaders",
                [
                    "Origin",
                    "Accept",
                    "X-Requested-With",
                    "Content-Type",
                    "Access-Control-Request-Method",
                    "Access-Control-Request-Headers",
                ],
            )
            .split(", "),
            "origins": [cors_config.get("allowOrigins", "*")],
            "credentials": cors_config.get("allowCredentials", False),
            "max_age": cors_config.get("handlePreflightRequests", {}).get(
                "maxAge", 3600
            ),
        },
        "plugin": "cors",
    }

    kopf.adopt(cors_plugin_manifest)

    try:
        # Check if plugin is already there
        existing_plugin = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=plugin_name,
        )
        resource_version = existing_plugin["metadata"]["resourceVersion"]
        cors_plugin_manifest["metadata"]["resourceVersion"] = resource_version
        response = api_instance.replace_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            name=plugin_name,
            plural=plural,
            body=cors_plugin_manifest,
        )
        logger.info(f"CORS Plugin '{plugin_name}' updated in namespace '{namespace}'.")
        return plugin_name  # Returning plugin name on success
    except ApiException as e:
        if e.status == 404:
            # Creating plugin if not existing
            response = api_instance.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=cors_plugin_manifest,
            )
            logger.info(
                f"CORS Plugin '{plugin_name}' created in namespace '{namespace}'."
            )
            return plugin_name  # Returning plugin name on success
        else:
            logger.error(f"API exception when accessing CORS Plugin: {e}")
            raise


def update_httproute_annotations(name, namespace, annotations):
    """
    Updates the annotations of an HTTPRoute resource to include references to any plugins/policies applied.

    This function attempts to patch the existing HTTPRoute with new plugins/policies .This helps in maintaining a clear record of what plugins are
    associated with which routes.

    Parameters:
        name (str): The name of the HTTPRoute resource.
        namespace (str): The Kubernetes namespace where the HTTPRoute is located.
        annotations (dict): A dictionary containing the annotations to be added or updated on the HTTPRoute.

    Returns:
        bool: True if the update is successful, False otherwise.

    Raises:
        ApiException: Error if the update fails.
    """
    api_instance = kubernetes.client.CustomObjectsApi()
    ingress_name = f"kong-api-route-{name}"
    group = "gateway.networking.k8s.io"
    version = "v1"
    plural = "httproutes"
    namespace = "components"

    try:
        # Fetch the current HTTPRoute to get the resourceVersion
        current_route = api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=ingress_name,
        )
        resource_version = current_route["metadata"]["resourceVersion"]

        api_instance.patch_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=ingress_name,
            body={
                "metadata": {
                    "annotations": annotations,
                    "resourceVersion": resource_version,
                }
            },
        )
        logger.info(
            f"HTTPRoute '{ingress_name}' updated with plugins/policies in namespace '{namespace}'."
        )
        return True
    except ApiException as e:
        logger.error(
            f"Failed to update plugins/policies for HTTPRoute '{ingress_name}': {e}"
        )
        return False


def check_url(url):
    """
    Checks the accessibility of a URL to ensure it is reachable.
    This function sends a HEAD request to the URL to verify if the URL is accessible without downloading the content.
    It logs an error if the URL is not reachable or returns an unsuccessful status code.

    Parameters:
        url (str): The URL to check for its accessibility.

    Returns:
        bool: True for accessible URL else its False
    """
    try:
        response = requests.head(url)
        response.raise_for_status()  # Raising HTTPError if the HTTP request returned an unsuccessful
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to reach the given URL in CR template: {url}. Error: {e}")
        return False


def download_template(url):
    """
    Downloads and parses a YAML template from a given URL.
    This function attempts to fetch content from a specified URL expecting it to be a YAML format. It parses the content
    into a list of documents. Using 'no-cache' headers to make sure fresh content is fetched always.

    Parameters:
        url (str): The URL from which to download the YAML template.

    Returns:
        list or None: A list of YAML documents or None if the download fails or content is invalid.
    """
    try:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        documents = yaml.safe_load_all(
            response.text
        )  # safe_load to handle one yaml and safe_load_all to handle multiple YAML documents
        return list(documents)
    except requests.RequestException as e:
        logger.error(f"Failed to download URL in CR template: {url}. Error: {e}")
        return None


def apply_plugins_from_template(templates, namespace, owner_references):
    """
    Applies plugin configurations to the Kubernetes cluster using the provided templates.
    Each template is expected to define a Kubernetes custom object for a plugin. This function manages the lifecycle of
    these plugins, updating existing ones and creating new ones as per requirement.

    Parameters:
        templates (list): A list of dictionaries, each representing a plugin configuration in YAML format.
        namespace (str): The Kubernetes namespace in which the plugins should be managed.
        owner_references (list): A list of owner references to ensure Kubernetes garbage collection is linked to the parent resource.

    Returns:
        list: A list of names of the plugins that were successfully created or updated.
    """
    # Applying the configurations from the template to the Kubernetes cluster
    plugin_names = []
    api_instance = kubernetes.client.CustomObjectsApi()

    for template in templates:
        # Add ownerReferences to the template
        template["metadata"]["ownerReferences"] = owner_references

        # Assign the metadata to the template to manage it as a child object
        kopf.adopt(template)

        plugin_name = template["metadata"]["name"]
        group, version = template["apiVersion"].split("/")
        plural = "kongplugins"

        try:
            # Attempt to get the existing plugin
            existing_plugin = api_instance.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=plugin_name,
            )
            resource_version = existing_plugin["metadata"]["resourceVersion"]
            template["metadata"]["resourceVersion"] = resource_version
            response = api_instance.replace_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=plugin_name,
                body=template,
            )
            logger.info(f"Plugin '{plugin_name}' updated in namespace '{namespace}'.")
        except ApiException as e:
            if e.status == 404:
                # If plugin not existing creating it
                response = api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=template,
                )
                logger.info(
                    f"Plugin '{plugin_name}' created in namespace '{namespace}'."
                )
            else:
                logger.error(f"Failed to apply plugin '{plugin_name}': {e}")
                continue

        plugin_names.append(plugin_name)
    return plugin_names


def manage_plugins_from_url(spec, name, namespace, meta):
    """
    Manages the download and application of plugins from a URL specified in the API resource specification.
    This function checks if a URL is provided and reachable, downloads the corresponding templates, and applies them
    as plugins in the specified namespace. It also handles setting up ownership for automatic cleanup and logs the results.

    Parameters:
        spec (dict): The specification dictionary that may contain a 'template' URL.
        name (str): The name of the API resource.
        namespace (str): The Kubernetes namespace where plugins will be applied.
        meta (dict): Metadata about the resource, used for managing ownership in Kubernetes.

    Returns:
        list: A list of plugin names that were applied from the URL in template in CR.
    """
    # Manages downloading and applying plugins from a URL specified
    plugin_names = []
    template_url = spec.get("template")
    if check_url(template_url):
        templates = download_template(template_url)
        if templates:
            # Prepare owner references for adoption
            owner_references = [
                {
                    "apiVersion": f"{GROUP}/{VERSION}",
                    "kind": "ExposedAPI",
                    "name": name,
                    "uid": meta.get("uid"),
                    "controller": True,
                    "blockOwnerDeletion": True,
                }
            ]
            plugin_names.extend(
                apply_plugins_from_template(templates, namespace, owner_references)
            )
            logger.info(f"Plugins applied from URL and their name are: {plugin_names}")
        else:
            logger.info("Template download failed or it was empty.")
    else:
        logger.info("Template URL is not reachable.")
    return plugin_names


# This function to only log the expected HTTPRoute deletion ,can be removed will not effect functionality
@kopf.on.delete(GROUP, VERSION, APIS_PLURAL, retries=1)
def delete_api_lifecycle(meta, name, namespace, **kwargs):
    """
    Handles the deletion event of an API resource and logs the expected cascading deletions.
    This function logs the deletion of an 'ExposedAPI' resource and the expected automatic deletion of its associated
    'HTTPRoute' due to Kubernetes ownership links that were created using kopf.adopt().

    Parameters:
        meta (dict): Metadata about the resource, which includes details like the resource's unique identifier.
        name (str): The name of the API resource that was deleted.
        namespace (str): The Kubernetes namespace from which the resource was deleted.
        kwargs: Arbitrary keyword arguments, primarily used for additional logging or context.

    Returns:
        None
    """
    logger.info(f"ExposedAPI '{name}' deleted from namespace '{namespace}'.")
    ingress_name = f"kong-api-route-{name}"
    logger.info(
        f"HTTPRoute '{ingress_name}'  to be automatically deleted as child resource of ExposedAPI '{name}' ."
    )
