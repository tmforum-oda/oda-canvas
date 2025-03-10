import kopf
import logging
import os
import re
import base64
import urllib.parse

import kubernetes
import kubernetes.client
from kubernetes.client.exceptions import ApiException

import yaml

from jinja2 import Environment, FileSystemLoader, select_autoescape


from service_inventory_client import ServiceInventoryAPI

from utils import safe_get

# import kubernetes.client
# from kubernetes.client.rest import ApiException
from log_wrapper import LogWrapper, logwrapper


DEPAPI_GROUP = "oda.tmforum.org"
DEPAPI_VERSION = "v1"
DEPAPI_PLURAL = "dependentapis"

HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409


# https://kopf.readthedocs.io/en/stable/install/

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
logger = logging.getLogger("oa2envf")
logger.setLevel(int(logging_level))
logger.info("Logging set to %s", logging_level)
logger.debug("debug logging is on")

LogWrapper.set_defaultLogger(logger)

CICD_BUILD_TIME = os.getenv("CICD_BUILD_TIME")
GIT_COMMIT_SHA = os.getenv("GIT_COMMIT_SHA")
if CICD_BUILD_TIME:
    logger.info("CICD_BUILD_TIME=%s", CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info("GIT_COMMIT_SHA=%s", GIT_COMMIT_SHA)

# for local testing set environment variable $CANVAS_INFO_ENDPOINT to "http://localhost:8638"
CANVAS_INFO_ENDPOINT = os.getenv(
    "CANVAS_INFO_ENDPOINT",
    "http://info.canvas.svc.cluster.local",
)
logger.info(f"CANVAS_INFO_ENDPOINT={CANVAS_INFO_ENDPOINT}")

OAUTH2_TOKEN_ENDPOINT = os.getenv(
    "OAUTH2_TOKEN_ENDPOINT",
    "http://canvas-keycloak.canvas.svc.cluster.local:8083/auth/realms/odari/protocol/openid-connect/token",
)
logger.info("OAUTH2_TOKEN_ENDPOINT=%s", OAUTH2_TOKEN_ENDPOINT)

ENVOY_SECRET_NAME = os.getenv("ENVOY_SECRET_NAME", "envoy-oauth2-secrets")
logger.info("ENVOY_SECRET_NAME=%s", ENVOY_SECRET_NAME)


componentname_label = os.getenv("COMPONENTNAME_LABEL", "oda.tmforum.org/componentName")

INSTANCES = {}


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, memo: kopf.Memo, **_):
    settings.peering.priority = 136
    settings.peering.name = "oa2envf"
    settings.watching.server_timeout = 1 * 60
    memo.counter = 0


def cavas_info_instance() -> ServiceInventoryAPI:
    if "svc_inv" not in INSTANCES:
        INSTANCES["svc_inv"] = ServiceInventoryAPI(CANVAS_INFO_ENDPOINT)
    return INSTANCES["svc_inv"]


def quick_get_comp_name(body):
    return safe_get(None, body, "metadata", "labels", componentname_label)


def half_anon(secret):
    if secret == None:
        return None
    if len(secret) < 6:
        return "****"
    return f"{secret[:2]}****{secret[-2:]}"


def b64d(enc_text: str):
    return base64.b64decode(enc_text).decode()


def b64e(text: str):
    return base64.b64encode(text.encode()).decode()


jinja2_env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")), autoescape=select_autoescape())


def create_sds_secret_yaml(client_secret):
    template = jinja2_env.get_template("sds_secret.yaml.jinja2")
    result = template.render(
        client_secret=client_secret,
    )
    return result


def url_hostname(url_str: str):
    url = urllib.parse.urlparse(url_str)
    return url.hostname


def url_port(url_str: str):
    url = urllib.parse.urlparse(url_str)
    result = url.port
    if result is None:
        if url.scheme == "https":
            result = 443
        elif url.scheme == "http":
            result = 80
        else:
            raise ValueError(f"unhandled scheme in token_endpoint '{url_str}'")
    return result


def create_envoyfilter_yaml(component_name, client_id, token_endpoint):

    token_endpoint_hostname = url_hostname(token_endpoint)
    token_endpoint_port = url_port(token_endpoint)

    template = jinja2_env.get_template("envoyfilter.yaml.jinja2")
    result = template.render(
        component_name=component_name,
        client_id=client_id,
        token_endpoint=token_endpoint,
        token_endpoint_hostname=token_endpoint_hostname,
        token_endpoint_port=token_endpoint_port,
    )
    return result


def create_serviceentry_yaml(host_name_list):
    template = jinja2_env.get_template("serviceentry.yaml.jinja2")
    result = template.render(host_name_list=host_name_list)
    return result


def create_destinationrule_yaml(comp_name, dependency_name, hostname):
    template = jinja2_env.get_template("destinationrule.yaml.jinja2")
    result = template.render(comp_name=comp_name, depapi_name=dependency_name, target_host=hostname)
    return result


