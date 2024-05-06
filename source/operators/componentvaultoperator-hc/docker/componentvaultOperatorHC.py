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
#from setuptools.command.setopt import config_file
from kubernetes.client.models.v1_replica_set import V1ReplicaSet
from kubernetes.client.models.v1_deployment import V1Deployment

COMPVAULT_GROUP = "oda.tmforum.org"
COMPVAULT_VERSION = "v1beta3"
COMPVAULT_PLURAL = "componentvaults"

COMP_GROUP = "oda.tmforum.org"
COMP_VERSION = "v1beta3"
COMP_PLURAL = "components"

HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

# https://kopf.readthedocs.io/en/stable/install/

# Setup logging
logging_level = os.environ.get('LOGGING', logging.INFO)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.WARNING)
logger = logging.getLogger('ComponentvaultOperator')
logger.setLevel(int(logging_level))
logger.info(f'Logging set to %s', logging_level)
logger.debug(f'debug logging active')

CICD_BUILD_TIME = os.getenv('CICD_BUILD_TIME')
GIT_COMMIT_SHA = os.getenv('GIT_COMMIT_SHA')
if CICD_BUILD_TIME:
    logger.info(f'CICD_BUILD_TIME=%s', CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f'GIT_COMMIT_SHA=%s', GIT_COMMIT_SHA)

#vault_addr = os.getenv('VAULT_ADDR', 'https://canvas-vault-hc.k8s.feri.ai')
vault_addr = os.getenv('VAULT_ADDR', 'http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200')
auth_path = os.getenv('AUTH_PATH', 'jwt-k8s-cv')
policy_name_tpl = os.getenv('POLICY_NAME_TPL', 'cv-{0}-policy')
login_role_tpl = os.getenv('LOGIN_ROLE_TPL', 'cv-{0}-role')
secrets_mount_tpl = os.getenv('SECRETS_MOUNT_TPL', 'kv-{0}')
secrets_base_path_tpl = os.getenv('SECRETS_BASE_PATH_TPL', 'sidecar')

audience = os.getenv('AUDIENCE', "https://kubernetes.default.svc.cluster.local")

hvac_token_enc = os.getenv('HVAC_TOKEN_ENC', "gAAAAABmOIdWCC1fkWaHnThsR45vWw3H-4cCq925h8Jdund9lbtsGLXHs8NjcKQHwdx5Cpoq270S-cDaIEFl9vP7SNXnuoLHEA==")


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


def get_cv_spec(cv_name, cv_namespace):
    coa = kubernetes.client.CustomObjectsApi()
    try:
        cv_cr = coa.get_namespaced_custom_object(COMPVAULT_GROUP, COMPVAULT_VERSION, cv_namespace, COMPVAULT_PLURAL, cv_name)
        return cv_cr["spec"]
    except ApiException:
        return None



def has_container(pod, container_name):
    for container in pod.spec.containers:
        if container.name == container_name:
            return True
    return False 



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
    
    cv_name = get_comp_name(body)
    if not cv_name:
        logger.info(f"Component name in label {componentname_label} not set, doing nothing")
        return

    pod_name = safe_get(None, body, "metadata", "name")
    if not pod_name:
        pod_name = safe_get(None, body, "metadata", "generateName")
    pod_namespace = body["metadata"]["namespace"]
    pod_serviceAccountName = safe_get("default", body, "spec", "serviceAccountName")
    logger.info(f"POD serviceaccount:{pod_namespace}:{pod_name}:{pod_serviceAccountName}")

    
    # HIERWEITER deployment = find_deployment(pod_namespace, pod_name, pod-template-hash)
    
    cv_cr_name = f"{cv_name}"
    logger.debug(f"getting componentvault cr {cv_cr_name} from namespace {pod_namespace} k8s")
    cv_spec = get_cv_spec(cv_cr_name, pod_namespace)
    logger.debug(f"componentvault spec: {cv_spec}")
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
        logger.info("cvsidecar container already exists, doing nothing")
        return

    containers.append(container_cvsidecar)
    patch.spec["containers"] = containers
    logger.debug(f"injecting cvsidecar container")
    

    if not entryExists(vols, "name", "cvsidecar-tmp"):
        vols.append(volume_cvsidecar_tmp)
        patch.spec['volumes'] = vols
        logger.debug(f"injecting cvsidecar-tmp volume")

    if not entryExists(vols, "name", "cvsidecar-kube-api-access"):
        vols.append(volume_cvsidecar_kube_api_access)
        patch.spec['volumes'] = vols
        logger.debug(f"injecting cvsidecar-kube-api-access volume")




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
        logger.info(f"POD mutate called with body: {type(body)} -  {body}")
        inject_sidecar(body, patch)
        logger.info(f"POD mutate returns patch: {type(patch)} -  {patch}")
    
    except:
        logger.exception(f"ERRPR podmutate failed!")
        warnings.append("internal error, patch not applied")
        patch.clear()
    
    
