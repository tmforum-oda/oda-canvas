"""Kubernetes operator for ODA Component custom resources.

Normally this module is deployed as part of an ODA Canvas. It uses the kopf kubernetes operator framework (https://kopf.readthedocs.io/).
It registers handler functions for:

1. New ODA Components - to create, update or delete child API custom resources. see `exposedAPIs <#componentOperator.componentOperator.exposedAPIs>`_ and `securityAPIs <#componentOperator.componentOperator.securityAPIs>`_
2. For status updates in the child API Custom resources, so that the Component status reflects a summary of all the childrens status. see `updateAPIStatus <#componentOperator.componentOperator.updateAPIStatus>`_ and `updateAPIReady <#componentOperator.componentOperator.updateAPIReady>`_
3. For new Services, Deployments, PersistentVolumeClaims that have a oda.tmforum.org/componentName label. These resources are updated to become children of the ODA Component resource. see `adopt_deployment <#componentOperator.componentOperator.adopt_deployment>`_ , `adopt_persistentvolumeclaim <#componentOperator.componentOperator.adopt_persistentvolumeclaim>`_ and `adopt_service <#componentOperator.componentOperator.adopt_service>`_
"""

import kopf
import kubernetes.client
import logging
from kubernetes.client.rest import ApiException
import os

# Setup logging
logging_level = os.environ.get('LOGGING', logging.INFO)
print('Logging set to ', logging_level)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger('ComponentOperator')
logger.setLevel(int(logging_level))

# Constants
HTTP_CONFLICT = 409
HTTP_NOT_FOUND = 404
GROUP = "oda.tmforum.org"
VERSION = "v1alpha2"
APIS_PLURAL = "apis"
COMPONENTS_PLURAL = "components"

@kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components')
async def exposedAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
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
        Dict: The exposedAPIs status that is put into the component envelope status field.

    :meta public:
    """
    logger.debug(
        f"[exposedAPIs/{namespace}/{name}] handler called with spec: {spec}")
    apiChildren = []

    # compare desired state (spec) with actual state (status) and initiate changes
    if status:  # if status exists (i.e. this is not a new component)
        # update a component - look in old and new to see if we need to delete any API resources
        oldExposedAPIs = status['exposedAPIs']
        newExposedAPIs = spec['coreFunction']['exposedAPIs']
        # find apis in old that are missing in new
        deletedAPIs = []
        for oldAPI in oldExposedAPIs:
            found = False
            for newAPI in newExposedAPIs:
                if oldAPI['name'] == name + '-' + newAPI['name']:
                    found = True
                    resultStatus = createOrPatchAPIResource(
                        False, newAPI, namespace, name)
                    apiChildren.append(resultStatus)
            if not found:
                deleteAPI(oldAPI['name'], name, status, namespace)

    # get exposed APIS
    exposedAPIs = spec['coreFunction']['exposedAPIs']
    logger.debug(f"exposedAPIs: {exposedAPIs}")

    for exposedAPI in exposedAPIs:
        # check if we have already patched this API
        alreadyProcessed = False
        for processedAPI in apiChildren:
            logger.info(
                f"Comparing {processedAPI['name']} to {name + '-' + exposedAPI['name']}")
            if processedAPI['name'] == name + '-' + exposedAPI['name']:
                alreadyProcessed = True
            # logger.info(exposedAPI)
        if alreadyProcessed == False:
            resultStatus = createOrPatchAPIResource(
                True, exposedAPI, namespace, name)
            apiChildren.append(resultStatus)

    # Update the parent's status.
    return apiChildren


def deleteAPI(deleteAPIName, componentName, status, namespace):
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
    logger.debug(f'[deleteAPI/{namespace}/{componentName}] Delete API {deleteAPIName} if it appears in new status (i.e. it had been created)')
    for api in status['exposedAPIs']:
        if api['name'] == deleteAPIName:
            logger.info(f"[deleteAPI/{namespace}/{componentName}] delete api {api['name']}")
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            try:
                api_response = custom_objects_api.delete_namespaced_custom_object(
                    group = GROUP, 
                    version = VERSION, 
                    namespace=namespace, 
                    plural = APIS_PLURAL, 
                    name=api['name'])
                logger.debug(f"[deleteAPI/{namespace}/{api['name']}] api_response = {api_response}")
            except ApiException as e:
                logger.error(f"[deleteAPI/{namespace}/{api['name']}] Exception when calling CustomObjectsApi->delete_namespaced_custom_object: {e}")


@kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components')
async def securityAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for **security** part of new or updated components.
    
    Processes the **security** part of the component envelope and creates the child API resources.

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

    logger.debug(f"[securityAPIs/{namespace}/{name}] handler called with spec: {spec}")

    apiChildren = {}

    # get security exposed APIS
    try:
        partyRole = spec['security']['partyrole']
        partyRole['name'] = 'partyrole'
        logger.debug(f"Status {status}")

        componentDeployedPreviously = False
        if status:
            if 'securityAPIs' in status.keys():
                if 'partyrole' in status['securityAPIs'].keys():
                    logger.debug('Existing partyrole api')
                    componentDeployedPreviously = True
        if componentDeployedPreviously:
            apiChildren['partyrole'] = createOrPatchAPIResource(
                False, partyRole, namespace, name)
        else:
            apiChildren['partyrole'] = createOrPatchAPIResource(
                True, partyRole, namespace, name)
    except KeyError:
        logger.warning(f"[securityAPIs/{namespace}/{name}] component {name} has no partyrole property")

    return apiChildren


def createOrPatchAPIResource(inCreate, inAPI, namespace, name):
    """Helper function to create or update API Custom objects.
    
    Args:
        * inCreate (Boolean): *True* to create a new API resource; *False* to patch an existing API resource 
        * inAPI (Dict): The API definition 
        * namespace (String): The namespace for the Component and API
        * name (String): The name of the API resource

    Returns:
        Dict with updated API definition including uuid of the API resource and ready status.

    :meta private:
    """
    logger.debug(f"[createOrPatchAPIResource/{namespace}/{name}] API resource : {inAPI}")

    my_resource = {
        "apiVersion": "oda.tmforum.org/v1alpha2",
        "kind": "api",
        "metadata": {},
        "spec": {
        }
    }

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(my_resource)
    logger.debug(f"my_resource (adopted): {my_resource}")
    newName = (my_resource['metadata']['ownerReferences'][0]['name'] + '-' + inAPI['name']).lower()
    my_resource['metadata']['name'] = newName
    my_resource['spec'] = inAPI
    if 'developerUI' in inAPI.keys():
        my_resource['spec']['developerUI'] = inAPI['developerUI']
    apiReadyStatus = False
    returnAPIObject = {}
    # create the resource
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        #apiObj = {"metadata":{"uid": "test"}}
        if inCreate:
            apiObj = custom_objects_api.create_namespaced_custom_object(
                group = GROUP,
                version = VERSION,
                namespace = namespace,
                plural = APIS_PLURAL,
                body = my_resource)
            logger.debug(f"Resource created: {apiObj}")
            logger.info(
                f"[createOrPatchAPIResource/{namespace}/{name}] creating api resource {my_resource['metadata']['name']}")
            returnAPIObject = {"name": my_resource['metadata']['name'], "uid": apiObj['metadata']['uid'], "ready": apiReadyStatus}
        else:
            # only patch if the API resource spec has changed

            #get current api resource and compare it to my_resource
            apiObj = custom_objects_api.get_namespaced_custom_object(
                group = GROUP,                 
                version = VERSION,
                namespace = namespace,
                plural = APIS_PLURAL,
                name = newName)

            logger.debug(
                f"[createOrPatchAPIResource/{namespace}/{name}] comparing {my_resource['spec']} to {apiObj['spec']}")
            if not(my_resource['spec'] == apiObj['spec']):
                apiObj = custom_objects_api.patch_namespaced_custom_object(
                    group = GROUP,
                    version = VERSION,
                    namespace = namespace,
                    plural = APIS_PLURAL,
                    name = newName,
                    body = my_resource)
                apiReadyStatus = apiObj['status']['implementation']['ready']
                logger.debug(f"Resource patched: {apiObj}")
                logger.info(
                    f"[createOrPatchAPIResource/{namespace}/{name}] patching api resource {my_resource['metadata']['name']}")
            returnAPIObject = apiObj['status']['apiStatus']
            returnAPIObject["uid"] = apiObj['metadata']['uid']
            if 'implementation' in apiObj['status'].keys():
                returnAPIObject['ready'] =  apiObj['status']['implementation']['ready']


    except ApiException as e:
        logger.warning(
            f"Exception when calling api.create_namespaced_custom_object: error: {e} API resource: {my_resource}")
        raise kopf.TemporaryError("Exception creating API custom resource.")
    return returnAPIObject


# When api adds url address of where api is exposed, update parent Component object
@kopf.on.field('oda.tmforum.org', 'v1alpha2', 'apis', field='status.apiStatus')
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

    logger.debug(f"status: {status}")
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

                # find the correct array entry to update either in exposedAPIs or securityAPIs

                logger.debug(f'Updating parent component APIs')
                for key in range(len(parent_component['status']['exposedAPIs'])):
                    logger.debug(f"COMPARING {parent_component['status']['exposedAPIs'][key]['uid']} TO {meta['uid']} FOR KEY {key}")

                    if parent_component['status']['exposedAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['exposedAPIs'][key]['url'] = status['apiStatus']['url']
                        logger.info(f"Updating parent component exposedAPIs APIs with url {status['apiStatus']['url']}")

                        if 'developerUI' in status['apiStatus'].keys():
                            parent_component['status']['exposedAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']
                for key in (parent_component['status']['securityAPIs']):
                    if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['securityAPIs'][key]['url'] = status['apiStatus']['url']
                        logger.info(f"Updating parent component securityAPIs APIs with url {status['apiStatus']['url']}")
                        if 'developerUI' in status['apiStatus'].keys():
                            parent_component['status']['securityAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']
                summaryAndUpdate(status, namespace, name, parent_component)

# When api confirms implementation is ready, update parent Component object


@kopf.on.field('oda.tmforum.org', 'v1alpha2', 'apis', field='status.implementation')
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
    logger.debug(f"status: {status}")
    if 'ready' in status['implementation'].keys():
        if status['implementation']['ready'] == True:
            if 'ownerReferences' in meta.keys():
                # str | the custom object's name
                name = meta['ownerReferences'][0]['name']

                try:
                    custom_objects_api = kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(
                        GROUP, VERSION, namespace, COMPONENTS_PLURAL, name)
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + name)
                    else:
                        logger.error(
                            "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                # find the correct array entry to update either in exposedAPIs or securityAPIs
                for key in range(len(parent_component['status']['exposedAPIs'])):
                    if parent_component['status']['exposedAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['exposedAPIs'][key]['ready'] = True
                for key in (parent_component['status']['securityAPIs']):
                    if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['securityAPIs'][key]['ready'] = True
                summaryAndUpdate(status, namespace, name, parent_component)


def summaryAndUpdate(status, namespace, name, parent_component):
    """Helper function to get all the exposed APIs in the status, create a summary string and then patch the component custom definition.
    
    Args:
        * status (Dict): The status from the API resource showing the actual state.
        * namespace (String): The namespace for the API resource
        * name (String): The name of the API resource
        * parent_component (Dict): The parent component object.
        * plural (String): The custom resource's plural name e.g. *components*
        * group (String): The custom resource's group e.g. *oda.tmforum.org*
        * version (String): The custom resource's version e.g. *v1alpha2*

    Returns:
        Dict with updated API definition including uuid of the API resource and ready status.

    :meta private:
    """
    
    exposedAPIsummary = ''
    developerUIsummary = ''
    countOfCompleteAPIs = 0
    for api in parent_component['status']['exposedAPIs']:
        if 'url' in api.keys():
            exposedAPIsummary = exposedAPIsummary + api['url'] + ' '
            if 'developerUI' in api.keys():
                developerUIsummary = developerUIsummary + \
                    api['developerUI'] + ' '
            if api['ready'] == True:
                countOfCompleteAPIs = countOfCompleteAPIs + 1
    for api in parent_component['status']['securityAPIs']:
        if 'url' in parent_component['status']['securityAPIs'][api].keys():
            if parent_component['status']['securityAPIs'][api]['ready'] == True:
                countOfCompleteAPIs = countOfCompleteAPIs + 1
    parent_component['status']['exposedAPIsummary'] = exposedAPIsummary
    parent_component['status']['developerUIsummary'] = developerUIsummary
    if countOfCompleteAPIs == (len(parent_component['status']['exposedAPIs']) + len(parent_component['status']['securityAPIs'])):
        parent_component['status']['deployment_status'] = 'Complete'
    else:
        parent_component['status']['deployment_status'] = 'In-Progress'
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        api_response = custom_objects_api.patch_namespaced_custom_object(
            GROUP, VERSION, namespace, COMPONENTS_PLURAL, name, parent_component)
        logger.info(
            f"[summaryAndUpdate/{namespace}/{name}] updated status to parent component: {name}")
        logger.debug(f"api_response {api_response}")
    except ApiException as e:
        logger.warning(
            "Exception when calling api_instance.patch_namespaced_custom_object: %s", e)
        raise kopf.TemporaryError(
            "Exception when calling api_instance.patch_namespaced_custom_object for component " + name)


# -------------------------------------------------------------------------------
# Make services, deployments and persistentvolumeclaims children of the component

@kopf.on.resume('', 'v1', 'services')
@kopf.on.create('', 'v1', 'services')
async def adopt_service(meta, spec, body, namespace, labels, name, **kwargs):
    """Handler function for new services
    
    If the service has an oda.tmforum.org/componentName label, it makes the service a child of the named component.
    This can help with navigating around the different resources that belong to the component. It also ensures that the kubernetes garbage collection
    will delete these resources automatically if the component is deleted.

    Args:
        * meta (Dict): The metadata from the yaml service definition 
        * spec (Dict): The spec from the yaml service definition showing the intent (or desired state) 
        * status (Dict): The status from the yaml service definition showing the actual state.
        * body (Dict): The entire yaml service definition
        * namespace (String): The namespace for the service
        * labels (Dict): The labels attached to the service. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the service

    Returns:
        No return value.

    :meta public:
    """
    logger.debug(
        f"[adopt_service/{namespace}/{name}] handler called with spec: {spec}")
    logger.debug("adopt_service called for service - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")

    if 'oda.tmforum.org/componentName' in labels.keys():

        # get the parent component object
        # str | the custom object's name
        component_name = labels['oda.tmforum.org/componentName']
        try:
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(
                GROUP, VERSION, namespace, COMPONENTS_PLURAL, component_name)
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError(
                    "Cannot find parent component " + component_name)
            else:
                logger.error(
                    "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

        # append oener reference to parent component
        newBody = dict(body)  # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            api_response = core_api_instance.patch_namespaced_service(
                newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug(
                'Patch service with owner. api_response = %s', api_response)
            logger.info(
                f'[adopt_service/{namespace}/{name}] Adding component {component_name} as parent of service')
        except ApiException as e:
            if e.status == HTTP_CONFLICT:  # Conflict = try again
                raise kopf.TemporaryError("Conflict updating service.")
            else:
                logger.error(
                    "Exception when calling core_api_instance.patch_namespaced_service: %s", e)


@kopf.on.resume('apps', 'v1', 'deployments')
@kopf.on.create('apps', 'v1', 'deployments')
async def adopt_deployment(meta, spec, body, namespace, labels, name, **kwargs):
    """ Handler function for new deployments
    
    If the deployment has an oda.tmforum.org/componentName label, it makes the deployment a child of the named component.
    This can help with navigating around the different resources that belong to the component. It also ensures that the kubernetes garbage collection
    will delete these resources automatically if the component is deleted.

    Args:
        * meta (Dict): The metadata from the yaml deployment definition 
        * spec (Dict): The spec from the yaml deployment definition showing the intent (or desired state) 
        * status (Dict): The status from the yaml deployment definition showing the actual state.
        * body (Dict): The entire yaml deployment definition
        * namespace (String): The namespace for the deployment
        * labels (Dict): The labels attached to the deployment. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the deployment

    Returns:
        No return value.

    :meta public:
    """
    logger.debug(
        f"[adopt_deployment/{namespace}/{name}] handler called with spec: {spec}")
    logger.debug("adopt_deployment called for deployment - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")

    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        # str | the custom object's name
        component_name = labels['oda.tmforum.org/componentName']
        try:
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(
                GROUP, VERSION, namespace, COMPONENTS_PLURAL, component_name)
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError(
                    "Cannot find parent component " + component_name)
            else:
                logger.error(
                    "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

        newBody = dict(body)  # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        apps_api_instance = kubernetes.client.AppsV1Api()
        try:
            api_response = apps_api_instance.patch_namespaced_deployment(
                newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug(
                'Patch deployment with owner. api_response = %s', api_response)
            logger.info(
                f'[adopt_deployment/{namespace}/{name}] Adding component {component_name} as parent of deployment')
        except ApiException as e:
            if e.status == HTTP_CONFLICT:  # Conflict = try again
                raise kopf.TemporaryError("Conflict updating deployment.")
            else:
                logger.error(
                    "Exception when calling apps_api_instance.patch_namespaced_deployment: %s", e)


@kopf.on.resume('', 'v1', 'persistentvolumeclaims')
@kopf.on.create('', 'v1', 'persistentvolumeclaims')
async def adopt_persistentvolumeclaim(meta, spec, body, namespace, labels, name, **kwargs):
    """ Handler function for new persistentvolumeclaims
    
    If the persistentvolumeclaim has an oda.tmforum.org/componentName label, it makes the persistentvolumeclaim a child of the named component.
    This can help with navigating around the different resources that belong to the component. It also ensures that the kubernetes garbage collection
    will delete these resources automatically if the component is deleted.

    Args:
        * meta (Dict): The metadata from the yaml persistentvolumeclaim definition 
        * spec (Dict): The spec from the yaml persistentvolumeclaim definition showing the intent (or desired state) 
        * status (Dict): The status from the yaml persistentvolumeclaim definition showing the actual state.
        * body (Dict): The entire yaml persistentvolumeclaim definition
        * namespace (String): The namespace for the persistentvolumeclaim
        * labels (Dict): The labels attached to the persistentvolumeclaim. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the persistentvolumeclaim

    Returns:
        No return value.

    :meta public:
    """

    logger.debug(
        f"[adopt_persistentvolumeclaim/{namespace}/{name}] handler called with spec: {spec}")
    logger.debug("adopt_persistentvolumeclaim called for persistentvolumeclaim - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")

    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        # str | the custom object's name
        component_name = labels['oda.tmforum.org/componentName']
        try:
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(
                GROUP, VERSION, namespace, COMPONENTS_PLURAL, component_name)
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError(
                    "Cannot find parent component " + component_name)
            else:
                logger.error(
                    "Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

        newBody = dict(body)  # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            logger.debug(
                f"[{namespace}/{name}] core_api_instance.patch_namespaced_persistent_volume_claim")
            api_response = core_api_instance.patch_namespaced_persistent_volume_claim(
                newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug(
                'Patch deployment with owner. api_response = %s', api_response)
            logger.info(
                f'[adopt_persistentvolumeclaim/{namespace}/{name}] Adding {component_name} as parent of persistentvolumeclaim')
        except ApiException as e:
            if e.status == HTTP_CONFLICT:  # Conflict = try again
                raise kopf.TemporaryError(
                    "Conflict updating persistentvolumeclaim.")
            else:
                logger.error(
                    "Exception when calling apps_api_instance.patch_namespaced_persistent_volume_claim: %s", e)
