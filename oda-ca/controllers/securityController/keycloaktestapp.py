import requests
import argparse
import os
import argparse
import sys
import uuid
import datetime

from cloudevents.http import CloudEvent, to_structured

kcBaseURL = "http://k8s-1:8080/auth"
componentName = "r1-productcatalog"
prBaseURL = "http://localhost/" + componentName + "/tmf-api/partyRoleManagement/v4"
realm = "myrealm"

def reportEvent(message, subject):
    """
    Report a CloudEvents compliant event to syslog
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

    print(event)
    #syslog.syslog(event)

def argHandler():
    """
    Process command line arguments

    We request username and password from the command line as options:
    
    -u, --username \<username\>

    -p, --password \<password\>
    
    Note: these are optional because it's also possible to provide the via environment
    variables KEYCLOAK_USER and KEYCLOAK_PASSWORD. These environment variables are
    prioritised over the command line options if both are provided.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--password", help="initial password for access to keycloak")
    parser.add_argument("-u", "--username", help="initial username for access to keycloak")
    return parser.parse_args()

def credHandler(args) -> tuple:
    """
    Returns a tuple containing whatever credentials we can find
    
    This function prioritises the OS environment over the command line and kills the script if it can't get enough credentials.
    """

    if "KEYCLOAK_USER" in os.environ:
        uname = os.environ["KEYCLOAK_USER"]
    elif args.username is not None:
        uname = args.username
    else:
        reportEvent("No valid user provided. Either set the KEYCLOAK_USER environment variable or via the command line (use -h for help)", "Fatal secCon error")
        sys.exit(1)
    if "KEYCLOAK_PASSWORD" in os.environ:
        pwd = os.environ["KEYCLOAK_PASSWORD"]
    elif args.password is not None:
        pwd = args.password
    else:
        reportEvent("No valid password provided. Either set the KEYCLOAK_PASSWORD environment variable or via the command line (use -h for help)", "Fatal secCon error")
        sys.exit(1)
    return (uname, pwd)

def getToken(user: str, pwd: str) -> str:
    """
    Takes the admin username and password and returns a session token for future Bearer authentication
    """
    try:
        r = requests.post(kcBaseURL + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.HTTPError as e:
        reportEvent(str(e), "secCon couldn't GET Keycloak token")

def getRoles() -> list:
    """
    GETs a list of partyRoles from the component partyRoleManagement API
    """
    try:
        r = requests.get(prBaseURL + '/partyRole')
        r.raise_for_status()
        return [d['name'] for d in r.json() if 'name' in d]
    except requests.HTTPError as e:
            reportEvent(str(e), "secCon couldn't GET partyRoles")

def getClientList(token: str, realm: str) -> bool:
    """
    GETs a list of clients in the realm to ensure there is a client to match the componentName
    """
    try:
        r = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients', headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
        clientList = dict((d['clientId'], d['id']) for d in r.json())
        print(clientList)
        return clientList
    except requests.HTTPError as e:
            reportEvent(str(e), f"secCon couldn't GET clients for {realm}")

def addRolesToClient(token: str, realm: str, clientId: str, clientroles: list):
    """
    POST new roles to the right client in the right realm in Keycloak
    """

    try: # to get a list of existing roles
        r = requests.get(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + clientId + '/roles', headers={'Authorization': 'Bearer ' + token})
        r.raise_for_status()
    except requests.HTTPError as e:
            reportEvent(str(e), f"secCon couldn't GET list of roles for {clientId}")

    existingRoles = [d['name'] for d in r.json() if 'name' in d]
    newRoles = list(set(clientroles) - set(existingRoles))
    print(newRoles)
    for roleName in newRoles:
        print(roleName)
        try: # to add new roles to Keycloak
            r = requests.post(kcBaseURL + '/admin/realms/'+ realm +'/clients/' + clientId + '/roles', json = {"name": roleName}, headers={'Authorization': 'Bearer ' + token})
            r.raise_for_status()
        except requests.HTTPError as e:
                reportEvent(str(e), f"secCon couldn't POST new role for {clientId}")



def main():
    args = argHandler()
    adminUser, adminPassword = credHandler(args)
    roles = getRoles()
    token = getToken(adminUser, adminPassword)
    clients = getClientList(token, realm)
    if componentName in clients:
        addRolesToClient(token, realm, clients[componentName], roles)
    else:
        reportEvent(f"{componentName} not found as a client in realm {realm}", "secCon couldn't find client for roles")

if __name__ == "__main__":
    main()