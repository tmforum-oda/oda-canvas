import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os
import requests
import uuid
import datetime

from cloudevents.http import CloudEvent, to_structured

# Helper functions ----------

def getToken(user: str, pwd: str) -> str:
    """
    Takes the admin username and password and returns a session token for future Bearer authentication
    """
    try:
        r = requests.post(kcBaseURL + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.HTTPError as e:
        logging.warning(reportEvent(str(e), "secCon couldn't GET Keycloak token"))

def createClient(client: str, token: str, realm: str) -> bool:
    """
    POSTs a new client named according to the componentName for a new component
    """
    try:
        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients', json={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        return True
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't POST new client {client} in realm {realm}"))
            return False

def delClient(client: str, token: str, realm: str) -> bool:
    """
    DELETEs a client
    """
    try:
        r_a = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', params={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
        r_a.raise_for_status()
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't GET ID for client {client} in realm {realm}"))
            return False
    targetClient = r_a.json()[0]['id']
    try:
        r_b = requests.delete(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + targetClient, headers={'Authorization': 'Bearer ' + token})
        r_b.raise_for_status()
        return True
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't DELETE client {client} in realm {realm}"))
            return False

def formatCloudEvent(message: str, subject: str) -> str:
    """
    Returns a correctly formatted CloudEvents compliant event
    """
    attributes = {
        "specversion" : "1.0",
        "type" : "org.tmforum.for.type.event.an.invented.burton.brian",
        "source" : "https://example.com/security-controller",
        "subject": subject,
        "id" : str(uuid.uuid4()),
        "time" : datetime.datetime.now().isoformat(),
        "datacontenttype" : "application/json",
    }

    data = {"message": message}

    event = CloudEvent(attributes, data)
    headers, body = to_structured(event)

    return body

# Script setup --------------

logging_level = os.environ.get('LOGGING',20)
username = os.environ.get('KEYCLOAK_USER')
password = os.environ.get('KEYCLOAK_PASSWORD')
kcBaseURL = os.environ.get('KEYCLOAK_BASE')
kcRealm = os.environ.get('KEYCLOAK_REALM')
print('Logging set to ',logging_level)  
logger = logging.getLogger()
logger.setLevel(int(logging_level)) #Logging level default = INFO


# Kopf handlers -------------


# @kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components', field='status.deployment_status', value='Complete') # called by kopf framework when a component's status is updated
def securityRoles(meta, spec, status, body, namespace, labels, name, old, new, **kwargs):
    """
    Handler for component create/update
    """
    logging.info(f'status.deployment_status = {old} -> {new}')
    token = getToken(username, password)
    if not createClient(name, token, kcRealm):
        logging.info(formatCloudEvent(f"Could not add oda.tmforum.org component {name}. Will rety.", f"secCon: component create/update"))
        raise kopf.TemporaryError("Could not add component to Keycloak. Will retry.", delay=20)
    else:
        logging.info(formatCloudEvent(f"oda.tmforum.org component {name} created/updated", f"secCon: component create/update"))
    statusValue = {'identityProvider': 'Keycloak'}
    return statusValue # the return value is added to the status field of the k8s object under securityRoles parameter (corresponds to function name)
    

@kopf.on.delete('oda.tmforum.org', 'v1alpha2', 'components') # called by kopf framework when a component is deleted
def securityRolesDelete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """
    token = getToken(username, password)
    if not delClient(name, token, kcRealm):
        logging.info(formatCloudEvent(f"Could not delete oda.tmforum.org component {name}. Will rety.", f"secCon: component delete"))
        raise kopf.TemporaryError("Could not delete component from Keycloak. Will rety.", delay=20)
    else:
        logging.info(formatCloudEvent(f"oda.tmforum.org component {name} deleted", f"secCon: component delete"))