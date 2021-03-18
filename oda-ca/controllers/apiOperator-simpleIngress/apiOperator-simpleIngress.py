import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os

logger = logging.getLogger()
ingress_class = os.environ.get('INGRESS_CLASS','nginx') 
print('Ingress set to ',ingress_class)

HTTP_SCHEME = "http://"


# structure
#
# create/update spec of this resource - compare desired state (spec) with actual state (status) and initiate changes
#
# register for changes to status of child resources - update the status to reflect those changes. (includes deletion). 
# again, compare desired state and actual state and initiate changes.



@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'apis')
def ingress(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"oda.tmforum.org api is called with body: {spec}")

    # get API details and create ingress
    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api implementation at: {spec['implementation']}")

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

    except ApiException as e:
        logging.warning("Exception when calling NetworkingV1beta1Api: %s\n" % e)
        raise kopf.TemporaryError("Exception creating ingress.")                  

    body = {
        "apiVersion": "networking.k8s.io/v1beta1",
        "kind": "Ingress",
        "metadata": {
            "name": meta['name'],
            "annotations": {"kubernetes.io/ingress.class": ingress_class}
            },
        "spec": ingress_spec
    }

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(body)
    logging.debug(f"body (adopted): {body}")

    # create the resource
    logging.debug(f"Creating ingress with: {body}")
    ingressResource = networking_v1_beta1_api.create_namespaced_ingress(
        namespace=namespace,
        body=body
    )
    logging.debug(f"ingressResource created: {ingressResource}")
    logging.info(f"[{namespace}/{name}] ingress resource created with name {meta['name']}")
    mydict = ingressResource.to_dict()
    updateImplementationStatus(namespace, spec['implementation'])
    # Update the parent's status.
    return {"name": meta['name'], "uid": mydict['metadata']['uid']}

# in case api is updated, manually update the api implementation status from endpointslice
def updateImplementationStatus(namespace, name):
    # Create an instance of the API class
    logging.info(f"updateImplementationStatus namespace={namespace} name={name}")

    discovery_api_instance = kubernetes.client.DiscoveryV1beta1Api()
    try:
        api_response = discovery_api_instance.list_namespaced_endpoint_slice(namespace, label_selector='kubernetes.io/service-name=' + name)
        if len(api_response.items) > 0:
            createAPIImplementationStatus(name, api_response.items[0].endpoints, namespace)
    except ValueError as e: # if there are no endpoints it will create a ValueError
        logging.info(f"[{namespace}/{name}]ValueError when calling DiscoveryV1beta1Api->list_namespaced_endpoint_slice: {e}\n")   
    except ApiException as e:
        logging.error(f"[{namespace}/{name}]ApiException when calling DiscoveryV1beta1Api->list_namespaced_endpoint_slice: {e}\n")           

# When ingress adds IP address/dns of load balancer, update parent API object
@kopf.on.field('networking.k8s.io', 'v1beta1', 'ingresses', field='status.loadBalancer')
def ingress_status(meta, spec, status, body, namespace, labels, name, **kwargs): 
    logging.debug(f"Status: {status}")
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
                logging.warning("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
                raise kopf.TemporaryError("Exception updating service.")

            logging.debug(f"ingress parent is {parent_api}")

            #get ip or hostname where ingress is exposed
            loadBalancer = status['loadBalancer']

            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]
                        if 'hostname' in parent_api['spec'].keys(): #if api specifies hostname then use hostname
                            parent_api['status']['ingress']['url'] = HTTP_SCHEME + parent_api['spec']['hostname'] + parent_api['spec']['path']
                            if 'developerUI' in parent_api['spec']:
                                parent_api['status']['ingress']['developerUI'] = HTTP_SCHEME + parent_api['spec']['hostname'] + parent_api['spec']['developerUI']
                            if 'ip' in ingressTarget.keys():
                                parent_api['status']['ingress']['ip'] = ingressTarget['ip']
                            elif 'hostname' in ingressTarget.keys():
                                parent_api['status']['ingress']['ip'] = ingressTarget['hostname'] 
                            else:
                                logging.warning('Ingress target does not contain ip or hostname')
                            try:
                                api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                            except ApiException as e:
                                logging.warning("Exception when calling api_instance.patch_namespaced_custom_object: %s\n" % e)
                                raise kopf.TemporaryError("Exception updating API.")

                            logging.info(f"[{namespace}/{name}] Updated parent api: {name} status to {parent_api['status']}")

                            logging.debug(f"api_response {api_response}")
                        else:    #if api doesn't specify hostname then use ip
                            if 'ip' in ingressTarget.keys():
                                parent_api['status']['ingress']['url'] = HTTP_SCHEME + ingressTarget['ip'] + parent_api['spec']['path']
                                if 'developerUI' in parent_api['spec']:
                                    parent_api['status']['ingress']['developerUI'] = HTTP_SCHEME + ingressTarget['ip'] + parent_api['spec']['developerUI']
                                parent_api['status']['ingress']['ip'] = ingressTarget['ip']
                                api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                            elif 'hostname' in ingressTarget.keys():
                                parent_api['status']['ingress']['url'] = HTTP_SCHEME + ingressTarget['hostname'] + parent_api['spec']['path']
                                if 'developerUI' in parent_api['spec']:
                                    parent_api['status']['ingress']['developerUI'] = HTTP_SCHEME + ingressTarget['hostname'] + parent_api['spec']['developerUI']
                                parent_api['status']['ingress']['ip'] = ingressTarget['hostname']
                                try:
                                    api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                                except ApiException as e:
                                    logging.warning("Exception when calling api_instance.patch_namespaced_custom_object: %s\n" % e)
                                    raise kopf.TemporaryError("Exception updating API.")

                                logging.info(f"[{namespace}/{name}] Updated parent api: {name} status to {parent_api['status']}")
                                logging.debug(f"api_response {api_response}")
                            else:
                                logging.warning('Ingress target does not contain ip or hostname')

                    else:
                        logging.warning('Ingress is an empty list')
                else:
                    logging.warning('Ingress is not a list')

            else:
                logging.debug('Load Balancer doesnt have an ingress resource')


# When service where implementation is ready, update parent API object
@kopf.on.create('discovery.k8s.io', 'v1beta1', 'endpointslice')
@kopf.on.update('discovery.k8s.io', 'v1beta1', 'endpointslice')
def implementation_status(meta, spec, status, body, namespace, labels, name, **kwargs):
    logging.debug(f"[{namespace}][{name}] endpointslice body: {body}")
    createAPIImplementationStatus(meta['ownerReferences'][0]['name'], body['endpoints'], namespace)

def createAPIImplementationStatus(serviceName, endpointsArray, namespace):
    anyEndpointReady = False
    if endpointsArray != None:
        for endpoint in endpointsArray:
            logging.debug(f"endpoint: {endpoint}")
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
                logging.debug(f"[endpointslice/{serviceName}] api list has ={ len(api_response['items'])} items")
                for api in api_response['items']:  
                    if api['spec']['implementation'] == serviceName:
                        found = True
                        # logging.info(f"[endpointslice/{serviceName}] api={api}")
                        if not('status' in api.keys()):
                            api['status'] = {}
                        api['status']['implementation'] = {"ready": True}
                        api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, api['metadata']['name'], api)
                        logging.info(f"[{namespace}][{serviceName}] added implementation ready status to api resource")

                if found == False:
                    logging.info("[endpointslice/" + serviceName + "] Can't find API resource.")                  
    logging.info(f"[endpointslice/{serviceName}] is ready={anyEndpointReady}")

