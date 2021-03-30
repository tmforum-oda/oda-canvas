import kopf
import logging
import os
import requests
import uuid
import datetime
import secconkeycloak

from cloudevents.http import CloudEvent, to_structured

# Helper functions ----------

#def getToken(user: str, pwd: str) -> str:
#    """
#    Takes the admin username and password and returns a session token for future Bearer authentication
#
#    Returns the token, or raises an exception for the caller to catch
#    """
#
#    try: # to get the token from Keycloak
#        r = requests.post(kcBaseURL + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
#        r.raise_for_status()
#        return r.json()["access_token"]
#    except requests.HTTPError as e:
#        raise

#def createClient(client: str, url: str, token: str, realm: str) -> None:
#    """
#    POSTs a new client named according to the componentName for a new component
#
#    Returns nothing, or raises an exception for the caller to catch
#    """
#
#    try: # to create the client in Keycloak
#        r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients', json={"clientId": client, "rootUrl": url}, headers={'Authorization': 'Bearer ' + token})
#        r.raise_for_status()
#    except requests.HTTPError as e:
#        # ! This might hide actual errors
#        # ! The keycloak API isn't idempotent.
#        # ! If a client exists it returns 409 instead of 201
#        # ! But why did we call createClient for a client that exists?
#        if e.response.status_code == 409:
#            pass # because the client (already) exists, which is what we want
#        else:
#            raise

#def delClient(client: str, token: str, realm: str) -> bool:
#    """
#    DELETEs a client
#
#    Returns nothing, or raises an exception for the caller to catch
#    """
#
#    try: # to GET the id of the existing client that we need to DELETE it
#        r_a = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', params={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
#        r_a.raise_for_status()
#    except requests.HTTPError as e:
#        logger.error(formatCloudEvent(str(e), f"secCon couldn't GET ID for client {client} in realm {realm}"))
#        raise
#
#    if len(r_a.json()) > 0: # we found a client with a matching name
#        targetClient = r_a.json()[0]['id']
#
#        try: # to delete the client matching the id we found
#            r_b = requests.delete(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + targetClient, headers={'Authorization': 'Bearer ' + token})
#            r_b.raise_for_status()
#        except requests.HTTPError as e:
#            logger.error(formatCloudEvent(str(e), f"secCon couldn't DELETE client {client} in realm {realm}"))
#            raise
#
#    else: # we didn't find a client with a matching name
#        # ! This might hide actual errors
#        # ! if the client doesn't exist the API call returns an empty JSON array
#        # ! But why did we call delClient for a client that didn't exist?
#        pass # because the client doesn't exist, which is what we want
        
def registerListener(url: str) -> None:
    """
    Register the listener URL with partyRoleManagement for role updates

    Returns nothing, or raises an exception for the caller to catch
    """

    try: # to register the listener
        r = requests.post(url, json = {"callback": "http://seccon.canvas:5000/listener"})
        r.raise_for_status()
    except requests.HTTPError as e:
        raise

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
logging_level = os.environ.get('LOGGING', logging.INFO)
print('Logging set to ', logging_level)
logger = logging.getLogger('SecurityOperator')
logger.setLevel(int(logging_level))

username = os.environ.get('KEYCLOAK_USER')
password = os.environ.get('KEYCLOAK_PASSWORD')
kcBaseURL = os.environ.get('KEYCLOAK_BASE')
kcRealm = os.environ.get('KEYCLOAK_REALM')

kc = secconkeycloak.Keycloak(kcBaseURL)


# Kopf handlers -------------


# @kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components', field='status.deployment_status', value='Complete') # called by kopf framework when a component's status is updated
def securityClientAdd(meta, spec, status, body, namespace, labels, name, old, new, **kwargs):
    """
    Handler for component create/update
    """

    rooturl = 'http://' + spec['security']['partyrole']['implementation'] + '.' + namespace + '.svc.cluster.local:' + str(spec['security']['partyrole']['port']) + spec['security']['partyrole']['path']
    logger.debug(f"using component root url: {rooturl}")
    logger.debug(f'status.deployment_status = {old} -> {new}')

    try: # to authenticate and get a token
        token = kc.getToken(username, password)
    except requests.HTTPError as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't GET Keycloak token"))
    except requests.URLRequired as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't determine Keycloak URL"))
        raise kopf.PermanentError("Could not determine Keycloak URL. Will NOT retry.")

    try: # to create the client in Keycloak
        kc.createClient(name, rooturl, token, kcRealm)
    except requests.HTTPError as e:
        logger.error(formatCloudEvent(str(e), f"secCon couldn't POST new client {name} in realm {kcRealm}"))
        raise kopf.TemporaryError("Could not add component to Keycloak. Will retry.", delay=10)
    except requests.URLRequired as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't determine Keycloak URL"))
        raise kopf.PermanentError("Could not determine Keycloak URL. Will NOT retry.")
    else:
        logger.info(formatCloudEvent(f"oda.tmforum.org component {name} created", f"secCon: component created"))
        try: # to register with the partyRoleManagement API
            registerListener(rooturl + "/hub")
        except requests.HTTPError as e:
            logger.warning(formatCloudEvent(str(e), "secCon couldn't register partyRoleManagement listener"))
            statusValue = {'identityProvider': 'Keycloak', 'listenerRegistered': False}
            raise kopf.TemporaryError("Could not register listener. Will retry.", delay=10)
        else:
            statusValue = {'identityProvider': 'Keycloak', 'listenerRegistered': True}
    
    return statusValue # the return value is added to the status field of the k8s object under securityRoles parameter (corresponds to function name)
    

@kopf.on.delete('oda.tmforum.org', 'v1alpha2', 'components', retries=5) # called by kopf framework when a component is deleted
def securityClientDelete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """

    try: # to authenticate and get a token
        token = kc.getToken(username, password)
    except requests.HTTPError as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't GET Keycloak token"))
    except requests.URLRequired as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't determine Keycloak URL"))
        raise kopf.PermanentError("Could not determine Keycloak URL. Will NOT retry.")

    try: # to delete the client from Keycloak
        kc.delClient(name, token, kcRealm)
    except requests.HTTPError as e:
        logger.error(formatCloudEvent(str(e), f"secCon couldn't DELETE client {name} in realm {kcRealm}"))
        raise kopf.TemporaryError("Could not delete component from Keycloak. Will retry.", delay=10)
    except requests.URLRequired as e:
        logger.error(formatCloudEvent(str(e), "secCon couldn't determine Keycloak URL"))
        raise kopf.PermanentError("Could not determine Keycloak URL. Will NOT retry.")