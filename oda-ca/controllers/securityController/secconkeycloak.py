import requests

class Keycloak:

    def __init__(self, url):
        self._url = url

    def getToken(self, user: str, pwd: str) -> str:
        """
        Takes the admin username and password and returns a session token for future Bearer authentication

        Returns the token, or raises an exception for the caller to catch
        """
        try: # to get the token from Keycloak
            r = requests.post(self._url + '/realms/master/protocol/openid-connect/token', data = {"username": user, "password": pwd, "grant_type": "password", "client_id": "admin-cli"})
            r.raise_for_status()
            return r.json()["access_token"]
        except (requests.HTTPError, requests.URLRequired) as e:
            raise

    def createClient(self, client: str, url: str, token: str, realm: str) -> None:
        """
        POSTs a new client named according to the componentName for a new component

        Returns nothing, or raises an exception for the caller to catch
        """

        try: # to create the client in Keycloak
            r = requests.post(self._url + '/admin/realms/'+ realm +'/clients', json={"clientId": client, "rootUrl": url}, headers={'Authorization': 'Bearer ' + token})
            r.raise_for_status()
        except requests.HTTPError as e:
            # ! This might hide actual errors
            # ! The keycloak API isn't idempotent.
            # ! If a client exists it returns 409 instead of 201
            # ! But why did we call createClient for a client that exists?
            if e.response.status_code == 409:
                pass # because the client (already) exists, which is what we want
            else:
                raise
        except requests.URLRequired as e:
            raise

    def delClient(self, client: str, token: str, realm: str) -> None:
        """
        DELETEs a client

        Returns nothing, or raises an exception for the caller to catch
        """
        
        try: # to GET the id of the existing client that we need to DELETE it
            r_a = requests.get(self._url + '/admin/realms/'+ realm +'/clients', params={"clientId": client}, headers={'Authorization': 'Bearer ' + token})
            r_a.raise_for_status()
        except (requests.HTTPError, requests.URLRequired) as e:
            raise

        if len(r_a.json()) > 0: # we found a client with a matching name
            targetClient = r_a.json()[0]['id']

            try: # to delete the client matching the id we found
                r_b = requests.delete(self._url + '/admin/realms/'+ realm +'/clients/' + targetClient, headers={'Authorization': 'Bearer ' + token})
                r_b.raise_for_status()
            except (requests.HTTPError, requests.URLRequired) as e:
                raise

        else: # we didn't find a client with a matching name
            # ! This might hide actual errors
            # ! if the client doesn't exist the API call returns an empty JSON array
            # ! But why did we call delClient for a client that didn't exist?
            pass # because the client doesn't exist, which is what we want

    def getClientList(self, token: str, realm: str) -> dict:
        """
        GETs a list of clients in the realm to ensure there is a client to match the componentName

        Returns a dictonary of clients and ids or raises an exception for the caller to catch
        """
        try:
            r = requests.get(self._url + '/admin/realms/'+ realm +'/clients', headers={'Authorization': 'Bearer ' + token})
            r.raise_for_status()
            clientList = dict((d['clientId'], d['id']) for d in r.json())
            return clientList
        except (requests.HTTPError, requests.URLRequired) as e:
            raise

    def addRole(self, role: str, clientId: str, token: str, realm: str) -> None:
        """
        POST new roles to the right client in the right realm in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try: # to add new role to Keycloak
            r = requests.post(self._url + '/admin/realms/'+ realm +'/clients/' + clientId + '/roles', json = {"name": role}, headers={'Authorization': 'Bearer ' + token})
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 409:
                pass # because the role already exists, which is acceptable but suspicious
            else:
                raise # because we failed to add the role
        except requests.URLRequired as e:
            raise

    def delRole(self, role: str, client: str, token: str, realm: str) -> None:
        """
        DELETE removed roles from the right client in the right realm in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try: # to to remove role from Keycloak
            r = requests.delete(self._url + '/admin/realms/'+ realm +'/clients/' + client + '/roles/' + role, headers={'Authorization': 'Bearer ' + token})
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 404:
                pass # because the role does not exist which is acceptable but suspicious
            else:
                raise # because we failed to delete the role
        except requests.URLRequired as e:
            raise