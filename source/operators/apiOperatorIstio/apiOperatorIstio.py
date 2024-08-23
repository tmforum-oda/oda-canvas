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
import json
from kubernetes.client.rest import ApiException
import os
import re

logging_level = os.environ.get('LOGGING',logging.INFO)

kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)

logger = logging.getLogger('APIOperator')
logger.setLevel(int(logging_level))
logger.info(f'Logging set to %s', logging_level)

HTTP_SCHEME = "http://"
HTTP_K8s_LABELS = ['http', 'http2']
HTTP_STANDARD_PORTS = [80, 443]
GROUP = "oda.tmforum.org"
VERSION = "v1beta3"
APIS_PLURAL = "exposedapis"

# get environment variables
OPENMETRICS_IMPLEMENTATION = os.environ.get('OPENMETRICS_IMPLEMENTATION', 'ServiceMonitor') # could be ServiceMonitor or PrometheusAnnotation or DataDogAnnotation
logger.info(f'OpenMetrics implementation pattern set to {OPENMETRICS_IMPLEMENTATION}')

APIOPERATORISTIO_PUBLICHOSTNAME = os.environ.get('APIOPERATORISTIO_PUBLICHOSTNAME') # hostname to be used for calling public APIs. 
publichostname_loadBalancer = None                                                  # Overwrites the LB ip/hostname retrieved from istioingress service.
if APIOPERATORISTIO_PUBLICHOSTNAME:
    logger.info(f'Public hostname set: {APIOPERATORISTIO_PUBLICHOSTNAME}')
    if re.match("^[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+$", APIOPERATORISTIO_PUBLICHOSTNAME):
        publichostname_loadBalancer = {"ingress": [{"ip": APIOPERATORISTIO_PUBLICHOSTNAME}]}
    else:
        publichostname_loadBalancer = {"ingress": [{"hostname": APIOPERATORISTIO_PUBLICHOSTNAME}]}

@kopf.on.create(GROUP, VERSION, APIS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL, retries=5)
def apiStatus(meta, spec, status, body, namespace, labels, name, **kwargs):
    """Handler function for new or updated APIs.
    
    Processes the spec of the API and create child Kubernetes VirtualService resources (for open-api type) or ServiceMonitor resources (for prometheus metrics type).

    Args:
        * meta (Dict): The metadata from the API Custom Resource 
        * spec (Dict): The spec from the API Custom Resource showing the intent (or desired state) 
        * status (Dict): The status from the API Custom Resource showing the actual state.
        * body (Dict): The entire API Custom Resource
        * namespace (String): The namespace for the API Custom Resource
        * labels (Dict): The labels attached to the API Custom Resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the API Custom Resource

    Returns:
        Dict: The apiStatus status that is put into the API Custom Resource status field.

    """
    componentName = labels['oda.tmforum.org/componentName']

    logWrapper(logging.DEBUG, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "apiStatus handler called with ", spec)

    outputStatus = {}
    if status: # there is a status object
        if 'apiStatus' in status.keys(): # there is an existing apiStatus to compare against
            # work out delta between desired and actual state
            apiStatus = status['apiStatus'] # starting point for return status is the previous status
            # check if there is a difference in the api we created previously
            if name == apiStatus['name'] and spec['path'] == apiStatus['path'] and spec['port'] == apiStatus['port'] and spec['implementation'] == apiStatus['implementation']:
                # unchanged, so just return previous status
                logWrapper(logging.DEBUG, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "Unchanged", "Returning previous status")
                return apiStatus
            else:
                logWrapper(logging.INFO, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "Patching", "Istio Virtual Service")
                # if the apitype of the api is 'prometheus' then we need to also create a ServiceMonitor resource
                if 'apitype' in spec.keys():
                    if spec['apitype'] == 'prometheus':
                        # create a ServiceMonitor resource
                        logWrapper(logging.INFO, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "Patching", "Prometheus Service Monitor")
                        createOrPatchObservability(True, spec, namespace, name, 'apiStatus', componentName)
                return createOrPatchVirtualService(True, spec, namespace, name, 'apiStatus', componentName)

    # if we get here then we are creating a new API            
    logWrapper(logging.INFO, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "Creating", "Istio Virtual Service")    
    # if the apitype of the api is 'prometheus' then we need to also create a ServiceMonitor resource
    if 'apitype' in spec.keys():
        if spec['apitype'] == 'prometheus':
            # create a ServiceMonitor resource
            logWrapper(logging.INFO, 'apiStatus', 'apiStatus', 'api/' + name, componentName, "Creating", "Prometheus Service Monitor")    
            createOrPatchObservability(False, spec, namespace, name, 'apiStatus', componentName)
    return createOrPatchVirtualService(False, spec, namespace, name, 'apiStatus', componentName)

