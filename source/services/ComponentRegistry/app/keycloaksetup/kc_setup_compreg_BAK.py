from dotenv import load_dotenv
load_dotenv()  # take environment variables

import os
import json

from app.keycloaksetup.keycloakUtils import Keycloak

KC_USERNAME = os.getenv("KC_USERNAME")
KC_PASSWORD = os.getenv("KC_PASSWORD")
KC_BASE_URL = os.getenv("KC_BASE_URL")
KC_REALM = os.getenv("KC_REALM")
COMPREG_ADMIN_INIT_PASSWORD = os.getenv("COMPREG_ADMIN_INIT_PASSWORD", "CompregAdmin123!")

def check_kc(
        crmgr_client_id: str = "compreg-manager2", 
        user_name: str = "compreg-admin2", 
        user_init_password: str = COMPREG_ADMIN_INIT_PASSWORD, 
        ui_role: str = "compreg_ui",
        sync_role: str = "compreg_sync",
        query_role: str = "compreg_query2",
        depapi_client_id: str = "dependentapi-operator"
    ):
    kc = Keycloak(KC_BASE_URL, KC_REALM, KC_USERNAME, KC_PASSWORD)


    clients = kc.get_client_list()
    if not crmgr_client_id in clients:
        print(f"Creating {crmgr_client_id} client...")
        kc.create_client(crmgr_client_id)
        clients = kc.get_client_list()

    if not depapi_client_id in clients:
        print(f"Creating {depapi_client_id} client...")
        kc.create_client(depapi_client_id)
        clients = kc.get_client_list()
        
    client = clients[crmgr_client_id]
    print(json.dumps(client, indent=2))

    print(json.dumps(clients[depapi_client_id], indent=2))
    
    sa_crmgr = kc.get_service_account_user(client['id'])
    print("--- SERVICE ACCOUNT USER ----")
    print(json.dumps(sa_crmgr, indent=2))
    
    roles = kc.get_roles(client['id'])
    if not ui_role in roles:
        print(f"Creating {ui_role} role...")
        kc.add_role(ui_role, client['id'], description="Role for Compreg UI access")
        roles = kc.get_roles(client['id'])
    if not sync_role in roles:
        print(f"Creating {sync_role} role...")
        kc.add_role(sync_role, client['id'], description="Role for Compreg SYNC access")
        roles = kc.get_roles(client['id'])
    if not query_role in roles:
        print(f"Creating {query_role} role...")
        kc.add_role(query_role, client['id'], description="Role for Compreg QUERY access")
        roles = kc.get_roles(client['id'])
    
    print("--- ROLES ----")
    print(json.dumps(roles, indent=2))

    try:
        user = kc.get_user_by_username(user_name)
    except Exception as e:
        print(f"Creating {user_name} user...")
        user = kc.create_user(user_name, COMPREG_ADMIN_INIT_PASSWORD)
    print("--- USER ----")
    print(json.dumps(user, indent=2))
    
    mapped_roles = kc.get_mapped_roles(user['id'], client['id'])
    if not ui_role in mapped_roles:
        print(f"Mapping {ui_role} role to {user_name} user...")
        kc.map_role_to_user(user['id'], client['id'], ui_role)
        mapped_roles = kc.get_mapped_roles(user['id'], client['id'])
    print("--- MAPPED ROLES ----")
    print(json.dumps(mapped_roles, indent=2))

    sa_crmgr = kc.get_service_account_user(clients[depapi_client_id]['id'])
    print("--- SERVICE ACCOUNT USER ----")
    print(json.dumps(sa_crmgr, indent=2))
    
    mapped_depapi_roles = kc.get_mapped_roles(sa_crmgr['id'], client['id'])

    if not query_role in mapped_depapi_roles:
        print(f"Mapping {query_role} role to {depapi_client_id} service account user...")
        kc.map_role_to_user(sa_crmgr['id'], client['id'], query_role)
        mapped_depapi_roles = kc.get_mapped_roles(sa_crmgr['id'], client['id'])

    print("--- MAPPPED ROLES ----")
    print(json.dumps(mapped_depapi_roles, indent=2))



if __name__ == "__main__":
    check_kc()