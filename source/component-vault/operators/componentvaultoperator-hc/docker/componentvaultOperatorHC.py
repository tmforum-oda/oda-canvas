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
from kubernetes.client.models.v1_replica_set import V1ReplicaSet
from kubernetes.client.models.v1_deployment import V1Deployment


# https://kopf.readthedocs.io/en/stable/install/

logger = logging.getLogger()
logger.setLevel(int(os.getenv('LOGGING', 10)))

#vault_addr = os.getenv('VAULT_ADDR', 'https://canvas-vault-hc.k8s.feri.ai')
vault_addr = os.getenv('VAULT_ADDR', 'http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200')
auth_path = os.getenv('AUTH_PATH', 'jwt-k8s-cv')
policy_name_tpl = os.getenv('POLICY_NAME_TPL', 'cv-{0}-policy')
login_role_tpl = os.getenv('LOGIN_ROLE_TPL', 'cv-{0}-role')
secrets_mount_tpl = os.getenv('SECRETS_MOUNT_TPL', 'kv-{0}')
secrets_base_path_tpl = os.getenv('SECRETS_BASE_PATH_TPL', 'sidecar')

audience = os.getenv('AUDIENCE', "https://kubernetes.default.svc.cluster.local")

webhook_service_name = os.getenv('WEBHOOK_SERVICE_NAME', 'dummyservicename') 
webhook_service_namespace = os.getenv('WEBHOOK_SERVICE_NAMESPACE', 'dummyservicenamespace') 
webhook_service_port = int(os.getenv('WEBHOOK_SERVICE_PORT', '443'))

componentname_label = os.getenv('COMPONENTNAME_LABEL', 'oda.tmforum.org/componentName')
componentvaulttype_label = os.getenv('COMPONENTVAULTTYPE_LABEL', "oda.tmforum.org/componentvault")


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
    settings.peering.priority = 200
    settings.peering.name = "componentvault"
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = 'cv.sidecar.kopf'
    settings.watching.server_timeout = 1 * 60


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



def test_kubeconfig():
    v1 = kubernetes.client.CoreV1Api()
    nameSpaceList = v1.list_namespace()
    for nameSpace in nameSpaceList.items:
        print(nameSpace.metadata.name)


def get_comp_name(body):
    
    cv_name = safe_get(None, body, "metadata", "labels", componentname_label)
    if cv_name:
        return cv_name
    namespace = safe_get(None, body, "metadata", "namespace")
    owners = safe_get(None, body, "metadata", "ownerReferences")
    if not owners:
        return
    for owner in owners:
        kind = safe_get(None, owner, "kind")
        if kind and kind == "ReplicaSet":
            rs_name = safe_get(None, owner, "name")
            rs_uid = safe_get(None, owner, "uid")
            aV1 = kubernetes.client.AppsV1Api()
            replica_set:V1ReplicaSet = aV1.read_namespaced_replica_set(rs_name, namespace)
            # print(replica_set)
            if replica_set.metadata.uid == rs_uid:
                rs_owners = replica_set.metadata.owner_references
                if rs_owners:
                    for rs_owner in rs_owners:
                        kind = rs_owner.kind
                        if kind and kind == "Deployment":
                            dep_name = rs_owner.name
                            dep_uid = rs_owner.uid
                            deployment:V1Deployment = aV1.read_namespaced_deployment(dep_name, namespace)
                            # print(deployment)
                            if deployment.metadata.uid == dep_uid:
                                labels = deployment.metadata.labels
                                # print(labels)
                                if labels and componentname_label in labels:
                                    cv_name = labels[componentname_label]
                                    return cv_name 
            

