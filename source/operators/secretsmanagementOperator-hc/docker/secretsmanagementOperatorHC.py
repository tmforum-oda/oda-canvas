import kopf
import hvac
import logging
import os
import fnmatch
from cryptography.fernet import Fernet
import base64
import kubernetes
from kubernetes.client.rest import ApiException
from typing import AsyncIterator
from kubernetes.client.models.v1_replica_set import V1ReplicaSet
from kubernetes.client.models.v1_deployment import V1Deployment
from hvac.exceptions import InvalidPath
import asyncio

from log_wrapper import LogWrapper, logwrapper

SMAN_GROUP = "oda.tmforum.org"
SMAN_VERSION = "v1beta4"
SMAN_PLURAL = "secretsmanagements"

COMP_GROUP = "oda.tmforum.org"
COMP_VERSION = "v1beta4"
COMP_PLURAL = "components"

HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

# https://kopf.readthedocs.io/en/stable/install/

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
logger = logging.getLogger("SManOP")
logger.setLevel(int(logging_level))
logger.info("Logging set to %s", logging_level)
logger.debug("debug logging active")

LogWrapper.set_defaultLogger(logger)

SOURCE_DATE_EPOCH = os.getenv("SOURCE_DATE_EPOCH")
GIT_COMMIT_SHA = os.getenv("GIT_COMMIT_SHA")
CICD_BUILD_TIME = os.getenv("CICD_BUILD_TIME")
if SOURCE_DATE_EPOCH:
    logger.info("SOURCE_DATE_EPOCH=%s", SOURCE_DATE_EPOCH)
if GIT_COMMIT_SHA:
    logger.info("GIT_COMMIT_SHA=%s", GIT_COMMIT_SHA)
if CICD_BUILD_TIME:
    logger.info("CICD_BUILD_TIME=%s", CICD_BUILD_TIME)


vault_addr = os.getenv(
    "VAULT_ADDR", "https://canvas-vault-hc.canvas-vault.svc.cluster.local:8200"
)

vault_skip_verify = bool(os.getenv("VAULT_SKIP_VERIFY", "true"))

if vault_skip_verify:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


auth_path = os.getenv("AUTH_PATH", "jwt-k8s-sman")
policy_name_tpl = os.getenv("POLICY_NAME_TPL", "sman-{0}-policy")
login_role_tpl = os.getenv("LOGIN_ROLE_TPL", "sman-{0}-role")
secrets_mount_tpl = os.getenv("SECRETS_MOUNT_TPL", "kv-{0}")
secrets_base_path_tpl = os.getenv("SECRETS_BASE_PATH_TPL", "sidecar")

audience = os.getenv("AUDIENCE", "https://kubernetes.default.svc.cluster.local")

hvac_token = os.getenv(
    "HVAC_TOKEN",
    None,
)

hvac_token_enc = os.getenv(
    "HVAC_TOKEN_ENC",
    None,
)

sidecar_image = os.getenv(
    "SIDECAR_IMAGE", "tmforumodacanvas/secretsmanagement-sidecar:0.1.0"
)

webhook_service_name = os.getenv("WEBHOOK_SERVICE_NAME", "dummyservicename")
webhook_service_namespace = os.getenv(
    "WEBHOOK_SERVICE_NAMESPACE", "dummyservicenamespace"
)
webhook_service_port = int(os.getenv("WEBHOOK_SERVICE_PORT", "443"))

componentname_label = os.getenv("COMPONENTNAME_LABEL", "oda.tmforum.org/componentName")
secretsmanagementtype_label = os.getenv(
    "SECRETSMANAGEMENTTYPE_LABEL", "oda.tmforum.org/secretsmanagement"
)


# Inheritance: https://github.com/nolar/kopf/blob/main/docs/admission.rst#custom-serverstunnels
# https://github.com/nolar/kopf/issues/785#issuecomment-859931945


