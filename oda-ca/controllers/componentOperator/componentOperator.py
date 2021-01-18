import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os
print('Logging set to ',os.environ.get('LOGGING'))

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 30))) #Logging level default = WARNING
componentNameSpaceList = os.getenv('COMPONENT_NAMESPACE', 30).split(',')
logging.info("Component controller monitoring namespaces: %s", ''.join(componentNameSpaceList))


@kopf.on.create('', 'v1', 'services')
def adopt_service(meta, spec, body, **kwargs):
    logging.debug("adopt_service called for service - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")    
    namespace = meta.get('namespace')
    logging.debug("Checking if namespace %s is in componentNameSpaceList %s ", namespace, ''.join(componentNameSpaceList))
    if namespace in componentNameSpaceList:
        if 'labels' in meta.keys():
            labels = meta.get('labels')
            logging.debug("Checking if oda.tmforum.org/componentName is in labels %s ", ''.join(labels.keys()))
            if 'oda.tmforum.org/componentName' in labels.keys():
                # get the component object
                api_instance =  kubernetes.client.CustomObjectsApi()
                group = 'oda.tmforum.org' # str | the custom resource's group
                version = 'v1alpha1' # str | the custom resource's version
                plural = 'components' # str | the custom resource's plural name
                name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
                try:
                    parent_component = api_instance.get_namespaced_custom_object(group, version, namespace, plural, name)
                except ApiException as e:
                    logging.warning("Exception when getting parent component: calling api_instance.get_namespaced_custom_object: %s\n" % e)
                    raise kopf.TemporaryError("Exception updating service.")
                
                newBody = dict(body) # cast the service body to a dict

                kopf.append_owner_reference(newBody, owner=parent_component)
                core_api_instance = kubernetes.client.CoreV1Api()
                try:
                    api_response = core_api_instance.patch_namespaced_service(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
                    logging.debug('Patch service with owner. api_response = %s', api_response)
                    logging.info('Adding component %s as parent of service %s', name, meta.get('name'))
                except ApiException as e:   
                    logging.warning("Exception when calling core_api_instance.patch_namespaced_service:")
                    logging.info(e)
                    raise kopf.TemporaryError("Exception updating service.")





@kopf.on.create('apps', 'v1', 'deployments')
def adopt_deployment(meta, spec, body, **kwargs):
    logging.debug("Create called for deployment - if it is part of a component (oda.tmforum.org/componentName as a label) then make it a child ")
    namespace = meta.get('namespace')
    logging.debug("Checking if namespace %s is in componentNameSpaceList %s ", namespace, ''.join(componentNameSpaceList))
    if namespace in componentNameSpaceList:   
        if 'labels' in meta.keys():
            labels = meta.get('labels')
            if isinstance(labels, dict):
                if 'oda.tmforum.org/componentName' in labels.keys():
                    # get the component object
                    api_instance =  kubernetes.client.CustomObjectsApi()
                    group = 'oda.tmforum.org' # str | the custom resource's group
                    version = 'v1alpha1' # str | the custom resource's version
                    plural = 'components' # str | the custom resource's plural name
                    name = labels['oda.tmforum.org/componentName'] # str | the custom object's name
                    try:
                        parent_component = api_instance.get_namespaced_custom_object(group, version, namespace, plural, name)
                    except ApiException as e:
                        logging.warning("Exception when getting parent component: calling api_instance.get_namespaced_custom_object: %s\n" % e)
                        raise kopf.TemporaryError("Exception updating deployment.")
                        
                    newBody = dict(body) # cast the service body to a dict    
                    kopf.append_owner_reference(newBody, owner=parent_component)
                    apps_api_instance = kubernetes.client.AppsV1Api()
                    try:
                        api_response = apps_api_instance.patch_namespaced_deployment(newBody['metadata']['name'], newBody['metadata']['namespace'], newBody)
                        logging.debug('Patch deployment with owner. api_response = %s', api_response)
                    except ApiException as e:
                        logging.warning("Exception when calling apps_api_instance.patch_namespaced_deployment:")
                        logging.info(e)
                        raise kopf.TemporaryError("Exception updating deployment.")





@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'components')
def exposedAPIs(meta, spec, status, **kwargs):

    logging.debug(f"oda.tmforum.org components is called with spec: {spec}")
    logging.debug(f"oda.tmforum.org components is called with status: {status}")
    namespace = meta.get('namespace')
    logging.debug("Checking if namespace %s is in componentNameSpaceList %s ", namespace, ''.join(componentNameSpaceList))
    if namespace in componentNameSpaceList:   

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
                logging.warning("Exception when calling api.create_namespaced_custom_object:")
                logging.info(e)
                raise kopf.TemporaryError("Exception creating API custom resource.")
            apiChildren.append({"name": my_resource['metadata']['name'], "uid": apiObj['metadata']['uid']})

        # Update the parent's status.
        return apiChildren


# When api adds url address of where api is exposed, update parent API object
@kopf.on.field('oda.tmforum.org', 'v1alpha1', 'apis', field='status.ingress')
def api_status(meta, status, spec, **kwargs):
    logging.info(f"Update called for api {meta['name']}")
    logging.debug(f"status: {status}")
    namespace = meta.get('namespace')

    if 'ownerReferences' in meta.keys():

        api_instance = kubernetes.client.CustomObjectsApi()
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha1' # str | the custom resource's version
        plural = 'components' # str | the custom resource's plural name
        name = meta['ownerReferences'][0]['name'] # str | the custom object's name

        try:
            parent_component = api_instance.get_namespaced_custom_object(group, version, namespace, plural, name)

        except ApiException as e:
            logging.warning("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
            raise kopf.TemporaryError("Exception updating service.")

        logging.debug(f"api parent is {parent_component}")

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
            api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_component)
            logging.info(f"Added ip: {status['ingress']['url']} to parent component: {name}")
            logging.debug(f"api_response {api_response}")
        except ApiException as e:
            logging.warning("Exception when calling api_instance.patch_namespaced_custom_object:")
            logging.info(e)
