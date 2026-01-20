"""Kubernetes operator for ODA Component custom resources.

Normally this module is deployed as part of an ODA Canvas. It uses the kopf kubernetes operator framework (https://kopf.readthedocs.io/).
It registers handler functions for:

1. New ODA Components - to create, update or delete child API custom resources. see `coreAPIs <#componentOperator.componentOperator.coreAPIs>`_ and `securityAPIs <#componentOperator.componentOperator.securityAPIs>`_
2a. For status updates in the child API Custom resources, so that the Component status reflects a summary of all the childrens status. see `updateAPIStatus <#componentOperator.componentOperator.updateAPIStatus>`_ and `updateAPIReady <#componentOperator.componentOperator.updateAPIReady>`_
2b. For status updates in the child DependentAPI Custom resources, so that the Component status reflects a summary of all the childrens status. see `updateDependentAPIStatus <#componentOperator.componentOperator.updateDependentAPIStatus>`_ and `updateDependentAPIReady <#componentOperator.componentOperator.updateDependentAPIReady>`_
3. For new Services, Deployments, PersistentVolumeClaims and Jobs that have a oda.tmforum.org/componentName label. These resources are updated to become children of the ODA Component resource. see `adopt_deployment <#componentOperator.componentOperator.adopt_deployment>`_ , `adopt_persistentvolumeclaim <#componentOperator.componentOperator.adopt_persistentvolumeclaim>`_ , `adopt_job <#componentOperator.componentOperator.adopt_job>`_ and `adopt_service <#componentOperator.componentOperator.adopt_service>`_
"""

import kopf
import kubernetes.client
import logging
import traceback
from kubernetes.client.rest import ApiException
import os
import asyncio
from log_wrapper import LogWrapper, logwrapper

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger("ComponentOperator")
logger.setLevel(int(logging_level))
logger.info(f"Logging set to %s", logging_level)
logger.debug("debug logging active")

LogWrapper.set_defaultLogger(logger)

CICD_BUILD_TIME = os.getenv("CICD_BUILD_TIME")
GIT_COMMIT_SHA = os.getenv("GIT_COMMIT_SHA")
if CICD_BUILD_TIME:
    logger.info(f"CICD_BUILD_TIME=%s", CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f"GIT_COMMIT_SHA=%s", GIT_COMMIT_SHA)


# get namespace to monitor
component_namespace = os.environ.get("COMPONENT_NAMESPACE", "components")
logger.info(f"Monitoring namespace %s", component_namespace)

componentname_label = os.getenv("COMPONENTNAME_LABEL", "oda.tmforum.org/componentName")

# Constants
HTTP_CONFLICT = 409
HTTP_NOT_FOUND = 404
GROUP = "oda.tmforum.org"
VERSION = "v1"
EXPOSEDAPIS_PLURAL = "exposedapis"
EXPOSEDAPI_KIND = "ExposedAPI"
COMPONENTS_PLURAL = "components"

SECRETSMANAGEMENT_GROUP = "oda.tmforum.org"
SECRETSMANAGEMENT_VERSION = "v1"
SECRETSMANAGEMENT_PLURAL = "secretsmanagements"
SECRETSMANAGEMENT_KIND = "SecretsManagement"

IDENTITYCONFIG_GROUP = "oda.tmforum.org"
IDENTITYCONFIG_VERSION = "v1"
IDENTITYCONFIG_PLURAL = "identityconfigs"
IDENTITYCONFIG_KIND = "IdentityConfig"

DEPENDENTAPI_GROUP = "oda.tmforum.org"
DEPENDENTAPI_VERSION = "v1"
DEPENDENTAPI_PLURAL = "dependentapis"
DEPENDENTAPI_KIND = "DependentAPI"

IDENTITY_PROVIDER_NOT_SET = "Not set"

PUBLISHEDNOTIFICATIONS_PLURAL = "publishednotifications"
SUBSCRIBEDNOTIFICATIONS_PLURAL = "subscribednotifications"


# try to recover from broken watchers https://github.com/nolar/kopf/issues/1036
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60


@logwrapper
async def deleteExposedAPI(
    logw: LogWrapper, deleteExposedAPIName, componentName, status, namespace, inHandler
):
    """Helper function to delete API Custom objects.

    Args:
        * deleteExposedAPIName (String): Name of the API Custom Object to delete
        * componentName (String): Name of the component the API is linked to
        * status (Dict): The status from the yaml component envelope.
        * namespace (String): The namespace for the component

    Returns:
        No return value

    :meta private:
    """

    logw.info(f"Deleting API {deleteExposedAPIName}")
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        api_response = custom_objects_api.delete_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=namespace,
            plural=EXPOSEDAPIS_PLURAL,
            name=deleteExposedAPIName,
        )
        logw.debug(f"API response {api_response}")
    except ApiException as e:
        logw.error(
            f"Exception when calling CustomObjectsApi->delete_namespaced_custom_object {e}"
        )


@logwrapper
async def deleteDependentAPI(
    logw: LogWrapper, dependentAPIName, componentName, status, namespace, inHandler
):
    """Helper function to delete DependentAPI Custom objects.

    Args:
        * dependentAPIName (String): Name of the DependentAPI Custom Resource to delete
        * componentName (String): Name of the component the dependent API is linked to
        * status (Dict): The status from the yaml component envelope.
        * namespace (String): The namespace for the component
        * inHandler (String): The name of the handler that called this function

    Returns:
        No return value

    :meta private:
    """

    logw.info(f"Deleting DependentAPI {dependentAPIName}")

    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        dependentapi_response = custom_objects_api.delete_namespaced_custom_object(
            group=GROUP,
            version=DEPENDENTAPI_VERSION,
            namespace=namespace,
            plural=DEPENDENTAPI_PLURAL,
            name=dependentAPIName,
        )
        logw.debug(f"DependentAPI response {dependentapi_response}")
    except ApiException as e:
        logw.error(
            f"Exception when calling CustomObjectsApi->delete_namespaced_custom_object {e}"
        )


@logwrapper
async def deleteSecretsManagement(
    logw: LogWrapper, secretsManagementName, componentName, status, namespace, inHandler
):
    """Helper function to delete SecretsManagement Custom objects.

    Args:
        * secretsManagementName (String): Name of the SecretsManagement Custom Resource to delete
        * componentName (String): Name of the component the SecretsManagement is linked to
        * status (Dict): The status from the yaml component envelope.
        * namespace (String): The namespace for the component
        * inHandler (String): The name of the handler that called this function

    Returns:
        No return value

    :meta private:
    """

    logw.info(f"Deleting SecretsManagement {secretsManagementName}")
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        secretsmanagement_response = custom_objects_api.delete_namespaced_custom_object(
            group=GROUP,
            version=SECRETSMANAGEMENT_VERSION,
            namespace=namespace,
            plural=SECRETSMANAGEMENT_PLURAL,
            name=secretsManagementName,
        )
        logs.debug(f"SecretsManagement response {secretsmanagement_response}")
    except ApiException as e:
        logw.error(
            f"Exception when calling CustomObjectsApi->delete_namespaced_custom_object {e}"
        )


@logwrapper
async def deleteIdentityConfig(
    logw: LogWrapper, identityConfigName, componentName, status, namespace, inHandler
):
    """Helper function to delete IdentityConfig Custom objects.

    Args:
        * identityConfigName (String): Name of the IdentityConfig Custom Resource to delete
        * componentName (String): Name of the component the IdentityConfig is linked to
        * status (Dict): The status from the yaml component envelope.
        * namespace (String): The namespace for the component
        * inHandler (String): The name of the handler that called this function

    Returns:
        No return value

    :meta private:
    """

    logw.info(f"Deleting IdentityConfig {identityConfigName}")
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        identityconfig_response = custom_objects_api.delete_namespaced_custom_object(
            group=GROUP,
            version=IDENTITYCONFIG_VERSION,
            namespace=namespace,
            plural=IDENTITYCONFIG_PLURAL,
            name=identityConfigName,
        )
        logs.debug(f"IdentityConfig response {identityconfig_response}")
    except ApiException as e:
        logw.error(
            f"Exception when calling CustomObjectsApi->delete_namespaced_custom_object {e}"
        )


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


