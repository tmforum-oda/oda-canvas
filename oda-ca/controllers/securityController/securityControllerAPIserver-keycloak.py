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

    Returns the token, or raises an exception for the caller to catch
    """

    try: # to get the token from Keycloak
        r = requests.post(kcBaseURL + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.HTTPError as e:
        raise

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

    Returns a dictonary of clients and ids or raises an exception for the caller to catch
    """
    try:
        r = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        clientList = dict((d['clientId'], d['id']) for d in r.json())
        return clientList
    except requests.HTTPError as e:
        raise

def addRole(role: str, clientId: str, token: str, realm: str) -> None:
    """
    POST new roles to the right client in the right realm in Keycloak

    Returns nothing or raises an exception for the caller to catch
    """

    try: # to add new role to Keycloak
        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + clientId + '/roles', json = {"name": role}, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
    except requests.HTTPError as e:
        if r.status_code == 409:
            pass # because the role already exists, which is acceptable but suspicious
        else:
            raise # because we failed to add the role

def delRole(role: str, client: str, token: str, realm: str) -> bool:
    """
    DELETE removed roles from the right client in the right realm in Keycloak

    Returns nothing or raises an exception for the caller to catch
    """

    try: # to to remove role from Keycloak
        r = requests.delete(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + client + '/roles/' + role, headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
    except requests.HTTPError as e:
        if r.status_code == 404:
            pass # because the role does not exist which is acceptable but suspicious
        else:
            raise # because we failed to delete the role

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

# Flask app --------------------------------------------------------------

app = Flask(__name__)
@app.route('/listener', methods=['POST'])
def partyRoleListener():
    client = ''
    doc = request.json
    logging.debug(f"security-APIListener received {doc}")
    partyRole = doc['event']['partyRole']
    logging.debug(f"partyRole = {partyRole}")
    if partyRole['@baseType'] == 'PartyRole':
        eventType = doc['eventType']
        logging.debug(f"security-APIListener called with eventType {eventType}")
        componentName = partyRole['href'].split('/')[3]
        
        try: # to authenticate and get a token
            token = getToken(username, password)
        except requests.HTTPError as e:
            logging.error(formatCloudEvent(str(e), "security-APIListener couldn't GET Keycloak token"))
            raise

        try: # to get the list of existing clients
            clientList = getClientList(token, kcRealm)
        except requests.HTTPError as e:
            logging.error(formatCloudEvent(str(e), f"security-APIListener couldn't GET clients for {kcRealm}"))
        else:
            client = clientList[componentName]

        if client != "":
            if eventType==PARTY_ROLE_CREATION:
                try: # to add the role to the client in Keycloak
                    addRole(partyRole["name"], client, token, kcRealm)
                except requests.HTTPError as e:
                    logging.error(formatCloudEvent(f'Keycloak role create failed for {partyRole["name"]} in {componentName}', "security-APIListener event listener error"))
                else:
                    logging.info(formatCloudEvent(f'Keycloak role {partyRole["name"]} added to {componentName}', "security-APIListener event listener success"))
            elif eventType==PARTY_ROLE_DELETION:
                try: # to add the role to the client in Keycloak
                    delRole(partyRole["name"], client, token, kcRealm)
                except requests.HTTPError as e:
                    logging.error(formatCloudEvent(f'Keycloak role delete failed for {partyRole["name"]} in {componentName}', "security-APIListener event listener error"))
                else:
                    logging.info(formatCloudEvent(f'Keycloak role {partyRole["name"]} removed from {componentName}', "security-APIListener event listener success"))
            elif eventType==PARTY_ROLE_UPDATE:
                pass # because we don't need to do anything for updates
                logging.debug(f"Update Keycloak for UPDATE")
            else:
                logging.warning(formatCloudEvent(f'eventType was {eventType} - not processed'), 'security-APIListener called with invalid eventType')
        else:
            logging.error(formatCloudEvent(f'No client found in Keycloak for {partyRole["name"]}'), 'security-APIListener called for non-existent client')
    else:
        logging.warning(formatCloudEvent(f'@baseType was {partyRole["@baseType"]} - not processed'), 'security-APIListener called with invalid @baseType')

    return ''