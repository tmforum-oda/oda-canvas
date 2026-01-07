from dotenv import load_dotenv
load_dotenv()  # take environment variables

import os
import json

from keycloak_utils import Keycloak
from k8s_utils import create_or_update_k8s_secret

KC_USERNAME = os.getenv("KC_USERNAME")
KC_PASSWORD = os.getenv("KC_PASSWORD")
KC_ADMIN_CLIENT_ID = os.getenv("KC_ADMIN_CLIENT_ID")
KC_ADMIN_CLIENT_SECRET = os.getenv("KC_ADMIN_CLIENT_SECRET")
KC_BASE_URL = os.getenv("KC_BASE_URL")
KC_REALM = os.getenv("KC_REALM")
COMPREG_ADMIN_INIT_PASSWORD = os.getenv("COMPREG_ADMIN_INIT_PASSWORD")
COMPREG_VIEWER_INIT_PASSWORD = os.getenv("COMPREG_VIEWER_INIT_PASSWORD")

K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
        


SUFFIX = os.getenv("SUFFIX", "")


def create_clients_users_and_roles(
        crmgr_client_id: str = f"componentregistry{SUFFIX}", 
        ui_viewer_user_name: str = f"compreg-viewer{SUFFIX}", 
        ui_admin_user_name: str = f"compreg-admin{SUFFIX}", 
        ui_viewer_user_init_password: str = COMPREG_VIEWER_INIT_PASSWORD,
        ui_admin_user_init_password: str = COMPREG_ADMIN_INIT_PASSWORD, 
        ui_viewer_role: str = f"ui-viewer{SUFFIX}",
        ui_admin_role: str = f"ui-admin{SUFFIX}",
        sync_role: str = f"sync{SUFFIX}",
        query_role: str = f"query{SUFFIX}",
        depapi_client_id: str = f"dependentapi-operator{SUFFIX}"
    ):
    """
    Creates Keycloak clients, users, and roles for Component Registry Manager.
    
    KeyCloak:
      Clients:
        - Client "componentregistry"
          - Role "ui-viewer"
          - Role "ui-admin"
          - Role "sync"
          - Role "query"
        - Client "dependentapi-operator"
      Users:
        - User "compreg-viewer"
          - mappedRole "componentregistry:ui-viewer"
        - User "compreg-admin"
          - mappedRoles "componentregistry:ui-admin"
        - User "service-account-dependentapi-operator"
          - mappedRole "componentregistry:query"
        - User "service-account-componentregistry"
          - mappedRole "componentregistry:sync"
          
    Kubernetes:
      - Secret "componentregistry-oidc-secret"
          - client_id
          - client_secret
          - token_url
      - Secret "dependentapi-operator-oidc-secret"
          - client_id
          - client_secret
          - token_url
          
    """
    kc = Keycloak(KC_BASE_URL, KC_REALM, user=KC_USERNAME, pwd=KC_PASSWORD, admin_client_id=KC_ADMIN_CLIENT_ID, admin_client_secret=KC_ADMIN_CLIENT_SECRET)

    clients = kc.get_client_list()

    if not crmgr_client_id in clients:
        print(f"Creating {crmgr_client_id} client...")
        kc.create_client(crmgr_client_id)
        clients = kc.get_client_list()
    crmgr_client = clients[crmgr_client_id]
    create_or_update_k8s_secret(K8S_NAMESPACE, crmgr_client_id, crmgr_client['secret'], kc.get_token_url())
    print("--- COMPREG MANAGER CLIENT ----")
    print(json.dumps(crmgr_client, indent=2))
    
    if not depapi_client_id in clients:
        print(f"Creating {depapi_client_id} client...")
        kc.create_client(depapi_client_id)
        clients = kc.get_client_list()
    depapi_client = clients[depapi_client_id]
    create_or_update_k8s_secret(K8S_NAMESPACE, depapi_client_id, depapi_client['secret'], kc.get_token_url())
    print("--- DEPAPI CLIENT ----")
    print(json.dumps(depapi_client, indent=2))

    roles = kc.get_roles(crmgr_client['id'])
    if not ui_viewer_role in roles:
        print(f"Creating {ui_viewer_role} role...")
        kc.add_role(ui_viewer_role, crmgr_client['id'], description="Role for Compreg UI access")
        roles = kc.get_roles(crmgr_client['id'])
    if not ui_admin_role in roles:
        print(f"Creating {ui_admin_role} role...")
        kc.add_role(ui_admin_role, crmgr_client['id'], description="Role for Compreg UI access")
        roles = kc.get_roles(crmgr_client['id'])
    if not sync_role in roles:
        print(f"Creating {sync_role} role...")
        kc.add_role(sync_role, crmgr_client['id'], description="Role for Compreg SYNC access")
        roles = kc.get_roles(crmgr_client['id'])
    if not query_role in roles:
        print(f"Creating {query_role} role...")
        kc.add_role(query_role, crmgr_client['id'], description="Role for Compreg QUERY access")
        roles = kc.get_roles(crmgr_client['id'])
    
    print("--- ROLES ----")
    print(json.dumps(roles, indent=2))

    ui_viewer_user = kc.get_user_by_username(ui_viewer_user_name)
    if ui_viewer_user is None:
        print(f"Creating {ui_viewer_user_name} user...")
        ui_viewer_user = kc.create_user(ui_viewer_user_name, ui_viewer_user_init_password)
    print("--- USER ----")
    print(json.dumps(ui_viewer_user, indent=2))
      
    mapped_roles = kc.get_mapped_roles(ui_viewer_user['id'], crmgr_client['id'])
    if not ui_viewer_role in mapped_roles:
        print(f"Mapping {ui_viewer_role} role to {ui_viewer_user_name} user...")
        kc.map_role_to_user(ui_viewer_user['id'], crmgr_client['id'], ui_viewer_role)
        mapped_roles = kc.get_mapped_roles(ui_viewer_user['id'], crmgr_client['id'])
    print("--- MAPPED ROLES ----")
    print(json.dumps(mapped_roles, indent=2))
 
    ui_admin_user = kc.get_user_by_username(ui_admin_user_name)
    if ui_admin_user is None:
        print(f"Creating {ui_admin_user_name} user...")
        ui_admin_user = kc.create_user(ui_admin_user_name, ui_admin_user_init_password)
    print("--- USER ----")
    print(json.dumps(ui_admin_user, indent=2))
      
    mapped_roles = kc.get_mapped_roles(ui_admin_user['id'], crmgr_client['id'])
    if not ui_admin_role in mapped_roles:
        print(f"Mapping {ui_admin_role} role to {ui_admin_user_name} user...")
        kc.map_role_to_user(ui_admin_user['id'], crmgr_client['id'], ui_admin_role)
        mapped_roles = kc.get_mapped_roles(ui_admin_user['id'], crmgr_client['id'])
    print("--- MAPPED ROLES ----")
    print(json.dumps(mapped_roles, indent=2))

    sa_depapi = kc.get_service_account_user(depapi_client['id'])
    print("--- SERVICE ACCOUNT USER ----")
    print(json.dumps(sa_depapi, indent=2))
    
    mapped_depapi_roles = kc.get_mapped_roles(sa_depapi['id'], crmgr_client['id'])

    if not query_role in mapped_depapi_roles:
        print(f"Mapping {query_role} role to {depapi_client_id} service account user...")
        kc.map_role_to_user(sa_depapi['id'], crmgr_client['id'], query_role)
        mapped_depapi_roles = kc.get_mapped_roles(sa_depapi['id'], crmgr_client['id'])

    print("--- MAPPPED ROLES ----")
    print(json.dumps(mapped_depapi_roles, indent=2))


    sa_crmgr = kc.get_service_account_user(crmgr_client['id'])
    print("--- SERVICE ACCOUNT USER ----")
    print(json.dumps(sa_crmgr, indent=2))
    
    mapped_crmgr_roles = kc.get_mapped_roles(sa_crmgr['id'], crmgr_client['id'])

    if not sync_role in mapped_crmgr_roles:
        print(f"Mapping {sync_role} role to {crmgr_client_id} service account user...")
        kc.map_role_to_user(sa_crmgr['id'], crmgr_client['id'], sync_role)
        mapped_crmgr_roles = kc.get_mapped_roles(sa_crmgr['id'], crmgr_client['id'])
    print("--- MAPPPED ROLES ----")
    print(json.dumps(mapped_crmgr_roles, indent=2))


if __name__ == "__main__":
    create_clients_users_and_roles()