"""Kubernetes operator for ODA Component custom resources.

Normally this module is deployed as part of an ODA Canvas. It uses the kopf kubernetes operator framework (https://kopf.readthedocs.io/).
It registers handler functions for:

1. New ODA Components - to create, update or delete child API custom resources. see `coreAPIs <#componentOperator.componentOperator.coreAPIs>`_ and `securityAPIs <#componentOperator.componentOperator.securityAPIs>`_
2a. For status updates in the child API Custom resources, so that the Component status reflects a summary of all the childrens status. see `updateAPIStatus <#componentOperator.componentOperator.updateAPIStatus>`_ and `updateAPIReady <#componentOperator.componentOperator.updateAPIReady>`_
2b. For status updates in the child DependentAPI Custom resources, so that the Component status reflects a summary of all the childrens status. see `updateDependentAPIStatus <#componentOperator.componentOperator.updateDependentAPIStatus>`_ and `updateDependentAPIReady <#componentOperator.componentOperator.updateDependentAPIReady>`_
3. For new Services, Deployments, PersistentVolumeClaims and Jobs that have a oda.tmforum.org/componentName label. These resources are updated to become children of the ODA Component resource. see `adopt_deployment <#componentOperator.componentOperator.adopt_deployment>`_ , `adopt_persistentvolumeclaim <#componentOperator.componentOperator.adopt_persistentvolumeclaim>`_ , `adopt_job <#componentOperator.componentOperator.adopt_job>`_ and `adopt_service <#componentOperator.componentOperator.adopt_service>`_
"""
import time
import kopf
import kubernetes.client
import logging
import traceback
from kubernetes.client.rest import ApiException
import os
import asyncio

# Setup logging
logging_level = os.environ.get('LOGGING', logging.INFO)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger('ComponentOperator')
logger.setLevel(int(logging_level))
logger.info(f'Logging set to %s', logging_level)

CICD_BUILD_TIME = os.getenv('CICD_BUILD_TIME')
GIT_COMMIT_SHA = os.getenv('GIT_COMMIT_SHA')
if CICD_BUILD_TIME:
    logger.info(f'CICD_BUILD_TIME=%s', CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f'GIT_COMMIT_SHA=%s', GIT_COMMIT_SHA)



# get namespace to monitor
component_namespace = os.environ.get('COMPONENT_NAMESPACE', 'components')
logger.info(f'Monitoring namespace %s', component_namespace)

# Constants
HTTP_CONFLICT = 409
HTTP_NOT_FOUND = 404
GROUP = "oda.tmforum.org"
VERSION = "v1beta3"
APIS_PLURAL = "apis"
COMPONENTS_PLURAL = "components"

DEPENDENTAPI_GROUP = 'oda.tmforum.org'
DEPENDENTAPI_VERSION = "v1beta3"
DEPENDENTAPI_PLURAL = "dependentapis"
DEPENDENTAPI_KIND = "DependentAPI" 

PUBLISHEDNOTIFICATIONS_PLURAL = "publishednotifications"
SUBSCRIBEDNOTIFICATIONS_PLURAL = "subscribednotifications"


