import kopf
import kubernetes.client
import yaml
import logging
import swaggerToConfigmap
import os

from kubernetes.client.rest import ApiException
logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 30))) #Logging level default = WARNING

# when an oda.tmforum.org api resource is created, create the corresponding wso2 custom resource (including
# storing the swagger for the api in a configmap). 
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'apis')
def ingress(meta, spec, **kwargs):

    logging.debug(f"oda.tmforum.org api is called with body: {spec}")
    namespace = meta.get('namespace')

    # get API details 
    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api implementation at: {spec['implementation']}")

    # create the configmap
    microgatewayName = 'wso2-' + meta['name'] 
    swaggerURL = spec['specification']
    apiPath = spec['path']
    implementation = ['http://' + spec['implementation'] + ':' + str(spec['port']) + spec['path']] # path to implementation internal to K8s
    configmapName = microgatewayName + '-swagger'
    logging.debug('swaggerURL %s', swaggerURL)
    logging.debug('apiPath %s', apiPath)
    logging.debug('implementation %s', implementation)
    logging.debug('configmapName %s', configmapName)

    configMap = swaggerToConfigmap.loadSwaggerYAML(swaggerURL, apiPath, implementation, configmapName)
    
    core_api_instance = kubernetes.client.CoreV1Api()
    try:
        api_response = core_api_instance.create_namespaced_config_map(namespace, configMap)
        logging.debug('core_api_instance.create_namespaced_config_map. api_response = %s', api_response)
    except ApiException as e:   
        logging.warning("Exception when calling core_api_instance.create_namespaced_config_map:")
        logging.info(e)
        raise kopf.TemporaryError("Exception creating configmap.")

    # create API.wso2.com custom resource
    wso2_custom_resource = {
        "apiVersion": "wso2.com/v1alpha1",
        "kind": "API",
        "metadata": {},
        "spec": {
            "definition": {
                "interceptors":{},
                "swaggerConfigmapNames": [configmapName],
                "type": "swagger"
            },
            "mode": "privateJet",
            "override": True,
            "replicas": 1
        }
    }

    # Make the CRD a child of the oda.cmforum.org api
    kopf.adopt(wso2_custom_resource)
    logging.debug(f"wso2_custom_resource (adopted): {wso2_custom_resource}")

    wso2_custom_resource['metadata']['name'] = microgatewayName

    # create the resource
    try:
        api = kubernetes.client.CustomObjectsApi()
        apiObj = api.create_namespaced_custom_object(
                group="wso2.com",
                version="v1alpha1",
                namespace=namespace,
                plural="apis",
                body=wso2_custom_resource,
            )
        logging.debug(f"Resource created: {apiObj}")
    except ApiException as e:
        logging.warning("Exception when calling api.create_namespaced_custom_object:")
        logging.info(e)
        raise kopf.TemporaryError("Exception creating API custom resource.")

    # Update the parent's status.
    return {"uid": apiObj['metadata']['uid']}


# When wso2 updates the LoadBalancer service, add IP address of load balancer on the parent API object
@kopf.on.field('', 'v1', 'services', field='status.loadBalancer')
def ingress_status(meta, status, spec, **kwargs):
    logging.info(f"Update called for service {meta['name']}")
    logging.debug(f"Status: {status}")
    namespace = meta.get('namespace')

    serviceName = meta.get('name')
    # if the service name begins with wso2-, find the corresponding api.oda.tmforum.org resource
    if serviceName[:5] == 'wso2-' :
        # api.oda.tmforum.org resource name is 
        tmfAPIResource = serviceName[5:]
        logging.info('api.oda.tmforum.org resource name is %s', tmfAPIResource)

        api_instance = kubernetes.client.CustomObjectsApi()
        group = 'oda.tmforum.org' # str | the custom resource's group
        version = 'v1alpha2' # str | the custom resource's version
        namespace = namespace # str | The custom resource's namespace
        plural = 'apis' # str | the custom resource's plural name

        try:
            parent_api = api_instance.get_namespaced_custom_object(group, version, namespace, plural, tmfAPIResource)

        except ApiException as e:
            logging.warning("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
            raise kopf.TemporaryError("Exception updating service_status.")

        logging.debug(f"Load Balancer service parent api resource is {parent_api}")

        #get ip or hostname where ingress is exposed
        loadBalancer = status['loadBalancer']

        if 'ingress' in loadBalancer.keys():
            ingress = loadBalancer['ingress']
            if isinstance(ingress, list):
                if len(ingress)>0:
                    ingressTarget = ingress[0]
                    if 'ip' in ingressTarget.keys():
                        parent_api['status']['ingress']['url'] = ingressTarget['ip'] + ':' + str(spec['ports'][0]['port']) + parent_api['spec']['path']
                        if 'developerUI' in parent_api['spec']:
                            parent_api['status']['ingress']['developerUI'] = ingressTarget['ip'] + ':' + str(spec['ports'][0]['port']) + parent_api['spec']['developerUI']
                        api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, tmfAPIResource, parent_api)
                    elif 'hostname' in ingressTarget.keys():
                        parent_api['status']['ingress']['url'] = ingressTarget['hostname'] + ':' + str(spec['ports'][0]['port']) + parent_api['spec']['path']
                        if 'developerUI' in parent_api['spec']:
                            parent_api['status']['ingress']['developerUI'] = ingressTarget['hostname'] + ':' + str(spec['ports'][0]['port']) + parent_api['spec']['developerUI']
                        api_response = api_instance.patch_namespaced_custom_object(group, version, namespace, plural, tmfAPIResource, parent_api)
                    else:
                        logging.warning('Ingress target does not contain ip or hostname')
                else:
                    logging.warning('Ingress is an empty list')
            else:
                logging.warning('Ingress is not a list')
        else:
            logging.warning('Load Balancer doesnt have an ingress resource')

        logging.info(f"Added ip: {status['loadBalancer']['ingress'][0]['ip']} to parent api: {tmfAPIResource}")
        logging.debug(f"api_response {api_response}")


if __name__ == '__main__':
    configMap = swaggerToConfigmap.loadSwaggerYAML("https://raw.githubusercontent.com/tmforum-rand/oda-component-definitions/wso2APIOperator/components/vodafone-next-productcatalog.swagger.json?token=ABYIJPQH7KR75YX44JF62XS626XTA",  '/catalogManagement', ['http://next-pc:8191/catalogManagement'], 'next-pc-swagger')
    with open('output.yml', 'w') as outfile:
      yaml.dump(configMap, outfile, default_flow_style=False)