def read_secret(namespace, secret_name):
    v1 = kubernetes.client.CoreV1Api()
    try:
        sec = v1.read_namespaced_secret(secret_name, namespace)
        return sec
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            return None
        raise e


def read_configmap(namespace, configmap_name):
    v1 = kubernetes.client.CoreV1Api()
    try:
        cm = v1.read_namespaced_config_map(configmap_name, namespace)
        return cm
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            return None
        raise e


def read_serviceentry(namespace):
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        serviceentry = custom_objects_api.get_namespaced_custom_object(
            group="networking.istio.io",
            version="v1",
            namespace=namespace,
            plural="serviceentries",
            name="add-https",
        )
        return serviceentry
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            return None
        raise e


def update_secret(namespace, name, k8s_secret):
    v1 = kubernetes.client.CoreV1Api()
    return v1.patch_namespaced_secret(name, namespace, k8s_secret)


def update_configmap(namespace, name, k8s_cm):
    v1 = kubernetes.client.CoreV1Api()
    return v1.patch_namespaced_config_map(name, namespace, k8s_cm)


def read_credentials(namespace, comp_name):
    sec = read_secret(namespace, f"{comp_name}-secret")
    if sec is None:
        raise kopf.TemporaryError(f"client credentials for {comp_name} do not yet exist")
    client_id = b64d(sec.data["client_id"])
    client_secret = b64d(sec.data["client_secret"])
    return (client_id, client_secret)


def create_secret(namespace, name, data):
    # data_b64values = {kv[0]: b64e(kv[1]) for kv in data_plainvalues.items()}
    secret = kubernetes.client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        data=data,
    )
    v1 = kubernetes.client.CoreV1Api()
    return v1.create_namespaced_secret(namespace=namespace, body=secret)


def create_configmap(namespace, name, data):
    cm = kubernetes.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        data=data,
    )
    v1 = kubernetes.client.CoreV1Api()
    return v1.create_namespaced_config_map(namespace=namespace, body=cm)


@logwrapper
def add_client_secrets_to_SDS(logw: LogWrapper, namespace, comp_name):
    """
    demo-b-productcatalogmanagement-secret:

        data:
          client_id: BASE64ENCODE(demo-b-productcatalogmanagement)
          client_secret: BASE64ENCODE(eeB...1OO)


    envoy-oauth2-secrets:

        data:
          demo-a-productcatalogmanagement.yaml: ...
          ...
          demo-b-productcatalogmanagement.yaml: BASE64ENCODE(
                resources:
                - "@type": "type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.Secret"
                  name: clientsecret
                  generic_secret:
                    secret:
                      inline_string: "eeB...1OO"
            )

    """
    logw.debug(f"adding client secrets to {ENVOY_SECRET_NAME}", f"{namespace}:{comp_name}")
    (client_id, client_secret) = read_credentials(namespace, comp_name)
    logw.debug("client_id", client_id)
    logw.debug("client_secret", half_anon(client_secret))

    yaml_filename = f"{comp_name}.yaml"
    yaml_content = create_sds_secret_yaml(client_secret)
    b64_yaml_content = b64e(yaml_content)

    envoy_secret_name = ENVOY_SECRET_NAME
    envoy_secret = read_secret(namespace, envoy_secret_name)
    if envoy_secret is None:
        logw.info(f"creating {ENVOY_SECRET_NAME} with client credentials", yaml_filename)
        create_secret(namespace, envoy_secret_name, {yaml_filename: b64_yaml_content})
    else:
        if yaml_filename in envoy_secret.data and envoy_secret.data[yaml_filename] == b64_yaml_content:
            logw.debug("credentials unchanged", yaml_filename)
        else:
            logw.info(f"updating client credentials in {ENVOY_SECRET_NAME}", yaml_filename)
            envoy_secret.data[yaml_filename] = b64_yaml_content
            update_secret(namespace, envoy_secret_name, envoy_secret)


@logwrapper
def add_url_to_dependency_configmap(logw, namespace, comp_name, dependency_name, url):
    url = url.replace("https://", "http://")
    dependency_configmap = f"deps-{comp_name}"
    env_name = dependency_name.upper()
    env_name = re.sub("[^A-Z0-9]+", "", env_name)
    env_name = f"DEPENDENCY_URL_{env_name}"
    logw.debug(f"adding {env_name} to dependency configmap {dependency_configmap}", url)
    cm = read_configmap(namespace, dependency_configmap)
    if cm is None:
        logw.info(f"creating {dependency_configmap} with env variable", f"{env_name}={url}")
        create_configmap(namespace, dependency_configmap, {env_name: url})
    else:
        if env_name in cm.data and cm.data[env_name] == url:
            logw.debug("envvar unchangedunchanged", env_name)
        else:
            logw.info(f"updating dependency configmap {dependency_configmap}", f"{env_name}={url}")
            cm.data[env_name] = url
            update_configmap(namespace, dependency_configmap, cm)


