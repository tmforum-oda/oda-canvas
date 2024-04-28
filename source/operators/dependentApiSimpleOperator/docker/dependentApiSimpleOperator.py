import kopf
import logging
import os

import kubernetes.client
from kubernetes.client.rest import ApiException


DEPAPI_GROUP = "oda.tmforum.org"
DEPAPI_VERSION = "v1beta3"
DEPAPI_PLURAL = "dependentapis"

HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409


# https://kopf.readthedocs.io/en/stable/install/

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.INFO)
logger = logging.getLogger("DependentApiSimpleOperator")
logger.setLevel(int(logging_level))
logger.info("Logging set to %s", logging_level)
logger.debug("debug logging is on")


CICD_BUILD_TIME = os.getenv("CICD_BUILD_TIME")
GIT_COMMIT_SHA = os.getenv("GIT_COMMIT_SHA")
if CICD_BUILD_TIME:
    logger.info(f"CICD_BUILD_TIME=%s", CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f"GIT_COMMIT_SHA=%s", GIT_COMMIT_SHA)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.peering.priority = 110
    settings.peering.name = "dependentapi"
    settings.watching.server_timeout = 1 * 60


# -------------------------------------------------- HELPER FUNCTIONS -------------------------------------------------- #


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


# -------------------------------------------------- ---------------- -------------------------------------------------- #


def implementationReady(depapiBody):
    return safe_get(None, depapiBody, "status", "implementation", "ready")


# triggered when an oda.tmforum.org dependentapi resource is created or updated
@kopf.on.resume(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.create(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.update(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiCreate(
    meta, spec, status, body, namespace, labels, name, **kwargs
):

    logger.info(f"Create/Update  called with name {name} in namespace {namespace}")
    logger.debug(f"Create/Update  called with body: {body}")

    # Dummy implementation set dummy url and ready status
    if not implementationReady(body):  # avoid recursion
        setDependentAPIStatus(namespace, name, f"http://dummy.url/{name}")


# when an oda.tmforum.org api resource is deleted
@kopf.on.delete(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiDelete(
    meta, spec, status, body, namespace, labels, name, **kwargs
):

    logger.info(f"Delete         called with name {name} in namespace {namespace}")
    logger.debug(f"Delete         called with body: {body}")


def setDependentAPIStatus(namespace, name, url):
    """Helper function to update the url and implementation Ready status on the DependentAPI custom resource.

    Args:
        * namespace (String): namespace of the DependentAPI cutom resours
        * name (String): name of the DependentAPI cutom resours
        * url (String): communication parameter url

    Returns:
        No return value.
    """
    logger.info(
        f"setting implementation status to ready for dependent api {namespace}:{name}"
    )
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        depapi = api_instance.get_namespaced_custom_object(
            DEPAPI_GROUP, DEPAPI_VERSION, namespace, DEPAPI_PLURAL, name
        )
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logger.error(
                f"setDependentAPIStatus: dependentapi {namespace}:{name} not found"
            )
            raise e
        else:
            logger.error(
                f"setDependentAPIStatus: Exception in get_namespaced_custom_object: {e.body}"
            )
            raise kopf.TemporaryError(
                f"setDependentAPIStatus: Exception in get_namespaced_custom_object: {e.body}"
            )
    da_name = depapi["spec"]["name"]
    if not ("status" in depapi.keys()):
        depapi["status"] = {}
    if not ("depapiStatus" in depapi["status"]):
        depapi["status"]["depapiStatus"] = {}
    depapi["status"]["depapiStatus"]["url"] = url
    depapi["status"]["implementation"] = {"ready": True}
    try:
        api_response = api_instance.patch_namespaced_custom_object(
            DEPAPI_GROUP, DEPAPI_VERSION, namespace, DEPAPI_PLURAL, name, depapi
        )
    except ApiException as e:
        logger.error(
            f"setDependentAPIStatus: Exception in patch_namespaced_custom_object: {e.body}"
        )
        raise kopf.TemporaryError(
            f"setDependentAPIStatus: Exception in patch_namespaced_custom_object: {e.body}"
        )