def quick_get_comp_name(body):
    return safe_get(None, body, "metadata", "labels", componentname_label)


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def coreAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **core function** part new or updated components.

    Processes the **core function** part of the component envelope and creates the child API resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The coreAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(handler_name="coreAPIs", function_name="coreAPIs")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("coreAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    apiChildren = (
        []
    )  # any existing API children of this component that have been patched
    oldCoreAPIs = (
        []
    )  # existing API children of this component (according to previous status)
    try:

        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if "coreAPIs" in status.keys():
                oldCoreAPIs = status["coreAPIs"]

            newCoreAPIs = spec["coreFunction"]["exposedAPIs"]
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldCoreAPIs:
                found = False
                for newAPI in newCoreAPIs:
                    logw.debug(
                        f"Comparing {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}"
                    )
                    if oldAPI["name"] == name + "-" + newAPI["name"].lower():
                        found = True
                        logw.info(f"Patching ExposedAPI {oldAPI['name']}")

                        resultStatus = await patchAPIResource(
                            logw, newAPI, namespace, name, "coreAPIs", "core"
                        )
                        apiChildren.append(resultStatus)
                if not found:
                    logw.info(f"Deleting ExposedAPI {oldAPI['name']}")
                    await deleteExposedAPI(
                        logw, oldAPI["name"], name, status, namespace, "coreAPIs"
                    )

        # get core APIS
        coreAPIs = spec["coreFunction"]["exposedAPIs"]
        logw.debug(f"Exposed API list {coreAPIs}")

        for coreAPI in coreAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logw.debug(
                    f"Comparing {processedAPI['name']} to {name + '-' + coreAPI['name'].lower()}"
                )

                if processedAPI["name"] == name + "-" + coreAPI["name"].lower():
                    alreadyProcessed = True
            if alreadyProcessed == False:
                logw.info(f"Calling createAPIResource {coreAPI['name']}")

                resultStatus = await createAPIResource(
                    logw, coreAPI, namespace, name, "coreAPIs", "core"
                )
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")

    # Update the parent's status.
    return apiChildren


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def managementAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **managementFunction** part new or updated components.

    Processes the **managementFunction** part of the component envelope and creates the child API resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The managementAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(handler_name="managementAPIs", function_name="managementAPIs")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("managementAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    apiChildren = []
    oldManagementAPIs = []
    try:

        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if "managementAPIs" in status.keys():
                oldManagementAPIs = status["managementAPIs"]

            newManagementAPIs = spec["managementFunction"]["exposedAPIs"]
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldManagementAPIs:
                found = False
                for newAPI in newManagementAPIs:
                    logw.debug(
                        f"Comparing {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}"
                    )

                    if oldAPI["name"] == name + "-" + newAPI["name"].lower():
                        found = True
                        resultStatus = await patchAPIResource(
                            logw,
                            newAPI,
                            namespace,
                            name,
                            "managementAPIs",
                            "management",
                        )
                        logw.info(f"Patching API {oldAPI['name']}")

                        apiChildren.append(resultStatus)
                if not found:
                    logw.info(f"Deleting API {oldAPI['name']}")

                    await deleteExposedAPI(
                        logw, oldAPI["name"], name, status, namespace, "managementAPIs"
                    )

        # get exposed APIS
        managementAPIs = spec["managementFunction"]["exposedAPIs"]
        logw.debug(f"Exposed API list {managementAPIs}")

        for managementAPI in managementAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logger.debug(
                    f"Comparing {processedAPI['name']} to {name + '-' + managementAPI['name'].lower()}"
                )
                logw.debug(
                    f"Comparing new APIs with status {processedAPI['name']} to {name + '-' + managementAPI['name'].lower()}"
                )

                if processedAPI["name"] == name + "-" + managementAPI["name"].lower():
                    alreadyProcessed = True

            if alreadyProcessed == False:
                logw.info(f"Calling createAPIResource {managementAPI['name']}")

                resultStatus = await createAPIResource(
                    logw, managementAPI, namespace, name, "managementAPIs", "management"
                )
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")

    # Update the parent's status.
    return apiChildren


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def securityAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **securityFunction** part new or updated components.

    Processes the **securityFunction** part of the component envelope and creates the child API resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The securityAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(handler_name="securityAPIs", function_name="securityAPIs")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("securityAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    apiChildren = []
    oldSecurityAPIs = []
    try:

        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if "securityAPIs" in status.keys():
                oldSecurityAPIs = status["securityAPIs"]
            newSecurityAPIs = spec["securityFunction"]["exposedAPIs"]
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldSecurityAPIs:
                found = False
                for newAPI in newSecurityAPIs:
                    logw.debug(
                        f"Comparing {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}"
                    )

                    if oldAPI["name"] == name + "-" + newAPI["name"].lower():
                        found = True
                        resultStatus = await patchAPIResource(
                            logw, newAPI, namespace, name, "securityAPIs", "security"
                        )
                        logw.info(f"Patching API {oldAPI['name']}")

                        apiChildren.append(resultStatus)
                if not found:
                    logw.info(f"Deleting API {oldAPI['name']}")

                    await deleteExposedAPI(
                        logw, oldAPI["name"], name, status, namespace, "securityAPIs"
                    )

        # get exposed APIS
        securityAPIs = spec["securityFunction"]["exposedAPIs"]
        logw.debug(f"Exposed API list {securityAPIs}")

        for securityAPI in securityAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logw.debug(
                    f"Comparing {processedAPI['name']} to {name + '-' + securityAPI['name'].lower()}"
                )

                if processedAPI["name"] == name + "-" + securityAPI["name"].lower():
                    alreadyProcessed = True

            if alreadyProcessed == False:
                logw.debug(f"Calling createAPIResource {securityAPI['name']}")

                resultStatus = await createAPIResource(
                    logw, securityAPI, namespace, name, "securityAPIs", "security"
                )
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")

    # Update the parent's status.
    return apiChildren


# -------------------------------------------------- HELPER FUNCTIONS -------------------------------------------------- #
def entryExists(dictionary, key, value):
    for entry in dictionary:
        if key in entry:
            if entry[key] == value:
                return True
    return False


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


def find_entry_by_keyvalue(entries, key, value):
    for entry in entries:
        if key in entry:
            if entry[key] == value:
                return entry
    return None


def find_entry_by_name(entries, name):
    return find_entry_by_keyvalue(entries, "name", name)


# -------------------------------------------------- ---------------- -------------------------------------------------- #


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def coreDependentAPIs(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """Handler function for **coreFunction** part new or updated components.

    Processes the **coreFunction.dependentAPIs** part of the component envelope and creates the child DependentAPI resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The coreDependentAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(
        handler_name="coreDependentAPIs", function_name="coreDependentAPIs"
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("coreDependentAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    dependentAPIChildren = []
    dapi_base_name = name

    try:
        oldCoreDependentAPIs = []
        if status:  # if status exists (i.e. this is not a new component)
            oldCoreDependentAPIs = safe_get([], status, "coreDependentAPIs")

        newCoreDependentAPIs = safe_get([], spec, "coreFunction", "dependentAPIs")

        # compare entries by name
        for oldCoreDependentAPI in oldCoreDependentAPIs:
            cr_name = oldCoreDependentAPI["name"]
            dapi_name = cr_name[len(dapi_base_name) + 1 :]
            print(dapi_name)
            newCoreDependentAPI = find_entry_by_name(newCoreDependentAPIs, dapi_name)
            if not newCoreDependentAPI:
                logw.info(f"Deleting DependentAPI {cr_name}")

                await deleteDependentAPI(
                    logw, cr_name, name, status, namespace, "coreDependentAPIs"
                )
            else:
                # TODO[FH] implement check for update
                logw.info(f"TODO: Update DependentAPI {cr_name}")
                dependentAPIChildren.append(oldCoreDependentAPI)

        for newCoreDependentAPI in newCoreDependentAPIs:
            dapi_name = newCoreDependentAPI["name"]
            cr_name = f"{dapi_base_name}-{dapi_name}"
            print(dapi_name)
            oldCoreDependentAPI = find_entry_by_name(oldCoreDependentAPIs, cr_name)
            if not oldCoreDependentAPI:
                logw.info(f"Calling createDependentAPI {cr_name}")
                resultStatus = await createDependentAPIResource(
                    logw,
                    newCoreDependentAPI,
                    namespace,
                    name,
                    cr_name,
                    "coreDependentAPIs",
                    "core",
                )
                dependentAPIChildren.append(resultStatus)
            # else: already handled above

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
    logw.info(f"result for status {dependentAPIChildren}")

    # Update the parent's status.
    return dependentAPIChildren


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def managementDependentAPIs(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """Handler function for **managementFunction** part new or updated components.

    Processes the **managementFunction.dependentAPIs** part of the component envelope and creates the child DependentAPI resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The managementDependentAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(
        handler_name="managementDependentAPIs", function_name="managementDependentAPIs"
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("managementDependentAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    dependentAPIChildren = []
    dapi_base_name = name

    try:
        oldManagementDependentAPIs = []
        if status:  # if status exists (i.e. this is not a new component)
            oldManagementDependentAPIs = safe_get([], status, "managementDependentAPIs")

        newManagementDependentAPIs = safe_get(
            [], spec, "managementFunction", "dependentAPIs"
        )

        # compare entries by name
        for oldManagementDependentAPI in oldManagementDependentAPIs:
            cr_name = oldManagementDependentAPI["name"]
            dapi_name = cr_name[len(dapi_base_name) + 1 :]
            print(dapi_name)
            newManagementDependentAPI = find_entry_by_name(
                newManagementDependentAPIs, dapi_name
            )
            if not newManagementDependentAPI:
                logw.info(f"Deleting DependentAPI {cr_name}")

                await deleteDependentAPI(
                    logw, cr_name, name, status, namespace, "managementDependentAPIs"
                )
            else:
                # TODO[FH] implement check for update
                logw.info(f"TODO: Update DependentAPI {cr_name}")
                dependentAPIChildren.append(oldManagementDependentAPI)

        for newManagementDependentAPI in newManagementDependentAPIs:
            dapi_name = newManagementDependentAPI["name"]
            cr_name = f"{dapi_base_name}-{dapi_name}"
            print(dapi_name)
            oldManagementDependentAPI = find_entry_by_name(
                oldManagementDependentAPIs, cr_name
            )
            if not oldManagementDependentAPI:
                logw.info(f"Calling createDependentAPI {cr_name}")
                resultStatus = await createDependentAPIResource(
                    logw,
                    newManagementDependentAPI,
                    namespace,
                    name,
                    cr_name,
                    "managementDependentAPIs",
                    "management",
                )
                dependentAPIChildren.append(resultStatus)
            # else: already handled above

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
    logw.info(f"result for status {dependentAPIChildren}")

    # Update the parent's status.
    return dependentAPIChildren


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def securityDependentAPIs(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """Handler function for **securityFunction** part new or updated components.

    Processes the **securityFunction.dependentAPIs** part of the component envelope and creates the child DependentAPI resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The securityDependentAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(
        handler_name="securityDependentAPIs", function_name="securityDependentAPIs"
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("securityDependentAPIs handler called", body)

    # del unused-arguments for linting
    del meta, labels, kwargs

    dependentAPIChildren = []
    dapi_base_name = name

    try:
        oldSecurityDependentAPIs = []
        if status:  # if status exists (i.e. this is not a new component)
            oldSecurityDependentAPIs = safe_get([], status, "securityDependentAPIs")

        newSecurityDependentAPIs = safe_get(
            [], spec, "securityFunction", "dependentAPIs"
        )

        # compare entries by name
        for oldSecurityDependentAPI in oldSecurityDependentAPIs:
            cr_name = oldSecurityDependentAPI["name"]
            dapi_name = cr_name[len(dapi_base_name) + 1 :]
            print(dapi_name)
            newSecurityDependentAPI = find_entry_by_name(
                newSecurityDependentAPIs, dapi_name
            )
            if not newSecurityDependentAPI:
                logw.info(f"Deleting DependentAPI {cr_name}")

                await deleteDependentAPI(
                    logw, cr_name, name, status, namespace, "securityDependentAPIs"
                )
            else:
                # TODO[FH] implement check for update
                logw.info(f"TODO: Update DependentAPI {cr_name}")
                dependentAPIChildren.append(oldSecurityDependentAPI)

        for newSecurityDependentAPI in newSecurityDependentAPIs:
            dapi_name = newSecurityDependentAPI["name"]
            cr_name = f"{dapi_base_name}-{dapi_name}"
            print(dapi_name)
            oldSecurityDependentAPI = find_entry_by_name(
                oldSecurityDependentAPIs, cr_name
            )
            if not oldSecurityDependentAPI:
                logw.info(f"Calling createDependentAPI {cr_name}")
                resultStatus = await createDependentAPIResource(
                    logw,
                    newSecurityDependentAPI,
                    namespace,
                    name,
                    cr_name,
                    "securityDependentAPIs",
                    "security",
                )
                dependentAPIChildren.append(resultStatus)
            # else: already handled above

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
    logw.info(f"result for status {dependentAPIChildren}")

    # Update the parent's status.
    return dependentAPIChildren


@kopf.on.update(
    GROUP,
    VERSION,
    COMPONENTS_PLURAL,
    field="status.summary/status.deployment_status",
    value="In-Progress-IDConfOp",
    retries=5,
)
async def identityConfig(
    meta, spec, status, body, namespace, labels, name, old, new, **kwargs
):  # temporarily changed name
    """Handler function for **identityConfig** part of new or updated components.

    Processes the **identityConfig** part of the component envelope and creates the child IdentityConfig resource.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component
        * old (Dict): The old component (for updates)
        * new (Dict): The new component (for updates)

    Returns:
        Dict: The identityConfig status that is put into the component envelope status/identityConfig/status.summary/status.deployment_status field.
    """
    logw = LogWrapper(handler_name="identityconfig", function_name="identityconfig")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("identityconfig handler called", body)

    # del unused-arguments for linting
    del meta, status, old, new, labels, kwargs

    try:
        # check if the identityConfig resource already exists
        identityConfigName = name
        identityConfig = None

        custom_objects_api = kubernetes.client.CustomObjectsApi()
        try:
            identityConfig = custom_objects_api.get_namespaced_custom_object(
                group=IDENTITYCONFIG_GROUP,
                version=IDENTITYCONFIG_VERSION,
                namespace=namespace,
                plural=IDENTITYCONFIG_PLURAL,
                name=identityConfigName,
            )
            logw.info(f"IdentityConfig resource already exists")
            logw.debug(f"IdentityConfig resource {identityConfig}")
            identityConfigStatus = "identityConfig resource already exists"
        except ApiException as e:
            if e.status == HTTP_NOT_FOUND:
                logw.info(f"IdentityConfig resource does not exist")
                logw.debug(f"Creating IdentityConfig {identityConfigName}")
            else:
                logw.error(
                    f"Exception when calling CustomObjectsApi->get_namespaced_custom_object {e}"
                )
                raise kopf.TemporaryError(e)

        if identityConfig:
            # compare existing identityConfig and Patch resource if it has changed
            resourceChanged = False
            if (
                identityConfig["spec"]["canvasSystemRole"]
                != spec["securityFunction"]["canvasSystemRole"]
            ):
                identityConfig["spec"]["canvasSystemRole"] = spec["securityFunction"][
                    "canvasSystemRole"
                ]
                resourceChanged = True
                logw.info(f"Updating canvasSystemRole")

            if "componentRole" in spec["securityFunction"]:
                if "componentRole" in identityConfig["spec"]:
                    if (
                        identityConfig["spec"]["componentRole"]
                        != spec["securityFunction"]["componentRole"]
                    ):
                        identityConfig["spec"]["componentRole"] = spec[
                            "securityFunction"
                        ]["componentRole"]
                        resourceChanged = True
                        logw.info(f"Updating componentRole")
                else:
                    identityConfig["spec"]["componentRole"] = spec["securityFunction"][
                        "componentRole"
                    ]
                    resourceChanged = True
                    logw.info(f"Adding componentRole")
            else:
                if "componentRole" in identityConfig["spec"]:
                    del identityConfig["spec"]["componentRole"]
                    resourceChanged = True
                    logw.info(f"Removing componentRole")

            if resourceChanged:
                try:
                    identityConfig = custom_objects_api.patch_namespaced_custom_object(
                        group=IDENTITYCONFIG_GROUP,
                        version=IDENTITYCONFIG_VERSION,
                        namespace=namespace,
                        plural=IDENTITYCONFIG_PLURAL,
                        name=identityConfigName,
                        body=identityConfig,
                    )
                    logw.info(f"IdentityConfig resource patched")
                    logw.debug(f"IdentityConfig resource {identityConfig}")
                except ApiException as e:
                    logw.error(
                        f"Exception when calling CustomObjectsApi->patch_namespaced_custom_object {e}"
                    )
                    raise kopf.TemporaryError(e)
                return "identityConfig resource updated"
            else:
                return "identityConfig resource unchanged"

        else:  # identityConfig does not exist

            identityConfigResource = {
                "canvasSystemRole": spec["securityFunction"]["canvasSystemRole"]
            }
            if "componentRole" in spec["securityFunction"]:
                identityConfigResource["componentRole"] = spec["securityFunction"][
                    "componentRole"
                ]
                logw.info(f"Adding componentRole statically defined roles")

            # check if the component has a partyrole API
            foundPartyRole = False
            if "exposedAPIs" in spec["securityFunction"]:
                for api in spec["securityFunction"]["exposedAPIs"]:
                    if "partyrole" in api["name"]:
                        partyRoleAPI = {}
                        partyRoleAPI["implementation"] = api["implementation"]
                        partyRoleAPI["path"] = api["path"]
                        partyRoleAPI["port"] = api["port"]
                        foundPartyRole = True
                        break
            if foundPartyRole:
                logw.info(f"Adding componentRole-PartyRole dynamically defined roles")
                # get the partyrole API and add to the identityConfig
                identityConfigResource["partyRoleAPI"] = partyRoleAPI

            # check if the component has a userrolesandpermissions API
            foundPermissionSpecificationSet = False
            if "exposedAPIs" in spec["securityFunction"]:
                for api in spec["securityFunction"]["exposedAPIs"]:
                    if "userrolesandpermissions" in api["name"]:
                        permissionSpecificationSetAPI = {}
                        permissionSpecificationSetAPI["implementation"] = api[
                            "implementation"
                        ]
                        permissionSpecificationSetAPI["path"] = api["path"]
                        permissionSpecificationSetAPI["port"] = api["port"]
                        foundPermissionSpecificationSet = True
                        break
            if foundPermissionSpecificationSet:
                logw.info(
                    f"Adding componentRole-PermissionSpecificationSet dynamically defined roles"
                )
                # get the permissionSpecificationSet API and add to the identityConfig
                identityConfigResource["permissionSpecificationSetAPI"] = (
                    permissionSpecificationSetAPI
                )

            # create the identityConfig resource (or patch existing resource if it is present)
            logw.debugInfo(
                f"Calling createIdentityConfig {identityConfigName}",
                f"Calling createIdentityConfig with resource {identityConfigResource}",
            )

            resultStatus = await createIdentityConfigResource(
                logw, identityConfigResource, namespace
            )
            logw.info(f"createIdentityConfigResource returned {resultStatus}")

            return "identityConfig resource created"
    except kopf.TemporaryError as e:
        raise e  # propagate
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
        raise kopf.TemporaryError(e)  # allow the operator to retry


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def securitySecretsManagement(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """Handler function for **securityFunction** part new or updated components.

    Processes the **securityFunction.secretsManagement** part of the component envelope and creates, if requested, the child SecretsManagement resource.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The securitySecretsManagement status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(
        handler_name="securitySecretsManagement",
        function_name="securitySecretsManagement",
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("securitySecretsManagement handler called", body)

    secretsManagementStatus = {}
    sman_name = f"sman_{name}"

    try:
        oldSecuritySecretsManagement = {}
        if status:  # if status exists (i.e. this is not a new component)
            oldSecuritySecretsManagement = safe_get(
                {}, status, "securitySecretsManagement"
            )
        logw.debug(f"Old SecretsManagement {oldSecuritySecretsManagement}")

        newSecuritySecretsManagement = safe_get(
            {}, spec, "securityFunction", "secretsManagement"
        )
        logw.debug(f"New SecretsManagement {newSecuritySecretsManagement}")

        if oldSecuritySecretsManagement != {} and newSecuritySecretsManagement == {}:
            logw.info(f"Deleting SecretsManagement {sman_name}")
            await deleteSecretsManagement(
                logw, sman_name, name, status, namespace, "securitySecretsManagement"
            )

        if oldSecuritySecretsManagement == {} and newSecuritySecretsManagement != {}:
            logw.info(f"Calling createSecretsManagement {sman_name}")
            resultStatus = await createSecretsManagementResource(
                logw,
                newSecuritySecretsManagement,
                namespace,
                name,
                "securitySecretsManagement",
            )
            secretsManagementStatus = resultStatus

        if oldSecuritySecretsManagement != {} and newSecuritySecretsManagement != {}:
            # TODO[FH] implement check for update
            secretsManagementStatus = newSecuritySecretsManagement

    except kopf.TemporaryError as e:
        raise e  # propagate
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
        raise kopf.TemporaryError(e)  # allow the operator to retry
    logw.info(f"result for status {secretsManagementStatus}")

    # Update the parent's status.
    return secretsManagementStatus


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def publishedEvents(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **publishedEvents** part of new or updated components.

    Processes the **publishedEvents** part of the component envelope and creates the child API resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The publishedEvents status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(handler_name="publishedEvents", function_name="publishedEvents")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("publishedEvents handler called", body)

    pubChildren = []
    try:

        # get security exposed APIS
        try:
            publishedEvents = spec["eventNotification"]["publishedEvents"]
            pubChildren = await asyncio.gather(
                *[
                    createPublishedNotificationResource(
                        logw, publishedEvent, namespace, name, "publishedEvents"
                    )
                    for publishedEvent in publishedEvents
                ]
            )
        except KeyError:
            logw.warning(f"component {name} has no publishedEvents property")

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")

    return pubChildren


@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def subscribedEvents(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **subscribedEvents** part of new or updated components.

    Processes the **subscribedEvents** part of the component envelope and creates the child API resources.

    Args:
        * meta (Dict): The metadata from the yaml component envelope
        * spec (Dict): The spec from the yaml component envelope showing the intent (or desired state)
        * status (Dict): The status from the yaml component envelope showing the actual state.
        * body (Dict): The entire yaml component envelope
        * namespace (String): The namespace for the component
        * labels (Dict): The labels attached to the component. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the component

    Returns:
        Dict: The subscribedEvents status that is put into the component envelope status field.

    :meta public:
    """
    logw = LogWrapper(handler_name="subscribedEvents", function_name="subscribedEvents")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("subscribedEvents handler called", body)

    subChildren = []
    try:

        # get security exposed APIS
        try:
            subscribedEvents = spec["eventNotification"]["subscribedEvents"]
            subChildren = await asyncio.gather(
                *[
                    createSubscribedNotificationResource(
                        logw, subscribedEvent, namespace, name, "subscribedEvents"
                    )
                    for subscribedEvent in subscribedEvents
                ]
            )
        except KeyError:
            logw.warning(f"component {name} has no subscribedEvents property")

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e)  # allow the operator to retry
    except Exception as e:
        logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")

    return subChildren


def constructAPIResourcePayload(inExposedAPI, segment=None):
    """Helper function to create payloads for API Custom objects.

    Args:
        * inExposedAPI (Dict): The API spec
        * segment (str): The segment (core, management, or security)

    Returns:
        API Custom object (Dict)

    :meta private:
    """
    APIResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": EXPOSEDAPI_KIND,
        "metadata": {},
        "spec": {},
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(APIResource)

    newName = (
        APIResource["metadata"]["ownerReferences"][0]["name"]
        + "-"
        + inExposedAPI["name"]
    ).lower()
    APIResource["metadata"]["name"] = newName
    # ungroup the gatewayConfiguration properties
    if "gatewayConfiguration" in inExposedAPI.keys():
        # for each property in inExposedAPI["spec"]["gatewayConfiguration"] add it to the inExposedAPI
        for key, value in inExposedAPI["gatewayConfiguration"].items():
            inExposedAPI[key] = value
        del inExposedAPI["gatewayConfiguration"]
    APIResource["spec"] = inExposedAPI
    if "developerUI" in inExposedAPI.keys():
        APIResource["spec"]["developerUI"] = inExposedAPI["developerUI"]
    # Add segment to spec if provided
    if segment:
        APIResource["spec"]["segment"] = segment
    return APIResource


def constructDependentAPIResourcePayload(inDependentAPI, cr_name, segment=None):
    """Helper function to create payloads for DependentAPI Custom objects.

    Args:
        * inDependentAPI (Dict): The DependentAPI spec
        * cr_name custom resource name of the dependent api
        * segment (str): The segment (core, management, or security)

    Returns:
        DependentAPI Custom object (Dict)

    :meta private:
    """
    DependentAPIResource = {
        "apiVersion": GROUP + "/" + DEPENDENTAPI_VERSION,
        "kind": DEPENDENTAPI_KIND,
        "metadata": {},
        "spec": {},
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(DependentAPIResource)
    newName = DependentAPIResource["metadata"]["ownerReferences"][0]["name"]
    # DependentAPIResource['metadata']['name'] = f"{newName}-{dapi_name}"
    DependentAPIResource["metadata"]["name"] = cr_name
    DependentAPIResource["spec"] = inDependentAPI
    # Add segment to spec if provided
    if segment:
        DependentAPIResource["spec"]["segment"] = segment
    return DependentAPIResource


def constructSecretsManagementResourcePayload(inSecretsManagement):
    """Helper function to create payloads for SecretsManagement Custom objects.

    Args:
        * inSecretsManagement (Dict): The SecretsManagement spec

    Returns:
        SecretsManagement Custom object (Dict)

    :meta private:
    """
    SecretsManagementResource = {
        "apiVersion": GROUP + "/" + SECRETSMANAGEMENT_VERSION,
        "kind": SECRETSMANAGEMENT_KIND,
        "metadata": {},
        "spec": {},
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(SecretsManagementResource)
    newName = SecretsManagementResource["metadata"]["ownerReferences"][0]["name"]
    SecretsManagementResource["metadata"]["name"] = newName
    SecretsManagementResource["spec"] = inSecretsManagement
    return SecretsManagementResource


def constructIdentityConfigResourcePayload(inIdentityConfig):
    """Helper function to create payloads for IdentityConfig Custom objects.

    Args:
        * inIdentityConfig (Dict): The IdentityConfig spec

    Returns:
        IdentityConfig Custom object (Dict)

    :meta private:
    """
    IdentityConfigResource = {
        "apiVersion": GROUP + "/" + IDENTITYCONFIG_VERSION,
        "kind": IDENTITYCONFIG_KIND,
        "metadata": {},
        "spec": {},
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(IdentityConfigResource)
    newName = IdentityConfigResource["metadata"]["ownerReferences"][0]["name"]
    IdentityConfigResource["metadata"]["name"] = newName
    IdentityConfigResource["spec"] = inIdentityConfig
    return IdentityConfigResource


@logwrapper
async def patchAPIResource(
    logw: LogWrapper, inExposedAPI, namespace, name, inHandler, segment=None
):
    """Helper function to patch API Custom objects.

    Args:
        * inExposedAPI (Dict): The API definition
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource
        * inHandler (String): The name of the handler that called this function
        * segment (String): The segment (core, management, or security)

    Returns:
        Dict with updated API definition including uuid of the API resource and ready status.

    :meta private:
    """
    logw.debug(f"patchAPIResource {inExposedAPI} ")

    APIResource = constructAPIResourcePayload(inExposedAPI, segment)

    apiReadyStatus = False
    returnAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        # only patch if the API resource spec has changed

        # get current api resource and compare it to APIResource
        apiObj = custom_objects_api.get_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=namespace,
            plural=EXPOSEDAPIS_PLURAL,
            name=APIResource["metadata"]["name"],
        )

        if not (APIResource["spec"] == apiObj["spec"]):
            # log the difference
            logw.debug(f"Comparing old API {APIResource['spec']}")
            logw.debug(f"Comparing new API {apiObj['spec']}")

            apiObj = custom_objects_api.patch_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=namespace,
                plural=EXPOSEDAPIS_PLURAL,
                name=APIResource["metadata"]["name"],
                body=APIResource,
            )
            apiReadyStatus = apiObj["status"]["implementation"]["ready"]
            logw.debugInfo(
                f"API Resource patched {APIResource["metadata"]["name"]}", apiObj
            )

        if "status" in apiObj.keys() and "apiStatus" in apiObj["status"].keys():
            returnAPIObject = apiObj["status"]["apiStatus"]
            returnAPIObject["uid"] = apiObj["metadata"]["uid"]
            if "implementation" in apiObj["status"].keys():
                returnAPIObject["ready"] = apiObj["status"]["implementation"]["ready"]
        else:
            returnAPIObject = {
                "name": APIResource["metadata"]["name"],
                "uid": apiObj["metadata"]["uid"],
                "ready": apiReadyStatus,
            }

    except ApiException as e:
        logw.error(f"API Exception patching {APIResource}")

        raise kopf.TemporaryError("Exception patching API custom resource.")
    return returnAPIObject


@logwrapper
async def createAPIResource(
    logw: LogWrapper, inExposedAPI, namespace, name, inHandler, segment=None
):
    """Helper function to create or update API Custom objects.

    Args:
        * inExposedAPI (Dict): The API definition
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource
        * inHandler (String): The name of the handler calling this function
        * segment (String): The segment (core, management, or security)

    Returns:
        Dict with API definition including uuid of the API resource and ready status.

    :meta private:
    """
    logw.debug(f"createAPIResource {inExposedAPI} ")

    APIResource = constructAPIResourcePayload(inExposedAPI, segment)

    apiReadyStatus = False
    returnAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logw.info(f"Creating ExposedAPI Custom Object {APIResource}")

        apiObj = custom_objects_api.create_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=namespace,
            plural=EXPOSEDAPIS_PLURAL,
            body=APIResource,
        )
        logw.debugInfo(
            f"API Resource created {APIResource["metadata"]["name"]}", apiObj
        )
        returnAPIObject = {
            "name": APIResource["metadata"]["name"],
            "uid": apiObj["metadata"]["uid"],
            "ready": apiReadyStatus,
        }

    except ApiException as e:
        logw.warning(f"API Exception creating {APIResource}")
        logw.warning(f"Exception {e}")

        raise kopf.TemporaryError("Exception creating API custom resource.")
    return returnAPIObject


@logwrapper
async def createDependentAPIResource(
    logw: LogWrapper,
    inDependentAPI,
    namespace,
    comp_name,
    cr_name,
    inHandler,
    segment=None,
):
    """Helper function to create or update API Custom objects.

    Args:
        * inDependentAPI (Dict): The DependentAPI definition
        * namespace (String): The namespace for the Component and API
        * cr_name (String): The name of the dependent API custom resource
        * inHandler (String): The name of the handler calling this function
        * segment (String): The segment (core, management, or security)

    Returns:
        Dict with DependentAPI definition including uuid of the DependentAPI resource and ready status.

    :meta private:
    """
    logw.debug(f"createDependentAPIResource {inDependentAPI} ")

    DependentAPIResource = constructDependentAPIResourcePayload(
        inDependentAPI, cr_name, segment
    )

    dependentAPIReadyStatus = False
    returnDependentAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logw.info(f"Creating DependentAPI Custom Object {DependentAPIResource}")

        dependentAPIObj = custom_objects_api.create_namespaced_custom_object(
            group=GROUP,
            version=DEPENDENTAPI_VERSION,
            namespace=namespace,
            plural=DEPENDENTAPI_PLURAL,
            body=DependentAPIResource,
        )
        logw.debugInfo(
            f"DependentAPI Resource created {DependentAPIResource["metadata"]["name"]}",
            dependentAPIObj,
        )

    except ApiException as e:
        if e.status != HTTP_CONFLICT:
            logw.warning(f"DependentAPI Exception creating {DependentAPIResource}")
            logw.warning(f"DependentAPI Exception creating {e}")

            raise kopf.TemporaryError(
                "Exception creating DependentAPI custom resource."
            )
        else:
            # Conflict = try updating existing cr
            logw.info(f"DependentAPI already exists {DependentAPIResource}")
            try:
                dependentAPIObj = custom_objects_api.patch_namespaced_custom_object(
                    group=GROUP,
                    version=DEPENDENTAPI_VERSION,
                    namespace=namespace,
                    plural=DEPENDENTAPI_PLURAL,
                    name=cr_name,
                    body=DependentAPIResource,
                )
                logw.debugInfo(
                    f"DependentAPI Resource updated {DependentAPIResource["metadata"]["name"]}",
                    dependentAPIObj,
                )

            except ApiException as e:
                logw.warning(f"DependentAPI Exception updating {DependentAPIResource}")
                logw.warning(f"DependentAPI Exception updating {e}")
                raise kopf.TemporaryError(
                    "Exception creating DependentAPI custom resource."
                )

    returnDependentAPIObject = {
        "name": DependentAPIResource["metadata"]["name"],
        "uid": dependentAPIObj["metadata"]["uid"],
        "ready": dependentAPIReadyStatus,
    }
    return returnDependentAPIObject


@logwrapper
async def createSecretsManagementResource(
    logw: LogWrapper, inSecretsManagement, namespace, name, inHandler
):
    """Helper function to create or update API Custom objects.

    Args:
        * inSecretsManagement (Dict): The SecretsManagement definition
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource
        * inHandler (String): The name of the handler calling this function

    Returns:
        Dict with SecretsManagement definition including uuid of the SecretsManagement resource and ready status.

    :meta private:
    """
    logw.debug(f"createSecretsManagementResource {inSecretsManagement} ")

    SecretsManagementResource = constructSecretsManagementResourcePayload(
        inSecretsManagement
    )

    secretsManagementReadyStatus = False
    returnSecretsManagementObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logw.info(
            f"Creating SecretsManagement Custom Object {SecretsManagementResource}"
        )

        secretsManagementObj = custom_objects_api.create_namespaced_custom_object(
            group=GROUP,
            version=SECRETSMANAGEMENT_VERSION,
            namespace=namespace,
            plural=SECRETSMANAGEMENT_PLURAL,
            body=SecretsManagementResource,
        )
        logw.debugInfo(
            f"SecretsManagement Resource created {SecretsManagementResource["metadata"]["name"]}",
            secretsManagementObj,
        )

        returnSecretsManagementObject = {
            "name": SecretsManagementResource["metadata"]["name"],
            "uid": secretsManagementObj["metadata"]["uid"],
            "ready": secretsManagementReadyStatus,
        }

    except ApiException as e:
        logw.warning(
            f"SecretsManagement Exception creating {SecretsManagementResource}"
        )
        logw.warning(f"SecretsManagement Exception creating {e}")

        raise kopf.TemporaryError(
            "Exception creating SecretsManagement custom resource."
        )
    return returnSecretsManagementObject


@logwrapper
async def createIdentityConfigResource(logw: LogWrapper, inIdentityConfig, namespace):
    """Helper function to create or update IdentityConfig Custom objects.

    Args:
        * inIdentityConfig (Dict): The IdentityConfig definition
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource

    Returns:
        Dict with IdentityConfig definition including uuid of the IdentityConfig resource and ready status.

    :meta private:
    """
    logw.debug(f"createIdentityConfigResource {inIdentityConfig} ")

    IdentityConfigResource = constructIdentityConfigResourcePayload(inIdentityConfig)

    identityConfigReadyStatus = False
    returnIdentityConfigObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logw.info(f"Creating IdentityConfig Custom Object {IdentityConfigResource}")

        identityConfigObj = custom_objects_api.create_namespaced_custom_object(
            group=GROUP,
            version=IDENTITYCONFIG_VERSION,
            namespace=namespace,
            plural=IDENTITYCONFIG_PLURAL,
            body=IdentityConfigResource,
        )
        logw.debugInfo(
            f"IdentityConfig Resource created {IdentityConfigResource["metadata"]["name"]}",
            identityConfigObj,
        )

        returnIdentityConfigObject = {
            "name": IdentityConfigResource["metadata"]["name"],
            "uid": identityConfigObj["metadata"]["uid"],
            "ready": identityConfigReadyStatus,
        }

    except ApiException as e:
        logw.warning(f"IdentityConfig Exception creating {IdentityConfigResource}")
        logw.warning(f"IdentityConfig Exception creating {e}")

        raise kopf.TemporaryError("Exception creating IdentityConfig custom resource.")
    return returnIdentityConfigObject


# -------------------------------------------------------------------------------
# Make services, deployments, persistentvolumeclaims, jobs, cronjobs, statefulsets, configmap, secret, serviceaccount, role, rolebinding children of the component
# These are resources that we support in a component. There are resources that we don't support (that will generate a warning in the Level 1 CTK:
# ingress - A developer should express a components intent via APIs and not via ingress. The canvas should create any required ingress
# pod, replicaset - a developer should use deployments (for stateless microservices) or statefulsets (for stateful microservices)
# demonset - a component developer should have no need for creating a demonset
# clusterrole, clusterrolebinding - a component developer should have no need for creating a clusterrole, clusterrolebinding they should be using role, rolebinding


@kopf.on.resume("", "v1", "services", retries=5)
@kopf.on.create("", "v1", "services", retries=5)
async def adopt_service(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "service"
    )


@kopf.on.resume("apps", "v1", "deployments", retries=5)
@kopf.on.create("apps", "v1", "deployments", retries=5)
async def adopt_deployment(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "deployment"
    )


@kopf.on.resume("", "v1", "persistentvolumeclaims", retries=5)
@kopf.on.create("", "v1", "persistentvolumeclaims", retries=5)
async def adopt_persistentvolumeclaim(
    meta, spec, body, namespace, labels, name, **kwargs
):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "persistentvolumeclaim"
    )


@kopf.on.resume("batch", "v1", "jobs", retries=5)
@kopf.on.create("batch", "v1", "jobs", retries=5)
async def adopt_job(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, "job")


@kopf.on.resume("batch", "v1", "cronjobs", retries=5)
@kopf.on.create("batch", "v1", "cronjobs", retries=5)
async def adopt_cronjob(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "cronjob"
    )


@kopf.on.resume("apps", "v1", "statefulsets", retries=5)
@kopf.on.create("apps", "v1", "statefulsets", retries=5)
async def adopt_statefulset(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "statefulset"
    )


@kopf.on.resume("", "v1", "configmap", retries=5)
@kopf.on.create("", "v1", "configmap", retries=5)
async def adopt_configmap(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "configmap"
    )


@kopf.on.resume("", "v1", "secret", retries=5)
@kopf.on.create("", "v1", "secret", retries=5)
async def adopt_secret(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, "secret")


@kopf.on.resume("", "v1", "serviceaccount", retries=5)
@kopf.on.create("", "v1", "serviceaccount", retries=5)
async def adopt_serviceaccount(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "serviceaccount"
    )


@kopf.on.resume("rbac.authorization.k8s.io", "v1", "role", retries=5)
@kopf.on.create("rbac.authorization.k8s.io", "v1", "role", retries=5)
async def adopt_role(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, "role")


@kopf.on.resume("rbac.authorization.k8s.io", "v1", "rolebinding", retries=5)
@kopf.on.create("rbac.authorization.k8s.io", "v1", "rolebinding", retries=5)
async def adopt_rolebinding(meta, spec, body, namespace, labels, name, **kwargs):
    # del unused-arguments for linting
    del kwargs

    return adopt_kubernetesResource(
        meta, spec, body, namespace, labels, name, "rolebinding"
    )


def adopt_kubernetesResource(meta, spec, body, namespace, labels, name, resourceType):
    """Helper function for adopting any kubernetes resource

    If the resource has an oda.tmforum.org/componentName label, it makes the resource a child of the named component.
    This can help with navigating around the different resources that belong to the component. It also ensures that the kubernetes garbage collection
    will delete these resources automatically if the component is deleted.

    Args:
        * meta (Dict): The metadata from the yaml resource definition
        * spec (Dict): The spec from the yaml resource definition showing the intent (or desired state)
        * body (Dict): The entire yaml resource definition
        * namespace (String): The namespace for the resource
        * labels (Dict): The labels attached to the resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the resource
        * resourceType (String): The type of resource (e.g. service, deployment, persistentvolumeclaim, job, cronjob, statefulset, configmap, secret, serviceaccount, role, rolebinding)

    Returns:
        No return value.

    :meta public:
    """
    if "oda.tmforum.org/componentName" in labels.keys():

        # check if the resource already has a parent with kind Component
        # look in the metadata.ownerReferences for a reference to a Component
        # if it exists, then we don't need to adopt it again
        if "ownerReferences" in meta.keys():
            for owner in meta["ownerReferences"]:
                if owner["kind"] == "Component":
                    return

        component_name = labels["oda.tmforum.org/componentName"]
        logw = LogWrapper(
            handler_name="adopt_" + resourceType, function_name="adopt_" + resourceType
        )
        logw.set(
            component_name=quick_get_comp_name(body),
            resource_name=quick_get_comp_name(body),
        )
        logw.debugInfo("adopt_" + resourceType + " handler called", body)

        try:
            parent_component = (
                kubernetes.client.CustomObjectsApi().get_namespaced_custom_object(
                    GROUP, VERSION, namespace, COMPONENTS_PLURAL, component_name
                )
            )
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError(
                    "Cannot find parent component " + component_name
                )
            else:
                logw.debug(
                    f"Exception when calling custom_objects_api.get_namespaced_custom_object {e}"
                )

        newBody = dict(body)  # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        try:
            if resourceType == "service":
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_service(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "persistentvolumeclaim":
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_persistent_volume_claim(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "deployment":
                api_response = (
                    kubernetes.client.AppsV1Api().patch_namespaced_deployment(
                        newBody["metadata"]["name"],
                        newBody["metadata"]["namespace"],
                        newBody,
                    )
                )
            elif resourceType == "configmap":
                api_response = (
                    kubernetes.client.CoreV1Api().patch_namespaced_config_map(
                        newBody["metadata"]["name"],
                        newBody["metadata"]["namespace"],
                        newBody,
                    )
                )
            elif resourceType == "secret":
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_secret(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "job":
                api_response = kubernetes.client.BatchV1Api().patch_namespaced_job(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "cronjob":
                api_response = kubernetes.client.BatchV1Api().patch_namespaced_cron_job(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "statefulset":
                api_response = (
                    kubernetes.client.AppsV1Api().patch_namespaced_stateful_set(
                        newBody["metadata"]["name"],
                        newBody["metadata"]["namespace"],
                        newBody,
                    )
                )
            elif resourceType == "role":
                api_response = (
                    kubernetes.client.RbacAuthorizationV1Api().patch_namespaced_role(
                        newBody["metadata"]["name"],
                        newBody["metadata"]["namespace"],
                        newBody,
                    )
                )
            elif resourceType == "rolebinding":
                api_response = kubernetes.client.RbacAuthorizationV1Api().patch_namespaced_role_binding(
                    newBody["metadata"]["name"],
                    newBody["metadata"]["namespace"],
                    newBody,
                )
            elif resourceType == "serviceaccount":
                api_response = (
                    kubernetes.client.CoreV1Api().patch_namespaced_service_account(
                        newBody["metadata"]["name"],
                        newBody["metadata"]["namespace"],
                        newBody,
                    )
                )
            else:
                logw.error(f"Unsupported resource type {resourceType}")

                raise kopf.PermanentError(
                    "Error adopting - unsupported resource type " + resourceType
                )
            logw.debugInfo(
                f"Adding component as parent of {resourceType}", api_response
            )

        except ApiException as e:
            if e.status == HTTP_CONFLICT:  # Conflict = try again
                raise kopf.TemporaryError("Conflict updating " + resourceType + ".")
            else:
                logw.warning(f"Exception when calling patch {resourceType}")


# When Component status changes, update status summary
@kopf.on.field(GROUP, VERSION, COMPONENTS_PLURAL, field="status", retries=5)
async def summary(meta, spec, status, body, namespace, labels, name, **kwargs):

    logw = LogWrapper(handler_name="summary", function_name="summary")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),
    )
    logw.debugInfo("summary handler called", body)

    # del unused-arguments for linting
    del meta, spec, namespace, labels, name, kwargs

    coreAPIsummary = ""
    coreDependentAPIsummary = ""
    managementDependentAPIsummary = ""
    securityDependentAPIsummary = ""
    securitySecretsManagementSummary = ""
    managementAPIsummary = ""
    securityAPIsummary = ""
    developerUIsummary = ""
    countOfCompleteAPIs = 0
    countOfDesiredAPIs = 0
    countOfDesiredDependentAPIs = 0
    countOfCompleteDependentAPIs = 0
    countOfDesiredSecretsManagements = 0
    countOfCompleteSecretsManagements = 0
    if "coreAPIs" in status.keys():
        countOfDesiredAPIs = countOfDesiredAPIs + len(status["coreAPIs"])
        for api in status["coreAPIs"]:
            if "url" in api.keys():
                coreAPIsummary = coreAPIsummary + api["url"] + " "
                if "developerUI" in api.keys():
                    developerUIsummary = developerUIsummary + api["developerUI"] + " "
                if "ready" in api.keys():
                    if api["ready"] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1
    if "coreDependentAPIs" in status.keys():
        countOfDesiredDependentAPIs = countOfDesiredDependentAPIs + len(
            status["coreDependentAPIs"]
        )
        for depapi in status["coreDependentAPIs"]:
            if "url" in depapi.keys():
                coreDependentAPIsummary = coreDependentAPIsummary + depapi["url"] + " "
                if "ready" in depapi.keys():
                    if depapi["ready"] == True:
                        countOfCompleteDependentAPIs = countOfCompleteDependentAPIs + 1
    if "managementDependentAPIs" in status.keys():
        countOfDesiredDependentAPIs = countOfDesiredDependentAPIs + len(
            status["managementDependentAPIs"]
        )
        for depapi in status["managementDependentAPIs"]:
            if "url" in depapi.keys():
                managementDependentAPIsummary = (
                    managementDependentAPIsummary + depapi["url"] + " "
                )
                if "ready" in depapi.keys():
                    if depapi["ready"] == True:
                        countOfCompleteDependentAPIs = countOfCompleteDependentAPIs + 1
    if "securityDependentAPIs" in status.keys():
        countOfDesiredDependentAPIs = countOfDesiredDependentAPIs + len(
            status["securityDependentAPIs"]
        )
        for depapi in status["securityDependentAPIs"]:
            if "url" in depapi.keys():
                securityDependentAPIsummary = (
                    securityDependentAPIsummary + depapi["url"] + " "
                )
                if "ready" in depapi.keys():
                    if depapi["ready"] == True:
                        countOfCompleteDependentAPIs = countOfCompleteDependentAPIs + 1
    if "securitySecretsManagement" in status.keys():
        sman = status["securitySecretsManagement"]
        if sman != {}:
            countOfDesiredSecretsManagements = 1
            securitySecretsManagementSummary = "initializing"
            if "ready" in sman:
                if sman["ready"] == True:
                    countOfCompleteSecretsManagements = (
                        countOfCompleteSecretsManagements + 1
                    )
                    securitySecretsManagementSummary = "ready"
    if "managementAPIs" in status.keys():
        countOfDesiredAPIs = countOfDesiredAPIs + len(status["managementAPIs"])
        for api in status["managementAPIs"]:
            if "url" in api.keys():
                managementAPIsummary = managementAPIsummary + api["url"] + " "
                if "developerUI" in api.keys():
                    developerUIsummary = developerUIsummary + api["developerUI"] + " "
                if "ready" in api.keys():
                    if api["ready"] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1
    if "securityAPIs" in status.keys():
        countOfDesiredAPIs = countOfDesiredAPIs + len(status["securityAPIs"])
        for api in status["securityAPIs"]:
            if "url" in api.keys():
                securityAPIsummary = securityAPIsummary + api["url"] + " "
                if "developerUI" in api.keys():
                    developerUIsummary = developerUIsummary + api["developerUI"] + " "
                if "ready" in api.keys():
                    if api["ready"] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1

    status_summary = {}
    status_summary["coreAPIsummary"] = coreAPIsummary
    status_summary["coreDependentAPIsummary"] = coreDependentAPIsummary
    status_summary["managementDependentAPIsummary"] = managementDependentAPIsummary
    status_summary["securityDependentAPIsummary"] = securityDependentAPIsummary
    status_summary["securitySecretsManagementSummary"] = (
        securitySecretsManagementSummary
    )
    status_summary["managementAPIsummary"] = managementAPIsummary
    status_summary["securityAPIsummary"] = securityAPIsummary
    status_summary["developerUIsummary"] = developerUIsummary
    logw.info(
        f"Creating summary - completed API count{str(countOfCompleteAPIs)}/{str(countOfDesiredAPIs)}"
    )

    status_summary["deployment_status"] = "In-Progress-CompCon"
    if countOfCompleteAPIs == countOfDesiredAPIs:
        status_summary["deployment_status"] = "In-Progress-IDConfOp"
        if ("identityConfig" in status.keys()) and (
            status["identityConfig"]["identityProvider"] != IDENTITY_PROVIDER_NOT_SET
        ):
            status_summary["deployment_status"] = "In-Progress-SecretMan"
            if countOfCompleteSecretsManagements == countOfDesiredSecretsManagements:
                status_summary["deployment_status"] = "In-Progress-DepApi"
                if countOfCompleteDependentAPIs == countOfDesiredDependentAPIs:
                    status_summary["deployment_status"] = "Complete"
    logw.info(
        f"Creating summary - deployment status {status_summary['deployment_status']}"
    )

    return status_summary


@logwrapper
async def createPublishedNotificationResource(
    logw: LogWrapper, definition, namespace, name, inHandler
):
    """Helper function to create or update PublishedNotification Custom objects.

    Args:
        * definition (Dict): The PublishedNotification definition
        * namespace (String): The namespace for the PublishedNotification
        * name (String): The name of the PublishedNotification resource
        * inHandler (String): The name of the handler calling this function

    Returns:
        Dict with PublishedNotification definition

    :meta private:
    """
    logw.info(f"createPublishedNotificationResource {definition} ")

    PublishedNotificationResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": "PublishedNotification",
        "metadata": {},
        "spec": {},
    }

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(PublishedNotificationResource)

    newName = (
        PublishedNotificationResource["metadata"]["ownerReferences"][0]["name"]
        + "-"
        + definition["name"]
    ).lower()

    PublishedNotificationResource["metadata"]["name"] = newName
    PublishedNotificationResource["spec"] = definition

    returnPublishedNotificationObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        try:
            custom_objects_api.get_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=namespace,
                plural=PUBLISHEDNOTIFICATIONS_PLURAL,
                name=newName,
            )
        except ApiException as e:
            if e.status == HTTP_NOT_FOUND:
                apiObj = custom_objects_api.create_namespaced_custom_object(
                    group=GROUP,
                    version=VERSION,
                    namespace=namespace,
                    plural=PUBLISHEDNOTIFICATIONS_PLURAL,
                    body=PublishedNotificationResource,
                )

                logw.info(f"PublishedNotification created {name}")
                custom_objects_api.patch_namespaced_custom_object_status(
                    group=GROUP,
                    version=VERSION,
                    namespace=namespace,
                    plural=PUBLISHEDNOTIFICATIONS_PLURAL,
                    name=newName,
                    field_manager="componentOperator",
                    body={"status": {"uid": "", "status": "initializing", "error": ""}},
                )

                returnPublishedNotificationObject = {
                    "name": PublishedNotificationResource["metadata"]["name"],
                    "uid": apiObj["metadata"]["uid"],
                }
            else:
                logw.warning(
                    f"Exception creating PublishedNotification custom resource - will retry"
                )
                raise kopf.TemporaryError(
                    "Exception creating PublishedNotification custom resource."
                )
    except ApiException as e:
        logw.error(f"PublishedNotification Exception creating {e}")

        raise kopf.TemporaryError(
            "Exception creating PublishedNotification custom resource."
        )
    return returnPublishedNotificationObject


@logwrapper
async def createSubscribedNotificationResource(
    logw: LogWrapper, definition, namespace, name, inHandler
):
    """Helper function to create or update SubscribedNotification Custom objects.

    Args:
        * definition (Dict): The SubscribedNotification definition
        * namespace (String): The namespace for the SubscribedNotification
        * name (String): The name of the SubscribedNotification resource
        * inHandler (String): The name of the handler calling this function

    Returns:
        Dict with SubscribedNotification definition

    :meta private:
    """
    logw.info(f"createSubscribedNotificationResource {definition} ")

    SubscribedNotificationResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": "SubscribedNotification",
        "metadata": {},
        "spec": {},
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(SubscribedNotificationResource)

    newName = (
        SubscribedNotificationResource["metadata"]["ownerReferences"][0]["name"]
        + "-"
        + definition["name"]
    ).lower()

    SubscribedNotificationResource["metadata"]["name"] = newName
    SubscribedNotificationResource["spec"] = definition

    returnSubscribedNotificationObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        try:
            custom_objects_api.get_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=namespace,
                plural=SUBSCRIBEDNOTIFICATIONS_PLURAL,
                name=newName,
            )
        except ApiException as e:
            if e.status == HTTP_NOT_FOUND:
                apiObj = custom_objects_api.create_namespaced_custom_object(
                    group=GROUP,
                    version=VERSION,
                    namespace=namespace,
                    plural=SUBSCRIBEDNOTIFICATIONS_PLURAL,
                    body=SubscribedNotificationResource,
                )

                custom_objects_api.patch_namespaced_custom_object_status(
                    group=GROUP,
                    version=VERSION,
                    namespace=namespace,
                    plural=SUBSCRIBEDNOTIFICATIONS_PLURAL,
                    name=newName,
                    field_manager="componentOperator",
                    body={"status": {"uid": "", "status": "initializing", "error": ""}},
                )
                logw.info(
                    f"SubscribedNotification created {SubscribedNotificationResource["metadata"]["name"]}"
                )

                returnSubscribedNotificationObject = {
                    "name": SubscribedNotificationResource["metadata"]["name"],
                    "uid": apiObj["metadata"]["uid"],
                }
            else:
                raise kopf.TemporaryError(
                    "Exception creating SubscribedNotification custom resource."
                )
    except ApiException as e:
        logw.error(f"SubscribedNotification Exception creating {e}")

        raise kopf.TemporaryError(
            "Exception creating SubscribedNotification custom resource."
        )

    return returnSubscribedNotificationObject
