"""Kubernetes operator for ODA API custom resources.

Normally this module is deployed as part of an ODA Canvas. It uses the kopf kubernetes operator framework (https://kopf.readthedocs.io/) to build an
operator that takes API custom resources and implements them using Istio Virtual Service resources linked to an Istio Gateway. 

This is the simplest API operator for an Istio Service Mesh canvas and is not suitable for a production environment. It is possible to create alternative API operators
that would configure an API gateway in front of the Service Mesh (This is the recommended production architecture).

It registers handler functions for:

1. New ODA APIs - to create, update or delete child Virtual Service resources to expose the API using a Virtual Service. see `apiStatus <#apiOperatorIstio.apiOperatorIstio.apiStatus>`_ 
2. For status updates in the child Ingress resources and EndPointSlice resources, so that the API status reflects a summary the Ingress and Implementation for the API. see `ingress_status <#apiOperatorIstio.apiOperatorIstio.ingress_status>`_ and `implementation_status <#apiOperatorIstio.apiOperatorIstio.implementation_status>`_
"""

import kopf
import kubernetes.client
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
GROUP = "oda.tmforum.org"
VERSION = "v1alpha3"
APIS_PLURAL = "apis"



@kopf.on.create('oda.tmforum.org', 'v1alpha3', 'apis')
@kopf.on.update('oda.tmforum.org', 'v1alpha3', 'apis')
def apiStatus(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for new or updated APIs.
    
    Processes the spec of the API and create child Kubernetes Ingress resources. The Kubernetes Ingress will expose the API to the outside.

    Args:
        * meta (Dict): The metadata from the API Custom Resource 
        * spec (Dict): The spec from the  showing the intent (or desired state) 
        * status (Dict): The status from the  showing the actual state.
        * body (Dict): The entire 
        * namespace (String): The namespace for the API Custom Resource
        * labels (Dict): The labels attached to the API Custom Resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the API Custom Resource

    Returns:
        Dict: The apiStatus status that is put into the API Custom Resource status field.

    :meta public:
    """
    logger.debug(f"[apiStatus/{namespace}/{name}] apiOperator-simpleIngress/apiStatus called with name:{name}, spec: {spec}")
    return actualToDesiredState(spec, status, namespace, name)


def actualToDesiredState(spec, status, namespace, name): 
    """Helper function to compare desired state (spec) with actual state (status) and initiate changes.
    
    Args:
        * spec (Dict): The spec from the  showing the intent (or desired state) 
        * status (Dict): The status from the  showing the actual state.
        * namespace (String): The namespace for the API Custom Resource
        * name (String): The name of the API Custom Resource

    Returns:
        Dict: The updated apiStatus that will be put into the status field of the API resource.

    :meta private:
    """
    outputStatus = {}
    if status: # there is a status object
        if 'apiStatus' in status.keys(): # there is an actual state to compare against
            # work out delta between desired and actual state
            apiStatus = status['apiStatus'] # starting point for return status is the previous status
            # check if there is a difference in the ingress we created previously
            if name == apiStatus['name'] and spec['path'] == apiStatus['path'] and spec['port'] == apiStatus['port'] and spec['implementation'] == apiStatus['implementation']:
                # unchanged, so just return previous status
                logger.info(f"[actualToDesiredState/{namespace}/{name}] returning previous status")
                return apiStatus
            else:
                logger.info(f"[actualToDesiredState/{namespace}/{name}] status has changed so patching Virtual Service")
                return createOrPatchVirtualService(True, spec, namespace, name)
    logger.info(f"[actualToDesiredState/{namespace}/{name}] status doesnt exist so creating Virtual Service")
    return createOrPatchVirtualService(False, spec, namespace, name)

def createOrPatchVirtualService(patch, spec, namespace, name):            
    """Helper function to get API details and create or patch VirtualService.
    
    Args:
        * patch (Boolean): True to patch an existing VirtualService; False to create a new VirtualService. 
        * spec (Dict): The spec from the API Resource showing the intent (or desired state) 
        * namespace (String): The namespace for the API Custom Resource
        * name (String): The name of the API Custom Resource

    Returns:
        Dict: The updated apiStatus that will be put into the status field of the API resource.

    :meta private:
    """
    
    client = kubernetes.client
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        hostname = None
        if 'hostname' in spec.keys():
            hostname=spec['hostname']

        VIRTUAL_SERVICE_GROUP = "networking.istio.io"
        VIRTUAL_SERVICE_VERSION = "v1alpha3"
        VIRTUAL_SERVICE_PLURAL = "virtualservices"

        # FIX required to optionally add hostname instead of ["*"]
        body = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "VirtualService",
            "metadata": {
                "name": name
                },
            "spec": {
                "hosts": ["*"],  
                "gateways": ["component-gateway"],
                "http": [
                    {
                        "match": [
                            {
                                "uri": {"prefix": spec['path']}
                            }
                        ],
                        "route": [
                            {
                                "destination": {
                                    "host": spec['implementation'],
                                    "port": {
                                        "number": spec['port']
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }

        # Make it our child: assign the namespace, name, labels, owner references, etc.
        kopf.adopt(body)
        logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] body (adopted): {body}")
        if patch == True:
            # patch the resource
            logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] Patching ingress with: {body}")
            virtualServiceResource = custom_objects_api.patch_namespaced_custom_object(VIRTUAL_SERVICE_GROUP, VIRTUAL_SERVICE_VERSION, namespace, VIRTUAL_SERVICE_PLURAL, name, body)
            logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] virtualServiceResource patched: {virtualServiceResource}")
            logger.info(f"[createOrPatchVirtualService/{namespace}/{name}] virtualServiceResource patched with name {name}")
            updateImplementationStatus(namespace, spec['implementation'])
            # update parent apiStatus
            loadBalancer = getIstioIngressStatus()
            apistatus = {'apiStatus': {"name": name, "uid": virtualServiceResource['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]
                        apistatus = buildAPIStatus(spec, apistatus, ingressTarget)
                        logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] apistatus = {apistatus}")

            return apistatus['apiStatus']
        else:
            # create the resource
            logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] Creating ingress with: {body}")
            virtualServiceResource = custom_objects_api.create_namespaced_custom_object(VIRTUAL_SERVICE_GROUP, VIRTUAL_SERVICE_VERSION, namespace, VIRTUAL_SERVICE_PLURAL, body)
            logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] virtualServiceResource created: {virtualServiceResource}")
            logger.info(f"[createOrPatchVirtualService/{namespace}/{name}] virtualServiceResource created with name {name}")
            updateImplementationStatus(namespace, spec['implementation'])
            # update parent apiStatus
            loadBalancer = getIstioIngressStatus()
            apistatus = {'apiStatus': {"name": name, "uid": virtualServiceResource['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]
                        apistatus = buildAPIStatus(spec, apistatus, ingressTarget)
                        logger.debug(f"[createOrPatchVirtualService/{namespace}/{name}] apistatus = {apistatus}")
            return apistatus['apiStatus']
    except ApiException as e:
        logger.warning("Exception when calling CustomObjectsApi: %s\n" % e)
        raise kopf.TemporaryError("Exception creating virtualService.")                  


def updateImplementationStatus(namespace, name):
    """Helper function to get EndPointSice and find the Ready status.
    
    Args:
        * namespace (String): The namespace for the Kubernetes Service that implements the API
        * name (String): The name of the Kubernetes Service that implements the API

    Returns:
        No return value.

    :meta private:
    """
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


# helper function to get Istio Ingress status
def getIstioIngressStatus():
    # get ip or hostname where ingress is exposed from the istio-ingressgateway service
    core_api_instance = kubernetes.client.CoreV1Api()
    ISTIO_NAMESPACE = "istio-system"
    ISTIO_INGRESSGATEWAY = "istio-ingressgateway"
    try:
        api_response = core_api_instance.read_namespaced_service(ISTIO_INGRESSGATEWAY, ISTIO_NAMESPACE)
        serviceStatus = api_response.status
        loadBalancer = serviceStatus.load_balancer.to_dict()
        logger.info(f"[getIstioIngressStatus] Istio Ingress Gateway is {loadBalancer}")
    except Exception as e:
        logger.warning("Exception when calling CoreApi->read_namespaced_service: %s\n" % e)
        raise kopf.TemporaryError("Exception getting IstioIngressStatus.")
    return loadBalancer

def buildAPIStatus(parent_api_spec, parent_api_status, ingressTarget):
    """Helper function to build the API Status Dict for the API custom resource.
    
    Args:
        * parent_api_spec (Dict): The spec (target state or intent) for the API Resource
        * parent_api_status (Dict): The status (actual state) for the API Resource
        * ingressTarget (Dict): The status (actual state) for the Ingress Resource

    Returns:
        Updated API status as Dict.

    :meta private:
    """
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
    """Handler function to register for status changes in EndPointSlide resources.
    
    The EndPointSlide resources show the implementation of an API linked the the API implementations Service Resource. 
    When EndPointSlide updates the ready-status of the implementation, update parent API object.

    Args:
        * meta (Dict): The metadata from the EndPointSlide Resource 
        * spec (Dict): The spec from the EndPointSlide Resource showing the intent (or desired state) 
        * status (Dict): The status from the EndPointSlide Resource showing the actual state.
        * body (Dict): The entire EndPointSlide Resource
        * namespace (String): The namespace for the EndPointSlide Resource
        * labels (Dict): The labels attached to the EndPointSlide Resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the EndPointSlide Resource

    Returns:
        No return value.

    :meta public:
    """
    logger.debug(f"[{namespace}][{name}] endpointslice body: {body}")
    createAPIImplementationStatus(meta['ownerReferences'][0]['name'], body['endpoints'], namespace)

def createAPIImplementationStatus(serviceName, endpointsArray, namespace):
    """Helper function to update the implementation Ready status on the API custom resource.
    
    Args:
        * serviceName (String): The name of Kubernetes Service that implements the API
        * endpointsArray (Array): The array of EndPointSlice resources that show the implementation Ready state for the Service.
        * namespace (String): The namespace for the Kubernetes Service that implements the API

    Returns:
        No return value.

    :meta private:
    """
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
                api_response = api_instance.list_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL)
                found = False
                logger.debug(f"[endpointslice/{serviceName}] api list has ={ len(api_response['items'])} items")
                for api in api_response['items']:  
                    if api['spec']['implementation'] == serviceName:
                        found = True
                        # logger.info(f"[endpointslice/{serviceName}] api={api}")
                        if not('status' in api.keys()):
                            api['status'] = {}
                        api['status']['implementation'] = {"ready": True}
                        api_response = api_instance.patch_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL, api['metadata']['name'], api)
                        logger.info(f"[createAPIImplementationStatus/{namespace}/{serviceName}] added implementation ready status {anyEndpointReady} to api resource")

                if found == False:
                    logger.info("[endpointslice/" + serviceName + "] Can't find API resource.")                  
    logger.debug(f"[createAPIImplementationStatus/{namespace}][{serviceName}] is ready={anyEndpointReady}")

