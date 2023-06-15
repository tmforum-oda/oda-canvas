import kopf
import hvac
import logging
import os
import time
import json
import sys
import fnmatch
from http.client import HTTPConnection
from cryptography.fernet import Fernet
import base64
import kubernetes
from kubernetes.client.rest import ApiException
from typing import AsyncIterator
from setuptools.command.setopt import config_file


# https://kopf.readthedocs.io/en/stable/install/

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 10)))

#vault_addr = os.getenv('VAULT_ADDR', 'https://canvas-vault.k8s.feri.ai')
vault_addr = os.getenv('VAULT_ADDR', 'http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200')
auth_path = os.getenv('AUTH_PATH', 'jwt-k8s-pv')
policy_name_tpl = os.getenv('POLICY_NAME_TPL', 'pv-{0}-policy')
login_role_tpl = os.getenv('LOGIN_ROLE_TPL', 'pv-{0}-role')
secrets_mount_tpl = os.getenv('SECRETS_MOUNT_TPL', 'kv-{0}')
secrets_base_path_tpl = os.getenv('SECRETS_BASE_PATH_TPL', 'sidecar')

audience = os.getenv('AUDIENCE', "https://kubernetes.default.svc.cluster.local")

webhook_service_name = os.getenv('WEBHOOK_SERVICE_NAME', 'dummyservicename') 
webhook_service_namespace = os.getenv('WEBHOOK_SERVICE_NAMESPACE', 'dummyservicenamespace') 
webhook_service_port = int(os.getenv('WEBHOOK_SERVICE_PORT', '443'))

componentname_label = os.getenv('COMPONENTNAME_LABEL', 'oda.tmforum.org/componentName')

privatevault_cr_namespace = os.getenv('PRIVATEVAULT_CR_NAMESPACE', 'privatevault-system')



# Inheritance: https://github.com/nolar/kopf/blob/main/docs/admission.rst#custom-serverstunnels
# https://github.com/nolar/kopf/issues/785#issuecomment-859931945


class ServiceTunnel:
    async def __call__(
        self, fn: kopf.WebhookFn
    ) -> AsyncIterator[kopf.WebhookClientConfig]:
        container_port = 9443
        server = kopf.WebhookServer(port=container_port, host=f"{webhook_service_name}.{webhook_service_namespace}.svc")
        async for client_config in server(fn):
            client_config["url"] = None
            client_config["service"] = kopf.WebhookClientConfigService(
                name=webhook_service_name, namespace=webhook_service_namespace, port=webhook_service_port
            )
            yield client_config


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = 'pv.sidecar.kopf'
    


def entryExists(dictionary, key, value):
    for entry in dictionary:
        if key in entry:
            if entry[key] == value:
                return True
    return False


def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result


