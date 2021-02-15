import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os
 
logging_level = os.environ.get('LOGGING',20)
print('Logging set to ',logging_level)
logger = logging.getLogger()
logger.setLevel(int(logging_level)) #Logging level default = INFO

CONST_HTTP_CONFLICT = 409
CONST_HTTP_NOT_FOUND = 404


@kopf.on.resume('', 'v1', 'services')
@kopf.on.create('', 'v1', 'services')
def adopt_service(meta, spec, body, namespace, labels, name, **kwargs):

    logging.debug("adopt_service called for service - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")    
    logging.debug("Checking if oda.tmforum.org/componentName is in labels %s ", ''.join(labels.keys()))
    if 'oda.tmforum.org/componentName' in labels.keys():

        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logging.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
        
        #append oener reference to parent component
        newBody = dict(body) # cast the service body to a dict
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            api_response = core_api_instance.patch_namespaced_service(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logging.debug('Patch service with owner. api_response = %s', api_response)
            logging.info(f'[{namespace}/{name}] Adding component {component_name} as parent of service')
        except ApiException as e:   
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating service.")
            else:
                logging.error("Exception when calling core_api_instance.patch_namespaced_service: %s", e)





@kopf.on.resume('apps', 'v1', 'deployments')
@kopf.on.create('apps', 'v1', 'deployments')
def adopt_deployment(meta, spec, body, namespace, labels, name, **kwargs):

    logging.debug("Create called for deployment - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")
    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logging.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
            
        newBody = dict(body) # cast the service body to a dict    
        kopf.append_owner_reference(newBody, owner=parent_component)
        apps_api_instance = kubernetes.client.AppsV1Api()
        try:
            api_response = apps_api_instance.patch_namespaced_deployment(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logging.debug('Patch deployment with owner. api_response = %s', api_response)
            logging.info(f'[{namespace}/{name}] Adding component {component_name} as parent of deployment')
        except ApiException as e:
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating deployment.")
            else:
                logging.error("Exception when calling apps_api_instance.patch_namespaced_deployment: %s", e)



@kopf.on.resume('', 'v1', 'persistentvolumeclaims')
@kopf.on.create('', 'v1', 'persistentvolumeclaims')
def adopt_persistentvolumeclaim(meta, spec, body, namespace, labels, name, **kwargs):

    logging.debug("Create called for persistentvolumeclaim - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")
    if 'oda.tmforum.org/componentName' in labels.keys():
        # get the parent component object
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        component_name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
        try:
            custom_objects_api =  kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, component_name)
        except ApiException as e:
            if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                raise kopf.TemporaryError("Cannot find parent component " + component_name)
            else:
                logging.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)
            
        newBody = dict(body) # cast the service body to a dict    
        kopf.append_owner_reference(newBody, owner=parent_component)
        core_api_instance = kubernetes.client.CoreV1Api()
        try:
            logging.info(f"[{namespace}/{name}] core_api_instance.patch_namespaced_persistent_volume_claim")
            api_response = core_api_instance.patch_namespaced_persistent_volume_claim(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
            logging.debug('Patch deployment with owner. api_response = %s', api_response)
            logging.info(f'[{namespace}/{name}] Adding {component_name} as parent of persistentvolumeclaim')
        except ApiException as e:
            if e.status == CONST_HTTP_CONFLICT: # Conflict = try again
                raise kopf.TemporaryError("Conflict updating persistentvolumeclaim.")
            else:
                logging.error("Exception when calling apps_api_instance.patch_namespaced_persistent_volume_claim: %s", e)


@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'components')
def exposedAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"oda.tmforum.org components is called with spec: {spec}")
    logging.debug(f"oda.tmforum.org components is called with status: {status}")
    namespace = meta.get('namespace')

    # get exposed APIS
    exposedAPIs = spec['coreFunction']['exposedAPIs']
    logging.debug(f"exposedAPIs: {exposedAPIs}")

    api = kubernetes.client.CustomObjectsApi()

    apiChildren = []
    for exposedAPI in exposedAPIs:
        # API as custom resource defined as Dict
        logging.debug(f"exposedAPI: {exposedAPI}")

        my_resource = {
            "apiVersion": "oda.tmforum.org/v1alpha1",
            "kind": "api",
            "metadata": {},
            "spec": {
            }
        }

        # Make it our child: assign the namespace, name, labels, owner references, etc.
        kopf.adopt(my_resource)
        logging.debug(f"my_resource (adopted): {my_resource}")
        newName = my_resource['metadata']['ownerReferences'][0]['name'] + '-' + exposedAPI['name']
        my_resource['metadata']['name'] = newName.lower()
        my_resource['spec'] = exposedAPI
        if 'developerUI' in exposedAPI.keys():
            my_resource['spec']['developerUI'] = exposedAPI['developerUI']
        # create the resource
        try:
            apiObj = api.create_namespaced_custom_object(
                    group="oda.tmforum.org",
                    version="v1alpha1",
                    namespace=namespace,
                    plural="apis",
                    body=my_resource,
                )
            logging.debug(f"Resource created: {apiObj}")
        except ApiException as e:
            logging.warning("Exception when calling api.create_namespaced_custom_object: %s", e)
            raise kopf.TemporaryError("Exception creating API custom resource.")
        apiChildren.append({"name": my_resource['metadata']['name'], "uid": apiObj['metadata']['uid']})

    # Update the parent's status.
    return apiChildren


