import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os

# Setup logging 
logging_level = os.environ.get('LOGGING',logging.INFO)
print('Logging set to ',logging_level)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger('ComponentOperator')
logger.setLevel(int(logging_level))

# Constants
CONST_HTTP_CONFLICT = 409
CONST_HTTP_NOT_FOUND = 404


@kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components')
async def exposedAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.debug(f"componentOperator/exposedAPIs called with name:{name}, spec: {spec}")
    apiChildren = []

    # compare desired state (spec) with actual state (status) and initiate changes
    if status: # if status exists (i.e. this is not a new component)
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
                    resultStatus=createOrPatchAPIResource(False, newAPI, namespace, name)
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
            logger.info(f"Comparing {processedAPI['name']} to {name + '-' + exposedAPI['name']}")
            if processedAPI['name'] == name + '-' + exposedAPI['name']:
                alreadyProcessed = True
            # logger.info(exposedAPI)
        if alreadyProcessed == False:
            resultStatus=createOrPatchAPIResource(True, exposedAPI, namespace, name)
            apiChildren.append(resultStatus)

    # Update the parent's status.
    return apiChildren

def deleteAPI(deleteAPIName, componentName, status, namespace):
    logger.debug(f'[deleteAPI/{namespace}/{componentName}] Delete API {deleteAPIName} if it appears in new status (i.e. it had been created)')
    for api in status['exposedAPIs']:
        if api['name'] == deleteAPIName:
            logger.info(f"[deleteAPI/{namespace}/{componentName}] delete api {api['name']}")
            # Create an instance of the API class
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            try:
                api_response = custom_objects_api.delete_namespaced_custom_object(group = 'oda.tmforum.org', version = 'v1alpha2', namespace = namespace, plural = 'apis', name = api['name'])
                logger.debug(api_response)
            except ApiException as e:
                logger.error(f"[{namespace}/{api['name']}]Exception when calling CustomObjectsApi->delete_namespaced_custom_object: {e}")

@kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components')
async def securityAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.debug(f"oda.tmforum.org components securityAPIs is called with spec: {spec}")
    logger.debug(f"oda.tmforum.org components securityAPIs is called with status: {status}")

    apiChildren = {}

    # get security exposed APIS
    try:
        partyRole = spec['security']['partyrole']
        partyRole['name'] = 'partyrole'
        if status: # if status exists (i.e. this is not a new component)
            apiChildren['partyrole'] = createOrPatchAPIResource(False, partyRole, namespace, name)
        else:
            apiChildren['partyrole'] = createOrPatchAPIResource(True, partyRole, namespace, name)
    except KeyError:
        logger.warning(f"oda.tmforum.org components securityAPIs - component {name} has no partyrole property")


    # Update the parent's status.
    return apiChildren

# helper function to create API resource
def createOrPatchAPIResource(inCreate, inAPI, namespace, name):

    # API as custom resource defined as Dict
    logger.debug(f"exposedAPI: {inAPI}")

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
    # create the resource
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()
        #apiObj = {"metadata":{"uid": "test"}}
        if inCreate:
            apiObj = custom_objects_api.create_namespaced_custom_object(
                    group="oda.tmforum.org",
                    version="v1alpha2",
                    namespace=namespace,
                    plural="apis",
                    body=my_resource,
                )
            logger.debug(f"Resource created: {apiObj}")
            logger.info(f"[createOrPatchAPIResource/{namespace}/{name}] creating api resource {my_resource['metadata']['name']}")
        else:
            apiObj = custom_objects_api.patch_namespaced_custom_object(
                    group="oda.tmforum.org",
                    version="v1alpha2",
                    namespace=namespace,
                    plural="apis",
                    name = newName,
                    body=my_resource,
                )
            apiReadyStatus = apiObj['status']['implementation']['ready']
            logger.debug(f"Resource patched: {apiObj}")
            logger.info(f"[createOrPatchAPIResource/{namespace}/{name}] patching api resource {my_resource['metadata']['name']}")

    except ApiException as e:
        logger.warning(f"Exception when calling api.create_namespaced_custom_object: error: {e} API resource: {my_resource}")
        raise kopf.TemporaryError("Exception creating API custom resource.")
    return {"name": my_resource['metadata']['name'], "uid": apiObj['metadata']['uid'], "ready": apiReadyStatus}