class ServiceTunnel:
    async def __call__(
        self, fn: kopf.WebhookFn
    ) -> AsyncIterator[kopf.WebhookClientConfig]:
        container_port = 9443
        server = kopf.WebhookServer(
            port=container_port,
            host=f"{webhook_service_name}.{webhook_service_namespace}.svc",
        )
        async for client_config in server(fn):
            client_config["url"] = None
            client_config["service"] = kopf.WebhookClientConfigService(
                name=webhook_service_name,
                namespace=webhook_service_namespace,
                port=webhook_service_port,
            )
            yield client_config


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.peering.priority = 200
    settings.peering.name = "secretsmanagement"
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = "sman.sidecar.kopf"
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


def get_sman_spec(sman_name, sman_namespace):
    coa = kubernetes.client.CustomObjectsApi()
    try:
        sman_cr = coa.get_namespaced_custom_object(
            SMAN_GROUP, SMAN_VERSION, sman_namespace, SMAN_PLURAL, sman_name
        )
        return sman_cr["spec"]
    except ApiException:
        return None


def has_container(pod, container_name):
    for container in pod.spec.containers:
        if container.name == container_name:
            return True
    return False


def implementationReady(smanBody):
    return safe_get(None, smanBody, "status", "implementation", "ready")


def toCIID(sman_namespace: str, sman_name: str):
    return f"{sman_namespace}-{sman_name}"


def quick_get_comp_name(body):
    return safe_get(None, body, "metadata", "labels", componentname_label)


def get_comp_name(body):
    sman_name = quick_get_comp_name(body)
    if sman_name:
        return sman_name
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
            replica_set: V1ReplicaSet = aV1.read_namespaced_replica_set(
                rs_name, namespace
            )
            # print(replica_set)
            if replica_set.metadata.uid == rs_uid:
                rs_owners = replica_set.metadata.owner_references
                if rs_owners:
                    for rs_owner in rs_owners:
                        kind = rs_owner.kind
                        if kind and kind == "Deployment":
                            dep_name = rs_owner.name
                            dep_uid = rs_owner.uid
                            deployment: V1Deployment = aV1.read_namespaced_deployment(
                                dep_name, namespace
                            )
                            # print(deployment)
                            if deployment.metadata.uid == dep_uid:
                                labels = deployment.metadata.labels
                                # print(labels)
                                if labels and componentname_label in labels:
                                    sman_name = labels[componentname_label]
                                    return sman_name


def get_pod_name(body):
    pod_name = safe_get(None, body, "metadata", "name")
    if not pod_name:
        pod_name = safe_get(None, body, "metadata", "generateName")
    return pod_name


def get_deployment_name(body):
    return safe_get(None, body, "metadata", "name")