@logwrapper
def create_envoyfilter(logw, namespace, comp_name):
    envoyfilter_yaml = create_envoyfilter_yaml(comp_name, comp_name, OAUTH2_TOKEN_ENDPOINT)
    logw.debug(envoyfilter_yaml)
    body = yaml.safe_load(envoyfilter_yaml)
    create_customresource(logw, namespace, body)


@logwrapper
def create_serviceentry(logw, namespace, host_name_list):
    serviceentry_yaml = create_serviceentry_yaml(host_name_list)
    logw.debug(serviceentry_yaml)
    body = yaml.safe_load(serviceentry_yaml)
    create_customresource(logw, namespace, body)


@logwrapper
def create_destinationrule(logw, namespace, comp_name, dependency_name, url):
    hostname = url_hostname(url)
    destinationrule_yaml = create_destinationrule_yaml(comp_name, dependency_name, hostname)
    logw.debug(destinationrule_yaml)
    body = yaml.safe_load(destinationrule_yaml)
    create_customresource(logw, namespace, body)


@logwrapper
def add_host_to_serviceentry(logw, namespace, comp_name, url):
    hostname = url_hostname(url)
    serviceentry = read_serviceentry(namespace)
    hosts = safe_get([], serviceentry, "spec", "hosts")
    if hostname in hosts:
        logw.debug(f"hostname {hostname} already in serviceentry")
        return
    new_hosts = list(hosts)
    new_hosts.append(hostname)
    logw.info("adding host to serviceentry", hostname)
    create_serviceentry(logw, namespace, new_hosts)


def create_customresource(logw, namespace, body, plural=None):

    apiVersion = body["apiVersion"]
    kind = body["kind"]
    name = body["metadata"]["name"]

    group = apiVersion.split("/")[0]
    version = apiVersion.split("/")[1]

    if plural is None:
        plural = f"{kind.lower()}s"  # maybe a map is needed for handling special cases
        if plural.endswith("ys"):
            plural = f"{plural[:-2]}ies"
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logw.debug(f"Creating {kind} {name}.{namespace}", body)
        customObj = custom_objects_api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            body=body,
        )
        logw.debugInfo(f"{kind} Resource {name} created", customObj)

    except ApiException as e:
        if e.status != HTTP_CONFLICT:
            logw.warning(f"{kind} Exception creating {name}.{namespace}")
            logw.warning(f"{kind} Exception creating {e}")

            raise kopf.TemporaryError(f"Exception creating {kind} custom resource {name}.{namespace}.")
        else:
            # Conflict = try updating existing cr
            logw.info(f"{kind} already exists {name}.{namespace}")
            try:
                customObj = custom_objects_api.patch_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    name=name,
                    body=body,
                )
                logw.debug(f"{kind} Resource updated {name}.{namespace}", customObj)

            except ApiException as e:
                logw.warning(f"{kind} Exception updating {name}.{namespace}")
                logw.warning(f"{kind} Exception updating {e}")
                raise kopf.TemporaryError(f"Exception creating {kind} custom resource {name}.")


@logwrapper
def process_envoy_filter(logw: LogWrapper, namespace, id, comp_name, dependency_name, url):
    logw.debug("processing dependency", dependency_name)
    add_client_secrets_to_SDS(logw, namespace, comp_name)
    create_envoyfilter(logw, namespace, comp_name)
    add_host_to_serviceentry(logw, namespace, comp_name, url)
    create_destinationrule(logw, namespace, comp_name, dependency_name, url)
    add_url_to_dependency_configmap(logw, namespace, comp_name, dependency_name, url)


@kopf.timer(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, interval=60.0)
async def depapi_timer(meta, spec, body, namespace, labels, name, status, memo: kopf.Memo, **kwargs):

    logw = LogWrapper(handler_name="depapi_timer", function_name="depapi_timer")
    comp_name = quick_get_comp_name(body)
    logw.set(
        component_name=comp_name,
        resource_name=f"DepApi/{name}",
    )

    logw.debug(f"Timer called for {name}.{namespace}", body)

    memo.counter = memo.get("counter", 0) + 1
    logw.debug("memo counter", f"called {memo.counter} times")

    svc_info = cavas_info_instance()
    svcs = svc_info.list_services(component_name=comp_name)
    logw.debug(f"querying services for componenent {comp_name} from canvas-info-service", len(svcs))
    for svc in svcs:
        id = svc["id"]
        logw.debug(f'svcid {svc["id"]}', svc)
        componentName = svc["componentName"]
        dependencyName = svc["dependencyName"]
        url = svc["url"]
        if comp_name != componentName:
            logw.error(
                f"strange things are happening, in returned service id {id}, componentName does not match filter criteria",
                f"'{componentName}' != '{comp_name}'",
            )
            raise ValueError("componentName '{componentName}' does not match filter criteria '{comp_name}' for service id {id}")
        process_envoy_filter(logw, namespace, id, componentName, dependencyName, url)