@kopf.on.mutate('deployments', labels={"oda.tmforum.org/componentvault": "sidecar"}, operation='CREATE', ignore_failures=True)
def deploymentmutate(body, meta, spec, status, patch: kopf.Patch, warnings: list[str], **_):
    try:
        logger.info(f"DEPLOYMENT mutate called with body: {type(body)} -  {body}")
        label_deployment_pods(body, patch)
        logger.info(f"DEPLOYMENT mutate returns patch: {type(patch)} -  {patch}")
    
    except:
        logger.exception(f"ERRPR deploymentmutate failed!")
        warnings.append("internal error, patch not applied")
        patch.clear()
    
    



def decrypt(encrypted_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    return Fernet(base64.b64encode((auth_path*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


def setupComponentVault(cv_namespace:str, cv_name:str, pod_name:str, pod_namespace:str, pod_service_account:str):
    try:
        logger.info(f"SETUP COMPONENTVAULT cv_namespace={cv_namespace}, cv_name={cv_name}, pod={pod_name}, ns={pod_namespace}, sa={pod_service_account}")
        
        policy_name = policy_name_tpl.format(cv_name)
        login_role = login_role_tpl.format(cv_name)
        secrets_mount = secrets_mount_tpl.format(cv_name)
        secrets_base_path = secrets_base_path_tpl.format(cv_name)

        logger.info(f"policy_name: {policy_name}")
        logger.info(f"login_role: {login_role}")
        logger.info(f"secrets_mount: {secrets_mount}")
        logger.info(f"secrets_base_path: {secrets_base_path}")

        
        token = decrypt(hvac_token_enc)
        # Authentication
        client = hvac.Client(
            url=vault_addr,
            token=token,
        )
    
        ### enable KV v2 engine 
        # https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?highlight=mount#hvac.api.system_backend.Mount.enable_secrets_engine
        #
        logger.info(f"enabling KV v2 engine at {secrets_mount}")
        client.sys.enable_secrets_engine("kv", secrets_mount, options={"version":"2"})
        
        ### create policy
        # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
        #
        logger.info(f'create policy {policy_name}')
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
        logger.info(f'create role {login_role}')
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
        
        setComponentVaultReady(cv_namespace, cv_name)
    except Exception as e:
        logger.exception(f"ERRPR setup vault {cv_namespace}:{cv_name} failed!")
        raise kopf.TemporaryError(e)
    

def deleteComponentVault(cv_name:str):
    try:
        logger.info(f"DELETE COMPONENTVAULT cv_name={cv_name}")
        
        login_role = login_role_tpl.format(cv_name)
        policy_name = policy_name_tpl.format(cv_name)
        secrets_mount = secrets_mount_tpl.format(cv_name)
        
        logger.info(f"policy_name: {policy_name}")
        logger.info(f"login_role: {login_role}")
        logger.info(f"secrets_mount: {secrets_mount}")
        
        token = decrypt(hvac_token_enc)
        # Authentication
        client = hvac.Client(
            url=vault_addr,
            token=token,
        )
    except Exception as e:
        logger.exception(f"ERRPR delete vault {cv_name} failed!")
        raise kopf.TemporaryError(e) # allow the operator to retry
        
    
    ### disable KV secrets engine
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/mount.html?highlight=mount#disable-secrets-engine
    #
    logger.info(f"disabling KV engine {secrets_mount}")
    try:
        client.sys.disable_secrets_engine(secrets_mount)
    except Exception as e:
        logger.exception(f"ERRPR disable secrets {secrets_mount} failed!")
        raise kopf.TemporaryError(e) # allow the operator to retry
        
    
    ### delete role
    # https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#delete-role
    #
    logger.info(f'delete role {login_role}')
    client.auth.jwt.delete_role(
        name=login_role,
        path = auth_path,
    )

    ### delete policy
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#delete-policy
    #
    logger.info(f'delete policy {policy_name}')
    client.sys.delete_policy(name=policy_name)
   



def restart_pods_with_missing_sidecar(namespace, podsel_name, podsel_namespace, podsel_serviceaccount):
    label_selector = "oda.tmforum.org/componentvault=sidecar"
    logger.info(f'searching for PODs to restart in namespace {namespace} with label {label_selector}')
    v1 = kubernetes.client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace, label_selector=label_selector)
    for pod in pod_list.items:
        pod_namespace = pod.metadata.namespace
        pod_name = pod.metadata.name
        pod_serviceAccountName = pod.spec.service_account_name
        matches = True
        if podsel_name and not fnmatch.fnmatch(pod_name, podsel_name):
            logger.debug(f'name {pod_name} does not match {podsel_name}')
            matches = False      
        if podsel_namespace and not fnmatch.fnmatch(pod_namespace, podsel_namespace):
            logger.debug(f'namespace {pod_namespace} does not match {podsel_namespace}')
            matches = False      
        if podsel_serviceaccount and not fnmatch.fnmatch(pod_serviceAccountName, podsel_serviceaccount):
            logger.debug(f'serviceaccount {pod_serviceAccountName} does not match {podsel_serviceaccount}')
            matches = False      
        
        has_sidecar = has_container(pod, "cvsidecar")
        
        logger.info(f'INFO FOR POD {pod_namespace}:{pod_name}:{pod_serviceAccountName}, matches: {matches}, has sidecar: {has_sidecar}')
        if matches and not has_sidecar:
            logger.info(f'RESTARTING POD {pod_namespace}:{pod_name}')
            body = kubernetes.client.V1DeleteOptions()
            v1.delete_namespaced_pod(pod_name, pod_namespace, body=body) 


# when an oda.tmforum.org componentvault resource is created or updated, configure policy and role 
@kopf.on.create(COMPVAULT_GROUP, COMPVAULT_VERSION, COMPVAULT_PLURAL)
@kopf.on.update(COMPVAULT_GROUP, COMPVAULT_VERSION, COMPVAULT_PLURAL)
def componentvaultCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.info(f"Create/Update  called with body: {body}")
    logger.debug(f"componentvault  called with namespace: {namespace}")
    logger.debug(f"componentvault  called with name: {name}")
    logger.debug(f"componentvault  called with labels: {labels}")

    # do not use safe_get for mandatory fields
    cv_namespace = namespace
    cv_name = name   # spec['name']
    pod_name = safe_get(None, spec, 'podSelector', 'name')
    pod_namespace = safe_get(None, spec, 'podSelector', 'namespace')
    pod_service_account = safe_get(None, spec, 'podSelector', 'serviceaccount')
    
    setupComponentVault(cv_namespace, cv_name, pod_name, pod_namespace, pod_service_account)
    
    restart_pods_with_missing_sidecar(cv_namespace, pod_name, pod_namespace, pod_service_account)
    
 
# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete(COMPVAULT_GROUP, COMPVAULT_VERSION, COMPVAULT_PLURAL, retries=5)
def componentvaultDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.info(f"Create/Update  called with body: {body}")
    logger.info(f"Create/Update  called with namespace: {namespace}")
    logger.info(f"Create/Update  called with name: {name}")
    logger.info(f"Create/Update  called with labels: {labels}")
    
    cv_name = name    # spec['name']

    deleteComponentVault(cv_name)



def setComponentVaultReady(namespace, name):
    """Helper function to update the implementation Ready status on the ComponentVault custom resource.

    Args:
        * namespace (String): namespace of the ComponentVault custom resource
        * name (String): name of the ComponentVault custom resource

    Returns:
        No return value.
    """
    logger.info(f"setting implementation status to ready for dependent api {namespace}:{name}")
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        compvault = api_instance.get_namespaced_custom_object(
            COMPVAULT_GROUP, COMPVAULT_VERSION, namespace, COMPVAULT_PLURAL, name
        )
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logger.error(f"setComponentVaultReady: componentvault {namespace}:{name} not found")
            raise kopf.TemporaryError(f"setComponentVaultReady: componentvault {namespace}:{name} not found")
        else:
            raise kopf.TemporaryError(f"setComponentVaultReady: Exception in get_namespaced_custom_object: {e.body}")
    if not ("status" in compvault.keys()):
        compvault["status"] = {}
    compvault["status"]["implementation"] = {"ready": True}
    try:
        api_response = api_instance.patch_namespaced_custom_object(
            COMPVAULT_GROUP, COMPVAULT_VERSION, namespace, COMPVAULT_PLURAL, name, compvault
        )
    except ApiException as e:
        raise kopf.TemporaryError(f"setComponentVaultReady: Exception in patch_namespaced_custom_object: {e.body}")



@kopf.on.field(
    COMPVAULT_GROUP,
    COMPVAULT_VERSION,
    COMPVAULT_PLURAL,
    field="status.implementation",
    retries=5,
)
async def updateComponentVaultReady(
    meta, spec, status, body, namespace, labels, name, **kwargs
):
    """moved from componentOperator to here, to avoid inifite loops.
    If possible to configure kopf correctly it should be ported back to componentOperator

    Propagate status updates of the *implementation* status in the ComponentVault Custom resources to the Component status 

    Args:
        * meta (Dict): The metadata from the ComponentVault resource
        * spec (Dict): The spec from the yaml ComponentVault resource showing the intent (or desired state)
        * status (Dict): The status from the ComponentVault resource showing the actual state.
        * body (Dict): The entire ComponentVault resource definition
        * namespace (String): The namespace for the ComponentVault resource
        * labels (Dict): The labels attached to the ComponentVault resource. All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the ComponentVault resource

    Returns:
        No return value, nothing to write into the status.
    """
    logger.info(f"updateComponentVaultReady called for {namespace}:{name}")
    logger.debug(
        f"updateComponentVaultReady called for {namespace}:{name} with body {body}"
    )
    if "ready" in status["implementation"].keys():
        if status["implementation"]["ready"] == True:
            if "ownerReferences" in meta.keys():
                parent_component_name = meta["ownerReferences"][0]["name"]
                logger.info(f"reading component {parent_component_name}")
                try:
                    api_instance = kubernetes.client.CustomObjectsApi()
                    parent_component = api_instance.get_namespaced_custom_object(
                        COMP_GROUP,
                        COMP_VERSION,
                        namespace,
                        COMP_PLURAL,
                        parent_component_name,
                    )
                except ApiException as e:
                    # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
                    if e.status == HTTP_NOT_FOUND:
                        raise kopf.TemporaryError(
                            "Cannot find parent component " + parent_component_name
                        )
                    logger.error(e)
                    raise kopf.TemporaryError(
                        f"Exception when calling api_instance.get_namespaced_custom_object {parent_component_name}: {e.body}"
                    )
                # find the entry to update in securityComponentVault status
                cv_status =parent_component["status"]["securityComponentVault"]
                ready = cv_status["ready"]
                if ready != True:  # avoid recursion
                    logger.info(f"patching securityComponentVault in component {parent_component_name}")
                    cv_status["ready"] = True
                    try:
                        api_response = (
                            api_instance.patch_namespaced_custom_object(
                                COMP_GROUP,
                                COMP_VERSION,
                                namespace,
                                COMP_PLURAL,
                                parent_component_name,
                                parent_component,
                            )
                        )
                    except ApiException as e:
                        raise kopf.TemporaryError(
                            f"updateComponentVaultReady: Exception in patch_namespaced_custom_object: {e.body}"
                        )