@logwrapper
def inject_sidecar(logw: LogWrapper, body, patch):

    sman_name = get_comp_name(body)
    logw.set(component_name=sman_name)
    if not sman_name:
        logw.info(
            "Component name label not found, doing nothing",
            componentname_label,
        )
        return
    pod_name = get_pod_name(body)
    logw.set(resource_name=f"POD/{pod_name}")
    pod_namespace = body["metadata"]["namespace"]
    pod_serviceAccountName = safe_get("default", body, "spec", "serviceAccountName")
    logw.info(
        "POD serviceaccount", f"{pod_namespace}:{pod_name}:{pod_serviceAccountName}"
    )

    # HIERWEITER deployment = find_deployment(pod_namespace, pod_name, pod-template-hash)

    # TODO: not really correct to use pod_namespace, if POD runs in a different namespace then the sman cr.
    ciid = toCIID(pod_namespace, sman_name)

    sman_cr_name = f"{sman_name}"
    logw.debug("getting secretsmanagement cr", f"{pod_namespace}:{sman_cr_name}")
    sman_spec = get_sman_spec(sman_cr_name, pod_namespace)
    logw.debug("secretsmanagement spec", sman_spec)
    if not sman_spec:
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name} has no spec.", code=400
        )

    smanname = sman_cr_name  # safe_get("", sman_spec, "name")
    s_type = safe_get("sideCar", sman_spec, "type")
    sidecar_port = int(safe_get("5000", sman_spec, "sideCar", "port"))
    podsel_name = safe_get("", sman_spec, "podSelector", "name")
    podsel_namespace = safe_get("", sman_spec, "podSelector", "namespace")
    podsel_serviceaccount = safe_get("", sman_spec, "podSelector", "serviceaccount")
    logw.debug(
        "pod-filter",
        f"name={podsel_name}, namespace={podsel_namespace}, serviceaccount={podsel_serviceaccount}",
    )
    if not smanname:
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name}: missing name.", code=400
        )
    if s_type != "sideCar":
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name}: unsupported type {s_type}.", code=400
        )
    if podsel_name and not fnmatch.fnmatch(pod_name, podsel_name):
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name}: pod name does not match selector.",
            code=400,
        )
    if podsel_namespace and not fnmatch.fnmatch(pod_namespace, podsel_namespace):
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name}: pod namespace does not match selector.",
            code=400,
        )
    if podsel_serviceaccount and not fnmatch.fnmatch(
        pod_serviceAccountName, podsel_serviceaccount
    ):
        raise kopf.AdmissionError(
            f"secretsmanagement {sman_cr_name}: pod serviceAccountName does not match selector.",
            code=400,
        )

    container_smansidecar = {
        "name": "smansidecar",
        "image": sidecar_image,
        "ports": [{"containerPort": sidecar_port, "protocol": "TCP"}],
        "env": [
            {"name": "SECRETSMANAGEMENT_NAME", "value": f"{ciid}"},
            {"name": "VAULT_ADDR", "value": vault_addr},
            {"name": "VAULT_SKIP_VERIFY", "value": str(vault_skip_verify)},
            {"name": "AUTH_PATH", "value": auth_path},
            {"name": "LOGIN_ROLE", "value": login_role_tpl.format(ciid)},
            {"name": "SCRETS_MOUNT", "value": secrets_mount_tpl.format(ciid)},
            {"name": "SCRETS_BASE_PATH", "value": secrets_base_path_tpl.format(ciid)},
        ],
        "resources": {},
        "volumeMounts": [
            {"name": "smansidecar-tmp", "mountPath": "/tmp"},
            {
                "name": "smansidecar-kube-api-access",
                "readOnly": True,
                "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount",
            },
        ],
        "terminationMessagePath": "/dev/termination-log",
        "terminationMessagePolicy": "File",
        "imagePullPolicy": "Always",
        "securityContext": {
            "capabilities": {"drop": ["ALL"]},
            "privileged": False,
            "readOnlyRootFilesystem": True,
            "allowPrivilegeEscalation": False,
        },
    }

    volume_smansidecar_tmp = {"name": "smansidecar-tmp", "emptyDir": {}}

    volume_smansidecar_kube_api_access = {
        "name": "smansidecar-kube-api-access",
        "projected": {
            "sources": [
                {"serviceAccountToken": {"expirationSeconds": 3607, "path": "token"}},
                {
                    "configMap": {
                        "name": "kube-root-ca.crt",
                        "items": [{"key": "ca.crt", "path": "ca.crt"}],
                    }
                },
                {
                    "downwardAPI": {
                        "items": [
                            {
                                "path": "namespace",
                                "fieldRef": {
                                    "apiVersion": "v1",
                                    "fieldPath": "metadata.namespace",
                                },
                            },
                            {
                                "path": "name",
                                "fieldRef": {
                                    "apiVersion": "v1",
                                    "fieldPath": "metadata.name",
                                },
                            },
                        ]
                    }
                },
            ],
            "defaultMode": 420,
        },
    }

    containers = safe_get([], body, "spec", "containers")
    vols = safe_get([], body, "spec", "volumes")

    if entryExists(containers, "name", "smansidecar"):
        logw.info("smansidecar container already exists, doing nothing")
        return

    containers.append(container_smansidecar)
    patch.spec["containers"] = containers
    logw.debug("injecting smansidecar container")

    if not entryExists(vols, "name", "smansidecar-tmp"):
        vols.append(volume_smansidecar_tmp)
        patch.spec["volumes"] = vols
        logw.debug("injecting smansidecar-tmp volume")

    if not entryExists(vols, "name", "smansidecar-kube-api-access"):
        vols.append(volume_smansidecar_kube_api_access)
        patch.spec["volumes"] = vols
        logw.debug("injecting smansidecar-kube-api-access volume")


