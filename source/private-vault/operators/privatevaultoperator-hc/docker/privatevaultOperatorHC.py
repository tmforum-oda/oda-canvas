import kopf
import logging
import os
import time
import json
from http.client import HTTPConnection
import kubernetes.client
from kubernetes.client.rest import ApiException

import hvac
import sys
from cryptography.fernet import Fernet
import base64

# https://kopf.readthedocs.io/en/stable/install/

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 10)))

vault_addr = os.getenv('VAULT_ADDR', 'https://canvas-vault-hc.k8s.feri.ai')
#vault_addr = os.getenv('VAULT_ADDR', 'http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200')
auth_path = os.getenv('AUTH_PATH', 'jwt-k8s-pv')
policy_name_tpl = os.getenv('POLICY_NAME_TPL', 'pv-{0}-policy')
login_role_tpl = os.getenv('LOGIN_ROLE_TPL', 'pv-{0}-role')
secrets_mount_tpl = os.getenv('SECRETS_MOUNT_TPL', 'kv-{0}')
secrets_base_path_tpl = os.getenv('SECRETS_BASE_PATH_TPL', 'sidecar')

audience = os.getenv('AUDIENCE', "https://kubernetes.default.svc.cluster.local")


def decrypt(encrypted_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


def setupPrivateVault(ciid:str, namespace:str, service_account:str):
    logging.info(f"SETUP PRIVATEVAULT ciid={ciid}, ns={namespace}, sa={service_account}")
    
    login_role = login_role_tpl.format(ciid)
    policy_name = policy_name_tpl.format(ciid)
    secrets_mount = secrets_mount_tpl.format(ciid)
    secrets_base_path = secrets_base_path_tpl.format(ciid)
    
    token = decrypt("gAAAAABkh0MEK0_rdLWahgD8PGgo6d5xgPlnHnMmTbvN4s1BdKyO0xOFFxagsN4nQCmGKNuoAlopr4GHfvuM3E6jNt5N-YLODQ==")
    # Authentication
    client = hvac.Client(
        url=vault_addr,
        token=token,
    )

    ### enable KV v2 engine 
    # https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?highlight=mount#hvac.api.system_backend.Mount.enable_secrets_engine
    #
    logging.info(f"enabling KV v2 engine at {secrets_mount}")
    client.sys.enable_secrets_engine("kv", secrets_mount, options={"version":"2"})
    
    ### create policy
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
    #
    logging.info(f'create policy {policy_name}')
    policy = f'''
    path "{secrets_mount}/data/{secrets_base_path}/*" {{
      capabilities = ["create", "read", "update", "delete", "list", "patch"]
    }}
    '''
    client.sys.create_or_update_policy(
        name=policy_name,
        policy=policy,
    )
    
    ### create role
    # https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#create-role
    #
    logging.info(f'create role {login_role}')
    allowed_redirect_uris = [f'{vault_addr}/jwt-test/callback'] # ?
    sub = f"system:serviceaccount:{namespace}:{service_account}"
    logging.info(f"sub={sub}")
    # JWT
    client.auth.jwt.create_role(
        name=login_role,
        role_type='jwt',
        user_claim='sub',
        bound_subject=sub,
        bound_audiences=[audience],
        token_policies=[policy_name],
        token_ttl=3600,
        allowed_redirect_uris=allowed_redirect_uris,  # why mandatory? 
        path = auth_path,
    )
    

def deletePrivateVault(ciid:str):
    logging.info(f"DELETE PRIVATEVAULT ciid={ciid}")
    
    login_role = login_role_tpl.format(ciid)
    policy_name = policy_name_tpl.format(ciid)
    secrets_mount = secrets_mount_tpl.format(ciid)
    secrets_base_path = secrets_base_path_tpl.format(ciid)
    
    token = decrypt("gAAAAABkh0MEK0_rdLWahgD8PGgo6d5xgPlnHnMmTbvN4s1BdKyO0xOFFxagsN4nQCmGKNuoAlopr4GHfvuM3E6jNt5N-YLODQ==")
    # Authentication
    client = hvac.Client(
        url=vault_addr,
        token=token,
    )
    
    ### disable KV secrets engine
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/mount.html?highlight=mount#disable-secrets-engine
    #
    logging.info(f"disabling KV engine {secrets_mount}")
    client.sys.disable_secrets_engine(secrets_mount)
    
    ### delete role
    # https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#delete-role
    #
    logging.info(f'delete role {login_role}')
    client.auth.jwt.delete_role(
        name=login_role,
        path = auth_path,
    )

    ### delete policy
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#delete-policy
    #
    logging.info(f'delete policy {policy_name}')
    client.sys.delete_policy(name=policy_name)


# when an oda.tmforum.org privatevault resource is created or updated, configure policy and role 
@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'privatevaults')
@kopf.on.update('oda.tmforum.org', 'v1alpha1', 'privatevaults')
def privatevaultCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with spec: {spec}")
    logging.debug(f"privatevault has name: {spec['comopnentInstanceID']}")
    logging.debug(f"privatevault has status: {status}")

    ciid = spec['comopnentInstanceID']
    namespace = spec['podSelector']['namespace']
    #namespace = meta.get('namespace')   # only if privatevault CR is in target namespace
    service_account = spec['podSelector']['serviceAccount']
    
    setupPrivateVault(ciid, namespace, service_account)
    



# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete('oda.tmforum.org', 'v1alpha1', 'privatevaults', retries=5)
def privatevaultDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with meta: {type(meta)} - {meta}")
    logging.info(f"Create/Update  called with status: {type(status)} - {status}")
    logging.info(f"Create/Update  called with body: {type(body)} - {body}")
    logging.info(f"Create/Update  called with namespace: {type(namespace)} - {namespace}")
    logging.info(f"Create/Update  called with labels: {type(labels)} - {labels}")
    logging.info(f"Create/Update  called with name: {type(name)} - {name}")

    logging.debug(f"privatevault has name: {spec['comopnentInstanceID']}")
    logging.debug(f"privatevault has status: {status}")
    logging.debug(f"privatevault is called with body: {spec}")
    
    ciid = spec['comopnentInstanceID']

    deletePrivateVault(ciid)



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


# def set_proxy():
#     os.environ["HTTP_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
#     os.environ["HTTPS_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
#     os.environ["NO_PROXY"]="10.0.0.0/8,.eks.amazonaws.com,.aws.telekom.de,caas-portal-test.telekom.de,caas-portal.telekom.de,.caas-t02.telekom.de"
#
#
# if __name__ == '__main__':
#     #set_proxy()
#     dummy = {}
#     spec = {
#         'comopnentInstanceID': 'demo-comp-123',
#         'podSelector': {
#             'namespace': 'demo-comp-123',
#             'serviceAccount': 'default'
#         },
#         'sideCar': {
#             'port': 5000,
#             'token': 'negotiate'
#         },
#         'type': 'sideCar'        
#     }
#     privatevaultDelete(dummy, spec, dummy, dummy, "dempo-comp-123", dummy, "privatevault-demo-comp-123")
#     privatevaultCreate(dummy, spec, dummy, dummy, "dempo-comp-123", dummy, "privatevault-demo-comp-123")
#