# try to recover from broken watchers https://github.com/nolar/kopf/issues/1036
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60


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
    logWrapper(logging.INFO, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Handler called", "")
    apiChildren = [] # any existing API children of this component that have been patched
    oldCoreAPIs = [] # existing API children of this component (according to previous status)
    try:
            
        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if 'coreAPIs' in status.keys():
                oldCoreAPIs = status['coreAPIs']
                
            newCoreAPIs = spec['coreFunction']['exposedAPIs']
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldCoreAPIs:
                found = False
                for newAPI in newCoreAPIs:
                    logWrapper(logging.DEBUG, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Comparing old and new APIs", f"Comparing  {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}")
                    if oldAPI['name'] == name + '-' + newAPI['name'].lower():
                        found = True
                        logWrapper(logging.INFO, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Patching API", newAPI['name'])
                        resultStatus = await patchAPIResource(newAPI, namespace, name, 'coreAPIs')
                        apiChildren.append(resultStatus)
                if not found:
                    logWrapper(logging.INFO, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Deleting API", oldAPI['name'])
                    await deleteAPI(oldAPI['name'], name, status, namespace, 'coreAPIs')

        # get core APIS
        coreAPIs = spec['coreFunction']['exposedAPIs']
        logWrapper(logging.DEBUG, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Exposed API list", f"{coreAPIs}")
        
        for coreAPI in coreAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logWrapper(logging.DEBUG, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Comparing new APIs with status", f"Comparing {processedAPI['name']} to {name + '-' + coreAPI['name'].lower()}")
                if processedAPI['name'] == name + '-' + coreAPI['name'].lower():
                    alreadyProcessed = True
            if alreadyProcessed == False:
                logWrapper(logging.INFO, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Calling createAPIResource", coreAPI['name'])
                resultStatus = await createAPIResource(coreAPI, namespace, name, 'coreAPIs')
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry
    except Exception as e:
        logWrapper(logging.ERROR, 'coreAPIs', 'coreAPIs', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")

    # Update the parent's status.
    return apiChildren


async def deleteAPI(deleteAPIName, componentName, status, namespace, inHandler):
    """Helper function to delete API Custom objects.
    
    Args:
        * deleteAPIName (String): Name of the API Custom Object to delete 
        * componentName (String): Name of the component the API is linked to 
        * status (Dict): The status from the yaml component envelope.
        * namespace (String): The namespace for the component

    Returns:
        No return value

    :meta private:
    """

    logWrapper(logging.INFO, 'deleteAPI', inHandler, 'component/' + componentName, componentName, "Deleting API", f"Deleting API {deleteAPIName}")
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        api_response = custom_objects_api.delete_namespaced_custom_object(
            group = GROUP, 
            version = VERSION, 
            namespace = namespace, 
            plural = APIS_PLURAL, 
            name = deleteAPIName)
        logWrapper(logging.DEBUG, 'deleteAPI', inHandler, 'component/' + componentName, componentName, "API response", api_response)
    except ApiException as e:
        logWrapper(logging.DEBUG, 'deleteAPI', inHandler, 'component/' + componentName, componentName, "Exception when calling CustomObjectsApi->delete_namespaced_custom_object", e)
        logWrapper(logging.ERROR, 'deleteAPI', inHandler, 'component/' + componentName, componentName, "Exception", " when calling CustomObjectsApi->delete_namespaced_custom_object")


async def deleteDependentAPI(dependentAPIName, componentName, status, namespace, inHandler):
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

    logWrapper(logging.INFO, 'deleteDependentAPI', inHandler, 'component/' + componentName, componentName, "Deleting DependentAPI", f"Deleting DependentAPI {dependentAPIName}")
    custom_objects_api = kubernetes.client.CustomObjectsApi()
    try:
        dependentapi_response = custom_objects_api.delete_namespaced_custom_object(
            group = GROUP, 
            version = DEPENDENTAPI_VERSION, 
            namespace = namespace, 
            plural = DEPENDENTAPI_PLURAL, 
            name = dependentAPIName)
        logWrapper(logging.DEBUG, 'deleteDependentAPI', inHandler, 'component/' + componentName, componentName, "DependentAPI response", dependentapi_response)
    except ApiException as e:
        logWrapper(logging.DEBUG, 'deleteDependentAPI', inHandler, 'component/' + componentName, componentName, "Exception when calling CustomObjectsApi->delete_namespaced_custom_object", e)
        logWrapper(logging.ERROR, 'deleteDependentAPI', inHandler, 'component/' + componentName, componentName, "Exception", " when calling CustomObjectsApi->delete_namespaced_custom_object")



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
    logWrapper(logging.INFO, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Handler called", "")
    apiChildren = []
    oldManagementAPIs = []
    try:

        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if 'managementAPIs' in status.keys():
                oldManagementAPIs = status['managementAPIs']

            newManagementAPIs = spec['managementFunction']['exposedAPIs']
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldManagementAPIs:
                found = False
                for newAPI in newManagementAPIs:

                    logWrapper(logging.DEBUG, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Comparing old and new APIs", f"Comparing  {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}")
                    if oldAPI['name'] == name + '-' + newAPI['name'].lower():
                        found = True
                        logWrapper(logging.INFO, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Patching API", newAPI['name'])
                        resultStatus = await patchAPIResource(newAPI, namespace, name, 'managementAPIs')
                        apiChildren.append(resultStatus)
                if not found:
                    logWrapper(logging.INFO, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Deleting API", oldAPI['name'])
                    await deleteAPI(oldAPI['name'], name, status, namespace, 'managementAPIs')

        # get exposed APIS
        managementAPIs = spec['managementFunction']['exposedAPIs']
        logWrapper(logging.DEBUG, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Exposed API list", f"{managementAPIs}")

        for managementAPI in managementAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logger.debug(
                    f"Comparing {processedAPI['name']} to {name + '-' + managementAPI['name'].lower()}")
                logWrapper(logging.DEBUG, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Comparing new APIs with status", f"Comparing {processedAPI['name']} to {name + '-' + managementAPI['name'].lower()}")
                if processedAPI['name'] == name + '-' + managementAPI['name'].lower():
                    alreadyProcessed = True

            if alreadyProcessed == False:
                logWrapper(logging.INFO, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Calling createAPIResource", managementAPI['name'])
                resultStatus = await createAPIResource(managementAPI, namespace, name, 'managementAPIs')
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry            
    except Exception as e:
        logWrapper(logging.ERROR, 'managementAPIs', 'managementAPIs', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")
        
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
    logWrapper(logging.INFO, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Handler called", "")
    apiChildren = []
    oldSecurityAPIs = []
    try:

        # compare desired state (spec) with actual state (status) and initiate changes
        if status:  # if status exists (i.e. this is not a new component)
            # update a component - look in old and new to see if we need to delete any API resources
            if 'securityAPIs' in status.keys():
                oldSecurityAPIs = status['securityAPIs']
            newSecurityAPIs = spec['securityFunction']['exposedAPIs']
            # find apis in old that are missing in new
            deletedAPIs = []
            for oldAPI in oldSecurityAPIs:
                found = False
                for newAPI in newSecurityAPIs:

                    logWrapper(logging.DEBUG, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Comparing old and new APIs", f"Comparing  {oldAPI['name']} to {name + '-' + newAPI['name'].lower()}")
                    if oldAPI['name'] == name + '-' + newAPI['name'].lower():
                        found = True
                        logWrapper(logging.INFO, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Patching API", newAPI['name'])
                        resultStatus = await patchAPIResource(newAPI, namespace, name, 'securityAPIs')
                        apiChildren.append(resultStatus)
                if not found:
                    logWrapper(logging.INFO, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Deleting API", oldAPI['name'])
                    await deleteAPI(oldAPI['name'], name, status, namespace, 'securityAPIs')

        # get exposed APIS
        securityAPIs = spec['securityFunction']['exposedAPIs']
        logWrapper(logging.DEBUG, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Exposed API list", f"{securityAPIs}")

        for securityAPI in securityAPIs:
            # check if we have already patched this API
            alreadyProcessed = False
            for processedAPI in apiChildren:
                logger.debug(
                    f"Comparing {processedAPI['name']} to {name + '-' + securityAPI['name'].lower()}")
                logWrapper(logging.DEBUG, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Comparing new APIs with status", f"Comparing {processedAPI['name']} to {name + '-' + securityAPI['name'].lower()}")
                if processedAPI['name'] == name + '-' + securityAPI['name'].lower():
                    alreadyProcessed = True

            if alreadyProcessed == False:
                logWrapper(logging.INFO, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Calling createAPIResource", securityAPI['name'])
                resultStatus = await createAPIResource(securityAPI, namespace, name, 'securityAPIs')
                apiChildren.append(resultStatus)

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry            
    except Exception as e:
        logWrapper(logging.ERROR, 'securityAPIs', 'securityAPIs', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")
        
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
async def coreDependentAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
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
    ### TODO INFO->DEBUG
    logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "Handler called with body", f"{body}")
    logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "Handler called", "")
    dependentAPIChildren = []
    dapi_base_name = f"{name}-dapi"

    try:
        oldCoreDependentAPIs = []
        if status:  # if status exists (i.e. this is not a new component)
            oldCoreDependentAPIs = safe_get([], status, 'coreDependentAPIs')
        logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "--- OLD DEPENDENTAPI (from status) ---", f"{oldCoreDependentAPIs}, type={type(oldCoreDependentAPIs)}")
            
        newCoreDependentAPIs = safe_get([], spec, 'coreFunction', 'dependentAPIs')
        logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "--- NEW DEPENDENTAPI ---", f"{newCoreDependentAPIs}")

        # compare entries by name
        for oldCoreDependentAPI in oldCoreDependentAPIs:
            cr_name = oldCoreDependentAPI["name"] 
            dapi_name = cr_name[len(dapi_base_name)+1:]
            print(dapi_name)
            newCoreDependentAPI = find_entry_by_name(newCoreDependentAPIs, dapi_name)
            if not newCoreDependentAPI:
                logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "Deleting DependentAPIs", cr_name)
                await deleteDependentAPI(cr_name, name, status, namespace, 'coreDependentAPIs')
            else:
                # TODO[FH] implement check for update
                logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "TODO: Update DependentAPIs", cr_name)
                dependentAPIChildren.append(oldCoreDependentAPI)                 
        
        for newCoreDependentAPI in newCoreDependentAPIs:
            dapi_name = newCoreDependentAPI["name"] 
            cr_name = f"{dapi_base_name}-{dapi_name}"
            print(dapi_name)
            oldCoreDependentAPI = find_entry_by_name(oldCoreDependentAPIs, cr_name)
            if not oldCoreDependentAPI:
                logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "Calling createDependentAPI", cr_name)
                resultStatus = await createDependentAPIResource(newCoreDependentAPI, namespace, name, cr_name, 'coreDependentAPIs')
                dependentAPIChildren.append(resultStatus)                
            # else: already handled above        

            
    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry            
    except Exception as e:
        logWrapper(logging.ERROR, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")

    logWrapper(logging.INFO, 'coreDependentAPIs', 'coreDependentAPIs', 'component/' + name, name, "result for status ", f"{dependentAPIChildren}")
        
    # Update the parent's status.
    return dependentAPIChildren

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
    logWrapper(logging.INFO, 'publishedEvents', 'publishedEvents', 'component/' + name, name, "Handler called", "")
    pubChildren = []
    try:

        # get security exposed APIS
        try:
            publishedEvents = spec['eventNotification']['publishedEvents']
            pubChildren = await asyncio.gather(*[createPublishedNotificationResource(publishedEvent, namespace, name, 'publishedEvents') for publishedEvent in publishedEvents])
        except KeyError:
            logWrapper(logging.WARNING, 'publishedEvents', 'publishedEvents', 'component/' + name, name, "No publishedEvents property", f"component {name} has no publishedEvents property")

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry
    except Exception as e:
        logWrapper(logging.ERROR, 'publishedEvents', 'publishedEvents', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")

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
    logWrapper(logging.INFO, 'subscribedEvents', 'subscribedEvents', 'component/' + name, name, "Handler called", "")
    subChildren = []
    try:

        # get security exposed APIS
        try:
            subscribedEvents = spec['eventNotification']['subscribedEvents']
            subChildren = await asyncio.gather(*[createSubscribedNotificationResource(subscribedEvent, namespace, name, 'subscribedEvents') for subscribedEvent in subscribedEvents])
        except KeyError:
            logWrapper(logging.WARNING, 'subscribedEvents', 'subscribedEvents', 'component/' + name, name, "No subscribedEvents property", f"component {name} has no subscribedEvents property")

    except kopf.TemporaryError as e:
        raise kopf.TemporaryError(e) # allow the operator to retry
    except Exception as e:
        logWrapper(logging.ERROR, 'subscribedEvents', 'subscribedEvents', 'component/' + name, name, "Unhandled exception", f"{e}: {traceback.format_exc()}")

    return subChildren




def constructAPIResourcePayload(inAPI):
    """Helper function to create payloads for API Custom objects.

    Args:
        * inAPI (Dict): The API spec 

    Returns:
        API Custom object (Dict)

    :meta private:
    """
    APIResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": "API",
        "metadata": {},
        "spec": {}
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(APIResource)
    newName = (APIResource['metadata']['ownerReferences'][0]['name'] + '-' + inAPI['name']).lower()
    APIResource['metadata']['name'] = newName
    APIResource['spec'] = inAPI
    if 'developerUI' in inAPI.keys():
        APIResource['spec']['developerUI'] = inAPI['developerUI']
    return APIResource

def constructDependentAPIResourcePayload(inDependentAPI, cr_name):
    """Helper function to create payloads for DependentAPI Custom objects.

    Args:
        * inDependentAPI (Dict): The DependentAPI spec 
        * cr_name custom resource name of the dependent api 

    Returns:
        DependentAPI Custom object (Dict)

    :meta private:
    """
    DependentAPIResource = {
        "apiVersion": GROUP + "/" + DEPENDENTAPI_VERSION,
        "kind": DEPENDENTAPI_KIND,
        "metadata": {},
        "spec": {}
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(DependentAPIResource)
    newName = (DependentAPIResource['metadata']['ownerReferences'][0]['name'])
    #DependentAPIResource['metadata']['name'] = f"{newName}-{dapi_name}"
    DependentAPIResource['metadata']['name'] = cr_name
    DependentAPIResource['spec'] = inDependentAPI
    return DependentAPIResource

async def patchAPIResource(inAPI, namespace, name, inHandler):
    """Helper function to patch API Custom objects.

    Args:
        * inAPI (Dict): The API definition 
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource
        * inHandler (String): The name of the handler that called this function

    Returns:
        Dict with updated API definition including uuid of the API resource and ready status.

    :meta private:
    """
    logWrapper(logging.DEBUG, 'patchAPIResource', inHandler, 'component/' + name, name, "Patch API", inAPI)

    APIResource = constructAPIResourcePayload(inAPI)
    
    apiReadyStatus = False
    returnAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        # only patch if the API resource spec has changed

        #get current api resource and compare it to APIResource
        apiObj = custom_objects_api.get_namespaced_custom_object(
            group = GROUP,                 
            version = VERSION,
            namespace = namespace,
            plural = APIS_PLURAL,
            name = APIResource['metadata']['name'])


        if not(APIResource['spec'] == apiObj['spec']):
            # log the difference
            logWrapper(logging.INFO, 'patchAPIResource', inHandler, 'component/' + name, name, "Comparing new and existing API ", f"Old {APIResource['spec']}")
            logWrapper(logging.INFO, 'patchAPIResource', inHandler, 'component/' + name, name, "Comparing new and existing API ", f"New {apiObj['spec']}")
            logWrapper(logging.INFO, 'patchAPIResource', inHandler, 'component/' + name, name, "Comparing new and existing API ", f"New {(APIResource['spec'] == apiObj['spec'])}")

            apiObj = custom_objects_api.patch_namespaced_custom_object(
                group = GROUP,
                version = VERSION,
                namespace = namespace,
                plural = APIS_PLURAL,
                name = APIResource['metadata']['name'],
                body = APIResource)
            apiReadyStatus = apiObj['status']['implementation']['ready']
            logWrapper(logging.DEBUG, 'patchAPIResource', inHandler, 'component/' + name, name, "API Resource patched", apiObj)
            logWrapper(logging.INFO, 'patchAPIResource', inHandler, 'component/' + name, name, "API patched", APIResource['metadata']['name'])

        if 'status' in apiObj.keys() and 'apiStatus' in apiObj['status'].keys():       
            returnAPIObject = apiObj['status']['apiStatus']
            returnAPIObject["uid"] = apiObj['metadata']['uid']
            if 'implementation' in apiObj['status'].keys():
                returnAPIObject['ready'] =  apiObj['status']['implementation']['ready']
        else:
            returnAPIObject = {"name": APIResource['metadata']['name'], "uid": apiObj['metadata']['uid'], "ready": apiReadyStatus}

    except ApiException as e:
        logWrapper(logging.WARNING, 'patchAPIResource', inHandler, 'component/' + name, name, "API Exception patching", APIResource)
        raise kopf.TemporaryError("Exception patching API custom resource.")
    return returnAPIObject


async def createAPIResource(inAPI, namespace, name, inHandler):
    """Helper function to create or update API Custom objects.

    Args:
        * inAPI (Dict): The API definition 
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource
        * inHandler (String): The name of the handler calling this function

    Returns:
        Dict with API definition including uuid of the API resource and ready status.

    :meta private:
    """
    logWrapper(logging.DEBUG, 'createAPIResource', inHandler, 'component/' + name, name, "Create API", inAPI)

    APIResource = constructAPIResourcePayload(inAPI)
    
    apiReadyStatus = False
    returnAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logWrapper(logging.INFO, 'createAPIResource', inHandler, 'component/' + name, name, "Creating API Custom Object", APIResource)

        apiObj = custom_objects_api.create_namespaced_custom_object(
            group = GROUP,
            version = VERSION,
            namespace = namespace,
            plural = APIS_PLURAL,
            body = APIResource)

        logWrapper(logging.DEBUG, 'createAPIResource', inHandler, 'component/' + name, name, "API Resource created", apiObj)
        logWrapper(logging.INFO, 'createAPIResource', inHandler, 'component/' + name, name, "API created", APIResource['metadata']['name'])
        returnAPIObject = {"name": APIResource['metadata']['name'], "uid": apiObj['metadata']['uid'], "ready": apiReadyStatus}

    except ApiException as e:
        logWrapper(logging.WARNING, 'createAPIResource', inHandler, 'component/' + name, name, "API Exception creating", APIResource)
        logWrapper(logging.WARNING, 'createAPIResource', inHandler, 'component/' + name, name, "API Exception creating", e)
        
        raise kopf.TemporaryError("Exception creating API custom resource.")
    return returnAPIObject


async def createDependentAPIResource(inDependentAPI, namespace, comp_name, cr_name, inHandler):
    """Helper function to create or update API Custom objects.

    Args:
        * inDependentAPI (Dict): The DependentAPI definition 
        * namespace (String): The namespace for the Component and API
        * cr_name (String): The name of the dependent API custom resource
        * inHandler (String): The name of the handler calling this function

    Returns:
        Dict with DependentAPI definition including uuid of the DependentAPI resource and ready status.

    :meta private:
    """
    logWrapper(logging.DEBUG, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "Create DependentAPI", inDependentAPI)

    DependentAPIResource = constructDependentAPIResourcePayload(inDependentAPI, cr_name)
    
    dependentAPIReadyStatus = False
    returnDependentAPIObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        logWrapper(logging.INFO, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "Creating DependentAPI Custom Object", DependentAPIResource)

        dependentAPIObj = custom_objects_api.create_namespaced_custom_object(
            group = GROUP,
            version = DEPENDENTAPI_VERSION,
            namespace = namespace,
            plural = DEPENDENTAPI_PLURAL,
            body = DependentAPIResource)

        logWrapper(logging.DEBUG, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI Resource created", dependentAPIObj)
        logWrapper(logging.INFO, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI created", DependentAPIResource['metadata']['name'])

    except ApiException as e:
        if e.status != HTTP_CONFLICT:
            logWrapper(logging.WARNING, 'createDependentAPIResource', inHandler, 'component/' + comp_name, comp_name, "DependentAPI Exception creating", DependentAPIResource)
            logWrapper(logging.WARNING, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI Exception creating", e)
            raise kopf.TemporaryError("Exception creating DependentAPI custom resource.")
        else:
            # Conflict = try updating existing cr
            logWrapper(logging.INFO, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI already exists", f"Error:{str(e.status)}")
            try:
                dependentAPIObj = custom_objects_api.patch_namespaced_custom_object(
                    group = GROUP,
                    version = DEPENDENTAPI_VERSION,
                    namespace = namespace,
                    plural = DEPENDENTAPI_PLURAL,
                    name = cr_name,
                    body = DependentAPIResource)
                
                logWrapper(logging.DEBUG, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI Resource updated", dependentAPIObj)
                logWrapper(logging.INFO, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI updated", DependentAPIResource['metadata']['name'])
            
            except ApiException as e:
                logWrapper(logging.WARNING, 'createDependentAPIResource', inHandler, 'component/' + comp_name, comp_name, "DependentAPI Exception updating", DependentAPIResource)
                logWrapper(logging.WARNING, 'createDependentAPIResource', inHandler, 'component/' + comp_name, cr_name, "DependentAPI Exception updating", e)
                raise kopf.TemporaryError("Exception creating DependentAPI custom resource.")
            
    returnDependentAPIObject = {"name": DependentAPIResource['metadata']['name'], "uid": dependentAPIObj['metadata']['uid'], "ready": dependentAPIReadyStatus}
    return returnDependentAPIObject
            


# When api adds url address of where api is exposed, update parent Component object
@kopf.on.field(GROUP, VERSION, 'apis', field='status.apiStatus', retries=5)
async def updateAPIStatus(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function to register for status changes in child API resources.
    Processes status updates to the *apiStatus* in the child API Custom resources, so that the Component status reflects a summary of all the childrens status.

    Args:
        * meta (Dict): The metadata from the API resource 
        * spec (Dict): The spec from the yaml API resource showing the intent (or desired state) 
        * status (Dict): The status from the API resource showing the actual state.
        * body (Dict): The entire API resource definition
        * namespace (String): The namespace for the API resource
        * labels (Dict): The labels attached to the API resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the API resource

    Returns:
        No return value.

    :meta public:
    """

    if 'apiStatus' in status.keys():
        if 'url' in status['apiStatus'].keys():
            if 'ownerReferences' in meta.keys():
                # str | the custom object's name
                name = meta['ownerReferences'][0]['name']

                try:
                    custom_objects_api = kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(
                        group = GROUP, 
                        version = VERSION, 
                        namespace = namespace, 
                        plural = COMPONENTS_PLURAL, 
                        name = name)
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + name)
                    else:
                        logger.error(
                            "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                logWrapper(logging.INFO, 'updateAPIStatus', 'updateAPIStatus', 'api/' + name, parent_component['metadata']['name'], "Handler called", "")

                # find the correct array entry to update either in coreAPIs, managementAPIs or securityAPIs
                if 'coreAPIs' in parent_component['status'].keys():
                    for key in range(len(parent_component['status']['coreAPIs'])):
                        if parent_component['status']['coreAPIs'][key]['uid'] == meta['uid']:
                            parent_component['status']['coreAPIs'][key]['url'] = status['apiStatus']['url']
                            logWrapper(logging.INFO, 'updateAPIStatus', 'updateAPIStatus', 'api/' + name, parent_component['metadata']['name'], "Updating parent component coreAPIs APIs with url", status['apiStatus']['url'])
                            if 'developerUI' in status['apiStatus'].keys():
                                parent_component['status']['coreAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']
                if 'managementAPIs' in parent_component['status'].keys():
                    for key in range(len(parent_component['status']['managementAPIs'])):
                        if parent_component['status']['managementAPIs'][key]['uid'] == meta['uid']:
                            parent_component['status']['managementAPIs'][key]['url'] = status['apiStatus']['url']
                            logWrapper(logging.INFO, 'updateAPIStatus', 'updateAPIStatus', 'api/' + name, parent_component['metadata']['name'], "Updating parent component managementAPIs APIs with url", status['apiStatus']['url'])
                            if 'developerUI' in status['apiStatus'].keys():
                                parent_component['status']['managementAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']

                if 'securityAPIs' in parent_component['status'].keys():
                    for key in range(len(parent_component['status']['securityAPIs'])):
                        if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                            parent_component['status']['securityAPIs'][key]['url'] = status['apiStatus']['url']
                            logWrapper(logging.INFO, 'updateAPIStatus', 'updateAPIStatus', 'api/' + name, parent_component['metadata']['name'], "Updating parent component securityAPIs APIs with url", status['apiStatus']['url'])
                            if 'developerUI' in status['apiStatus'].keys():
                                parent_component['status']['securityAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']

                await patchComponent(namespace, name, parent_component, 'updateAPIStatus')

@kopf.on.field(GROUP, VERSION, 'apis', field='status.implementation', retries=5)
async def updateAPIReady(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function to register for status changes in child API resources.
    
    Processes status updates to the *implementation* status in the child API Custom resources, so that the Component status reflects a summary of all the childrens status.

    Args:
        * meta (Dict): The metadata from the API resource 
        * spec (Dict): The spec from the yaml API resource showing the intent (or desired state) 
        * status (Dict): The status from the API resource showing the actual state.
        * body (Dict): The entire API resource definition
        * namespace (String): The namespace for the API resource
        * labels (Dict): The labels attached to the API resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the API resource

    Returns:
        No return value.

    :meta public:
    """

    if 'ready' in status['implementation'].keys():
        if status['implementation']['ready'] == True:
            if 'ownerReferences' in meta.keys():
                # str | the custom object's name
                parent_component_name = meta['ownerReferences'][0]['name']

                try:
                    custom_objects_api = kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(
                        GROUP, VERSION, namespace, COMPONENTS_PLURAL, parent_component_name)
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + parent_component_name)
                    else:
                        logger.error(
                            "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                logWrapper(logging.INFO, 'updateAPIReady', 'updateAPIReady', 'api/' + name, parent_component['metadata']['name'], "Handler called", "")

                # find the correct array entry to update either in coreAPIs, managementAPIs or securityAPIs
                for key in range(len(parent_component['status']['coreAPIs'])):
                    if parent_component['status']['coreAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['coreAPIs'][key]['ready'] = True
                        logWrapper(logging.INFO, 'updateAPIReady', 'updateAPIReady', 'api/' + name, parent_component['metadata']['name'], "Updating component coreAPIs status", status['implementation']['ready'])
                        await patchComponent(namespace, parent_component_name, parent_component, 'updateAPIReady')
                        return
                for key in range(len(parent_component['status']['managementAPIs'])):
                    if parent_component['status']['managementAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['managementAPIs'][key]['ready'] = True
                        logWrapper(logging.INFO, 'updateAPIReady', 'updateAPIReady', 'api/' + name, parent_component['metadata']['name'], "Updating component managementAPIs status", status['implementation']['ready'])
                        await patchComponent(namespace, parent_component_name, parent_component, 'updateAPIReady')
                        return
                for key in range(len(parent_component['status']['securityAPIs'])):
                    if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['securityAPIs'][key]['ready'] = True
                        logWrapper(logging.INFO, 'updateAPIReady', 'updateAPIReady', 'api/' + name, parent_component['metadata']['name'], "Updating component securityAPIs status", status['implementation']['ready'])
                        await patchComponent(namespace, parent_component_name, parent_component, 'updateAPIReady')
                        return



@kopf.on.field(DEPENDENTAPI_GROUP, DEPENDENTAPI_VERSION, DEPENDENTAPI_PLURAL, field='status.implementation', retries=5)
async def updateDepedentAPIReady(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function to register for status changes in child DependentAPI resources.
    
    Processes status updates to the *implementation* status in the child DependentAPI Custom resources, so that the Component status reflects a summary of all the childrens status.

    Args:
        * meta (Dict): The metadata from the API resource 
        * spec (Dict): The spec from the yaml API resource showing the intent (or desired state) 
        * status (Dict): The status from the API resource showing the actual state.
        * body (Dict): The entire API resource definition
        * namespace (String): The namespace for the API resource
        * labels (Dict): The labels attached to the API resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the API resource

    Returns:
        No return value.

    :meta public:
    """
    ### TODO INFO->DEBUG
    logWrapper(logging.INFO, 'updateDepedentAPIReady', 'updateDepedentAPIReady', 'depapi/' + name, "?", f"Handler called with body", f"{body}")
    logWrapper(logging.INFO, 'updateDepedentAPIReady', 'updateDepedentAPIReady', 'depapi/' + name, "?", "Handler called", "")

    if 'ready' in status['implementation'].keys():
        if status['implementation']['ready'] == True:
            depapi_url = safe_get(None, status, 'depapiStatus', 'url') 
            if 'ownerReferences' in meta.keys():
                # str | the custom object's name
                parent_component_name = meta['ownerReferences'][0]['name']

                try:
                    custom_objects_api = kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(
                        GROUP, VERSION, namespace, COMPONENTS_PLURAL, parent_component_name)
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + parent_component_name)
                    else:
                        logger.error(
                            "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                logWrapper(logging.INFO, 'updateDependentAPIReady', 'updateDependentAPIReady', 'depapi/' + name, parent_component['metadata']['name'], "Handler called", "")

                # find the correct array entry to update either in coreDependentAPIs, managementAPIs or securityAPIs
                for key in range(len(parent_component['status']['coreDependentAPIs'])):
                    if parent_component['status']['coreDependentAPIs'][key]['uid'] == meta['uid']:
                        logger.info(parent_component['status']['coreDependentAPIs'][key]['ready'])
                        logger.info(type(parent_component['status']['coreDependentAPIs'][key]['ready']))
                        if parent_component['status']['coreDependentAPIs'][key]['ready'] != True:   # avoid recursion
                            logger.info("patching component!")
                            parent_component['status']['coreDependentAPIs'][key]['ready'] = True
                            parent_component['status']['coreDependentAPIs'][key]['url'] = depapi_url
                            logWrapper(logging.INFO, 'updateDependentAPIReady', 'updateDependentAPIReady', 'depapi/' + name, parent_component['metadata']['name'], "Updating component coreDependentAPIs status", status['implementation']['ready'])
                            await patchComponent(namespace, parent_component_name, parent_component, 'updateDependentAPIReady')
                            return



async def patchComponent(namespace, name, component, inHandler):
    """Helper function to patch a component.

    Args:
        * namespace (String): The namespace for the Component resource
        * name (String): The name of the Component resource
        * component (Dict): The component object.

    Returns:
        No return value.

    :meta private:
    """
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        api_response = custom_objects_api.patch_namespaced_custom_object(
            GROUP, VERSION, namespace, COMPONENTS_PLURAL, name, component)
        logWrapper(logging.DEBUG, 'patchComponent', inHandler, 'api/' + name, component['metadata']['name'], "custom_objects_api.patch_namespaced_custom_object response", api_response)
    except ApiException as e:
        logWrapper(logging.DEBUG, 'patchComponent', inHandler, 'api/' + name, component['metadata']['name'], "Exception when calling api_instance.patch_namespaced_custom_object", e)
        logWrapper(logging.INFO, 'patchComponent', inHandler, 'api/' + name, component['metadata']['name'], "Exception when calling api_instance.patch_namespaced_custom_object - will retry","")

        raise kopf.TemporaryError(
            "Exception when calling api_instance.patch_namespaced_custom_object for component " + name)



# -------------------------------------------------------------------------------
# Make services, deployments, persistentvolumeclaims, jobs, cronjobs, statefulsets, configmap, secret, serviceaccount, role, rolebinding children of the component
# These are resources that we support in a component. There are resources that we don't support (that will generate a warning in the Level 1 CTK:
# ingress - A developer should express a components intent via APIs and not via ingress. The canvas should create any required ingress
# pod, replicaset - a developer should use deployments (for stateless microservices) or statefulsets (for stateful microservices)
# demonset - a component developer should have no need for creating a demonset
# clusterrole, clusterrolebinding - a component developer should have no need for creating a clusterrole, clusterrolebinding they should be using role, rolebinding


@kopf.on.resume('', 'v1', 'services', retries=5)
@kopf.on.create('', 'v1', 'services', retries=5)
async def adopt_service(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'service')

@kopf.on.resume('apps', 'v1', 'deployments', retries=5)
@kopf.on.create('apps', 'v1', 'deployments', retries=5)
async def adopt_deployment(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'deployment')

@kopf.on.resume('', 'v1', 'persistentvolumeclaims', retries=5)
@kopf.on.create('', 'v1', 'persistentvolumeclaims', retries=5)
async def adopt_persistentvolumeclaim(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'persistentvolumeclaim')

@kopf.on.resume('batch', 'v1', 'jobs', retries=5)
@kopf.on.create('batch', 'v1', 'jobs', retries=5)
async def adopt_job(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'job')

@kopf.on.resume('batch', 'v1', 'cronjobs', retries=5)
@kopf.on.create('batch', 'v1', 'cronjobs', retries=5)
async def adopt_cronjob(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'cronjob')

@kopf.on.resume('apps', 'v1', 'statefulsets', retries=5)
@kopf.on.create('apps', 'v1', 'statefulsets', retries=5)
async def adopt_statefulset(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'statefulset')  

@kopf.on.resume('', 'v1', 'configmap', retries=5)
@kopf.on.create('', 'v1', 'configmap', retries=5)
async def adopt_configmap(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'configmap')

@kopf.on.resume('', 'v1', 'secret', retries=5)
@kopf.on.create('', 'v1', 'secret', retries=5)
async def adopt_secret(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'secret')

@kopf.on.resume('', 'v1', 'serviceaccount', retries=5)
@kopf.on.create('', 'v1', 'serviceaccount', retries=5)
async def adopt_serviceaccount(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'serviceaccount')

@kopf.on.resume('rbac.authorization.k8s.io', 'v1', 'role', retries=5)
@kopf.on.create('rbac.authorization.k8s.io', 'v1', 'role', retries=5)
async def adopt_role(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'role')

@kopf.on.resume('rbac.authorization.k8s.io', 'v1', 'rolebinding', retries=5)
@kopf.on.create('rbac.authorization.k8s.io', 'v1', 'rolebinding', retries=5)
async def adopt_rolebinding(meta, spec, body, namespace, labels, name, **kwargs):
    return adopt_kubernetesResource(meta, spec, body, namespace, labels, name, 'rolebinding')

def adopt_kubernetesResource(meta, spec, body, namespace, labels, name, resourceType):

    """ Helper function for adopting any kubernetes resource
    
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

    if 'oda.tmforum.org/componentName' in labels.keys():

        component_name = labels['oda.tmforum.org/componentName']
        logWrapper(logging.INFO, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Handler called", "")
        try:
            parent_component = kubernetes.client.CustomObjectsApi().get_namespaced_custom_object(GROUP, VERSION, namespace, COMPONENTS_PLURAL, component_name)
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logWrapper(logging.WARNING, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Exception when calling custom_objects_api.get_namespaced_custom_object", e)

        newBody = dict(body)  # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        try:
            if resourceType == 'service':
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_service(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'persistentvolumeclaim':
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_persistent_volume_claim(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'deployment':
                api_response = kubernetes.client.AppsV1Api().patch_namespaced_deployment(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'configmap':
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_config_map(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'secret':
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_secret(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'job':
                api_response = kubernetes.client.BatchV1Api().patch_namespaced_job(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)  
            elif resourceType == 'cronjob':
                api_response = kubernetes.client.BatchV1Api().patch_namespaced_cron_job(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'statefulset':
                api_response = kubernetes.client.AppsV1Api().patch_namespaced_stateful_set(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody) 
            elif resourceType == 'role':
                api_response = kubernetes.client.RbacAuthorizationV1Api().patch_namespaced_role(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'rolebinding':
                api_response = kubernetes.client.RbacAuthorizationV1Api().patch_namespaced_role_binding(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            elif resourceType == 'serviceaccount':
                api_response = kubernetes.client.CoreV1Api().patch_namespaced_service_account(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)                
            else:
                logWrapper(logging.ERROR, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Unsupported resource type", resourceType)
                raise kopf.PermanentError("Error adopting - unsupported resource type " + resourceType)

            logWrapper(logging.DEBUG, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Patch " + resourceType + " response", api_response)
            logWrapper(logging.INFO, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Adding component as parent of " + resourceType, component_name)
        except ApiException as e:
            if e.status == HTTP_CONFLICT:  # Conflict = try again
                raise kopf.TemporaryError(
                    "Conflict updating " + resourceType + ".")
            else:
                logWrapper(logging.WARNING, 'adopt_' + resourceType, 'adopt_' + resourceType, resourceType + '/' + name, component_name, "Exception when calling patch " + resourceType, e)

# When Component status changes, update status summary
@kopf.on.field(GROUP, VERSION, COMPONENTS_PLURAL, field='status', retries=5)
async def summary(meta, spec, status, body, namespace, labels, name, **kwargs):

    logWrapper(logging.INFO, 'summary', 'summary', 'component/' + name, name, "Handler called", "")

    coreAPIsummary = ''
    coreDependentAPIsummary = ''
    managementAPIsummary = ''
    securityAPIsummary = ''
    developerUIsummary = ''
    countOfCompleteAPIs = 0
    countOfDesiredAPIs = 0
    countOfCompleteDependentAPIs = 0
    countOfDesiredDependentAPIs = 0
    if 'coreAPIs' in status.keys():
        countOfDesiredAPIs = countOfDesiredAPIs + len(status['coreAPIs'])
        for api in status['coreAPIs']:
            if 'url' in api.keys():
                coreAPIsummary = coreAPIsummary + api['url'] + ' '
                if 'developerUI' in api.keys():
                    developerUIsummary = developerUIsummary + \
                        api['developerUI'] + ' '
                if 'ready' in api.keys():
                    if api['ready'] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1
    if 'coreDependentAPIs' in status.keys():
        countOfDesiredDependentAPIs = countOfDesiredDependentAPIs + len(status['coreDependentAPIs'])
        for depapi in status['coreDependentAPIs']:
            if 'url' in depapi.keys():
                coreDependentAPIsummary = coreDependentAPIsummary + depapi['url'] + ' '
                if 'ready' in depapi.keys():
                    if depapi['ready'] == True:
                        countOfCompleteDependentAPIs = countOfCompleteDependentAPIs + 1
    if 'managementAPIs' in status.keys():  
        countOfDesiredAPIs = countOfDesiredAPIs + len(status['managementAPIs'])                                    
        for api in status['managementAPIs']:
            if 'url' in api.keys():
                managementAPIsummary = managementAPIsummary + api['url'] + ' '
                if 'developerUI' in api.keys():
                    developerUIsummary = developerUIsummary + \
                        api['developerUI'] + ' '
                if 'ready' in api.keys():
                    if api['ready'] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1
    if 'securityAPIs' in status.keys():  
        countOfDesiredAPIs = countOfDesiredAPIs + len(status['securityAPIs'])                  
        for api in status['securityAPIs']:
            if 'url' in api.keys():
                securityAPIsummary = securityAPIsummary + api['url'] + ' '
                if 'developerUI' in api.keys():
                    developerUIsummary = developerUIsummary + \
                        api['developerUI'] + ' '
                if 'ready' in api.keys():
                    if api['ready'] == True:
                        countOfCompleteAPIs = countOfCompleteAPIs + 1

    status_summary = {}
    status_summary['coreAPIsummary'] = coreAPIsummary
    status_summary['coreDependentAPIsummary'] = coreDependentAPIsummary
    status_summary['managementAPIsummary'] = managementAPIsummary
    status_summary['securityAPIsummary'] = securityAPIsummary
    status_summary['developerUIsummary'] = developerUIsummary
    logWrapper(logging.INFO, 'summary', 'summary', 'component/' + name, name, "Creating summary - completed API count", str(countOfCompleteAPIs) + "/" + str(countOfDesiredAPIs))

    status_summary['deployment_status'] = 'In-Progress-CompCon'
    if countOfCompleteAPIs == countOfDesiredAPIs:
        status_summary['deployment_status'] = 'In-Progress-SecCon'
        if (('security_client_add/status.summary/status.deployment_status' in status.keys()) and (status['security_client_add/status.summary/status.deployment_status']['listenerRegistered'] == True)):
            status_summary['deployment_status'] = 'In-Progress-DepApi'
            if countOfCompleteDependentAPIs == countOfDesiredDependentAPIs:
                status_summary['deployment_status'] = 'Complete'
    logWrapper(logging.INFO, 'summary', 'summary', 'component/' + name, name, "Creating summary - deployment status", status_summary['deployment_status'])

    return status_summary

async def createPublishedNotificationResource(definition, namespace, name, inHandler):
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
    logWrapper(logging.INFO, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "Create PublishedNotification", definition)

    PublishedNotificationResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": "PublishedNotification",
        "metadata": {},
        "spec": {}
    }

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(PublishedNotificationResource)

    newName = (PublishedNotificationResource['metadata']['ownerReferences'][0]['name'] + '-' + definition['name']).lower()

    PublishedNotificationResource['metadata']['name'] = newName
    PublishedNotificationResource['spec'] = definition;

    returnPublishedNotificationObject = {}
    
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        try:
            custom_objects_api.get_namespaced_custom_object(
                group = GROUP,
                version = VERSION,
                namespace = namespace,
                plural = PUBLISHEDNOTIFICATIONS_PLURAL,
                name = newName
            )
        except ApiException as e:
            if e.status == HTTP_NOT_FOUND:
                apiObj = custom_objects_api.create_namespaced_custom_object(
                    group = GROUP,
                    version = VERSION,
                    namespace = namespace,
                    plural = PUBLISHEDNOTIFICATIONS_PLURAL,
                    body = PublishedNotificationResource
                )

                logWrapper(logging.INFO, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "PublishedNotification patch status", "")
                custom_objects_api.patch_namespaced_custom_object_status(
                    group = GROUP,
                    version = VERSION,
                    namespace = namespace,
                    plural = PUBLISHEDNOTIFICATIONS_PLURAL,
                    name = newName,
                    field_manager = "componentOperator",
                    body = {
                        "status": {
                            "uid": "",
                            "status": "initializing",
                            "error": ""
                        }
                    }
                )

                logWrapper(logging.INFO, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "PublishedNotification created", PublishedNotificationResource['metadata']['name'])
                returnPublishedNotificationObject = {"name": PublishedNotificationResource['metadata']['name'], "uid": apiObj['metadata']['uid']}
            else:
                logWrapper(logging.WARNING, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "PublishedNotification Exception checking for existing object ", e)
                raise kopf.TemporaryError("Exception creating PublishedNotification custom resource.")
    except ApiException as e:
        logWrapper(logging.DEBUG, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "PublishedNotification Exception creating", e)
        logWrapper(logging.WARNING, 'createPublishedNotificationResource', inHandler, 'component/' + name, name, "Exception", " creating PublishedNotification custom resource - will retry")
        raise kopf.TemporaryError("Exception creating PublishedNotification custom resource.")
    return returnPublishedNotificationObject


async def createSubscribedNotificationResource(definition, namespace, name, inHandler):
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
    logWrapper(logging.INFO, 'createSubscribedNotificationResource', inHandler, 'component/' + name, name, "Create SubscribedNotification", definition)

    SubscribedNotificationResource = {
        "apiVersion": GROUP + "/" + VERSION,
        "kind": "SubscribedNotification",
        "metadata": {},
        "spec": {}
    }
    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(SubscribedNotificationResource)

    newName = (SubscribedNotificationResource['metadata']['ownerReferences'][0]['name'] + '-' + definition['name']).lower()

    SubscribedNotificationResource['metadata']['name'] = newName
    SubscribedNotificationResource['spec'] = definition

    returnSubscribedNotificationObject = {}

    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        try:
            custom_objects_api.get_namespaced_custom_object(
                group = GROUP,
                version = VERSION,
                namespace = namespace,
                plural = SUBSCRIBEDNOTIFICATIONS_PLURAL,
                name = newName
            )
        except ApiException as e:
            if e.status == HTTP_NOT_FOUND:
                apiObj = custom_objects_api.create_namespaced_custom_object(
                    group = GROUP,
                    version = VERSION,
                    namespace = namespace,
                    plural = SUBSCRIBEDNOTIFICATIONS_PLURAL,
                    body = SubscribedNotificationResource
                )

                logWrapper(logging.INFO, 'createSubscribedNotificationResource', inHandler, 'component/' + name, name, "SubscribedNotification patch status", "")


                custom_objects_api.patch_namespaced_custom_object_status(
                    group = GROUP,
                    version = VERSION,
                    namespace = namespace,
                    plural = SUBSCRIBEDNOTIFICATIONS_PLURAL,
                    name = newName,
                    field_manager = "componentOperator",
                    body = {
                        "status": {
                            "uid": "",
                            "status": "initializing",
                            "error": ""
                        }
                    }
                )

                logWrapper(logging.INFO, 'createSubscribedNotificationResource', inHandler, 'component/' + name, name, "SubscribedNotification created", SubscribedNotificationResource['metadata']['name'])
                returnSubscribedNotificationObject = {"name": SubscribedNotificationResource['metadata']['name'], "uid": apiObj['metadata']['uid']}
            else:
                raise kopf.TemporaryError("Exception creating SubscribedNotification custom resource.")
    except ApiException as e:
        logWrapper(logging.DEBUG, 'createSubscribedNotificationResource', inHandler, 'component/' + name, name, "SubscribedNotification Exception creating", e)
        logWrapper(logging.WARNING, 'createSubscribedNotificationResource', inHandler, 'component/' + name, name, "Exception", " creating SubscribedNotification custom resource - will retry")
        raise kopf.TemporaryError("Exception creating SubscribedNotification custom resource.")

    return returnSubscribedNotificationObject


def logWrapper(logLevel, functionName, handlerName, resourceName, componentName, subject, message):
    """Helper function to standardise logging output.
    
    Args:
        * logLevel (Number): The level to log e.g. logging.INFO
        * functionName (String): The name of the function calling the logWrapper
        * handlerName (String): The name of the handler calling the logWrapper
        * resourceName (String): The name of the resource being logged
        * componentName (String): The name of the component being logged
        * subject (String): The subject of the log message
        * message (String): The message to be logged - can contain relavant data
    
    Returns:
        No return value.
    """
    logger.log(logLevel, f"[{componentName}|{resourceName}|{handlerName}|{functionName}] {subject}: {message}")
    return