@logwrapper
def label_deployment_pods(logw: LogWrapper, body, patch):

    labels = safe_get(None, body, "metadata", "labels")
    if labels and componentname_label in labels:
        component_name = labels[componentname_label]
        logw.set(component_name=component_name)
        sman_type = safe_get("sidecar", labels, secretsmanagementtype_label)
        logw.info("COMPONENTNAME", component_name)

        labels = safe_get({}, body, "spec", "template", "metadata", "labels")
        if componentname_label not in labels:
            labels[componentname_label] = component_name

        if secretsmanagementtype_label not in labels:
            labels[secretsmanagementtype_label] = sman_type

        patch.spec["template"] = {"metadata": {"labels": labels}}


@kopf.on.mutate(
    "pods",
    labels={"oda.tmforum.org/secretsmanagement": "sidecar"},
    operation="CREATE",
    ignore_failures=True,
)
async def podmutate(
    body,
    meta,
    spec,
    status,
    patch: kopf.Patch,
    warnings: list[str],
    **_,
):
    logw = LogWrapper(handler_name="podmutate", function_name="podmutate")
    try:
        logw.set(
            component_name=quick_get_comp_name(body),
            resource_name=f"POD/{get_pod_name(body)}"
        )
        logw.debugInfo("POD mutate called", body)
        inject_sidecar(logw, body, patch)
        logw.debugInfo(f"POD mutate returns patch (size {len(str(patch))})", patch)

    except Exception as e:
        logw.exception("Unhandled exception", e)
        warnings.append("internal error, patch not applied")
        patch.clear()


@kopf.on.mutate(
    "deployments",
    labels={"oda.tmforum.org/secretsmanagement": "sidecar"},
    operation="CREATE",
    ignore_failures=True,
)
async def deploymentmutate(
    body,
    meta,
    spec,
    status,
    patch: kopf.Patch,
    warnings: list[str],
    logw: LogWrapper = None,
    **_,
):
    logw = LogWrapper(handler_name="deploymentmutate", function_name="deploymentmutate")
    try:
        logw.set(
            component_name=quick_get_comp_name(body),
            resource_name=f"Deployment/{get_deployment_name(body)}",
        )
        logw.debugInfo("DEPLOYMENT mutate called with body", body)
        label_deployment_pods(logw, body, patch)
        logw.debugInfo(
            f"DEPLOYMENT mutate returns patch (size {len(str((patch)))}", patch
        )

    except Exception as ex:
        logw.exception("deploymentmutate failed", ex)
        warnings.append("internal error, patch not applied")
        patch.clear()


def decrypt(encrypted_text):
    return (
        Fernet(base64.b64encode((auth_path * 32)[:32].encode("ascii")).decode("ascii"))
        .decrypt(encrypted_text.encode("ascii"))
        .decode("ascii")
    )


def encrypt(plain_text):
    return (
        Fernet(base64.b64encode((auth_path * 32)[:32].encode("ascii")).decode("ascii"))
        .encrypt(plain_text.encode("ascii"))
        .decode("ascii")
    )