def inject_sidecar(body, patch):
    
    logging.debug(f"loading k8s config")
    k8s_load_config()

    cv_name = get_comp_name(body)
    if not cv_name:
        logging.info(f"Component name in label {componentname_label} not set, doing nothing")
        return

    pod_name = safe_get(None, body, "metadata", "name")
    if not pod_name:
        pod_name = safe_get(None, body, "metadata", "generateName")
    pod_namespace = body["metadata"]["namespace"]
    pod_serviceAccountName = safe_get("default", body, "spec", "serviceAccountName")
    logging.info(f"POD serviceaccount:{pod_namespace}:{pod_name}:{pod_serviceAccountName}")

    
    # HIERWEITER deployment = find_deployment(pod_namespace, pod_name, pod-template-hash)
    
    cv_cr_name = f"{cv_name}"
    logging.debug(f"getting componentvault cr {cv_cr_name} from namespace {pod_namespace} k8s")
    cv_spec = get_cv_spec(cv_cr_name, pod_namespace)
    logging.debug(f"componentvault spec: {cv_spec}")
    if not cv_spec:
        raise kopf.AdmissionError(f"componentvault {cv_cr_name} has no spec.", code=400)
    
    cvname = cv_cr_name # safe_get("", cv_spec, "name")
    type = safe_get("sideCar", cv_spec, "type")
    sidecar_port = int(safe_get("5000", cv_spec, "sideCar", "port"))
    podsel_name = safe_get("", cv_spec, "podSelector", "name")
    podsel_namespace = safe_get("", cv_spec, "podSelector", "namespace")
    podsel_serviceaccount = safe_get("", cv_spec, "podSelector", "serviceaccount")
    logger.debug(f"filter: name={podsel_name}, namespace={podsel_namespace}, serviceaccount={podsel_serviceaccount}")
    if not cvname:
        raise kopf.AdmissionError(f"componentvault {cv_cr_name}: missing name.", code=400)      
    if type != "sideCar":
        raise kopf.AdmissionError(f"componentvault {cv_cr_name}: unsupported type {type}.", code=400)
    if podsel_name and not fnmatch.fnmatch(pod_name, podsel_name):
        raise kopf.AdmissionError(f"componentvault {cv_cr_name}: pod name does not match selector.", code=400)      
    if podsel_namespace and not fnmatch.fnmatch(pod_namespace, podsel_namespace):
        raise kopf.AdmissionError(f"componentvault {cv_cr_name}: pod namespace does not match selector.", code=400)      
    if podsel_serviceaccount and not fnmatch.fnmatch(pod_serviceAccountName, podsel_serviceaccount):
        raise kopf.AdmissionError(f"componentvault {cv_cr_name}: pod serviceAccountName does not match selector.", code=400)      

    container_cvsidecar = {
            "name": "cvsidecar",
            "image": "mtr.devops.telekom.de/magenta_canvas/public:component-vault-sidecar-0.1.0-rc",
            "ports": [
                {
                    "containerPort": sidecar_port,
                    "protocol": "TCP"
                }
            ],
            "env": [
                {
                    "name": "COMPONENTVAULT_NAME",
                    "value": f"{cvname}"
                },
                {
                    "name": "VAULT_ADDR",
                    "value": vault_addr
                },
                {
                    "name": "AUTH_PATH",
                    "value": auth_path
                },
                {
                    "name": "LOGIN_ROLE",
                    "value": f"cv-{cvname}-role"
                },
                {
                    "name": "SCRETS_MOUNT",
                    "value": f"kv-{cvname}"
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
                    "name": "cvsidecar-tmp",
                    "mountPath": "/tmp"
                },
                {
                    "name": "cvsidecar-kube-api-access",
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
            
    volume_cvsidecar_tmp = {
            "name": "cvsidecar-tmp",
            "emptyDir": {}
        }

    volume_cvsidecar_kube_api_access = {
            "name": "cvsidecar-kube-api-access",
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

    if entryExists(containers, "name", "cvsidecar"):
        logging.info("cvsidecar container already exists, doing nothing")
        return

    containers.append(container_cvsidecar)
    patch.spec["containers"] = containers
    logging.debug(f"injecting cvsidecar container")
    

    if not entryExists(vols, "name", "cvsidecar-tmp"):
        vols.append(volume_cvsidecar_tmp)
        patch.spec['volumes'] = vols
        logging.debug(f"injecting cvsidecar-tmp volume")

    if not entryExists(vols, "name", "cvsidecar-kube-api-access"):
        vols.append(volume_cvsidecar_kube_api_access)
        patch.spec['volumes'] = vols
        logging.debug(f"injecting cvsidecar-kube-api-access volume")




def label_deployment_pods(body, patch):
    
    labels = safe_get(None, body, 'metadata', 'labels')
    if labels and componentname_label in labels:
        component_name = labels[componentname_label]
        cv_type = safe_get("sidecar", labels, componentvaulttype_label)
        logger.info(f"COMPONENTNAME: {component_name}")

        labels = safe_get({}, body, "spec", "template", "metadata", "labels")
        if not componentname_label in labels:
           labels[componentname_label] = component_name
           
        if not componentvaulttype_label in labels:
           labels[componentvaulttype_label] = cv_type

        patch.spec["template"] = {"metadata": {"labels": labels}}



    

@kopf.on.mutate('pods', labels={"oda.tmforum.org/componentvault": "sidecar"}, operation='CREATE', ignore_failures=True)
def podmutate(body, meta, spec, status, patch: kopf.Patch, warnings: list[str], **_):
    try:
        logging.info(f"POD mutate called with body: {type(body)} -  {body}")
        inject_sidecar(body, patch)
        logging.info(f"POD mutate returns patch: {type(patch)} -  {patch}")
    
    except:
        logging.exception(f"ERRPR podmutate failed!")
        warnings.append("internal error, patch not applied")
        patch.clear()
    
    
@kopf.on.mutate('deployments', labels={"oda.tmforum.org/componentvault": "sidecar"}, operation='CREATE', ignore_failures=True)
def deploymentmutate(body, meta, spec, status, patch: kopf.Patch, warnings: list[str], **_):
    try:
        logging.info(f"DEPLOYMENT mutate called with body: {type(body)} -  {body}")
        label_deployment_pods(body, patch)
        logging.info(f"DEPLOYMENT mutate returns patch: {type(patch)} -  {patch}")
    
    except:
        logging.exception(f"ERRPR deploymentmutate failed!")
        warnings.append("internal error, patch not applied")
        patch.clear()
    
    



def decrypt(encrypted_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


def setupComponentVault(cv_name:str, pod_name:str, pod_namespace:str, pod_service_account:str):
    try:
        logging.info(f"SETUP COMPONENTVAULT cv_name={cv_name}, pod={pod_name}, ns={pod_namespace}, sa={pod_service_account}")
        
        policy_name = policy_name_tpl.format(cv_name)
        login_role = login_role_tpl.format(cv_name)
        secrets_mount = secrets_mount_tpl.format(cv_name)
        secrets_base_path = secrets_base_path_tpl.format(cv_name)

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
          capabilities = ["create", "read", "update", "delete", "patch"]   # do not support "list" for security reasons   
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

        
        bound_claims = {}
        if pod_name:
            bound_claims["/kubernetes.io/pod/name"] = pod_name;
        if pod_namespace:
            bound_claims["/kubernetes.io/namespace"] = pod_namespace;
        if pod_service_account:
            bound_claims["/kubernetes.io/serviceaccount/name"] = pod_service_account;
        
        client.auth.jwt.create_role(
            name=login_role,
            role_type='jwt',
            bound_audiences=[audience],
            user_claim='sub',
            #user_claim='/kubernetes.io/pod/uid',  # not yet supported, see PR #998
            #user_claim_json_pointer=True,         # https://github.com/hvac/hvac/pull/998
            bound_claims_type = "glob",
            bound_claims = bound_claims,
            token_policies=[policy_name],
            token_ttl=3600,
            allowed_redirect_uris=allowed_redirect_uris,  # why mandatory? 
            path = auth_path,

        )
    except:
        logging.exception(f"ERRPR setup vault {cv_name} failed!")
    

def deleteComponentVault(cv_name:str):
    try:
        logging.info(f"DELETE COMPONENTVAULT cv_name={cv_name}")
        
        login_role = login_role_tpl.format(cv_name)
        policy_name = policy_name_tpl.format(cv_name)
        secrets_mount = secrets_mount_tpl.format(cv_name)
        
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
        logging.exception(f"ERRPR delete vault {cv_name} failed!")
        
    
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
   


# when an oda.tmforum.org componentvault resource is created or updated, configure policy and role 
@kopf.on.create('oda.tmforum.org', 'v1alpha1', 'componentvaults')
@kopf.on.update('oda.tmforum.org', 'v1alpha1', 'componentvaults')
def componentvaultCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with body: {body}")
    logging.debug(f"componentvault  called with namespace: {namespace}")
    logging.debug(f"componentvault  called with name: {name}")
    logging.debug(f"componentvault  called with labels: {labels}")

    # do not use safe_get for mandatory fields
    cv_name = name   # spec['name']
    pod_name = safe_get(None, spec, 'podSelector', 'name')
    pod_namespace = safe_get(None, spec, 'podSelector', 'namespace')
    pod_service_account = safe_get(None, spec, 'podSelector', 'serviceAccount')
    
    setupComponentVault(cv_name, pod_name, pod_namespace, pod_service_account)
    
 
# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete('oda.tmforum.org', 'v1alpha1', 'componentvaults', retries=5)
def componentvaultDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info(f"Create/Update  called with body: {body}")
    logging.info(f"Create/Update  called with namespace: {namespace}")
    logging.info(f"Create/Update  called with name: {name}")
    logging.info(f"Create/Update  called with labels: {labels}")
    
    cv_name = name    # spec['name']

    deleteComponentVault(cv_name)



def set_proxy():
    os.environ["HTTP_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["HTTPS_PROXY"]="http://specialinternetaccess-lb.telekom.de:8080"
    os.environ["NO_PROXY"]="10.0.0.0/8,.eks.amazonaws.com,.aws.telekom.de,caas-portal-test.telekom.de,caas-portal.telekom.de,.caas-t02.telekom.de"

def testCreateCV():
    #set_proxy()
    dummy = {}
    spec = {
        'name': 'demoa-comp-one',
        'type': 'sideCar',        
        'sideCar': {
            'port': 5000,
            'token': 'negotiate'
        },
        'podSelector': {
            'namespace': 'demo-comp',
            'name': 'demoa-comp-one-*',
            'serviceAccount': 'default'
        }
    }
    componentvaultCreate(dummy, spec, dummy, dummy, "demoa-comp-one", dummy, "componentvault-demoa-comp-one")

def testDeleteCV():
    #set_proxy()
    dummy = {}
    spec = {
        'name': 'demoa-comp-one',
        'type': 'sideCar',        
        'sideCar': {
            'port': 5000,
            'token': 'negotiate'
        },
        'podSelector': {
            'namespace': 'demo-comp',
            'name': 'demoa-comp-one-*',
            'serviceAccount': 'default'
        }
    }
    componentvaultDelete(dummy, spec, dummy, dummy, "demoa-comp-one", dummy, "componentvault-demoa-comp-one")


def test_inject_sidecar():
    # body_json_file = 'test/pod/mutate/mutate-body.json'
    body_json_file = 'test/pod/mutate/create-demo-comp-one-pod-body.json'
    with open (body_json_file, 'r') as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = body["status"]
    patch = kopf.Patch({})
    warnings = []
    podmutate(body, meta, spec, status, patch, warnings)


def test_label_deployment_pods():
    # body_json_file = 'test/pod/mutate/mutate-body.json'
    body_json_file = 'test/deployment/create/demoa-deployment-create.json'
    with open (body_json_file, 'r') as f:
        body = json.load(f)
    meta = body["metadata"]
    spec = body["spec"]
    status = body["status"]
    patch = kopf.Patch({})
    warnings = []
    deploymentmutate(body, meta, spec, status, patch, warnings)



def k8s_load_config():
    if kubernetes.client.Configuration._default:
        return
    try:
        kubernetes.config.load_incluster_config()
        print("loaded incluster config")
    except kubernetes.config.ConfigException:
        try:
            kube_config_file = "~/.kube/config-vps5"
            proxy = "http://specialinternetaccess-lb.telekom.de:8080"
            kubernetes.config.load_kube_config(config_file = kube_config_file)
            kubernetes.client.Configuration._default.proxy = proxy 
            print("loaded config "+kube_config_file+" with proxy "+proxy)
        except kubernetes.config.ConfigException:
            try:
                kubernetes.config.load_kube_config()
                print("loaded default config")
            except kubernetes.config.ConfigException:
                raise Exception("Could not configure kubernetes python client")
    



def get_cv_spec(cv_name, cv_namespace):
    coa = kubernetes.client.CustomObjectsApi()
    try:
        cv_cr = coa.get_namespaced_custom_object("oda.tmforum.org", "v1alpha1", cv_namespace, "componentvaults", cv_name)
        return cv_cr["spec"]
    except ApiException:
        return None


def test_get_cv_spec():
    k8s_load_config()
    cv_spec = get_cv_spec("componentvault-demo-comp-123", "components")
    print(cv_spec)
    name = safe_get("", cv_spec, "name")
    podsel_name = safe_get("", cv_spec, "podSelector", "name")
    podsel_namespace = safe_get("", cv_spec, "podSelector", "namespace")
    podsel_serviceaccount = safe_get("", cv_spec, "podSelector", "serviceaccount")
    sidecar_port = int(safe_get("5000", cv_spec, "sideCar", "port"))
    type = safe_get("sideCar", cv_spec, "type")
    print(f"CV name: {name}")
    print(f"CV podsel_name: {podsel_name}")
    print(f"CV podsel_namespace: {podsel_namespace}")
    print(f"CV podsel_serviceaccount: {podsel_serviceaccount}")
    print(f"CV sidecar_port: {sidecar_port}")
    print(f"CV type: {type}")

    if not fnmatch.fnmatch("demo-comp-1234fedc-zyxw7756", podsel_name):
        raise kopf.AdmissionError(f"pod name does not match selector.", code=400)

if __name__ == '__main__':
    logging.info(f"main called")
    #set_proxy()
    #k8s_load_config()
    #test_kubeconfig()
    #testDeleteCV()
    #testCreateCV()
    test_inject_sidecar()
    #test_get_cv_spec()
    #test_label_deployment_pods()
    

