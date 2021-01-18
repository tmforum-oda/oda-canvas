import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
logger = logging.getLogger()
#logger.setLevel(10) #DEBUG

@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'apis')
def ingress(meta, spec, **kwargs):

    logging.debug(f"oda.tmforum.org api is called with body: {spec}")
    namespace = meta.get('namespace')

    # get API details and create ingress
    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api implementation at: {spec['implementation']}")

    # newName = my_resource['metadata']['ownerReferences'][0]['name'] + '-' + exposedAPI['name']
    # my_resource['metadata']['name'] = newName.lower()
    # my_resource['spec']['specification'] = exposedAPI['specification']
    # my_resource['spec']['implementation'] = exposedAPI['implementation']

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
            "annotations": {"kubernetes.io/ingress.class": "nginx"}
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

    mydict = ingressResource.to_dict()

    # Update the parent's status.
    return {"name": meta['name'], "uid": mydict['metadata']['uid']}


# When ingress adds IP address of load balancer, update parent API object
@kopf.on.field('networking.k8s.io', 'v1beta1', 'ingresses', field='status.loadBalancer')
def ingress_status(meta, status, spec, **kwargs):
    logging.info(f"Update called for ingress {meta['name']}")
    logging.debug(f"Status: {status}")
    namespace = meta.get('namespace')

    labels = meta.get('labels')
    if 'oda.tmforum.org/componentName' in labels.keys():

        if 'ownerReferences' in meta.keys():

            api_instance = kubernetes.client.CustomObjectsApi()
            group = 'oda.tmforum.org' # str | the custom resource's group
            version = 'v1alpha1' # str | the custom resource's version
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
                            parent_api['status']['ingress']['url'] = parent_api['spec']['hostname'] + parent_api['spec']['path']
                            if 'developerUI' in parent_api['spec']:
                                parent_api['status']['ingress']['developerUI'] = parent_api['spec']['hostname'] + parent_api['spec']['developerUI']
                            if 'ip' in ingressTarget.keys():
                                parent_api['status']['ingress']['ip'] = ingressTarget['ip']
                            elif 'hostname' in ingressTarget.keys():
                                parent_api['status']['ingress']['ip'] = ingressTarget['hostname'] 
                            else:
                                logging.warning('Ingress target does not contain ip or hostname')
                            api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                            logging.info(f"Updated parent api: {name} status to {parent_api['status']}")
                            logging.debug(f"api_response {api_response}")
                        else:    #if api doesn't specify hostname then use ip
                            if 'ip' in ingressTarget.keys():
                                parent_api['status']['ingress']['url'] = ingressTarget['ip'] + parent_api['spec']['path']
                                if 'developerUI' in parent_api['spec']:
                                    parent_api['status']['ingress']['developerUI'] = ingressTarget['ip'] + parent_api['spec']['developerUI']
                                parent_api['status']['ingress']['ip'] = ingressTarget['ip']
                                api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                            elif 'hostname' in ingressTarget.keys():
                                parent_api['status']['ingress']['url'] = ingressTarget['hostname'] + parent_api['spec']['path']
                                if 'developerUI' in parent_api['spec']:
                                    parent_api['status']['ingress']['developerUI'] = ingressTarget['hostname'] + parent_api['spec']['developerUI']
                                parent_api['status']['ingress']['ip'] = ingressTarget['hostname']
                                api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, name, parent_api)
                                logging.info(f"Updated parent api: {name} status to {parent_api['status']}")
                                logging.debug(f"api_response {api_response}")
                            else:
                                logging.warning('Ingress target does not contain ip or hostname')

                    else:
                        logging.warning('Ingress is an empty list')
                else:
                    logging.warning('Ingress is not a list')

            else:
                logging.warning('Load Balancer doesnt have an ingress resource')


