import kopf
import requests
import base64
import logging
import kubernetes.client
from kubernetes.client.rest import ApiException
import json
import os

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
logger = logging.getLogger('CredentialsOperator')
logger.setLevel(int(logging_level))
logger.info("Logging set to %s", logging_level)

# Script setup --------------

credsOp_client_id = os.environ.get("CLIENT_ID")
credsOp_client_secret = os.environ.get("CLIENT_SECRET")
kcBaseurl = os.environ.get("KEYCLOAK_BASE")
kcRealm = os.environ.get("KEYCLOAK_REALM")

GROUP = "oda.tmforum.org"
VERSION = "v1"
IDENTITYCONFIG_VERSION = "v1"
IDENTITYCONFIG_PLURAL = "identityconfigs"

# Kopf handlers -------------

# try to recover from broken watchers https://github.com/nolar/kopf/issues/1036
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60


def is_status_changed(status, **_):
    return status.get('credentialsOperator/status.identityConfig') != "secret created"


@kopf.on.field(GROUP, IDENTITYCONFIG_VERSION, IDENTITYCONFIG_PLURAL, field="status.identityConfig", when=is_status_changed, retries=5)
def credentialsOperator(
    meta, spec, status, body, namespace, labels, name, old, new, **kwargs
):
    
    # del unused-arguments for linting
    del status, labels, kwargs

    # Takes the clientId and secret of credentialsOperator client to authenticate and get a token
    try:
        r = requests.post(
                kcBaseurl + "/realms/"+ kcRealm +"/protocol/openid-connect/token",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    "client_id": credsOp_client_id,
                    "client_secret":credsOp_client_secret,
                    "grant_type": "client_credentials",
                },
            )

        r.raise_for_status()
        token = r.json()["access_token"]
    except requests.exceptions.RequestException as e:
        raise kopf.TemporaryError(
            f"request for token failed with HTTP status {r.status_code}: {e}"
        ) 
    else:
        logger.info( "token retrieved" )

    # clientId of component which kubernetes secret is to be created
    client_id = name

    # to get the list of existing clients and the client secret for this component
    try:
        r = requests.get(
                kcBaseurl + "/admin/realms/" + kcRealm + "/clients",
                params={"clientId": client_id},
                headers={"Authorization": "Bearer " + token},
            )
            
        r.raise_for_status()
        client_secret = r.json()[0]["secret"]
    except requests.exceptions.RequestException as e:
        raise kopf.TemporaryError(
            f"request for client_secret failed with HTTP status {r.status_code}: {e}"
        )
    else:
        logger.info( f'client secret retrieved' )

    # encoded clientId and secret in base64
    encoded_client_id = base64.b64encode(client_id.encode('utf-8')).decode('utf-8')
    encoded_client_secret = base64.b64encode(client_secret.encode('utf-8')).decode('utf-8')

    # to create a kubernetes secret
    try:
        core_v1_api = kubernetes.client.CoreV1Api()
        
        secret = kubernetes.client.V1Secret(
            metadata=kubernetes.client.V1ObjectMeta(name=client_id + "-secret"),
            data={"client_id": encoded_client_id, "client_secret": encoded_client_secret}  # Base64 encoded values
        )

        # Make it child of IdentityConfigResource
        kopf.adopt(secret)
        
        core_v1_api.create_namespaced_secret(namespace=namespace, body=secret)
    except ApiException as e:
        raise kopf.TemporaryError(
            f"secret creation failed : {e} "
        )
    else:
        logger.info( 'kubernetes secret is created' )

    # the return value is added to the status field of the k8s object 
    # under credentialsOperator/status.identityConfig parameter (corresponds to function name and field)
    return "secret created"