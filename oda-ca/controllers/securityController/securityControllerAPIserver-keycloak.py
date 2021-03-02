# To run this using Flask: 
# 1) set the environment variable $env:FLASK_APP = "securityControllerAPIserver-keycloak.py"
# 2) type 'flask run'

from flask import Flask
from flask import request
import logging
import os
 
logging_level = os.environ.get('LOGGING',20)
print('Logging set to ',logging_level)
logger = logging.getLogger()
logger.setLevel(int(logging_level)) #Logging level default = INFO

PARTY_ROLE_CREATION = 'PartyRoleCreationNotification'
PARTY_ROLE_UPDATE = 'PartyRoleAttributeValueChangeNotification'
PARTY_ROLE_DELETION = 'PartyRoleRemoveNotification'

app = Flask(__name__)
@app.route('/listener', methods=['POST'])
def partyRoleListener():
    try: # to process incomming POSTs
        doc = request.json
        logging.debug(f"security-APIListener received {doc}")
        partyRole = doc['event']['partyRole']
        logging.debug(f"partyRole = {partyRole}")
        if partyRole['@baseType'] != 'PartyRole':
            raise Exception("Event Resource is not of baseType PartyRole")
        eventType = doc['eventType']
        logging.info(f"security-APIListener called with eventType {eventType}")

        if eventType==PARTY_ROLE_CREATION:
            logging.debug(f"Update Keycloak for CREATE")
        elif eventType==PARTY_ROLE_UPDATE:
            logging.debug(f"Update Keycloak for UPDATE")
        elif eventType==PARTY_ROLE_DELETION:
            logging.debug(f"Update Keycloak for DELETE")
        else:
            raise Exception(f"Unknown event {eventType}")


    except Exception as e:
        logging.error(f"security-APIListener error {e}")
        return e

    return ''