if hvac_token:
    hvac_token_enc = encrypt(hvac_token)
    logger.warn(
        f"Environment variable HVAC_TOKEN given as plaintext. Please remove HVAC_TOKEN variable and use HVAC_TOKEN_ENC: {hvac_token_enc}"
    )
if not hvac_token_enc:
    logger.error("Missing environment variable HVAC_TOKEN for HashiCorp Vault token!")
    raise ValueError(
        "Missing environment variable HVAC_TOKEN for HashiCorp Vault token!"
    )
# check encrypted token
decrypt(hvac_token_enc)


@logwrapper
def setupSecretsManagement(
    logw: LogWrapper,
    sman_namespace: str,
    sman_name: str,
    pod_name: str,
    pod_namespace: str,
    pod_service_account: str,
):
    try:
        logw.info(
            "SETUP SECRETSMANAGEMENT",
            f"sman_namespace={sman_namespace}, sman_name={sman_name}, pod={pod_name}, ns={pod_namespace}, sa={pod_service_account}",
        )

        ciid = toCIID(sman_namespace, sman_name)
        policy_name = policy_name_tpl.format(ciid)
        login_role = login_role_tpl.format(ciid)
        secrets_mount = secrets_mount_tpl.format(ciid)
        secrets_base_path = secrets_base_path_tpl.format(ciid)

        logw.info("policy_name", policy_name)
        logw.info("login_role", login_role)
        logw.info("secrets_mount", secrets_mount)
        logw.info("secrets_base_path", secrets_base_path)

        token = decrypt(hvac_token_enc)
        # Authentication
        client = hvac.Client(
            url=vault_addr,
            verify=not vault_skip_verify,
            token=token,
            strict_http=True,  # workaround BadRequest for LIST method (https://github.com/hvac/hvac/issues/773)
        )

        # == enable KV v2 engine
        # https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?highlight=mount#hvac.api.system_backend.Mount.enable_secrets_engine
        #
        logw.info("enabling KV v2 engine", secrets_mount)
        existing_secret_engines = client.sys.list_mounted_secrets_engines()
        if f"{secrets_mount}/" in existing_secret_engines:
            # == TODO[FH]: additional security checks to ensure no orphane vault is reused
            logw.info("  KV v2 engine already exists", secrets_mount)
        else:
            client.sys.enable_secrets_engine(
                "kv",
                secrets_mount,
                options={
                    "version": "2",
                    "description": f"ODA SecretsManagement for {sman_namespace}:{sman_name}",
                },
            )

        # == create policy
        # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
        #
        logw.info("create policy", policy_name)
        policy = f"""
        path "{secrets_mount}/data/{secrets_base_path}/*" {{
          capabilities = ["create", "read", "update", "delete", "patch"]   # do not support "list" for security reasons
        }}
        """

        policies = client.sys.list_policies()["data"]["policies"]
        if policy_name in policies:
            logw.info("  policy already exists", policy_name)
            # == TODO[FH] read policy and check for changes
        else:
            client.sys.create_or_update_policy(
                name=policy_name,
                policy=policy,
            )

        # == create role
        # https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#create-role
        #
        logw.info("create role", login_role)
        allowed_redirect_uris = [f"{vault_addr}/jwt-test/callback"]  # ?

        bound_claims = {}
        if pod_name:
            bound_claims["/kubernetes.io/pod/name"] = pod_name
        if pod_namespace:
            bound_claims["/kubernetes.io/namespace"] = pod_namespace
        if pod_service_account:
            bound_claims["/kubernetes.io/serviceaccount/name"] = pod_service_account

        try:
            role_names = client.auth.jwt.list_roles(path=auth_path)["data"]["keys"]
        except InvalidPath:
            role_names = []
        if login_role in role_names:
            # == TODO[FH]: read role using
            # == client.auth.jwt.read_role(name=login_role, path=auth_path)
            # == and check for changes
            logw.info("  role already exists", login_role)
        else:
            client.auth.jwt.create_role(
                name=login_role,
                role_type="jwt",
                bound_audiences=[audience],
                user_claim="sub",
                # user_claim='/kubernetes.io/pod/uid',  # not yet supported, see PR #998
                # user_claim_json_pointer=True,         # https://github.com/hvac/hvac/pull/998
                bound_claims_type="glob",
                bound_claims=bound_claims,
                token_policies=[policy_name],
                token_ttl=3600,
                allowed_redirect_uris=allowed_redirect_uris,  # why mandatory?
                path=auth_path,
            )

    except Exception as e:
        logw.exception("ERROR setup vault {sman_name}.{sman_namespace} failed!", e)
        raise kopf.TemporaryError(e)