# When api adds url address of where api is exposed, update parent API object
@kopf.on.field('oda.tmforum.org', 'v1alpha1', 'apis', field='status.ingress')
def api_status(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"[{namespace}/{name}] Update called for api ")
    logging.debug(f"status: {status}")
    if 'ingress' in status.keys(): 
        if 'url' in status['ingress'].keys(): 
            if 'ownerReferences' in meta.keys():
                group = 'oda.tmforum.org' # str | the custom resource's group
                version = 'v1alpha1' # str | the custom resource's version
                plural = 'components' # str | the custom resource's plural name
                name = meta['ownerReferences'][0]['name'] # str | the custom object's name

                try:
                    custom_objects_api =  kubernetes.client.CustomObjectsApi()
                    parent_component = custom_objects_api.get_namespaced_custom_object(group, version, namespace, plural, name)
                except ApiException as e:
                    if e.status == CONST_HTTP_NOT_FOUND: # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                        raise kopf.TemporaryError("Cannot find parent component " + name)
                    else:
                        logging.error("Exception when calling custom_objects_api.get_namespaced_custom_object: %s", e)

                # find the correct array entry to update
                for key in range(len(parent_component['status']['exposedAPIs'])):
                    if parent_component['status']['exposedAPIs'][key]['uid'] == meta['uid']:
                        parent_component['status']['exposedAPIs'][key]['url'] = status['ingress']['url']
                        if 'developerUI' in status['ingress'].keys():
                            parent_component['status']['exposedAPIs'][key]['developerUI'] = status['ingress']['developerUI']

                #get all the exposed APIs in the staus and create a summary string
                exposedAPIsummary = ''
                developerUIsummary = ''
                countOfCompleteAPIs = 0
                for api in parent_component['status']['exposedAPIs']:
                    if 'url' in api.keys():
                        exposedAPIsummary = exposedAPIsummary + api['url'] + ' '
                        if 'developerUI' in api.keys():
                            developerUIsummary = developerUIsummary + api['developerUI'] + ' '
                        countOfCompleteAPIs = countOfCompleteAPIs + 1
                parent_component['status']['exposedAPIsummary'] = exposedAPIsummary 
                parent_component['status']['developerUIsummary'] = developerUIsummary 
                if countOfCompleteAPIs == len(parent_component['status']['exposedAPIs']):
                    parent_component['status']['deployment_status'] = 'Complete'
                else:
                    parent_component['status']['deployment_status'] = 'In-Progress'
                try:
                    custom_objects_api =  kubernetes.client.CustomObjectsApi()
                    api_response = custom_objects_api.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_component)
                    logging.info(f"[{namespace}/{name}] Added ip: {status['ingress']['url']} to parent component: {name}")
                    logging.debug(f"api_response {api_response}")
                except ApiException as e:
                    logging.warning("Exception when calling api_instance.patch_namespaced_custom_object: %s", e)
