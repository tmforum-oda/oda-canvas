# To run this using Flask: 
# 1) set the environment variable $env:FLASK_APP = "securityControllerAPIserver-keycloak.py"
# 2) type 'flask run'

from flask import Flask
from flask import request
import logging
import os
import requests
import uuid
import datetime

from cloudevents.http import CloudEvent, to_structured

# Helper functions -------------------------------------------------------

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

def getClientList(token: str, realm: str) -> dict:
    """
    GETs a list of clients in the realm to ensure there is a client to match the componentName
    """
    try:
        r = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        clientList = dict((d['clientId'], d['id']) for d in r.json())
        logging.debug(clientList)
        return clientList
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't GET clients for {realm}"))

def createRole(role: str, client: str, token: str, realm: str) -> bool:
    """
    POSTs a new role to a client named according to the componentName for a new component
    """
    try:
        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients', json={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        return True
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't POST new client {client} in realm {realm}"))
            return False

def delRole(role: str, client: str, token: str, realm: str) -> bool:
    """
    DELETEs a client
    """
    try:
        r_a = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', params={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
        r_a.raise_for_status()
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't GET ID for client {client} in realm {realm}"))
            return False
    try: # to find the right client
        targetClient = r_a.json()[0]['id']
    except:
        pass
    try:
        r_b = requests.delete(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + targetClient, headers={'Authorization': 'Bearer ' + token})
        r_b.raise_for_status()
        return True
    except requests.HTTPError as e:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't DELETE client {client} in realm {realm}"))
            return False

# Initial setup ----------------------------------------------------------

logging_level = os.environ.get('LOGGING',20)
username = os.environ.get('KEYCLOAK_USER')
password = os.environ.get('KEYCLOAK_PASSWORD')
kcBaseURL = os.environ.get('KEYCLOAK_BASE')
kcRealm = os.environ.get('KEYCLOAK_REALM')
print('Logging set to ',logging_level)
logger = logging.getLogger()
logger.setLevel(int(logging_level)) #Logging level default = INFO

PARTY_ROLE_CREATION = 'PartyRoleCreationNotification'
PARTY_ROLE_UPDATE = 'PartyRoleAttributeValueChangeNotification'
PARTY_ROLE_DELETION = 'PartyRoleRemoveNotification'

app = Flask(__name__)
@app.route('/listener', methods=['POST'])
def partyRoleListener():
    try: # to process incoming POSTs
        doc = request.json
        logging.debug(f"security-APIListener received {doc}")
        partyRole = doc['event']['partyRole']
        logging.debug(f"partyRole = {partyRole}")
        if partyRole['@baseType'] != 'PartyRole':
            raise Exception("Event Resource is not of baseType PartyRole")
        eventType = doc['eventType']
        logging.info(f"security-APIListener called with eventType {eventType}")

        token = getToken(username, password)
        clientList = getClientList(token, kcRealm)
        client = clientList[componentName]
        if eventType==PARTY_ROLE_CREATION:
            if createRole(partyRole, client, token, kcRealm):
                logging.debug(formatCloudEvent(f"Keycloak role {partyRole} added to {client}", "secCon event listener success"))
            else:
                logging.debug(formatCloudEvent(f"Keycloak role update failed for {partyRole} in {client}", "secCon event listener error"))
        elif eventType==PARTY_ROLE_UPDATE:
            pass
            #logging.debug(f"Update Keycloak for UPDATE")
        elif eventType==PARTY_ROLE_DELETION:
            if delRole(partyRole, client, token, kcRealm):
                logging.debug(formatCloudEvent(f"Keycloak role {partyRole} deleted from {client}", "secCon event listener success"))
            else:
                logging.debug(formatCloudEvent(f"Keycloak role delete failed for {partyRole} in {client}", "secCon event listener error"))
        else:
            raise Exception(f"Unknown event {eventType}")


    except Exception as e:
        logging.error(f"security-APIListener error {e}")
        return e

    return ''