def createOrPatchObservability(patch, spec, namespace, name, inHandler, componentName): 
    """Helper function to switch between the different patterns for scraping Prometheus APIs.
    
    Args:
        * patch (Boolean): True to patch an existing ServiceMonitor; False to create a new ServiceMonitor. 
        * spec (Dict): The spec from the API Resource showing the intent (or desired state) 
        * namespace (String): The namespace for the API Custom Resource
        * name (String): The name of the API Custom Resource
        * inHandler (String): The name of the handler function calling this function
        * componentName (String): The name of the ODA Component that the API is part of

    Returns:
        nothing    
    """
    if OPENMETRICS_IMPLEMENTATION == 'ServiceMonitor':
        createOrPatchServiceMonitor(patch, spec, namespace, name, inHandler, componentName)
    elif OPENMETRICS_IMPLEMENTATION == 'PrometheusAnnotation':
        createOrPatchPrometheusAnnotation(patch, spec, namespace, name, inHandler, componentName)
    elif OPENMETRICS_IMPLEMENTATION == 'DataDogAnnotation':
        createOrPatchDataDogAnnotation(patch, spec, namespace, name, inHandler, componentName)
    else:
        logWrapper(logging.WARNING, 'createOrPatchObservability', inHandler, 'api/' + name, componentName, "Unknown Prometheus Pattern", OPENMETRICS_IMPLEMENTATION)


