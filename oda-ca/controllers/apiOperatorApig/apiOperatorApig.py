import kopf
import logging
import os
import time
import json
from http.client import HTTPConnection
import kubernetes.client
from kubernetes.client.rest import ApiException

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 10)))

# when an oda.tmforum.org api resource is created or updated, bind the apig api
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'apis')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'apis')
def apigBind(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api has status: {status}")
    logging.debug(f"api is called with body: {spec}")
    namespace = meta.get('namespace')
    apigEndpoint = os.getenv('APIG_ENDPOINT', "apig-operator-uportal.%s:8080"%namespace)
    apigIngressName = os.getenv('APIG_INGRESS', "apig-operator-uportal")
    apigBindPath = "/operator/AutoCreation/createAPIFromSwagger"
    
    apiSpec = {
        "path":spec['path'],
        "name":meta['name'],
        "specification":spec['specification'],
        "implementation": spec['implementation'],
        "port": spec['port']
    }
    
    MOCK_ALL = os.getenv('MOCK_ALL', "")
    if MOCK_ALL != "":
        return {"response": "success", "spec": MOCK_ALL}

    if not ( status and ('apigBind' in status.keys()) and status['apigBind']['spec'] == apiSpec ):
        resp = restCall(apigEndpoint, apigBindPath, apiSpec)
        if not resp or resp['res_code'] != "00000":
            raise kopf.TemporaryError( "Bind apig failed, return %s"%resp )
        # if bind success, update CRD status
        try:
            customObjectsApi = kubernetes.client.CustomObjectsApi()
            group = 'oda.tmforum.org' # str | the custom resource's group
            version = 'v1alpha2' # str | the custom resource's version
            plural = 'apis' # str | the custom resource's plural name
            apiObj = customObjectsApi.get_namespaced_custom_object(group, version, namespace, plural, meta['name'] )
            
            ingressApi = kubernetes.client.NetworkingV1beta1Api()
            listIngressResp = ingressApi.read_namespaced_ingress( apigIngressName, namespace )
            logging.info("List ingress response: %s\n" % listIngressResp)
            apigIngress = listIngressResp.to_dict()
           
            if 'status' in apigIngress.keys():
                if 'load_balancer' in apigIngress['status'].keys():
                    loadBalancer = apigIngress['status']['load_balancer']
                    if 'ingress' in loadBalancer.keys():
                        ingress = loadBalancer['ingress']
                        if len(ingress)>0:
                            ingressTarget = ingress[0]['ip']
            if ingressTarget:
                if not('status' in apiObj.keys()):
                    apiObj['status'] = {}
                if not('apiStatus' in apiObj['status'].keys()):
                    apiObj['status']['apiStatus'] = {}
                apiObj['status']['apiStatus']
                apiObj['status']['apiStatus']['developerUI'] = "http://" + ingressTarget + spec['path'] + "/docs/"
                apiObj['status']['apiStatus']['ip'] = ingressTarget
                apiObj['status']['apiStatus']['name'] = meta['name']
                apiObj['status']['apiStatus']['url'] = "http://" + ingressTarget + spec['path']
                apiObj['status']['implementation'] = {"ready": True}
                patchRslt = customObjectsApi.patch_namespaced_custom_object(group, version, namespace, plural, meta['name'] , apiObj)
                logging.debug("Patch apis response: %s\n" % patchRslt)
        except ApiException as e:
            logging.warning("Exception when calling kubernetes api: %s\n" % e)
            raise kopf.TemporaryError("Exception when bind apig, kubernetes api failed")
        return {"response": resp, "spec": apiSpec}
    return

# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete('oda.tmforum.org', 'v1alpha2', 'apis', retries=5)
def apigUnBind(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api has status: {status}")
    logging.debug(f"api is called with body: {spec}")
    
    MOCK_ALL = os.getenv('MOCK_ALL', "")
    if MOCK_ALL != "":
        return {"response": "success", "spec": MOCK_ALL }
    
    namespace = meta.get('namespace')
    apigEndpoint = os.getenv('APIG_ENDPOINT', "apig-operator-uportal.%s:8080"%namespace) 
    apigUnBindPath = "/operator/AutoCreation/removeAPIFromSwagger"
    
    apiSpec = {
        "path":spec['path'],
        "name":meta['name'],
        "specification":spec['specification'],
        "implementation": spec['implementation'],
        "port": spec['port']
    }
    resp = restCall(apigEndpoint, apigUnBindPath, apiSpec)
    
    if not resp or resp['res_code'] != "00000":
        raise kopf.TemporaryError( "UnBind apig failed , return %s"%resp )
    return {"response": resp}

# a simple Restful API caller
def restCall( host, path, spec ):
    APIG_MOCK = os.getenv('APIG_MOCK', "")
    if APIG_MOCK != "":
        return {"res_code": "00000", "res_message": APIG_MOCK }
        
    hConn=HTTPConnection(host)
    respBody = None
    try:
        data = json.dumps(spec)
        headers = {"Content-type": "application/json"}
        hConn.request('POST', path, data.encode('utf-8'), headers)
        logging.info(f"host: %s, path: %s, body: %s"%(host,path,data))
        resp = hConn.getresponse()
        data=resp.read()
        if data:
            respStr = data.decode('utf-8')
            logging.info(f"Rest api response code: %s, body: %s"%(resp.status, respStr))
            respBody = json.loads(respStr)
        hConn.close()
        if resp.status != 200:
            raise kopf.TemporaryError("Exception when calling rest api, return code: %s\n" % resp.status)
        return respBody
    except Exception as StrError:
        hConn.close()
        logging.warn("Exception when calling restful api: %s\n" % StrError)
        time.sleep(2)