def inject_sidecar(body, patch):
    
    pv_name = safe_get(None, body, "metadata", "labels", componentname_label)
    if not pv_name:
        logging.info(f"Component name in label {componentname_label} not set, doing nothing")
        return

    pod_name = safe_get(None, body, "metadata", "name")
    if not pod_name:
        pod_name = safe_get(None, body, "metadata", "generateName")
    pod_namespace = body["metadata"]["namespace"]
    pod_serviceAccountName = safe_get("default", body, "spec", "serviceAccountName")
    logging.info(f"POD serviceaccount:{pod_namespace}:{pod_name}:{pod_serviceAccountName}")

    logging.debug(f"loading k8s config")
    k8s_load_config()
    
    pv_cr_name = f"privatevault-{pv_name}"
    logging.debug(f"getting privatevault cr {pv_cr_name} from k8s")
    pv_spec = get_pv_spec(pv_cr_name)
    logging.debug(f"privatevault spec: {pv_spec}")
    if not pv_spec:
        raise kopf.AdmissionError(f"privatevault {pv_cr_name} has no spec.", code=400)
    
    pvname = safe_get("", pv_spec, "name")
    type = safe_get("sideCar", pv_spec, "type")
    sidecar_port = int(safe_get("5000", pv_spec, "sideCar", "port"))
    podsel_name = safe_get("", pv_spec, "podSelector", "name")
    podsel_namespace = safe_get("", pv_spec, "podSelector", "namespace")
    podsel_serviceaccount = safe_get("", pv_spec, "podSelector", "serviceaccount")
    logger.debug(f"filter: name={podsel_name}, namespace={podsel_namespace}, serviceaccount={podsel_serviceaccount}")
    if not pvname:
        raise kopf.AdmissionError(f"privatevault {pv_cr_name}: missing name.", code=400)      
    if type != "sideCar":
        raise kopf.AdmissionError(f"privatevault {pv_cr_name}: unsupported type {type}.", code=400)
    if podsel_name and not fnmatch.fnmatch(pod_name, podsel_name):
        raise kopf.AdmissionError(f"privatevault {pv_cr_name}: pod name does not match selector.", code=400)      
    if podsel_namespace and not fnmatch.fnmatch(pod_namespace, podsel_namespace):
        raise kopf.AdmissionError(f"privatevault {pv_cr_name}: pod namespace does not match selector.", code=400)      
    if podsel_serviceaccount and not fnmatch.fnmatch(pod_serviceAccountName, podsel_serviceaccount):
        raise kopf.AdmissionError(f"privatevault {pv_cr_name}: pod serviceAccountName does not match selector.", code=400)      

    container_pvsidecar = {
            "name": "pvsidecar",
            "image": "mtr.devops.telekom.de/magenta_canvas/private-vault-service:0.1.1",
            "ports": [
                {
                    "containerPort": sidecar_port,
                    "protocol": "TCP"
                }
            ],
            "env": [
                {
                    "name": "PRIVATEVAULT_NAME",
                    "value": f"{pvname}"
                },
                {
                    "name": "VAULT_ADDR",
                    "value": vault_addr
                },
                {
                    "name": "AUTH_PATH",
                    "value": "jwt-k8s-pv"
                },
                {
                    "name": "LOGIN_ROLE",
                    "value": f"pv-{pvname}-role"
                },
                {
                    "name": "SCRETS_MOUNT",
                    "value": f"kv-{pvname}"
                },
                {
                    "name": "SCRETS_BASE_PATH",
                    "value": "sidecar"
                }
            ],
            "resources": {
            },
            "volumeMounts": [
                {
                    "name": "pvsidecar-tmp",
                    "mountPath": "/tmp"
                },
                {
                    "name": "pvsidecar-kube-api-access",
                    "readOnly": True,
                    "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount"
                }
            ],
            "terminationMessagePath": "/dev/termination-log",
            "terminationMessagePolicy": "File",
            "imagePullPolicy": "Always",
            "securityContext": {
                "capabilities": {
                    "drop": [
                        "ALL"
                    ]
                },
                "privileged": False,
                "readOnlyRootFilesystem": True,
                "allowPrivilegeEscalation": False
            }
        }
            
    volume_pvsidecar_tmp = {
            "name": "pvsidecar-tmp",
            "emptyDir": {}
        }

    volume_pvsidecar_kube_api_access = {
            "name": "pvsidecar-kube-api-access",
            "projected": {
                "sources": [
                    {
                        "serviceAccountToken": {
                            "expirationSeconds": 3607,
                            "path": "token"
                        }
                    },
                    {
                        "configMap": {
                            "name": "kube-root-ca.crt",
                            "items": [
                                {
                                    "key": "ca.crt",
                                    "path": "ca.crt"
                                }
                            ]
                        }
                    },
                    {
                        "downwardAPI": {
                            "items": [
                                {
                                    "path": "namespace",
                                    "fieldRef": {
                                        "apiVersion": "v1",
                                        "fieldPath": "metadata.namespace"
                                    }
                                },
                                {
                                    "path": "name",
                                    "fieldRef": {
                                        "apiVersion": "v1",
                                        "fieldPath": "metadata.name"
                                    }
                                }
                            ]
                        }
                    }
                ],
                "defaultMode": 420
            }
        }

    containers = safe_get([], body, "spec", "containers")
    vols = safe_get([], body, "spec", "volumes")

    if entryExists(containers, "name", "pvsidecar"):
        logging.info("pvsidecar container already exists, doing nothing")
        return

    containers.append(container_pvsidecar)
    patch.spec["containers"] = containers
    logging.debug(f"injecting pvsidecar container")
    

    if not entryExists(vols, "name", "pvsidecar-tmp"):
        vols.append(volume_pvsidecar_tmp)
        patch.spec['volumes'] = vols
        logging.debug(f"injecting pvsidecar-tmp volume")

    if not entryExists(vols, "name", "pvsidecar-kube-api-access"):
        vols.append(volume_pvsidecar_kube_api_access)
        patch.spec['volumes'] = vols
        logging.debug(f"injecting pvsidecar-kube-api-access volume")


    

@kopf.on.mutate('pods', annotations={privatevaultname_annotation: kopf.PRESENT}, operation='CREATE', ignore_failures=True)
def podmutate(body, meta, spec, status, patch: kopf.Patch, warnings: list[str], **_):
    try:
        logging.info(f"POD mutate called with body: {type(body)} -  {body}")
        inject_sidecar(body, patch)
        logging.info(f"POD mutate returns patch: {type(patch)} -  {patch}")
    
    except:
        logging.exception(f"ERRPR podmutate failed!")
        warnings.append("internal error, patch not applied")
        patch.clear()
    
    



