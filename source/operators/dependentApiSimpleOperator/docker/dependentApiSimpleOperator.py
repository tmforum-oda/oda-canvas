import kopf
import logging
import os

import kubernetes.client
from kubernetes.client.rest import ApiException


DEPAPI_GROUP = "oda.tmforum.org"
DEPAPI_VERSION = "v1beta3"
DEPAPI_PLURAL = "dependentapis"

COMP_GROUP = "oda.tmforum.org"
COMP_VERSION = "v1beta3"
COMP_PLURAL = "components"

API_PLURAL = "apis"

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


def get_depapi_spec(depapi_name, depapi_namespace):
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        depapi = api_instance.get_namespaced_custom_object(
            DEPAPI_GROUP, DEPAPI_VERSION, depapi_namespace, DEPAPI_PLURAL, depapi_name
        )
        return depapi["spec"]
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logger.error(
                f"setDependentAPIStatus: dependentapi {depapi_namespace}:{depapi_name} not found"
            )
        else:
            raise kopf.TemporaryError(
                f"setDependentAPIStatus: Exception in get_namespaced_custom_object: {e.body}"
            )


def get_expapi():
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        exp_apis = api_instance.list_cluster_custom_object(
            DEPAPI_GROUP, DEPAPI_VERSION, API_PLURAL, pretty="true"
        )
        return exp_apis
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logger.error(f"openAPIStatus: openapi not found")
        else:
            raise kopf.TemporaryError(
                f"openAPIStatus: Exception in list_cluster_custom_object: {e.body}"
            )


def get_depapi_url(depapi_name, depapi_namespace):
    dep_api = get_depapi_spec(depapi_name, depapi_namespace)
    depapi_specification = dep_api["specification"]
    exp_apis = get_expapi()
    for exp_api in exp_apis["items"]:
        if not ("specification" in exp_api["spec"].keys()):
            continue
        else:
            if (
                exp_api["spec"]["apitype"] == "openapi"
                and exp_api["spec"]["specification"][0] == depapi_specification
                and safe_get(False, exp_api,"status","implementation","ready") == True
            ):
                return exp_api["status"]["apiStatus"]["url"]
    return None


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
        url = get_depapi_url(name, namespace)
        if url != None:
            setDependentAPIStatus(namespace, name, url)


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
        raise kopf.TemporaryError(
            f"setDependentAPIStatus: Exception in patch_namespaced_custom_object: {e.body}"
        )


@kopf.on.field(
    DEPAPI_GROUP,
    DEPAPI_VERSION,
    DEPAPI_PLURAL,
    field="status.implementation",
    retries=5,
)
async def updateDepedentAPIReady(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """moved from componentOperator to here, to avoid inifite loops.
    If possible to configure kopf correctly it should be ported back to componentOperator

    Processes status updates to the *implementation* status in the child DependentAPI Custom resources, so that the Component status reflects a summary of all the childrens status.

    Args:
        * meta (Dict): The metadata from the DependentAPI resource
        * spec (Dict): The spec from the yaml DependentAPI resource showing the intent (or desired state)
        * status (Dict): The status from the DependentAPI resource showing the actual state.
        * body (Dict): The entire DependentAPI resource definition
        * namespace (String): The namespace for the DependentAPI resource
        * labels (Dict): The labels attached to the DependentAPI resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the DependentAPI resource

    Returns:
        No return value, nothing to write into the status.
    """
    logger.info(f"updateDepedentAPIReady called for {namespace}:{name}")
    logger.debug(
        f"updateDepedentAPIReady called for {namespace}:{name} with body {body}"
    )
    if "ready" in status["implementation"].keys():
        if status["implementation"]["ready"] == True:
            depapi_url = safe_get(None, status, "depapiStatus", "url")
            if "ownerReferences" in meta.keys():
                parent_component_name = meta["ownerReferences"][0]["name"]
                logger.info(f"reading component {parent_component_name}")
                try:
                    api_instance = kubernetes.client.CustomObjectsApi()
                    parent_component = api_instance.get_namespaced_custom_object(
                        COMP_GROUP,
                        COMP_VERSION,
                        namespace,
                        COMP_PLURAL,
                        parent_component_name,
                    )
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + parent_component_name
                        )
                    logger.error(e)
                    raise kopf.TemporaryError(
                        f"Exception when calling api_instance.get_namespaced_custom_object {parent_component_name}: {e.body}"
                    )
                # find the correct array entry to update either in coreDependentAPIs, managementAPIs or securityAPIs
                for key in range(len(parent_component["status"]["coreDependentAPIs"])):
                    if (
                        parent_component["status"]["coreDependentAPIs"][key]["uid"]
                        == meta["uid"]
                    ):
                        ready = parent_component["status"]["coreDependentAPIs"][key][
                            "ready"
                        ]
                        if (
                            parent_component["status"]["coreDependentAPIs"][key][
                                "ready"
                            ]
                            != True
                        ):  # avoid recursion
                            logger.info(
                                f"patching coreDependentAPI {key} in component {parent_component_name}"
                            )
                            parent_component["status"]["coreDependentAPIs"][key][
                                "ready"
                            ] = True
                            parent_component["status"]["coreDependentAPIs"][key][
                                "url"
                            ] = depapi_url
                            try:
                                api_response = (
                                    api_instance.patch_namespaced_custom_object(
                                        COMP_GROUP,
                                        COMP_VERSION,
                                        namespace,
                                        COMP_PLURAL,
                                        parent_component_name,
                                        parent_component,
                                    )
                                )
                            except ApiException as e:
                                raise kopf.TemporaryError(
                                    f"updateDepedentAPIReady: Exception in patch_namespaced_custom_object: {e.body}"
                                )
                        return