# When api adds url address of where api is exposed, update parent Component object
@kopf.on.field('oda.tmforum.org', 'v1alpha2', 'apis', field='status.apiStatus')
async def api_status(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.debug(f"status: {status}")
    if 'apiStatus' in status.keys(): 
        if 'url' in status['apiStatus'].keys(): 
            if 'ownerReferences' in meta.keys():
                group = 'oda.tmforum.org' # str | the custom resource's group
                version = 'v1alpha2' # str | the custom resource's version
                plural = 'components' # str | the custom resource's plural name
                name = meta['ownerReferences'][0]['name'] # str | the custom object's name

                try:
                    custom_objects_api =  kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, name)
                except ApiException as e:
                    if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                        raise kopf.TemporaryError("Cannot find parent component " + name)
                    else:
                        logger.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                # find the correct array entry to update either in exposedAPIs or securityAPIs
                for key in range(len(parent_component['status']['exposedAPIs'])):
                    if parent_component['status']['exposedAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['exposedAPIs'][key]['url'] = status['apiStatus']['url']
                        if 'developerUI' in status['apiStatus'].keys():
                            parent_component['status']['exposedAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']
                for key in (parent_component['status']['securityAPIs']):
                    if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['securityAPIs'][key]['url'] = status['apiStatus']['url']
                        if 'developerUI' in status['apiStatus'].keys():
                            parent_component['status']['securityAPIs'][key]['developerUI'] = status['apiStatus']['developerUI']
                summaryAndUpdate(status, namespace, name, parent_component, plural, group, version)

# When api confirms implementation is ready, update parent Component object
@kopf.on.field('oda.tmforum.org', 'v1alpha2', 'apis', field='status.implementation')
async def api_status(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.debug(f"status: {status}")
    if 'ready' in status['implementation'].keys(): 
        if status['implementation']['ready'] == True:
            if 'ownerReferences' in meta.keys():
                group = 'oda.tmforum.org' # str | the custom resource's group
                version = 'v1alpha2' # str | the custom resource's version
                plural = 'components' # str | the custom resource's plural name
                name = meta['ownerReferences'][0]['name'] # str | the custom object's name

                try:
                    custom_objects_api =  kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, name)
                except ApiException as e:
                    if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                        raise kopf.TemporaryError("Cannot find parent component " + name)
                    else:
                        logger.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                # find the correct array entry to update either in exposedAPIs or securityAPIs
                for key in range(len(parent_component['status']['exposedAPIs'])):
                    if parent_component['status']['exposedAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['exposedAPIs'][key]['ready'] = True
                for key in (parent_component['status']['securityAPIs']):
                    if parent_component['status']['securityAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['securityAPIs'][key]['ready'] = True
                summaryAndUpdate(status, namespace, name, parent_component, plural, group, version)


def summaryAndUpdate(status, namespace, name, parent_component, plural, group, version):

    #get all the exposed APIs in the staus and create a summary string
    exposedAPIsummary = ''
    developerUIsummary = ''
    countOfCompleteAPIs = 0
    for api in parent_component['status']['exposedAPIs']:
        if 'url' in api.keys():
            exposedAPIsummary = exposedAPIsummary + api['url'] + ' '
            if 'developerUI' in api.keys():
                developerUIsummary = developerUIsummary + api['developerUI'] + ' '
            if api['ready']==True:
                countOfCompleteAPIs = countOfCompleteAPIs + 1
    for api in parent_component['status']['securityAPIs']:
        if 'url' in parent_component['status']['securityAPIs'][api].keys():
            if parent_component['status']['securityAPIs'][api]['ready']==True:
                countOfCompleteAPIs = countOfCompleteAPIs + 1
    parent_component['status']['exposedAPIsummary'] = exposedAPIsummary 
    parent_component['status']['developerUIsummary'] = developerUIsummary 
    if countOfCompleteAPIs == (len(parent_component['status']['exposedAPIs']) + len(parent_component['status']['securityAPIs'])):
        parent_component['status']['deployment_status'] = 'Complete'
    else:
        parent_component['status']['deployment_status'] = 'In-Progress'
    try:
        custom_objects_api =  kubernetes.client.CustomObjectsApi()
        api_response = custom_objects_api.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_component)
        logger.info(f"[summaryAndUpdate/{namespace}/{name}] updated status to parent component: {name}")
        logger.debug(f"api_response {api_response}")
    except ApiException as e:
        logger.warning("Exception when calling api_instance.patch_namespaced_custom_object: %s", e)
        raise kopf.TemporaryError("Exception when calling api_instance.patch_namespaced_custom_object for component " + name)


# -------------------------------------------------------------------------------
# Make services, deployments and persistentvolumeclaims children of the component

@kopf.on.resume('', 'v1', 'services')
@kopf.on.create('', 'v1', 'services')
async def adopt_service(meta, spec, body, namespace, labels, name, **kwargs):

    logger.debug("adopt_service called for service - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")    
    logger.debug("Checking if oda.tmforum.org/componentName is in labels %s ", ''.join(labels.keys()))
    if 'oda.tmforum.org/componentName' in labels.keys():

        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha2' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logger.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
        
        #append oener reference to parent component
        newBody = dict(body) # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            api_response = core_api_instance.patch_namespaced_service(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug('Patch service with owner. api_response = %s', api_response)
            logger.info(f'[adopt_service/{namespace}/{name}] Adding component {component_name} as parent of service')
        except ApiException as e:   
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating service.")
            else:
                logger.error("Exception when calling core_api_instance.patch_namespaced_service: %s", e)


@kopf.on.resume('apps', 'v1', 'deployments')
@kopf.on.create('apps', 'v1', 'deployments')
async def adopt_deployment(meta, spec, body, namespace, labels, name, **kwargs):

    logger.debug("Create called for deployment - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")
    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha2' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logger.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
            
        newBody = dict(body) # cast the service body to a dict    
        kopf.append_owner_reference(newBody, owner=parent_component)
        apps_api_instance = kubernetes.client.AppsV1Api()
        try:
            api_response = apps_api_instance.patch_namespaced_deployment(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug('Patch deployment with owner. api_response = %s', api_response)
            logger.info(f'[adopt_deployment/{namespace}/{name}] Adding component {component_name} as parent of deployment')
        except ApiException as e:
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating deployment.")
            else:
                logger.error("Exception when calling apps_api_instance.patch_namespaced_deployment: %s", e)

@kopf.on.resume('', 'v1', 'persistentvolumeclaims')
@kopf.on.create('', 'v1', 'persistentvolumeclaims')
async def adopt_persistentvolumeclaim(meta, spec, body, namespace, labels, name, **kwargs):

    logger.debug("Create called for persistentvolumeclaim - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")
    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha2' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logger.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
            
        newBody = dict(body) # cast the service body to a dict    
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            logger.debug(f"[{namespace}/{name}] core_api_instance.patch_namespaced_persistent_volume_claim")
            api_response = core_api_instance.patch_namespaced_persistent_volume_claim(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logger.debug('Patch deployment with owner. api_response = %s', api_response)
            logger.info(f'[adopt_persistentvolumeclaim/{namespace}/{name}] Adding {component_name} as parent of persistentvolumeclaim')
        except ApiException as e:
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating persistentvolumeclaim.")
            else:
                logger.error("Exception when calling apps_api_instance.patch_namespaced_persistent_volume_claim: %s", e)

