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

def processUrl(url: str) -> str:
    """
    This is an horrific bodge until we can add the URL scheme to status.securityAPIs.url
    """
    if (url.find("http://") == -1) and (url.find("https://") == -1):
        url = "http://" + url
    return url

def registerListener(url: str) -> bool:
    """
    Register the listener URL with partyRoleManagement for role updates
    """
    try:
        r = requests.post(url, json = {"callback": "http://seccon.canvas:5000/listener"})
        #r = requests.post(url, json = {"callback": "http://192.168.3.226:5000/listener"})
        r.raise_for_status()
        return True
    except requests.HTTPError as e:
        logging.warning(formatCloudEvent(str(e), "secCon couldn't register partyRoleManagement listener"))
        return False


def getToken(user: str, pwd: str) -> str:
    """
    Takes the admin username and password and returns a session token for future Bearer authentication
    """
    try:
        r = requests.post(kcBaseURL + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.HTTPError as e:
        logging.warning(formatCloudEvent(str(e), "secCon couldn't GET Keycloak token"))

def createClient(client: str, url: str, token: str, realm: str) -> bool:
    """
    POSTs a new client named according to the componentName for a new component
    """
    try:
        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients', json={"clientId": client, "rootUrl": url}, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        return True
    except requests.HTTPError as e:
        # ! This might hide actual errors
        # ! The keycloak API isn't idempotent.
        # ! If a client exists it returns 409 instead of 201
        # ! But why did we call createClient for a client that exists?
        if e.response.status_code == 409:
            return True # because the client (already) exists, which is what we want
        else:
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
    if len(r_a.json()) == 0:
        # ! This might hide actual errors
        # ! if the client doesn't exist the API call returns an empty JSON array
        # ! But why did we call delClient for a client that didn't exist?
        return True # because the client doesn't exist, which is what we want
    else:
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
        "source" : "http://seccon.canvas.svc.cluster.local",
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
def securityClientAdd(meta, spec, status, body, namespace, labels, name, old, new, **kwargs):
    """
    Handler for component create/update
    """
    logging.info(f'status.deployment_status = {old} -> {new}')
    logging.info(f'status is type {type(status)}')
    logging.info(f"status[\'securityAPIs\']: {status['securityAPIs']}")
    token = getToken(username, password)

    # ! This commented section is for the old version of status.securityAPIs based on lists
    #if len(status['securityAPIs']) > 0:
    #    for i in status['securityAPIs']:
    #        if i['url'].find("partyRoleManagement"):
    #            rooturl = processUrl(i['url'])
    #else:
    #    raise kopf.TemporaryError("status.SecurityAPIs not populated. Will retry.", delay=10)

    # ! This uncommented section is for the new version of status.securityAPIs based on dicts
    if 'securityAPIs' in status:
        #rooturl = status['securityAPIs']['partyrole']['url']
        rooturl = 'http://' + spec['security']['partyrole']['implementation'] + '.components.svc.cluster.local:' + str(spec['security']['partyrole']['port']) + spec['security']['partyrole']['path']
        logging.info(f"using component root url: {rooturl}")

    else:
        raise kopf.TemporaryError("status.SecurityAPIs not populated. Will retry.", delay=10)

    if not createClient(name, rooturl, token, kcRealm):
        logging.info(formatCloudEvent(f"Could not add oda.tmforum.org component {name}. Will rety.", f"secCon: component create/update"))
        raise kopf.TemporaryError("Could not add component to Keycloak. Will retry.", delay=10)
    else:
        logging.info(formatCloudEvent(f"oda.tmforum.org component {name} created/updated", f"secCon: component create/update"))
    if registerListener(rooturl + "/hub"):
        statusValue = {'identityProvider': 'Keycloak', 'listenerRegistered': True}
    else:
        statusValue = {'identityProvider': 'Keycloak', 'listenerRegistered': False}
    return statusValue # the return value is added to the status field of the k8s object under securityRoles parameter (corresponds to function name)
    

@kopf.on.delete('oda.tmforum.org', 'v1alpha2', 'components', retries=5) # called by kopf framework when a component is deleted
def securityClientDelete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """
    token = getToken(username, password)
    if not delClient(name, token, kcRealm):
        logging.info(formatCloudEvent(f"Could not delete oda.tmforum.org component {name}. Will rety.", f"secCon: component delete"))
        raise kopf.TemporaryError("Could not delete component from Keycloak. Will rety.", delay=10)
    else:
        logging.info(formatCloudEvent(f"oda.tmforum.org component {name} deleted", f"secCon: component delete"))