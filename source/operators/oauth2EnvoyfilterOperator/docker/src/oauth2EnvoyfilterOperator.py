import kopf
import logging
import os

from service_inventory_client import ServiceInventoryAPI

from utils import safe_get
from log_wrapper import LogWrapper

# import kubernetes.client
# from kubernetes.client.rest import ApiException
# from log_wrapper import LogWrapper, logwrapper


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


@kopf.timer(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, interval=60.0)
async def depapi_timer(meta, spec, body, namespace, labels, name, status, memo: kopf.Memo, **kwargs):

    logw = LogWrapper(handler_name="depapi_timer", function_name="depapi_timer")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=f"DepApi/{name}",
    )

    logw.debugInfo(f"Timer called for {name}.{namespace}", body)

    memo.counter = memo.get("counter", 0) + 1
    logw.info("memo counter", f"called {memo.counter} times")

    svc_info = cavas_info_instance()
    svcs = svc_info.list_services()
    logw.info("querying services from canvas-info-service", len(svcs))
    for svc in svcs:
        logw.debugInfo(f'svcid {svc["id"]}', svc)
