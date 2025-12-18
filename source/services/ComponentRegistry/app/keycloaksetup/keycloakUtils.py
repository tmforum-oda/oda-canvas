import requests
import json
from datetime import datetime, timedelta

class Keycloak:

    def __init__(self, url, realm: str, user: str, pwd: str, refresh_buffer = 30) -> None:
        self._url = url
        self._realm = realm
        self._user = user
        self._pwd = pwd
        self._access_token = None
        self._token_expiry = None
        self._refresh_buffer = 30  # seconds

        
    def create_client(self, client: str, root_url: str="") -> None:
        """
        POSTs a new client named according to the componentName for
        a new component

        Returns nothing, or raises an exception for the caller to catch
        """
        if root_url == "":
            json_obj = {"clientId": client, "serviceAccountsEnabled": True}
        else:
            json_obj = {"clientId": client, "rootUrl": root_url, "serviceAccountsEnabled": True}

        try:  # to create the client in Keycloak
            r = requests.post(
                self._url + "/admin/realms/" + self._realm + "/clients",
                json=json_obj,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            # ! This might hide actual errors
            # ! The keycloak API isn't idempotent.
            # ! If a client exists it returns 409 instead of 201
            # ! But why did we call create_client for a client that
            # ! exists?
            if r.status_code == 409:
                pass  # because the client exists, which is what we want
            else:
                raise RuntimeError(
                    "create_client failed with HTTP status " f"{r.status_code}: {e}"
                ) from None


    def del_client(self, client: str) -> None:
        """
        DELETEs a client

        Returns nothing, or raises an exception for the caller to catch
        """

        try:  # to GET the id of the existing client that we need to DELETE it
            r_a = requests.get(
                self._url + "/admin/realms/" + self._realm + "/clients",
                params={"clientId": client},
                headers={"Authorization": "Bearer " + self._token()},
            )
            r_a.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                "del_client failed to get client ID with HTTP status "
                f"{r_a.status_code}: {e}"
            ) from None

        if len(r_a.json()) > 0:  # we found a client with a matching name
            target_client_id = r_a.json()[0]["id"]

            try:  # to delete the client matching the id we found
                r_b = requests.delete(
                    self._url
                    + "/admin/realms/"
                    + self._realm
                    + "/clients/"
                    + target_client_id,
                    headers={"Authorization": "Bearer " + self._token()},
                )
                r_b.raise_for_status()
            except requests.HTTPError as e:
                raise RuntimeError(
                    "del_client failed to delete client with HTTP status "
                    f"{r_b.status_code}: {e}"
                ) from None

        else:  # we didn't find a client with a matching name
            # ! This might hide actual errors
            # ! If the client doesn't exist the API call returns an
            # ! empty JSON array, but why did we call del_client for a
            # ! client that didn't exist?
            pass  # because the client doesn't exist, which is OK

    def get_client_list(self) -> dict:
        """
        GETs a list of clients in the realm to ensure there is a
        client to match the componentName

        Returns a dictonary of clients and ids or raises
        an exception for the caller to catch
        """
        try:
            r = requests.get(
                self._url + "/admin/realms/" + self._realm + "/clients",
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            client_list = dict((d["clientId"], d) for d in r.json())
            return client_list
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_client_list failed with HTTP status " f"{r.status_code}: {e}"
            ) from None

    def get_roles(self, client_id: str) -> dict:
        """
        GETs a list of roles for the given client in the given
        realm in Keycloak

        Returns a dictonary of roles and their definitions or
        raises an exception for the caller to catch

        """

        try:
            r = requests.get(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/clients/"
                + client_id
                + "/roles",
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            role_list = dict((d["name"], d) for d in r.json())
            return role_list
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_roles failed with HTTP status " f"{r.status_code}: {e}"
            ) from None

    def add_role(self, role: str, client_id: str, description: str = None) -> None:
        """
        POST new roles to the right client in the right realm in
        Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        # Build the JSON payload with role name and optional description
        role_data = {"name": role}
        if description is not None:
            role_data["description"] = description

        try:  # to add new role to Keycloak
            r = requests.post(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/clients/"
                + client_id
                + "/roles",
                json=role_data,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 409:
                pass  # because the role already exists, which is acceptable but suspicious
            else:
                raise RuntimeError(
                    "add_role failed with HTTP status " f"{r.status_code}: {e}"
                ) from None

    def del_role(self, role: str, client: str) -> None:
        """
        DELETE removed roles from the right client in the right realm
        in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try:  # to remove role from Keycloak
            r = requests.delete(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/clients/"
                + client
                + "/roles/"
                + role,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 404:
                pass  # because the role does not exist which is acceptable but suspicious
            else:
                raise RuntimeError(
                    "del_role failed with HTTP status " f"{r.status_code}: {e}"
                ) from None

                
    def _token(self) -> str:
        """
        Takes the admin username and password and returns a session
        token for future Bearer authentication

        Returns the token, or raises an exception for the caller to
        catch
        """
        if self._is_token_valid():
            return self._access_token        
        try:
            r = requests.post(
                self._url + "/realms/master/protocol/openid-connect/token",
                data={
                    "username": self._user,
                    "password": self._pwd,
                    "grant_type": "password",
                    "client_id": "admin-cli",
                },
            )
            r.raise_for_status()
            
            
            token_data = r.json()
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 300)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return self._access_token
        except requests.HTTPError as e:
            raise RuntimeError(
                f"get_token failed with HTTP status {r.status_code}: {e}"
            ) from None


    def _is_token_valid(self):
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now() < (self._token_expiry - timedelta(seconds=self._refresh_buffer))
        

    def get_user_by_username(self, username: str) -> dict:
        """
        GETs a user by username in the given realm in Keycloak

        Returns a dictonary of the user definition or
        raises an exception for the caller to catch

        """

        try:
            r = requests.get(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/users",
                params={"username": username},
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            users = r.json()
            if users:
                return users[0]  # Return the first matching user
            else:
                raise RuntimeError(f"User '{username}' not found in realm '{self._realm}'")
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_user_by_username failed with HTTP status " f"{r.status_code}: {e}"
            ) from None
            
    def get_mapped_roles(self, user_id: str, client_id: str) -> dict:
        """
        GETs mapped roles for a user in the given realm in Keycloak

        Returns a dictonary of the mapped roles or
        raises an exception for the caller to catch

        """

        try:
            r = requests.get(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/users/"
                + user_id
                + "/role-mappings/clients/"
                + client_id,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            result = dict((d["name"], d) for d in r.json())
            return result
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_mapped_roles failed with HTTP status " f"{r.status_code}: {e}"
            ) from None

    def create_user(self, username: str, init_password) -> dict:
        """
        POSTs a new user named according to the username for
        a new user

        Returns the created user dictonary, or raises an exception for the caller to catch
        """
        json_obj = {
            "username": username,
            "enabled": True,
            "credentials": [{"type": "password", "value": init_password, "temporary": True}],
        }

        try:  # to create the user in Keycloak
            r = requests.post(
                self._url + "/admin/realms/" + self._realm + "/users",
                json=json_obj,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            # After creating the user, retrieve the user details to return
            return self.get_user_by_username(username)
        except requests.HTTPError as e:
            raise RuntimeError(
                "create_user failed with HTTP status " f"{r.status_code}: {e}"
            ) from None        


    def map_role_to_user(self, user_id: str, client_id: str, role_name: str) -> None:
        """
        POSTs a role mapping to a user in the given realm in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """
        # First, get the role details to map
        try:
            r_role = requests.get(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/clients/"
                + client_id
                + "/roles/"
                + role_name,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r_role.raise_for_status()
            role_data = r_role.json()
        except requests.HTTPError as e:
            raise RuntimeError(
                "map_role_to_user failed to get role details with HTTP status "
                f"{r_role.status_code}: {e}"
            ) from None

        # Now, map the role to the user
        try:
            r_map = requests.post(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/users/"
                + user_id
                + "/role-mappings/clients/"
                + client_id,
                json=[role_data],
                headers={"Authorization": "Bearer " + self._token()},
            )
            r_map.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                "map_role_to_user failed to map role with HTTP status "
                f"{r_map.status_code}: {e}"
            ) from None


    def get_mapped_client_roles(self, source_client_id: str, target_client_id: str) -> dict:
        """
        GETs mapped roles for a client in the given realm in Keycloak

        Returns a dictonary of the mapped roles or
        raises an exception for the caller to catch
        """
        try:
            r = requests.get(
                self._url
                + "/admin/realms/"
                + self._realm
                + "/clients/"
                + source_client_id
                + "/role-mappings/clients/"
                + target_client_id,
                headers={"Authorization": "Bearer " + self._token()},
            )
            r.raise_for_status()
            result = dict((d["name"], d) for d in r.json())
            return result
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_mapped_client_roles failed with HTTP status " f"{r.status_code}: {e}"
            ) from None