@logwrapper
def deleteSecretsManagement(logw: LogWrapper, sman_namespace: str, sman_name: str):
    try:
        logw.info("DELETE SECRETSMANAGEMENT", f"{sman_namespace}:{sman_name}")

        ciid = toCIID(sman_namespace, sman_name)
        policy_name = policy_name_tpl.format(ciid)
        login_role = login_role_tpl.format(ciid)
        secrets_mount = secrets_mount_tpl.format(ciid)

        logw.info("policy_name", policy_name)
        logw.info("login_role", login_role)
        logw.info("secrets_mount", secrets_mount)

        token = decrypt(hvac_token_enc)
        # Authentication
        client = hvac.Client(
            url=vault_addr,
            verify=not vault_skip_verify,
            token=token,
        )
    except Exception as e:
        logw.exception(f"ERRPR delete vault {sman_name} failed!", e)
        raise kopf.TemporaryError(e)  # allow the operator to retry

    # == disable KV secrets engine
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/mount.html?highlight=mount#disable-secrets-engine
    #
    logw.info("disabling KV engine", secrets_mount)
    try:
        client.sys.disable_secrets_engine(secrets_mount)
    except Exception as e:
        logw.exception(f"ERRPR disable secrets {secrets_mount} failed!", e)
        raise kopf.TemporaryError(e)  # allow the operator to retry

    # == delete role
    # https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#delete-role
    #
    logw.info("delete role", login_role)
    client.auth.jwt.delete_role(
        name=login_role,
        path=auth_path,
    )

    # == delete policy
    # https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#delete-policy
    #
    logw.info("delete policy", policy_name)
    client.sys.delete_policy(name=policy_name)


@logwrapper
def restart_pods_with_missing_sidecar(
    logw: LogWrapper, namespace, podsel_name, podsel_namespace, podsel_serviceaccount
):
    label_selector = "oda.tmforum.org/secretsmanagement=sidecar"
    logw.info(
        f"searching for PODs to restart in namespace {namespace} with label {label_selector}"
    )
    v1 = kubernetes.client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace, label_selector=label_selector)
    for pod in pod_list.items:
        pod_namespace = pod.metadata.namespace
        pod_name = pod.metadata.name
        pod_serviceAccountName = pod.spec.service_account_name
        matches = True
        if podsel_name and not fnmatch.fnmatch(pod_name, podsel_name):
            logw.debug(f"name {pod_name} does not match {podsel_name}")
            matches = False
        if podsel_namespace and not fnmatch.fnmatch(pod_namespace, podsel_namespace):
            logw.debug(f"namespace {pod_namespace} does not match {podsel_namespace}")
            matches = False
        if podsel_serviceaccount and not fnmatch.fnmatch(
            pod_serviceAccountName, podsel_serviceaccount
        ):
            logw.debug(
                f"serviceaccount {pod_serviceAccountName} does not match {podsel_serviceaccount}"
            )
            matches = False

        has_sidecar = has_container(pod, "smansidecar")

        logw.info(
            "INFO FOR POD",
            f"{pod_namespace}:{pod_name}:{pod_serviceAccountName}, matches: {matches}, has sidecar: {has_sidecar}",
        )
        if matches and not has_sidecar:
            logw.info("RESTARTING POD", f"{pod_namespace}:{pod_name}")
            body = kubernetes.client.V1DeleteOptions()
            v1.delete_namespaced_pod(pod_name, pod_namespace, body=body)


