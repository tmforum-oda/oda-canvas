import datetime
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
                self._url + "/realms/master/protocol/openid-connect/token",
                data={
                    "username": user,
                    "password": pwd,
                    "grant_type": "password",
                    "client_id": "admin-cli",
                },
            )
            r.raise_for_status()
            return r.json()["access_token"]
        except requests.HTTPError as e:
            raise RuntimeError(
                f"get_token failed with HTTP status {r.status_code}: {e}"
            ) from None

    def create_client(self, client: str, url: str, token: str, realm: str) -> None:
        """
        POSTs a new client named according to the componentName for
        a new component

        Returns nothing, or raises an exception for the caller to catch
        """
        if url == "":
            json_obj = {"clientId": client, "serviceAccountsEnabled": True}
        else:
            json_obj = {"clientId": client, "rootUrl": url, "serviceAccountsEnabled": True}

        try:  # to create the client in Keycloak
            r = requests.post(
                self._url + "/admin/realms/" + realm + "/clients",
                json=json_obj,
                headers={"Authorization": "Bearer " + token},
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

    def del_client(self, client: str, token: str, realm: str) -> None:
        """
        DELETEs a client

        Returns nothing, or raises an exception for the caller to catch
        """

        try:  # to GET the id of the existing client that we need to DELETE it
            r_a = requests.get(
                self._url + "/admin/realms/" + realm + "/clients",
                params={"clientId": client},
                headers={"Authorization": "Bearer " + token},
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
                    + realm
                    + "/clients/"
                    + target_client_id,
                    headers={"Authorization": "Bearer " + token},
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

    def get_client_list(self, token: str, realm: str) -> dict:
        """
        GETs a list of clients in the realm to ensure there is a
        client to match the componentName

        Returns a dictonary of clients and ids or raises
        an exception for the caller to catch
        """
        try:
            r = requests.get(
                self._url + "/admin/realms/" + realm + "/clients",
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
            client_list = dict((d["clientId"], d["id"]) for d in r.json())
            return client_list
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_client_list failed with HTTP status " f"{r.status_code}: {e}"
            ) from None

    def add_role(self, role: str, client_id: str, token: str, realm: str, description: str = None) -> None:
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
                + realm
                + "/clients/"
                + client_id
                + "/roles",
                json=role_data,
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 409:
                pass  # because the role already exists, which is acceptable but suspicious
            else:
                raise RuntimeError(
                    "add_role failed with HTTP status " f"{r.status_code}: {e}"
                ) from None

    def del_role(self, role: str, client: str, token: str, realm: str) -> None:
        """
        DELETE removed roles from the right client in the right realm
        in Keycloak

        Returns nothing or raises an exception for the caller to catch
        """

        try:  # to remove role from Keycloak
            r = requests.delete(
                self._url
                + "/admin/realms/"
                + realm
                + "/clients/"
                + client
                + "/roles/"
                + role,
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code == 404:
                pass  # because the role does not exist which is acceptable but suspicious
            else:
                raise RuntimeError(
                    "del_role failed with HTTP status " f"{r.status_code}: {e}"
                ) from None

    def get_client_by_uuid(self, token: str, realm: str, client_uuid: str) -> dict:
        """
        GETs a single Keycloak client by its internal UUID.

        Returns a ClientRepresentation dict whose 'clientId' field is the
        human-readable client name (which equals the ODA component name for
        component clients), or raises an exception for the caller to catch.

        Args:
            token: Bearer token from get_token()
            realm: Keycloak realm name
            client_uuid: The internal Keycloak client UUID (not the clientId
                string), as found in admin-event resourcePaths of the form
                users/{user-uuid}/role-mappings/clients/{client-uuid}
        """
        try:
            r = requests.get(
                self._url + "/admin/realms/" + realm + "/clients/" + client_uuid,
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_client_by_uuid failed with HTTP status "
                f"{r.status_code}: {e}"
            ) from None

    def get_user_by_uuid(self, token: str, realm: str, user_uuid: str) -> dict:
        """
        GETs a single Keycloak user by their internal UUID.

        Returns a UserRepresentation dict whose 'username' field for a service
        account is 'service-account-{clientId}', allowing the owning component
        to be identified. Raises an exception for the caller to catch.

        Args:
            token: Bearer token from get_token()
            realm: Keycloak realm name
            user_uuid: The internal Keycloak user UUID, as found in admin-event
                resourcePaths of the form users/{user-uuid}/role-mappings/...
        """
        try:
            r = requests.get(
                self._url + "/admin/realms/" + realm + "/users/" + user_uuid,
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_user_by_uuid failed with HTTP status "
                f"{r.status_code}: {e}"
            ) from None

    def get_realm_events_config(self, token: str, realm: str) -> dict:
        """
        GETs the event configuration for a realm, including whether
        admin events are enabled.

        Returns a RealmEventsConfigRepresentation dict, or raises an
        exception for the caller to catch.

        Key fields in the response:
          - adminEventsEnabled (bool): whether admin events are recorded
          - adminEventsDetailsEnabled (bool): whether full representations
            are included in admin events
        """
        try:
            r = requests.get(
                self._url + "/admin/realms/" + realm + "/events/config",
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_realm_events_config failed with HTTP status "
                f"{r.status_code}: {e}"
            ) from None

    def get_admin_events(
        self,
        token: str,
        realm: str,
        resource_types: list = None,
        operation_types: list = None,
        date_from: int = None,
        max_results: int = 100,
    ) -> list:
        """
        GETs admin events from Keycloak for a realm.

        Returns a list of AdminEventRepresentation dicts, or raises an
        exception for the caller to catch.

        Each AdminEventRepresentation contains:
          - id (str): unique event identifier
          - time (int): epoch milliseconds when the event occurred
          - realmId (str): realm in which the event occurred
          - authDetails (dict): details about the authenticated user who
            triggered the event
          - operationType (str): CREATE, UPDATE, or DELETE
          - resourceType (str): e.g. CLIENT_ROLE_MAPPING
          - resourcePath (str): e.g.
            users/{user-uuid}/role-mappings/clients/{client-uuid}
          - representation (str): JSON-encoded representation of the
            affected resource (only when adminEventsDetailsEnabled=True
            in the realm's event config)
          - error (str): error message if the operation failed

        Args:
            token: Bearer token from get_token()
            realm: Keycloak realm name
            resource_types: list of resourceType values to filter by,
                e.g. ["CLIENT_ROLE_MAPPING"]
            operation_types: list of operationType values to filter by,
                e.g. ["CREATE", "UPDATE", "DELETE"]
            date_from: include only events at or after this epoch
                millisecond timestamp; converted internally to an
                ISO-8601 datetime string as required by Keycloak
            max_results: maximum number of events to return (default 100)
        """
        params = {"max": max_results}
        if resource_types:
            params["resourceTypes"] = resource_types
        if operation_types:
            params["operationTypes"] = operation_types
        if date_from is not None:
            # Keycloak expects an ISO-8601 datetime string, not epoch milliseconds.
            params["dateFrom"] = datetime.datetime.fromtimestamp(
                date_from / 1000, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S")

        try:
            r = requests.get(
                self._url + "/admin/realms/" + realm + "/admin-events",
                params=params,
                headers={"Authorization": "Bearer " + token},
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            raise RuntimeError(
                "get_admin_events failed with HTTP status "
                f"{r.status_code}: {e}"
            ) from None
