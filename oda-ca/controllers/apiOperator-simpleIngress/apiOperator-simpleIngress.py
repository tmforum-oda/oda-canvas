import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os

logging_level = os.environ.get('LOGGING',logging.INFO)
print('Logging set to ',logging_level)

kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)

logger = logging.getLogger('APIOperator')
logger.setLevel(int(logging_level))

ingress_class = os.environ.get('INGRESS_CLASS','nginx') 
print('Ingress set to ',ingress_class)

HTTP_SCHEME = "http://"


# structure
#
# create/update spec of this resource - compare desired state (spec) with actual state (status) and initiate changes
#
# register for changes to status of child resources - update the status to reflect those changes. (includes deletion). 
# again, compare desired state and actual state and initiate changes.
#
# Status should have a copy of the spec it has set-out to create with any updates from downstream systems or resources



@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'apis')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'apis')
def apiStatus(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.debug(f"[apiStatus/{namespace}/{name}] apiOperator-simpleIngress/apiStatus called with name:{name}, spec: {spec}")
    return actualToDesiredState(spec, status, namespace, name)


def actualToDesiredState(spec, status, namespace, name): # compare desired state (spec) with actual state (status) and initiate changes
    outputStatus = {}
    if status: # there is a status object
        if 'apiStatus' in status.keys(): # there is an actual state to compare against
            # work out delta between desired and actual state
            apiStatus = status['apiStatus'] # starting point for return status is the previous status
            #check if there is a difference in the ingress we created previously
            if name == apiStatus['name'] and spec['path'] == apiStatus['path'] and spec['port'] == apiStatus['port'] and spec['implementation'] == apiStatus['implementation']:
                # unchanged, so just return previous status
                return apiStatus
            else:
                return createOrPatchIngress(True, spec, namespace, name)
    return createOrPatchIngress(False, spec, namespace, name)

def createOrPatchIngress(patch, spec, namespace, name):            
    # get API details and create ingress
    client = kubernetes.client
    try:
        networking_v1_beta1_api = client.NetworkingV1beta1Api()

        hostname = None
        if 'hostname' in spec.keys():
            hostname=spec['hostname']

        ingress_spec=client.NetworkingV1beta1IngressSpec(
            rules=[client.NetworkingV1beta1IngressRule(
                host=hostname,
                http=client.NetworkingV1beta1HTTPIngressRuleValue(
                    paths=[client.NetworkingV1beta1HTTPIngressPath(
                        path=spec['path'],
                        backend=client.NetworkingV1beta1IngressBackend(
                            service_port=spec['port'],
                            service_name=spec['implementation'])
                    )]
                )
            )]
        )
        body = {
            "apiVersion": "networking.k8s.io/v1beta1",
            "kind": "Ingress",
            "metadata": {
                "name": name,
                "annotations": {"kubernetes.io/ingress.class": ingress_class}
                },
            "spec": ingress_spec
        }
        # Make it our child: assign the namespace, name, labels, owner references, etc.
        kopf.adopt(body)
        logger.debug(f"[createOrPatchIngress/{namespace}/{name}] body (adopted): {body}")
        if patch == True:
            # patch the resource
            logger.debug(f"[createOrPatchIngress/{namespace}/{name}] Patching ingress with: {body}")
            ingressResource = networking_v1_beta1_api.patch_namespaced_ingress(
                name=name,
                namespace=namespace,
                body=body
            )
            logger.debug(f"[createOrPatchIngress/{namespace}/{name}] ingressResource patched: {ingressResource}")
            logger.info(f"[createOrPatchIngress/{namespace}/{name}] ingress resource patched with name {name}")
            updateImplementationStatus(namespace, spec['implementation'])

            # update ingress status
            mydict = ingressResource.to_dict()
            apistatus = {'apiStatus': {"name": name, "uid": mydict['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            if 'status' in mydict.keys():
                if 'load_balancer' in mydict['status'].keys():
                    loadBalancer = mydict['status']['load_balancer']

                    if 'ingress' in loadBalancer.keys():
                        ingress = loadBalancer['ingress']
                        
                        if isinstance(ingress, list):
                            if len(ingress)>0:
                                ingressTarget = ingress[0]
                                apistatus = buildAPIStatus(spec, apistatus, ingressTarget)
                                logger.debug(f"[createOrPatchIngress/{namespace}/{name}] apistatus = {apistatus}")

            return apistatus['apiStatus']
        else:
            # create the resource
            logger.debug(f"[createOrPatchIngress/{namespace}/{name}] Creating ingress with: {body}")
            ingressResource = networking_v1_beta1_api.create_namespaced_ingress(
                namespace=namespace,
                body=body
            )
            logger.debug(f"[createOrPatchIngress/{namespace}/{name}] ingressResource created: {ingressResource}")
            logger.info(f"[createOrPatchIngress/{namespace}/{name}] ingress resource created with name {name}")
            updateImplementationStatus(namespace, spec['implementation'])
            # Update the parent's status.
            mydict = ingressResource.to_dict()
            apistatus = {'apiStatus': {"name": name, "uid": mydict['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            return apistatus['apiStatus']
    except ApiException as e:
        logger.warning("Exception when calling NetworkingV1beta1Api: %s\n" % e)
        raise kopf.TemporaryError("Exception creating ingress.")                  



# in case api is updated, manually update the api implementation status from endpointslice
def updateImplementationStatus(namespace, name):
    # Create an instance of the API class
    logger.debug(f"[updateImplementationStatus/{namespace}/{name}] updateImplementationStatus namespace={namespace} name={name}")

    discovery_api_instance = kubernetes.client.DiscoveryV1beta1Api()
    try:
        api_response = discovery_api_instance.list_namespaced_endpoint_slice(namespace, label_selector='kubernetes.io/service-name=' + name)
        if len(api_response.items) > 0:
            createAPIImplementationStatus(name, api_response.items[0].endpoints, namespace)
    except ValueError as e: # if there are no endpoints it will create a ValueError
        logger.info(f"[updateImplementationStatus/{namespace}/{name}] ValueError when calling DiscoveryV1beta1Api->list_namespaced_endpoint_slice: {e}\n")   
    except ApiException as e:
        logger.error(f"[updateImplementationStatus/{namespace}/{name}] ApiException when calling DiscoveryV1beta1Api->list_namespaced_endpoint_slice: {e}\n")           

# When ingress adds IP address/dns of load balancer, update parent API object
@kopf.on.field('networking.k8s.io', 'v1beta1', 'ingresses', field='status.loadBalancer')
def ingress_status(meta, spec, status, body, namespace, labels, name, **kwargs): 
    logger.debug(f"[ingress_status/{namespace}/{name}] Status: {status}")
    namespace = meta.get('namespace')

    labels = meta.get('labels')
    if 'oda.tmforum.org/componentName' in labels.keys():

        if 'ownerReferences' in meta.keys():

            api_instance = kubernetes.client.CustomObjectsApi()
            group = 'oda.tmforum.org' # str | the custom resource's group
            version = 'v1alpha2' # str | the custom resource's version
            namespace = namespace # str | The custom resource's namespace
            plural = 'apis' # str | the custom resource's plural name
            name = meta['ownerReferences'][0]['name'] # str | the custom object's name

            try:
                parent_api = api_instance.get_namespaced_custom_object(group, version, namespace, plural, name)

            except ApiException as e:
                logger.warning("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
                raise kopf.TemporaryError("Exception updating service.")

            logger.debug(f"[ingress_status/{namespace}/{name}] ingress parent is {parent_api}")

            #get ip or hostname where ingress is exposed
            loadBalancer = status['loadBalancer']

            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]

                        # build api status
                        parent_api['status'] = buildAPIStatus(parent_api['spec'],parent_api['status'], ingressTarget)
                        
                        try:
                            api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                        except ApiException as e:
                            logger.warning("Exception when calling api_instance.patch_namespaced_custom_object: %s\n" % e)

                        logger.info(f"[ingress_status/{namespace}/{name}] Updated parent api: {name} status")
                        logger.debug(f"[ingress_status/{namespace}/{name}] api_response {api_response}")

                    else:
                        logger.warning('Ingress is an empty list')
                else:
                    logger.warning('Ingress is not a list')

            else:
                logger.debug('Load Balancer doesnt have an ingress resource')

def buildAPIStatus(parent_api_spec, parent_api_status, ingressTarget):
    if 'hostname' in parent_api_spec.keys(): #if api specifies hostname then use hostname
        parent_api_status['apiStatus']['url'] = HTTP_SCHEME + parent_api_spec['hostname'] + parent_api_spec['path']
        if 'developerUI' in parent_api_spec:
            parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + parent_api_spec['hostname'] + parent_api_spec['developerUI']
        if 'ip' in ingressTarget.keys():
            parent_api_status['apiStatus']['ip'] = ingressTarget['ip']
        elif 'hostname' in ingressTarget.keys():
            parent_api_status['apiStatus']['ip'] = ingressTarget['hostname'] 
        else:
            logger.warning('Ingress target does not contain ip or hostname')
    else:    #if api doesn't specify hostname then use ip
        if 'hostname' in ingressTarget.keys():
            parent_api_status['apiStatus']['url'] = HTTP_SCHEME + ingressTarget['hostname'] + parent_api_spec['path']
            if 'developerUI' in parent_api_spec:
                parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + ingressTarget['hostname'] + parent_api_spec['developerUI']
            parent_api_status['apiStatus']['ip'] = ingressTarget['hostname']
        elif 'ip' in ingressTarget.keys():
            parent_api_status['apiStatus']['url'] = HTTP_SCHEME + ingressTarget['ip'] + parent_api_spec['path']
            if 'developerUI' in parent_api_spec:
                parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + ingressTarget['ip'] + parent_api_spec['developerUI']
            parent_api_status['apiStatus']['ip'] = ingressTarget['ip']
        else:
            raise kopf.TemporaryError("Ingress target does not contain ip or hostname")
    return parent_api_status

# When service where implementation is ready, update parent API object
@kopf.on.create('discovery.k8s.io', 'v1beta1', 'endpointslice')
@kopf.on.update('discovery.k8s.io', 'v1beta1', 'endpointslice')
def implementation_status(meta, spec, status, body, namespace, labels, name, **kwargs):
    logger.debug(f"[{namespace}][{name}] endpointslice body: {body}")
    createAPIImplementationStatus(meta['ownerReferences'][0]['name'], body['endpoints'], namespace)

def createAPIImplementationStatus(serviceName, endpointsArray, namespace):
    anyEndpointReady = False
    if endpointsArray != None:
        for endpoint in endpointsArray:
            logger.debug(f"endpoint: {endpoint}")
            # endpoint could be an object or a dictionary
            ready = False
            if isinstance(endpoint, dict):
                ready = endpoint['conditions']['ready']
            else:
                ready = endpoint.conditions.ready
            if ready == True:
                anyEndpointReady = True 
                # find the corresponding API resource and update status
                # query for api with spec.implementation equal to service name
                api_instance = kubernetes.client.CustomObjectsApi()
                group = 'oda.tmforum.org' # str | the custom resource's group
                version = 'v1alpha2' # str | the custom resource's version
                namespace = namespace # str | The custom resource's namespace
                plural = 'apis' # str | the custom resource's plural name
                api_response = api_instance.list_namespaced_custom_object(group, version, namespace, plural)
                found = False
                logger.debug(f"[endpointslice/{serviceName}] api list has ={ len(api_response['items'])} items")
                for api in api_response['items']:  
                    if api['spec']['implementation'] == serviceName:
                        found = True
                        # logger.info(f"[endpointslice/{serviceName}] api={api}")
                        if not('status' in api.keys()):
                            api['status'] = {}
                        api['status']['implementation'] = {"ready": True}
                        api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, api['metadata']['name'], api)
                        logger.info(f"[createAPIImplementationStatus/{namespace}/{serviceName}] added implementation ready status {anyEndpointReady} to api resource")

                if found == False:
                    logger.info("[endpointslice/" + serviceName + "] Can't find API resource.")                  
    logger.debug(f"[createAPIImplementationStatus/{namespace}][{serviceName}] is ready={anyEndpointReady}")

