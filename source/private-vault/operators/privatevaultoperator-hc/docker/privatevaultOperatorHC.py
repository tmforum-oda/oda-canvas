import kopf
import logging
import os
import time
import json
from http.client import HTTPConnection
import kubernetes.client
from kubernetes.client.rest import ApiException

# https://kopf.readthedocs.io/en/stable/install/

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 10)))

# when an oda.tmforum.org privatevault resource is created or updated, configure policy and role 
@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'privatevaults')
@kopf.on.update('oda.tmforum.org', 'v1alpha1', 'privatevaults')
def privatevaultCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with body: {meta}")
    logging.debug(f"privatevault has name: {meta['name']}")
    logging.debug(f"privatevault has status: {status}")
    logging.debug(f"privatevault is called with body: {spec}")
    namespace = meta.get('namespace')

    return


# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete('oda.tmforum.org', 'v1alpha1', 'privatevaults', retries=5)
def privatevaultDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with body: {body}")

    logging.debug(f"privatevault has name: {meta['name']}")
    logging.debug(f"privatevault has status: {status}")
    logging.debug(f"privatevault is called with body: {spec}")

    return    

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
