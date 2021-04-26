import requests

class Keycloak:

    def __init__(self, url):
        self._url = url

    def get_token(self, user: str, pwd: str) -> str:
        """
        Takes the admin username and password and returns a session
        token for future Bearer authentication

        Returns the token, or raises an exception for the caller to
        catch
        """
        try:
            r = requests.post(
                self._url + '/realms/master/protocol/openid-connect/token',
                data = {
                    'username': user,
                    'password': pwd,
                    'grant_type': 'password',
                    'client_id': 'admin-cli'
                }
            )
            r.raise_for_status()
            return r.json()['access_token']
        except requests.HTTPError as e:
            raise RuntimeError(f'get_token failed with HTTP status {r.status_code}: {e}') from None

    def create_client(self, client: str, url: str, token: str, realm: str) -> None:
        """
        POSTs a new client named according to the componentName for
        a new component

        Returns nothing, or raises an exception for the caller to catch
        """

        try: # to create the client in Keycloak
            r = requests.post(
                self._url + '/admin/realms/'+ realm +'/clients',
                json={'clientId': client, 'rootUrl': url},
                headers={'Authorization': 'Bearer ' + token}
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            # ! This might hide actual errors
            # ! The keycloak API isn't idempotent.
            # ! If a client exists it returns 409 instead of 201
            # ! But why did we call create_client for a client that
            # ! exists?
            if r.status_code == 409:
                pass # because the client exists, which is what we want
            else:
                raise RuntimeError('create_client failed with HTTP status '
                                    f'{r.status_code}: {e}') from None

    def del_client(self, client: str, token: str, realm: str) -> None:
        """
        DELETEs a client

        Returns nothing, or raises an exception for the caller to catch
        """

        try: # to GET the id of the existing client that we need to DELETE it
            r_a = requests.get(
                self._url + '/admin/realms/'+ realm +'/clients',
                params={'clientId': client},
                headers={'Authorization': 'Bearer ' + token}
            )
            r_a.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError('del_client failed to get client ID with HTTP status '
                                f'{r_a.status_code}: {e}') from None

        if len(r_a.json()) > 0: # we found a client with a matching name
            target_client_id = r_a.json()[0]['id']

            try: # to delete the client matching the id we found
                r_b = requests.delete(
                    self._url + '/admin/realms/'+ realm +'/clients/' + target_client_id,
                    headers={'Authorization': 'Bearer ' + token}
                )
                r_b.raise_for_status()
            except requests.HTTPError as e:
                raise RuntimeError('del_client failed to delete client with HTTP status '
                                    f'{r_b.status_code}: {e}') from None

        else: # we didn't find a client with a matching name
            # ! This might hide actual errors
            # ! If the client doesn't exist the API call returns an
            # ! empty JSON array, but why did we call del_client for a
            # ! client that didn't exist?
            pass # because the client doesn't exist, which is OK

    def get_client_list(self, token: str, realm: str) -> dict:
        """
        GETs a list of clients in the realm to ensure there is a
        client to match the componentName

        Returns a dictonary of clients and ids or raises
        an exception for the caller to catch
        """
        try:
            r = requests.get(
                self._url + '/admin/realms/'+ realm +'/clients',
                headers={'Authorization': 'Bearer ' + token}
            )
            r.raise_for_status()
            client_list = dict((d['clientId'], d['id']) for d in r.json())
            return client_list
        except requests.HTTPError as e:
            raise RuntimeError('get_client_list failed with HTTP status '
                                f'{r.status_code}: {e}') from None

    def add_role(self, role: str, client_id: str, token: str, realm: str) -> None:
        """
        POST new roles to the right client in the right realm in
        Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try: # to add new role to Keycloak
            r = requests.post(
                self._url + '/admin/realms/'+ realm +'/clients/' + client_id + '/roles',
                json = {'name': role},
                headers={'Authorization': 'Bearer ' + token}
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 409:
                pass # because the role already exists, which is acceptable but suspicious
            else:
                raise RuntimeError('add_role failed with HTTP status '
                                    f'{r.status_code}: {e}') from None

    def del_role(self, role: str, client: str, token: str, realm: str) -> None:
        """
        DELETE removed roles from the right client in the right realm
        in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try: # to remove role from Keycloak
            r = requests.delete(
                self._url + '/admin/realms/'+ realm +'/clients/' + client + '/roles/' + role,
                headers={'Authorization': 'Bearer ' + token}
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 404:
                pass # because the role does not exist which is acceptable but suspicious
            else:
                raise RuntimeError('del_role failed with HTTP status '
                                    f'{r.status_code}: {e}') from None

    def add_role_to_user(self,
                        username: str,
                        role: str,
                        client: str,
                        token: str,
                        realm: str) -> None:
        """
        POST client role assignment to user in realm in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try: # to get the id for username
            r_a = requests.get(
                self._url + '/admin/realms/'+ realm +'/users',
                params = {'username': username},
                headers={'Authorization': 'Bearer ' + token}
            )
            r_a.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError('add_role_to_user failed to get user ID with HTTP status '
                                f'{r_a.status_code}: {e}') from None
        else:
            user_id = r_a.json()[0]['id']

        try: # to GET the id of the existing client that we need
            r_b = requests.get(
                self._url + '/admin/realms/'+ realm +'/clients',
                params={'clientId': client},
                headers={'Authorization': 'Bearer ' + token}
            )
            r_b.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError('add_role_to_user failed to get client ID with HTTP status '
                                f'{r_b.status_code}: {e}') from None
        else:
            target_client_id = r_b.json()[0]['id']

        try: # to GET the id of the role
            r_c = requests.get(
                self._url
                + '/admin/realms/'
                + realm
                +'/clients/'
                + target_client_id
                + '/roles/'
                + role,
                headers={'Authorization': 'Bearer ' + token}
            )
            r_c.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError('add_role_to_user failed to get role ID with HTTP status '
                                f'{r_c.status_code}: {e}') from None
        else:
            target_role_id = r_c.json()[0]['id']


        try: # to add role to user
            r_d = requests.post(
                self._url
                + '/admin/realms/'
                + realm
                + '/users/'
                + user_id
                + '/role_mapping/clients/'
                + target_client_id,
                json = {'name': role, 'id': target_role_id},
                headers={'Authorization': 'Bearer ' + token}
            )
            r_d.raise_for_status()
        except requests.HTTPError as e:
            pass