def createOrPatchPrometheusAnnotation(patch, spec, namespace, name, inHandler, componentName):   
    logWrapper(logging.WARNING, 'createOrPatchPrometheusAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchPrometheusAnnotation", "Prometheus Annotation NOT IMPLEMENTED YET")

    # This implementation not creted yet. Suggestion: copy the createOrPatchDataDogAnnotation - mopst of the logic is the same

    raise kopf.TemporaryError("Exception in createOrPatchPrometheusAnnotation.")   

def createOrPatchDataDogAnnotation(patch, spec, namespace, name, inHandler, componentName):      
    """Helper function to get API details for a prometheus metrics API and patch the corresponding kubernetes pod.
    
    Args:
        * patch (Boolean): True to patch an existing annotation; False to create a new annotation. Makes no difference for this function.
        * spec (Dict): The spec from the API Resource showing the intent (or desired state) 
        * namespace (String): The namespace for the API Custom Resource
        * name (String): The name of the API Custom Resource
        * inHandler (String): The name of the handler function calling this function
        * componentName (String): The name of the ODA Component that the API is part of

    Returns:
        nothing
    """
    logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation", "DataDog Annotation")

    # To get the pod name for the implementation, follow these steps:
    # 1. The API has an 'implementation' field which is the name of the service that exposes the API.
    # 2. The service will include a spec.selector which allows you to find the pod that implements the API.
    # 3. Get the pod and amend the annotation

    client = kubernetes.client
    try:
        # get the service
        core_api = client.CoreV1Api()
        service = core_api.read_namespaced_service(spec['implementation'], namespace)
        selector = service.spec.selector
        serviceName = service.metadata.name

        logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation selector=", selector)
        # get the pod using the selector
        key, value = next(iter(selector.items())) # get the first key/value pair - we don't have a way to handle multiple selectors
        selectorQuery = key + '=' + value
        logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation selectorQuery=", selectorQuery)

        pod_list = core_api.list_namespaced_pod(namespace, label_selector=selectorQuery)
        # get the first pod
        pod = pod_list.items[0]
        podName = pod.metadata.name
        logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation podName=", podName)

        podContainers = pod.spec.containers
        for container in podContainers:
            logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation container=", container.name)
        
        targetContainerName = podContainers[0].name # default to the first container

        # prepare the annotation
        path = None
        if 'path' in spec.keys():
            path=spec['path']
        port = None
        if 'port' in spec.keys():
            port=spec['port']

        annotationDict = {"openmetrics": 
                { "instances": 
                    [
                        { "openmetrics_endpoint": "http://" + serviceName + "." + namespace + ".svc.cluster.local:" + str(port) + path,
                            "namespace": "components","metrics": [".*"] 
                        }    
                    ]
                }
            }
        
        annotation = json.dumps(annotationDict)
        logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation patching pod with annotation=", annotation)
        
        if not pod.metadata.annotations:
            pod.metadata.annotations = {}
            
        pod.metadata.annotations['ad.datadoghq.com/' + targetContainerName + '.checks'] = annotation
        # patch the pod
        core_api.patch_namespaced_pod(podName, namespace, pod)

        logWrapper(logging.INFO, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "createOrPatchDataDogAnnotation pod patched with annotation=", annotation)

    except ApiException as e:
        logWrapper(logging.DEBUG, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "Exception", e)
        logWrapper(logging.WARNING, 'createOrPatchDataDogAnnotation', inHandler, 'api/' + name, componentName, "Exception", " in createOrPatchDataDogAnnotation - will retry")
        raise kopf.TemporaryError("Exception in createOrPatchDataDogAnnotation.")   

def createOrPatchServiceMonitor(patch, spec, namespace, name, inHandler, componentName):            
    """Helper function to get API details for a prometheus metrics API and create or patch ServiceMonitor resource.
    
    Args:
        * patch (Boolean): True to patch an existing ServiceMonitor; False to create a new ServiceMonitor. 
        * spec (Dict): The spec from the API Resource showing the intent (or desired state) 
        * namespace (String): The namespace for the API Custom Resource
        * name (String): The name of the API Custom Resource
        * inHandler (String): The name of the handler function calling this function
        * componentName (String): The name of the ODA Component that the API is part of

    Returns:
        nothing
    """

    client = kubernetes.client
    try:
        custom_objects_api = kubernetes.client.CustomObjectsApi()

        hostname = None
        if 'hostname' in spec.keys():
            hostname=spec['hostname']

        SERVICE_MONITOR_GROUP = "monitoring.coreos.com"
        SERVICE_MONITOR_VERSION = "v1"
        SERVICE_MONITOR_PLURAL = "servicemonitors"
        SERVICE_MONITOR_KIND = "ServiceMonitor"

        # FIX required to optionally add hostname instead of ["*"]
        body = {
            "apiVersion": SERVICE_MONITOR_GROUP + "/" + SERVICE_MONITOR_VERSION,
            "kind": SERVICE_MONITOR_KIND,
            "metadata": {
                "name": name,
                "namespace": namespace
                },
            "spec": {
                "selector": {
                    "matchLabels": {
                       "name": spec['implementation']  
                    }
                },
                "endpoints": [
                    {
                        "path": spec['path'],
                        "interval": "15s",
                        "scheme": "http",
                        "targetPort": spec['port']
                    }
                ]
            }
        }
        if 'basicAuth' in spec.keys():
            body['spec']['endpoints'][0]['basicAuth'] = spec['basicAuth']

        # Make it our child: assign the namespace, name, labels, owner references, etc.
        kopf.adopt(body)

        logWrapper(logging.DEBUG, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Service Monitor", body)    

        if patch == True:
            # patch the resource
            serviceMonitorResource = custom_objects_api.patch_namespaced_custom_object(SERVICE_MONITOR_GROUP, SERVICE_MONITOR_VERSION, namespace, SERVICE_MONITOR_PLURAL, name, body)
            logWrapper(logging.DEBUG, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Service Monitor patched", serviceMonitorResource)
            logWrapper(logging.INFO, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Service Monitor patched", name)
            return 
        else:
            # create the resource
            serviceMonitorResource = custom_objects_api.create_namespaced_custom_object(SERVICE_MONITOR_GROUP, SERVICE_MONITOR_VERSION, namespace, SERVICE_MONITOR_PLURAL, body)
            logWrapper(logging.DEBUG, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Service Monitor created", serviceMonitorResource)
            logWrapper(logging.INFO, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Service Monitor created", name)
            return 
    except ApiException as e:
        logWrapper(logging.DEBUG, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Exception when calling CustomObjectsApi", e)
        logWrapper(logging.WARNING, 'createOrPatchServiceMonitor', inHandler, 'api/' + name, componentName, "Exception", " when calling CustomObjectsApi - will retry")
        raise kopf.TemporaryError("Exception creating ServiceMonitor.")   


def createOrPatchVirtualService(patch, spec, namespace, inAPIName, inHandler, componentName):            
    """Helper function to get API details and create or patch VirtualService.
    
    Args:
        * patch (Boolean): True to patch an existing VirtualService; False to create a new VirtualService. 
        * spec (Dict): The spec from the API Resource showing the intent (or desired state) 
        * namespace (String): The namespace for the API Custom Resource
        * inAPIName (String): The name of the API Custom Resource
        * inHandler (String): The name of the handler calling this function
        * componentName (String): The name of the component that owns the API resource

    Returns:
        Dict: The updated apiStatus that will be put into the status field of the API resource.
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
        hostname = "*"
        if APIOPERATORISTIO_PUBLICHOSTNAME:
            hostname = APIOPERATORISTIO_PUBLICHOSTNAME
        body = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "VirtualService",
            "metadata": {
                "name": inAPIName
                },
            "spec": {
                "hosts": [hostname],  
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
        
        logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Virtual Service", body)    

        if patch == True:
            # patch the resource
            virtualServiceResource = custom_objects_api.patch_namespaced_custom_object(VIRTUAL_SERVICE_GROUP, VIRTUAL_SERVICE_VERSION, namespace, VIRTUAL_SERVICE_PLURAL, name, body)
            logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Virtual Service patched", virtualServiceResource)
            logWrapper(logging.INFO, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Virtual Service patched", inAPIName)
            updateImplementationStatus(namespace, spec['implementation'], inHandler, componentName)
            # update parent apiStatus
            istioStatus = getIstioIngressStatus(inHandler, 'api/' + inAPIName, componentName)
            loadBalancer = istioStatus['loadBalancer']
            ports = istioStatus['ports']
            apistatus = {'apiStatus': {"name": inAPIName, "uid": virtualServiceResource['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]
                        apistatus = buildAPIStatus(spec, apistatus, ingressTarget, ports, inAPIName, inHandler, componentName)
                        logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "apiStatus", apistatus)

            return apistatus['apiStatus']
        else:
            # create the resource
            virtualServiceResource = custom_objects_api.create_namespaced_custom_object(VIRTUAL_SERVICE_GROUP, VIRTUAL_SERVICE_VERSION, namespace, VIRTUAL_SERVICE_PLURAL, body)
            logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Virtual Service created", virtualServiceResource)
            logWrapper(logging.INFO, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Virtual Service created", inAPIName)
            updateImplementationStatus(namespace, spec['implementation'], inHandler, componentName)
            # update parent apiStatus
            istioStatus = getIstioIngressStatus(inHandler, 'api/' + inAPIName, componentName)
            loadBalancer = istioStatus['loadBalancer']
            ports = istioStatus['ports']
            apistatus = {'apiStatus': {"name": inAPIName, "uid": virtualServiceResource['metadata']['uid'], "path": spec['path'], "port": spec['port'], "implementation": spec['implementation']}}
            if 'ingress' in loadBalancer.keys():
                ingress = loadBalancer['ingress']
                if isinstance(ingress, list):
                    if len(ingress)>0:
                        ingressTarget = ingress[0]
                        apistatus = buildAPIStatus(spec, apistatus, ingressTarget, ports, inAPIName, inHandler, componentName)
                        logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "apiStatus", apistatus)
            return apistatus['apiStatus']
    except ApiException as e:
        logWrapper(logging.DEBUG, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Exception when calling CustomObjectsApi", e)
        logWrapper(logging.WARNING, 'createOrPatchVirtualService', inHandler, 'api/' + inAPIName, componentName, "Exception", " when calling CustomObjectsApi - will retry")
        raise kopf.TemporaryError("Exception creating virtualService.")                  


def updateImplementationStatus(namespace, name, inHandler, componentName):
    """Helper function to get EndPointSice and find the Ready status.
    
    Args:
        * namespace (String): The namespace for the Kubernetes Service that implements the API
        * name (String): The name of the Kubernetes Service that implements the API
        * inHandler (String): The name of the handler that is calling this function
        * componentName (String): The name of the component that owns the API resource

    Returns:
        No return value.

    :meta private:
    """
    logWrapper(logging.DEBUG, 'updateImplementationStatus', inHandler, 'api/' + name, componentName, "Update implementation status", name)

    discovery_api_instance = kubernetes.client.DiscoveryV1Api()
    try:
        api_response = discovery_api_instance.list_namespaced_endpoint_slice(namespace, label_selector='kubernetes.io/service-name=' + name)
        if len(api_response.items) > 0:
            createAPIImplementationStatus(name, api_response.items[0].endpoints, namespace, inHandler, componentName)
    except ValueError as e: # if there are no endpoints it will create a ValueError
        logWrapper(logging.INFO, 'updateImplementationStatus', inHandler, 'api/' + name, componentName, "Can not find", "Endpoint Slice")
    except ApiException as e:
        logWrapper(logging.DEBUG, 'updateImplementationStatus', inHandler, 'api/' + name, componentName, "ApiException calling list_namespaced_endpoint_slice", e)
        logWrapper(logging.WARNING, 'updateImplementationStatus', inHandler, 'api/' + name, componentName, "ApiException", " calling list_namespaced_endpoint_slice")


# helper function to get Istio Ingress status
def getIstioIngressStatus(inHandler, name, componentName):
    # get ip or hostname where ingress is exposed from the istio-ingressgateway service
    core_api_instance = kubernetes.client.CoreV1Api()
    ISTIO_INGRESSGATEWAY_LABEL = "istio=ingressgateway" 

    ## should get this by label (as this is what the gareway defines)
    try:
        # get the istio-ingressgateway service by label 'istio: ingressgateway'
        api_response = core_api_instance.list_service_for_all_namespaces(label_selector=ISTIO_INGRESSGATEWAY_LABEL)
        
        # api_response = core_api_instance.read_namespaced_service(ISTIO_INGRESSGATEWAY, ISTIO_NAMESPACE)
        if len(api_response.items) == 0:
            logWrapper(logging.WARNING, 'getIstioIngressStatus', inHandler, 'api/' + name, componentName, "Can not find", "Istio Ingress Gateway")
            raise kopf.TemporaryError("Can not find Istio Ingress Gateway.")

        serviceStatus = api_response.items[0].status
        serviceSpec = api_response.items[0].spec
        loadBalancer = None
        if serviceStatus.load_balancer is not None:
            loadBalancer = serviceStatus.load_balancer.to_dict()
        ports = serviceSpec.ports
        if publichostname_loadBalancer:
            loadBalancer = publichostname_loadBalancer
        response = {'loadBalancer': loadBalancer, 'ports': ports}
        logWrapper(logging.INFO, 'getIstioIngressStatus', inHandler, 'api/' + name, componentName, "Istio Ingress Gateway", "Received ingress status.")
    except Exception as e:
        logWrapper(logging.WARNING, 'getIstioIngressStatus', inHandler, 'api/' + name, componentName, "Exception in getIstioIngressStatus", str(e))
        raise kopf.TemporaryError("Exception getting IstioIngressStatus.")
    return response

def buildAPIStatus(parent_api_spec, parent_api_status, ingressTarget, ports, inAPIName, inHandler, componentName):
    """Helper function to build the API Status Dict for the API custom resource.
    
    Args:
        * parent_api_spec (Dict): The spec (target state or intent) for the API Resource
        * parent_api_status (Dict): The status (actual state) for the API Resource
        * ingressTarget (Dict): The status (actual state) for the Ingress Resource
        * ports (Dict): The ports for the Ingress Resource
        * inAPIName (String): The name of the API Resource
        * inHandler (String): The name of the handler that is processing the API Resource
        * componentName (String): The name of the component that owns the API Resource

    Returns:
        Updated API status as Dict.

    :meta private:
    """


    # choose which port to expose - default is http2 or http. If the port is 80 then don't need to add
    portsString = ''
    for port in ports:
        portDict = port.to_dict()
        if portDict['name'] in HTTP_K8s_LABELS:
            if not (portDict['port'] in HTTP_STANDARD_PORTS):
                portsString = ':' + str(portDict['port'])
            break
 
    if 'hostname' in parent_api_spec.keys(): #if api specifies hostname then use hostname
        parent_api_status['apiStatus']['url'] = HTTP_SCHEME + parent_api_spec['hostname'] + portsString + parent_api_spec['path']
        if 'developerUI' in parent_api_spec:
            parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + parent_api_spec['hostname'] + portsString + parent_api_spec['developerUI']
        if 'ip' in ingressTarget.keys() and ingressTarget['ip'] is not None:
            parent_api_status['apiStatus']['ip'] = ingressTarget['ip']
        elif 'hostname' in ingressTarget.keys() and ingressTarget['hostname'] is not None:
            parent_api_status['apiStatus']['ip'] = ingressTarget['hostname']
        else:
            logWrapper(logging.WARNING, 'buildAPIStatus', inHandler, 'api/' + inAPIName, componentName, "Ingress target does not contain ip or hostname", "")
    else:    #if api doesn't specify hostname then use ip
        if 'ip' in ingressTarget.keys() and ingressTarget['ip'] is not None:
            parent_api_status['apiStatus']['url'] = HTTP_SCHEME + ingressTarget['ip'] + portsString + parent_api_spec['path']
            if 'developerUI' in parent_api_spec:
                parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + ingressTarget['ip'] + portsString + parent_api_spec['developerUI']
            parent_api_status['apiStatus']['ip'] = ingressTarget['ip']
        elif 'hostname' in ingressTarget.keys() and ingressTarget['hostname'] is not None:
            parent_api_status['apiStatus']['url'] = HTTP_SCHEME + ingressTarget['hostname'] + portsString + parent_api_spec['path']
            if 'developerUI' in parent_api_spec:
                parent_api_status['apiStatus']['developerUI'] = HTTP_SCHEME + ingressTarget['hostname'] + portsString + parent_api_spec['developerUI']
            parent_api_status['apiStatus']['ip'] = ingressTarget['hostname']
        else:
            raise kopf.TemporaryError("Ingress target does not contain ip or hostname")
    return parent_api_status

# When service where implementation is ready, update parent API object
@kopf.on.create('discovery.k8s.io', 'v1', 'endpointslice', retries=5)
@kopf.on.update('discovery.k8s.io', 'v1', 'endpointslice', retries=5)
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
    try:
        componentName = labels['oda.tmforum.org/componentName']
        createAPIImplementationStatus(meta['ownerReferences'][0]['name'], body['endpoints'], namespace, 'implementation_status', componentName)
    except Exception as e:
        logWrapper(logging.WARNING, 'implementation_status', meta['ownerReferences'][0]['name'], 'api/' + name, componentName, "Exception in implementation_status", str(e))
        raise kopf.TemporaryError("Exception handling implementation_status.")


def createAPIImplementationStatus(serviceName, endpointsArray, namespace, inHandler, componentName):
    """Helper function to update the implementation Ready status on the API custom resource.
    
    Args:
        * serviceName (String): The name of Kubernetes Service that implements the API
        * endpointsArray (Array): The array of EndPointSlice resources that show the implementation Ready state for the Service.
        * namespace (String): The namespace for the Kubernetes Service that implements the API
        * inHandler (String): The name of the handler function calling this helper function
        * componentName (String): The name of the ODA Component that the API resource is owned by

    Returns:
        No return value.

    :meta private:
    """
    anyEndpointReady = False
    if endpointsArray != None:
        for endpoint in endpointsArray:
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
                for api in api_response['items']:  
                    if api['spec']['implementation'] == serviceName:
                        found = True
                        if not('status' in api.keys()):
                            api['status'] = {}
                        api['status']['implementation'] = {"ready": True}
                        api_response = api_instance.patch_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL, api['metadata']['name'], api)
                        logWrapper(logging.INFO, 'createAPIImplementationStatus', inHandler, 'endpointslice/' + api['metadata']['name'], componentName, "Added implementation ready status", anyEndpointReady)

                if found == False:
                    logWrapper(logging.INFO, 'createAPIImplementationStatus', inHandler, 'service/' + serviceName, componentName, "Can't find API resource", serviceName)


def logWrapper(logLevel, functionName, handlerName, resourceName, componentName, subject, message):
    """Helper function to standardise logging output.
    
    Args:
        * logLevel (Number): The level to log e.g. logging.INFO
        * functionName (String): The name of the function calling the logWrapper
        * resourceName (String): The name of the resource being logged
        * componentName (String): The name of the component being logged
        * subject (String): The subject of the log message
        * message (String): The message to be logged - can contain relavant data
    
    Returns:
        No return value.
    """
    logger.log(logLevel, f"[{componentName}|{resourceName}|{handlerName}|{functionName}] {subject}: {message}")
    return