def decrypt(encrypted_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


def setupPrivateVault(pv_name:str, namespace:str, service_account:str):
    try:
        logging.info(f"SETUP PRIVATEVAULT pv_name={pv_name}, ns={namespace}, sa={service_account}")
        
        policy_name = policy_name_tpl.format(pv_name)
        login_role = login_role_tpl.format(pv_name)
        secrets_mount = secrets_mount_tpl.format(pv_name)
        secrets_base_path = secrets_base_path_tpl.format(pv_name)

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
        logging.exception(f"ERRPR setup vault {pv_name} failed!")
    

def deletePrivateVault(pv_name:str):
    try:
        logging.info(f"DELETE PRIVATEVAULT pv_name={pv_name}")
        
        login_role = login_role_tpl.format(pv_name)
        policy_name = policy_name_tpl.format(pv_name)
        secrets_mount = secrets_mount_tpl.format(pv_name)
        
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
        logging.exception(f"ERRPR delete vault {pv_name} failed!")
        
    
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

    logging.info(f"Create/Update  called with body: {body}")
    logging.debug(f"privatevault  called with namespace: {namespace}")
    logging.debug(f"privatevault  called with name: {name}")
    logging.debug(f"privatevault  called with labels: {labels}")

    # do not use safe_get for mandatory fields
    pv_name = spec['name']
    namespace = spec['podSelector']['namespace']
    service_account = spec['podSelector']['serviceAccount']
    
    setupPrivateVault(pv_name, namespace, service_account)
    
 
# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete('oda.tmforum.org', 'v1alpha1', 'privatevaults', retries=5)
def privatevaultDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with body: {body}")
    logging.info(f"Create/Update  called with namespace: {namespace}")
    logging.info(f"Create/Update  called with name: {name}")
    logging.info(f"Create/Update  called with labels: {labels}")
    
    pv_name = spec['name']

    deletePrivateVault(pv_name)



def set_proxy():
    os.environ["HTTP_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["HTTPS_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["NO_PROXY"]="10.0.0.0/8,.eks.amazonaws.com,.aws.telekom.de,caas-portal-test.telekom.de,caas-portal.telekom.de,.caas-t02.telekom.de"

def testCreatePV():
    #set_proxy()
    dummy = {}
    spec = {
        'name': 'demo-comp-123',
        'podSelector': {
            'namespace': 'demo-comp-123',
            'serviceAccount': 'default',
            'namespace': 'demo-comp-eins-*'
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
        'name': 'demo-comp-123',
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


def test_inject_sidecar():
    with open ('test/pod/mutate/mutate-body.json', 'r') as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = body["status"]
    patch = kopf.Patch({})
    warnings = []
    podmutate(body, meta, spec, status, patch, warnings)



def k8s_load_config():
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        try:
            conf = kubernetes.client.Configuration()
            conf.http_proxy_url="http://specialinternetaccess-lb.telekom.de:8080"
            conf.https_proxy_url="http://specialinternetaccess-lb.telekom.de:8080"
            kubernetes.config.load_kube_config(config_file = "C:\\Users\\a307131\\.kube\\config-k8s-feri-ai", client_configuration=conf)
        except kubernetes.config.ConfigException:
            try:
                kubernetes.config.load_kube_config()
            except kubernetes.config.ConfigException:
                raise Exception("Could not configure kubernetes python client")
    



def get_pv_spec(pv_name):
    coa = kubernetes.client.CustomObjectsApi()
    try:
        pv_cr = coa.get_namespaced_custom_object("oda.tmforum.org", "v1alpha1", privatevault_cr_namespace, "privatevaults", pv_name)
        return pv_cr["spec"]
    except ApiException:
        return None


def test_get_pv_spec():
    k8s_load_config()
    pv_spec = get_pv_spec("privatevault-demo-comp-123")
    print(pv_spec)
    name = safe_get("", pv_spec, "name")
    podsel_name = safe_get("", pv_spec, "podSelector", "name")
    podsel_namespace = safe_get("", pv_spec, "podSelector", "namespace")
    podsel_serviceaccount = safe_get("", pv_spec, "podSelector", "serviceaccount")
    sidecar_port = int(safe_get("5000", pv_spec, "sideCar", "port"))
    type = safe_get("sideCar", pv_spec, "type")
    print(f"PV name: {name}")
    print(f"PV podsel_name: {podsel_name}")
    print(f"PV podsel_namespace: {podsel_namespace}")
    print(f"PV podsel_serviceaccount: {podsel_serviceaccount}")
    print(f"PV sidecar_port: {sidecar_port}")
    print(f"PV type: {type}")

    if not fnmatch.fnmatch("demo-comp-1234fedc-zyxw7756", podsel_name):
        raise kopf.AdmissionError(f"pod name does not match selector.", code=400)

if __name__ == '__main__':
    logging.info(f"main called")
    #set_proxy()
    #testDeletePV()
    #testCreatePV()
    test_inject_sidecar()
    #test_get_pv_spec()
    

