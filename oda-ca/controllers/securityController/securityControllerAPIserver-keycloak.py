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

def addRole(role: str, clientId: str, token: str, realm: str) -> bool:
    """
    POST new roles to the right client in the right realm in Keycloak
    """

    try: # to add new role to Keycloak
        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + clientId + '/roles', json = {"name": role}, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        return True # because the role was successfully created
    except requests.HTTPError as e:
        if r.status_code == 409:
            return True # because the role already exists, which is acceptable but suspicious
        else:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't POST new role for {clientId}"))
            return False # because we failed to add the role

def delRole(role: str, client: str, token: str, realm: str) -> bool:
    """
    DELETE removed roles from the right client in the right realm in Keycloak
    """

    try: # to to remove role from Keycloak
        r = requests.delete(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + client + '/roles/' + role, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        return True # because we deleted the role
    except requests.HTTPError as e:
        if r.status_code == 404:
            return True # because the role does not exist which is acceptable but suspicious
        else:
            logging.warning(formatCloudEvent(str(e), f"secCon couldn't POST new role for {client}"))
            return False # because we failed to delete the role

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
        logging.info(f"security-APIListener received {doc}")
        partyRole = doc['event']['partyRole']
        logging.debug(f"partyRole = {partyRole}")
        if partyRole['@baseType'] != 'PartyRole':
            raise Exception("Event Resource is not of baseType PartyRole")
        eventType = doc['eventType']
        logging.info(f"security-APIListener called with eventType {eventType}")

        token = getToken(username, password)
        clientList = getClientList(token, kcRealm)
        componentName = partyRole['href'].split('/tmf-api/')[0]
        componentName = componentName.split('://')[1]
        componentName = componentName.split('/')[1]
        
        client = clientList[componentName]

        if eventType==PARTY_ROLE_CREATION:
            if addRole(partyRole['name'], client, token, kcRealm):
                logging.debug(formatCloudEvent(f"Keycloak role {partyRole} added to {client}", "secCon event listener success"))
            else:
                logging.debug(formatCloudEvent(f"Keycloak role create failed for {partyRole} in {client}", "secCon event listener error"))
        elif eventType==PARTY_ROLE_UPDATE:
            pass
            #logging.debug(f"Update Keycloak for UPDATE")
        elif eventType==PARTY_ROLE_DELETION:
            if delRole(partyRole['name'], client, token, kcRealm):
                logging.debug(formatCloudEvent(f"Keycloak role {partyRole} deleted from {client}", "secCon event listener success"))
            else:
                logging.debug(formatCloudEvent(f"Keycloak role delete failed for {partyRole} in {client}", "secCon event listener error"))
        else:
            raise Exception(f"Unknown event {eventType}")


    except Exception as e:
        logging.error(f"security-APIListener error {e}")
        return e

    return ''