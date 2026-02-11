"""Manage Keycloak users and clients for ODA Canvas components.

Usage:
  python manage_keycloak_users.py --keycloak-url <URL> --admin-password <PASS> --realm <REALM> --action <ACTION> [options]

Actions:
  list-clients         List clients (components) in the realm
  list-roles           List roles for a specific client: --client-id <clientId>
  list-users           List users in the realm
  create-user          Create a user: --username <NAME> --password <PASS> --client-id <clientId> [--roles role1,role2]
  create-client        Create a confidential client with service accounts: --client-id <clientId>
  get-client-secret    Get the client secret: --client-id <clientId>
  assign-client-roles  Assign roles to a client service account: --client-id <clientId> --target-client <targetClientId> [--roles role1,role2]
"""
import json
import sys
import urllib.request
import urllib.error
import urllib.parse
import argparse


def get_admin_token(base_url, password):
    """Get admin access token from Keycloak."""
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": password,
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        data=data,
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]


def kc_api(method, url, token, body=None):
    """Make a Keycloak Admin REST API call."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        content = resp.read()
        if resp.status == 201:
            loc = resp.headers.get("Location", "")
            return {"location": loc, "id": loc.rsplit("/", 1)[-1] if loc else None}
        return json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        if e.code == 409:
            print(f"  Already exists: {body_text}", file=sys.stderr)
            return None
        print(f"  Error {e.code}: {body_text}", file=sys.stderr)
        sys.exit(1)


def find_client_uuid(base_url, token, realm, client_id):
    """Find a client UUID by its clientId."""
    clients = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients", token)
    client = next((c for c in clients if c["clientId"] == client_id), None)
    if not client:
        print(f"Client '{client_id}' not found in realm '{realm}'.")
        sys.exit(1)
    return client["id"]


def list_clients(base_url, token, realm):
    """List clients in a realm, filtering to ODA component clients."""
    clients = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients", token)
    builtin = {"account", "account-console", "admin-cli", "broker",
               "realm-management", "security-admin-console"}
    fmt = "{:<40} {:<40}"
    print(fmt.format("CLIENT ID", "UUID"))
    print(fmt.format("-" * 40, "-" * 40))
    for c in clients:
        cid = c["clientId"]
        marker = "" if cid in builtin else " *"
        print(fmt.format(cid + marker, c["id"]))
    print("\n  * = non-built-in client (likely ODA component)")


def list_roles(base_url, token, realm, client_id):
    """List roles for a specific client."""
    uuid = find_client_uuid(base_url, token, realm, client_id)
    roles = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients/{uuid}/roles", token)
    if not roles:
        print(f"No roles found for client '{client_id}'.")
        return
    fmt = "{:<30} {:<50}"
    print(fmt.format("ROLE NAME", "DESCRIPTION"))
    print(fmt.format("-" * 30, "-" * 50))
    for r in roles:
        desc = r.get("description", "\u2014") or "\u2014"
        print(fmt.format(r["name"], desc))


def list_users(base_url, token, realm):
    """List users in a realm."""
    users = kc_api("GET", f"{base_url}/admin/realms/{realm}/users?max=100", token)
    if not users:
        print("No users found.")
        return
    fmt = "{:<20} {:<20} {:<36} {:<8}"
    print(fmt.format("USERNAME", "NAME", "ID", "ENABLED"))
    print(fmt.format("-" * 20, "-" * 20, "-" * 36, "-" * 8))
    for u in users:
        name = f"{u.get('firstName', '')} {u.get('lastName', '')}".strip() or "\u2014"
        print(fmt.format(
            u.get("username", "?"),
            name,
            u.get("id", "?"),
            str(u.get("enabled", False)),
        ))


def create_user(base_url, token, realm, username, password, client_id, role_names):
    """Create a user and assign client roles."""
    print(f"Creating user '{username}'...")
    user_body = {
        "username": username,
        "enabled": True,
        "firstName": username.capitalize(),
        "credentials": [{
            "type": "password",
            "value": password,
            "temporary": False,
        }],
    }
    result = kc_api("POST", f"{base_url}/admin/realms/{realm}/users", token, user_body)
    if result is None:
        print(f"User '{username}' may already exist.")
        users = kc_api("GET", f"{base_url}/admin/realms/{realm}/users?username={urllib.parse.quote(username)}&exact=true", token)
        if users:
            user_id = users[0]["id"]
            print(f"  Found existing user ID: {user_id}")
        else:
            sys.exit(1)
    else:
        user_id = result["id"]
        print(f"  User ID: {user_id}")

    print("Setting password...")
    kc_api("PUT", f"{base_url}/admin/realms/{realm}/users/{user_id}/reset-password", token, {
        "type": "password",
        "value": password,
        "temporary": False,
    })

    client_uuid = find_client_uuid(base_url, token, realm, client_id)
    available_roles = kc_api(
        "GET",
        f"{base_url}/admin/realms/{realm}/clients/{client_uuid}/roles",
        token,
    )

    if not role_names:
        roles_to_assign = [r for r in available_roles if r["name"] != "canvasRole"]
    else:
        roles_to_assign = [r for r in available_roles if r["name"] in role_names]

    if not roles_to_assign:
        print("  No roles to assign (only canvasRole found, which is reserved for Canvas).")
        return

    print(f"Assigning {len(roles_to_assign)} role(s):")
    role_payload = [{"id": r["id"], "name": r["name"]} for r in roles_to_assign]
    for r in roles_to_assign:
        print(f"  - {r['name']}")
    kc_api(
        "POST",
        f"{base_url}/admin/realms/{realm}/users/{user_id}/role-mappings/clients/{client_uuid}",
        token,
        role_payload,
    )

    print(f"\nUser '{username}' created with {len(roles_to_assign)} role(s) for client '{client_id}'.")


def create_client(base_url, token, realm, client_id):
    """Create a confidential Keycloak client with service accounts enabled."""
    print(f"Creating client '{client_id}'...")
    client_body = {
        "clientId": client_id,
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": True,
        "standardFlowEnabled": False,
        "publicClient": False,
        "protocol": "openid-connect",
    }
    result = kc_api("POST", f"{base_url}/admin/realms/{realm}/clients", token, client_body)
    if result is None:
        print(f"Client '{client_id}' may already exist.")
        uuid = find_client_uuid(base_url, token, realm, client_id)
    else:
        uuid = result["id"]
        print(f"  Client UUID: {uuid}")

    secret_data = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients/{uuid}/client-secret", token)
    secret = secret_data.get("value", "(unknown)") if secret_data else "(unknown)"
    print(f"\nClient '{client_id}' created successfully.")
    print(f"  Client UUID:   {uuid}")
    print(f"  Client Secret: {secret}")
    print(f"\nConfiguration:")
    print(f"  Client authentication: Enabled (confidential)")
    print(f"  Service accounts:      Enabled (Client Credentials flow)")
    print(f"  Direct access grants:  Enabled (Password grant for testing)")
    print(f"  Standard flow:         Disabled (no browser login)")
    print(f"\nTest with Client Credentials flow:")
    print(f"  curl -s -X POST {base_url}/realms/{realm}/protocol/openid-connect/token \\")
    print(f'    -d "grant_type=client_credentials&client_id={client_id}&client_secret={secret}"')


def get_client_secret(base_url, token, realm, client_id):
    """Retrieve the client secret for a Keycloak client."""
    uuid = find_client_uuid(base_url, token, realm, client_id)
    secret_data = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients/{uuid}/client-secret", token)
    if secret_data and "value" in secret_data:
        print(f"Client ID:     {client_id}")
        print(f"Client UUID:   {uuid}")
        print(f"Client Secret: {secret_data['value']}")
    else:
        print(f"No client secret found for '{client_id}'. Is it a confidential client?")


def assign_client_roles(base_url, token, realm, client_id, target_client_id, role_names):
    """Assign roles from a target client to the service account of another client."""
    source_uuid = find_client_uuid(base_url, token, realm, client_id)
    sa_user = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients/{source_uuid}/service-account-user", token)
    if not sa_user:
        print(f"No service account found for client '{client_id}'. Is service accounts enabled?")
        sys.exit(1)
    sa_user_id = sa_user["id"]
    print(f"Service account user: {sa_user.get('username', '?')} (ID: {sa_user_id})")

    target_uuid = find_client_uuid(base_url, token, realm, target_client_id)
    available_roles = kc_api("GET", f"{base_url}/admin/realms/{realm}/clients/{target_uuid}/roles", token)

    if not role_names:
        roles_to_assign = [r for r in available_roles if r["name"] != "canvasRole"]
    else:
        roles_to_assign = [r for r in available_roles if r["name"] in role_names]

    if not roles_to_assign:
        print("  No roles to assign.")
        return

    print(f"Assigning {len(roles_to_assign)} role(s) from '{target_client_id}' to service account of '{client_id}':")
    role_payload = [{"id": r["id"], "name": r["name"]} for r in roles_to_assign]
    for r in roles_to_assign:
        print(f"  - {r['name']}")
    kc_api(
        "POST",
        f"{base_url}/admin/realms/{realm}/users/{sa_user_id}/role-mappings/clients/{target_uuid}",
        token,
        role_payload,
    )
    print(f"\nRoles assigned successfully.")


def main():
    parser = argparse.ArgumentParser(description="Manage Keycloak users and clients for ODA Canvas")
    parser.add_argument("--keycloak-url", required=True, help="Keycloak base URL (e.g. http://localhost:8083/auth)")
    parser.add_argument("--admin-password", required=True, help="Keycloak admin password")
    parser.add_argument("--realm", default="odari", help="Keycloak realm (default: odari)")
    parser.add_argument("--action", required=True,
                        choices=["list-clients", "list-roles", "list-users", "create-user",
                                 "create-client", "get-client-secret", "assign-client-roles"])
    parser.add_argument("--client-id", help="Keycloak client ID")
    parser.add_argument("--target-client", help="Target client ID for role assignment")
    parser.add_argument("--username", help="Username for create-user")
    parser.add_argument("--password", help="Password for create-user")
    parser.add_argument("--roles", help="Comma-separated role names (omit to assign all non-canvas roles)")

    args = parser.parse_args()

    token = get_admin_token(args.keycloak_url, args.admin_password)

    if args.action == "list-clients":
        list_clients(args.keycloak_url, token, args.realm)
    elif args.action == "list-roles":
        if not args.client_id:
            print("--client-id required for list-roles")
            sys.exit(1)
        list_roles(args.keycloak_url, token, args.realm, args.client_id)
    elif args.action == "list-users":
        list_users(args.keycloak_url, token, args.realm)
    elif args.action == "create-user":
        if not args.username or not args.password or not args.client_id:
            print("--username, --password, and --client-id required for create-user")
            sys.exit(1)
        role_list = [r.strip() for r in args.roles.split(",")] if args.roles else []
        create_user(args.keycloak_url, token, args.realm, args.username, args.password,
                    args.client_id, role_list)
    elif args.action == "create-client":
        if not args.client_id:
            print("--client-id required for create-client")
            sys.exit(1)
        create_client(args.keycloak_url, token, args.realm, args.client_id)
    elif args.action == "get-client-secret":
        if not args.client_id:
            print("--client-id required for get-client-secret")
            sys.exit(1)
        get_client_secret(args.keycloak_url, token, args.realm, args.client_id)
    elif args.action == "assign-client-roles":
        if not args.client_id or not args.target_client:
            print("--client-id and --target-client required for assign-client-roles")
            sys.exit(1)
        role_list = [r.strip() for r in args.roles.split(",")] if args.roles else []
        assign_client_roles(args.keycloak_url, token, args.realm, args.client_id,
                           args.target_client, role_list)


if __name__ == "__main__":
    main()