# when an oda.tmforum.org secretsmanagement resource is created or updated, configure policy and role
@kopf.on.create(SMAN_GROUP, SMAN_VERSION, SMAN_PLURAL)
@kopf.on.update(SMAN_GROUP, SMAN_VERSION, SMAN_PLURAL)
async def secretsmanagementCreate(
    meta, spec, status, body, namespace, labels, name, logw: LogWrapper = None, **kwargs
):
    logw = LogWrapper(
        handler_name="secretsmanagementCreate", function_name="secretsmanagementCreate"
    )
    logw.set(component_name=quick_get_comp_name(body), resource_name=f"SMan/{name}")

    logw.debugInfo("Create/Update  called", body)
    logw.debug("secretsmanagement  called with namespace", namespace)
    logw.debug("secretsmanagement  called with name", name)
    logw.debug("secretsmanagement  called with labels", labels)

    # do not use safe_get for mandatory fields
    sman_namespace = namespace
    sman_name = name  # spec['name']
    pod_name = safe_get(None, spec, "podSelector", "name")
    pod_namespace = safe_get(None, spec, "podSelector", "namespace")
    pod_service_account = safe_get(None, spec, "podSelector", "serviceaccount")

    setupSecretsManagement(
        logw, sman_namespace, sman_name, pod_name, pod_namespace, pod_service_account
    )

    if not implementationReady(body):
        setSecretsManagementReady(logw, sman_namespace, sman_name)

    restart_pods_with_missing_sidecar(
        logw, sman_namespace, pod_name, pod_namespace, pod_service_account
    )


# when an oda.tmforum.org api resource is deleted, unbind the apig api
@kopf.on.delete(SMAN_GROUP, SMAN_VERSION, SMAN_PLURAL, retries=5)
async def secretsmanagementDelete(
    meta, spec, status, body, namespace, labels, name, logw: LogWrapper = None, **kwargs
):
    logw = LogWrapper(
        handler_name="secretsmanagementDelete", function_name="secretsmanagementDelete"
    )
    logw.set(component_name=quick_get_comp_name(body), resource_name=f"SMan/{name}")

    logw.debugInfo("Delete  called with body", body)
    logw.info("Delete  called with namespace", namespace)
    logw.info("Delete  called with name", name)
    logw.info("Delete  called with labels", labels)

    sman_name = name  # spec['name']
    sman_namespace = namespace

    deleteSecretsManagement(logw, sman_namespace, sman_name)


@logwrapper
def setSecretsManagementReady(logw: LogWrapper, namespace, name):
    """Helper function to update the implementation Ready status on the SecretsManagement custom resource.

    Args:
        * namespace (String): namespace of the SecretsManagement custom resource
        * name (String): name of the SecretsManagement custom resource

    Returns:
        No return value.
    """
    logw.info(
        "setting implementation status to ready for dependent api",
        f"{namespace}:{name}",
    )
    api_instance = kubernetes.client.CustomObjectsApi()
    try:
        sman = api_instance.get_namespaced_custom_object(
            SMAN_GROUP, SMAN_VERSION, namespace, SMAN_PLURAL, name
        )
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logw.error(f"secretsmanagement {name}.{namespace} not found")
            raise kopf.TemporaryError(
                f"setSecretsManagementReady: secretsmanagement {namespace}:{name} not found"
            )
        else:
            raise kopf.TemporaryError(
                f"setSecretsManagementReady: Exception in get_namespaced_custom_object: {e.body}"
            )
    current_ready_status = safe_get(False, sman, "status", "implementation", "ready")
    if current_ready_status is True:
        return
    if not ("status" in sman.keys()):
        sman["status"] = {}
    sman["status"]["implementation"] = {"ready": True}
    try:
        _ = api_instance.patch_namespaced_custom_object(
            SMAN_GROUP, SMAN_VERSION, namespace, SMAN_PLURAL, name, sman
        )
    except ApiException as e:
        raise kopf.TemporaryError(
            f"setSecretsManagementReady: Exception in patch_namespaced_custom_object: {e.body}"
        )


