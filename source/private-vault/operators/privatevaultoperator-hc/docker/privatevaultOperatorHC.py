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

#vault_addr = os.getenv('VAULT_ADDR', 'https://canvas-vault-hc.k8s.feri.ai')
vault_addr = os.getenv('VAULT_ADDR', 'http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200')
auth_path = os.getenv('AUTH_PATH', 'jwt-k8s-pv')
policy_name_tpl = os.getenv('POLICY_NAME_TPL', 'pv-{0}-policy')
login_role_tpl = os.getenv('LOGIN_ROLE_TPL', 'pv-{0}-role')
secrets_mount_tpl = os.getenv('SECRETS_MOUNT_TPL', 'kv-{0}')
secrets_base_path_tpl = os.getenv('SECRETS_BASE_PATH_TPL', 'sidecar')

audience = os.getenv('AUDIENCE', "https://kubernetes.default.svc.cluster.local")


# Inheritance: https://github.com/nolar/kopf/blob/main/docs/admission.rst#custom-serverstunnels
# https://github.com/nolar/kopf/issues/785#issuecomment-859931945

from typing import AsyncIterator

class ServiceTunnel:
    async def __call__(
        self, fn: kopf.WebhookFn
    ) -> AsyncIterator[kopf.WebhookClientConfig]:
        namespace = "privatevault-system"
        name = "pvop-webhook-svc"
        service_port = 443
        container_port = 9443
        server = kopf.WebhookServer(port=container_port, host=f"{name}.{namespace}.svc")
        async for client_config in server(fn):
            client_config["url"] = None
            client_config["service"] = kopf.WebhookClientConfigService(
                name=name, namespace=namespace, port=service_port
            )
            yield client_config


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = 'pvop.kopf.dev'
    
    
    # try somehow to use WebhookClientConfigService, see https://github.com/nolar/kopf/issues/864
    
    
@kopf.on.mutate('pods', labels={'privatevault': 'sidecar'})
def podmutate(patch: kopf.Patch, warnings: list[str], **_):
    logging.info(f"POD mutate called with patch: {patch}")
    warnings.append("podmutate was called")
    patch.metadata.labels["newlabel"] = "setinmoothuk"



def decrypt(encrypted_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


def setupPrivateVault(ciid:str, namespace:str, service_account:str):
    try:
        logging.info(f"SETUP PRIVATEVAULT ciid={ciid}, ns={namespace}, sa={service_account}")
        
        policy_name = policy_name_tpl.format(ciid)
        login_role = login_role_tpl.format(ciid)
        secrets_mount = secrets_mount_tpl.format(ciid)
        secrets_base_path = secrets_base_path_tpl.format(ciid)

        logging.info(f"policy_name: {policy_name}")
        logging.info(f"login_role: {login_role}")
        logging.info(f"secrets_mount: {secrets_mount}")
        logging.info(f"secrets_base_path: {secrets_base_path}")

        
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
    except:
        logging.exception(f"ERRPR setup vault {ciid} failed!")
    

def deletePrivateVault(ciid:str):
    try:
        logging.info(f"DELETE PRIVATEVAULT ciid={ciid}")
        
        login_role = login_role_tpl.format(ciid)
        policy_name = policy_name_tpl.format(ciid)
        secrets_mount = secrets_mount_tpl.format(ciid)
        
        logging.info(f"policy_name: {policy_name}")
        logging.info(f"login_role: {login_role}")
        logging.info(f"secrets_mount: {secrets_mount}")
        
        token = decrypt("gAAAAABkh0MEK0_rdLWahgD8PGgo6d5xgPlnHnMmTbvN4s1BdKyO0xOFFxagsN4nQCmGKNuoAlopr4GHfvuM3E6jNt5N-YLODQ==")
        # Authentication
        client = hvac.Client(
            url=vault_addr,
            token=token,
        )
    except:
        logging.exception(f"ERRPR delete vault {ciid} failed!")
        
    
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


def injectSidecar(body):
    logging.info(f"POD inject sidecar: {body}")
    

# @kopf.on.create('pods', labels={'privatevault': 'sidecar'})
# def podCreate(meta, spec, status, body, namespace, labels, name, **kwargs):
#
#     logging.debug(f"POD Create/Update  called with spec: {spec}")
#     logging.debug(f"POD Create/Update  called with meta: {meta}")
#     logging.debug(f"POD Create/Update  called with body: {body}")
#     logging.debug(f"POD Create/Update  called with status: {status}")
#     logging.debug(f"POD Create/Update  called with labels: {labels}")
#     logging.debug(f"POD Create/Update  called with namespace: {namespace}")
#     logging.debug(f"POD Create/Update  called with name: {name}")





# when an oda.tmforum.org privatevault resource is created or updated, configure policy and role 
@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'privatevaults')
@kopf.on.update('oda.tmforum.org', 'v1alpha1', 'privatevaults')
def privatevaultCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with spec: {spec}")
    logging.info(f"Create/Update  called with meta: {meta}")
    logging.info(f"Create/Update  called with body: {body}")
    logging.debug(f"privatevault  called with status: {status}")
    logging.debug(f"privatevault  called with labels: {labels}")
    logging.debug(f"privatevault  called with namespace: {namespace}")
    logging.debug(f"privatevault  called with name: {name}")

    logging.debug(f"privatevault has name: {spec['comopnentInstanceID']}")

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


def set_proxy():
    os.environ["HTTP_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["HTTPS_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["NO_PROXY"]="10.0.0.0/8,.eks.amazonaws.com,.aws.telekom.de,caas-portal-test.telekom.de,caas-portal.telekom.de,.caas-t02.telekom.de"

def testCreatePV():
    #set_proxy()
    dummy = {}
    spec = {
        'comopnentInstanceID': 'demo-comp-123',
        'podSelector': {
            'namespace': 'demo-comp-123',
            'serviceAccount': 'default'
        },
        'sideCar': {
            'port': 5000,
            'token': 'negotiate'
        },
        'type': 'sideCar'        
    }
    privatevaultCreate(dummy, spec, dummy, dummy, "dempo-comp-123", dummy, "privatevault-demo-comp-123")

def testDeletePV():
    #set_proxy()
    dummy = {}
    spec = {
        'comopnentInstanceID': 'demo-comp-123',
        'podSelector': {
            'namespace': 'demo-comp-123',
            'serviceAccount': 'default'
        },
        'sideCar': {
            'port': 5000,
            'token': 'negotiate'
        },
        'type': 'sideCar'        
    }
    privatevaultDelete(dummy, spec, dummy, dummy, "demo-comp-123", dummy, "privatevault-demo-comp-123")



if __name__ == '__main__':
    logging.info(f"main called")
    #set_proxy()
    #testDeletePV()
    #testCreatePV()
    
    whs = kopf.WebhookServer(addr="0.0.0.0", port=9443, host="pvop-webhook-svc.privatevault-system.svc")
    print(whs)


