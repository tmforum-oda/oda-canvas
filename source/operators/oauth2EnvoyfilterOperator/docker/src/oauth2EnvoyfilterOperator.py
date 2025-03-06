import kopf
import logging
import os

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


@logwrapper
def add_client_secrets_to_SDS(logw: LogWrapper, namespace, componentName):
    """
    demo-b-productcatalogmanagement-secret:

        data:
          client_id: BASE64ENCODE(demo-b-productcatalogmanagement)
          client_secret: BASE64ENCODE(eeB...1OO(


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
    logw.info("adding client secrets to envoy-oauth2-secrets", f"{namespace}:{componentName}")


@logwrapper
def process_envoy_filter(logw: LogWrapper, namespace, id, componentName, dependencyName, url):
    logw.info("processing dependency", dependencyName)
    add_client_secrets_to_SDS(logw, namespace, componentName)


@kopf.timer(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, interval=60.0)
async def depapi_timer(meta, spec, body, namespace, labels, name, status, memo: kopf.Memo, **kwargs):

    logw = LogWrapper(handler_name="depapi_timer", function_name="depapi_timer")
    comp_name = quick_get_comp_name(body)
    logw.set(
        component_name=comp_name,
        resource_name=f"DepApi/{name}",
    )

    logw.debugInfo(f"Timer called for {name}.{namespace}", body)

    memo.counter = memo.get("counter", 0) + 1
    logw.info("memo counter", f"called {memo.counter} times")

    svc_info = cavas_info_instance()
    svcs = svc_info.list_services(component_name=comp_name)
    logw.info("querying services for componenent {comp_name} from canvas-info-service", len(svcs))
    for svc in svcs:
        id = svc["id"]
        logw.debugInfo(f'svcid {svc["id"]}', svc)
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
