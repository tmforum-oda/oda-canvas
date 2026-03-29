"""Kubernetes operator for ODA API custom resources.

It uses the kopf kubernetes operator framework (https://kopf.readthedocs.io/) to build an
operator that takes API custom resources and implements them using Whale Cloud APIG(API Gateway). 

"""
import kopf
import logging
import os
import time
import json
from http.client import HTTPConnection
import kubernetes.client
from kubernetes.client.rest import ApiException

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger("APIOperator")
logger.setLevel(int(logging_level))
logger.info(f"Logging set to %s", logging_level)

GROUP = "oda.tmforum.org"
VERSION = "v1beta4"
APIS_PLURAL = "exposedapis"
COMPONENTS_PLURAL = "components"

APIG_BIND_API = "/operator/AutoCreation/createAPIFromSwagger"
APIG_UNBIND_API = "/operator/AutoCreation/removeAPIFromSwagger"
APIG_DEFAULT_INGRESS = "apig-operator-uportal"
APIG_DEFAULT_PORT = 8080
APIG_SUCC_CODE = "0000"

# when an oda.tmforum.org api resource is created or updated, bind the apig api
@kopf.on.create(GROUP, VERSION, APIS_PLURAL)
@kopf.on.update(GROUP, VERSION, APIS_PLURAL)
def apigBind(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api has status: {status}")
    logging.debug(f"api is called with body: {spec}")
    namespace = meta.get('namespace')
    apigEndpoint = os.getenv('APIG_ENDPOINT', "%s.%s:%d"%(APIG_DEFAULT_INGRESS,namespace,APIG_DEFAULT_PORT))
    apigIngressName = os.getenv('APIG_INGRESS', APIG_DEFAULT_INGRESS)
    
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
        resp = restCall(apigEndpoint, APIG_BIND_API, apiSpec)
        if not resp or resp['res_code'] != APIG_SUCC_CODE:
            raise kopf.TemporaryError( "Bind apig failed, return %s"%resp )
        # if bind success, update CRD status
        try:
            customObjectsApi = kubernetes.client.CustomObjectsApi()
            apiObj = customObjectsApi.get_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL, meta['name'] )
            
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
                patchRslt = customObjectsApi.patch_namespaced_custom_object(GROUP, VERSION, namespace, APIS_PLURAL, meta['name'] , apiObj)
                logging.debug("Patch apis response: %s\n" % patchRslt)
        except ApiException as e:
            logging.warning("Exception when calling kubernetes api: %s\n" % e)
            raise kopf.TemporaryError("Exception when bind apig, kubernetes api failed")
        return {"response": resp, "spec": apiSpec}
    return

# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete(GROUP, VERSION, APIS_PLURAL, retries=5)
def apigUnBind(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.debug(f"api has name: {meta['name']}")
    logging.debug(f"api has status: {status}")
    logging.debug(f"api is called with body: {spec}")
    
    MOCK_ALL = os.getenv('MOCK_ALL', "")
    if MOCK_ALL != "":
        return {"response": "success", "spec": MOCK_ALL }
    
    namespace = meta.get('namespace')
    apigEndpoint = os.getenv('APIG_ENDPOINT', "%s.%s:%d"%(APIG_DEFAULT_INGRESS,namespace,APIG_DEFAULT_PORT))
    
    apiSpec = {
        "path":spec['path'],
        "name":meta['name'],
        "specification":spec['specification'],
        "implementation": spec['implementation'],
        "port": spec['port']
    }
    resp = restCall(apigEndpoint, APIG_UNBIND_API, apiSpec)
    
    if not resp or resp['res_code'] != APIG_SUCC_CODE:
        raise kopf.TemporaryError( "UnBind apig failed , return %s"%resp )
    return {"response": resp}

# call Apig Restful APIs
def restCall( host, path, spec ):
    APIG_MOCK = os.getenv('APIG_MOCK', "")
    if APIG_MOCK != "":
        return {"res_code": APIG_SUCC_CODE, "res_message": APIG_MOCK }
        
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
        logging.error("Exception when calling restful api: %s\n" % StrError)
        time.sleep(2)