@kopf.on.field(
    SMAN_GROUP, SMAN_VERSION, SMAN_PLURAL, field="status.implementation", retries=5
)
async def updateSecretsManagementReady(
    meta, spec, status, body, namespace, labels, name, logw: LogWrapper = None, **kwargs
):
    """moved from componentOperator to here, to avoid inifite loops.
    If possible to configure kopf correctly it should be ported back to componentOperator

    Propagate status updates of the *implementation* status in the SecretsManagement Custom resources to the Component status

    Args:
        * meta (Dict): The metadata from the SecretsManagement resource
        * spec (Dict): The spec from the yaml SecretsManagement resource showing the intent (or desired state)
        * status (Dict): The status from the SecretsManagement resource showing the actual state.
        * body (Dict): The entire SecretsManagement resource definition
        * namespace (String): The namespace for the SecretsManagement resource
        * labels (Dict): The labels attached to the SecretsManagement resource.
                         All ODA Components (and their children) should have a oda.tmforum.org/componentName label
        * name (String): The name of the SecretsManagement resource

    Returns:
        No return value, nothing to write into the status.
    """
    logw = LogWrapper(
        handler_name="updateSecretsManagementReady",
        function_name="updateSecretsManagementReady",
    )
    logw.set(component_name=quick_get_comp_name(body), resource_name=f"SMan/{name}")

    logw.debugInfo(f"updateSecretsManagementReady called for {name}.{namespace}", body)
    if "ready" in status["implementation"].keys():
        if status["implementation"]["ready"] is True:
            if "ownerReferences" in meta.keys():
                parent_component_name = meta["ownerReferences"][0]["name"]
                await patch_securitySecretsManagement_ready(
                    logw, namespace, parent_component_name, retry=5, delay=1
                )


@logwrapper
async def patch_securitySecretsManagement_ready(
    logw: LogWrapper, namespace, parent_component_name, retry=5, delay=1
):
    try_cnt = 0
    while True:
        try_cnt = try_cnt + 1
        if try_cnt > 1:
            logw.info(f"retrying failed patch in {delay} seconds, try number", try_cnt)
            await asyncio.sleep(delay)
        logw.info("reading component", parent_component_name)
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
            logw.exception(
                f"Exception when calling api_instance.get_namespaced_custom_object {parent_component_name}",
                e,
            )
            raise kopf.TemporaryError(
                f"Exception when calling api_instance.get_namespaced_custom_object {parent_component_name}: {e.body}"
            )
        # find the entry to update in securitySecretsManagement status
        sman_status = parent_component["status"]["securitySecretsManagement"]
        ready = sman_status["ready"]
        if ready is True:  # avoid recursion
            return
        logw.info(
            "patching securitySecretsManagement in component",
            parent_component_name,
        )
        sman_status["ready"] = True
        try:
            _ = api_instance.patch_namespaced_custom_object(
                COMP_GROUP,
                COMP_VERSION,
                namespace,
                COMP_PLURAL,
                parent_component_name,
                parent_component,
            )
            return
        except ApiException as e:
            logw.error(
                f"updateSecretsManagementReady: Exception in patch_namespaced_custom_object {parent_component_name}",
                e.body,
            )
            # TODO[FH] check for "the object has been modified"
            if try_cnt >= retry:
                raise kopf.TemporaryError(
                    f"updateSecretsManagementReady: Exception in patch_namespaced_custom_object {parent_component_name}: {e.body}"
                )
