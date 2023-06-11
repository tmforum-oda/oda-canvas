# https://hvac.readthedocs.io/en/stable/overview.html#getting-started
# https://github.com/hashicorp/vault-examples/blob/main/examples/_quick-start/python/example.py

component_instance_id = "demo-comp-123"
vault_addr = 'https://canvas-vault-hc.k8s.feri.ai'
auth_id = "jwt-k8s-pv"  # "jwtk8s"
login_role =  f'pv-{component_instance_id}-role'
secrets_mount = "private-vault"
secrets_base_path = f"component/{component_instance_id}"

import hvac
import sys

from cryptography.fernet import Fernet
import base64

def decrypt(encrypted_text):
    """
    decrypts an encrypted text. The seed (master-password) for decryption is read from the file ".seed.txt"
    Input: encrypted_text
    Output: the decrypted text. If the text was not encrypted with the same seed, 
            an exception is raised.
    """
    with open('.seed.txt') as f:
        seed = f.read().strip()
    return Fernet(base64.b64encode((seed*32)[:32].encode('ascii')).decode('ascii')).decrypt(encrypted_text.encode('ascii')).decode('ascii')

def encrypt(plain_text):
    """
    encrypts a given text. The seed (master-password) for encryption is read from the file ".seed.txt"
    Input: plain_text
    Output: the encrypted text
    """
    with open('.seed.txt') as f:
        seed = f.read().strip()
    return Fernet(base64.b64encode((seed*32)[:32].encode('ascii')).decode('ascii')).encrypt(plain_text.encode('ascii')).decode('ascii')


TOKEN=decrypt("gAAAAABkhhRpDlTVrH5lC9GjvDONgxK4ZosKeCTIjCBFuOpqOa9bj_7zkISxGMBM85ZtT8i-1-t21Yy8rrwmX_5uB7q2KfW0lA==")


namespace="demo-comp-123"
service_account="default"


# Authentication
client = hvac.Client(
    url=vault_addr,
    token=TOKEN,
)


### create policy
# https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
#


policy_name=f'pv-{component_instance_id}-policy'
print(f'create policy {policy_name}')

policy = f'''
path "{secrets_mount}/data/{secrets_base_path}/*" {{
  capabilities = ["create", "read", "update", "delete", "list", "patch"]
}}
'''

client.sys.create_or_update_policy(
    name=policy_name,
    policy=policy,
)



### create role
# https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#create-role
#


allowed_redirect_uris = [f'{vault_addr}/jwt-test/callback']

print(f'create role {login_role}')

sub = f"system:serviceaccount:{namespace}:{service_account}"
print(f"sub={sub}")
# JWT
client.auth.jwt.create_role(
    name=login_role,
    role_type='jwt',
    user_claim='sub',
    bound_subject=sub,
    bound_audiences=["https://kubernetes.default.svc.cluster.local"],
    token_policies=[policy_name],
    token_ttl=3600,
    allowed_redirect_uris=allowed_redirect_uris,  # why?
    path = auth_id,
)

"""
{
    "aud":["https://kubernetes.default.svc.cluster.local"],
    "exp":1718043240,
    "iat":1686507240,
    "iss":"https://kubernetes.default.svc.cluster.local",
    "kubernetes.io":{
        "namespace":"demo-comp-123",
        "pod":{
            "name":"demo-comp-123-5c8df86f44-w9tc4",
            "uid":"2594318f-29a6-43fc-be1c-5b82f759c2cf"
        },
        "serviceaccount":{
            "name":"default",
            "uid":"cfec7dd2-5ee6-47d9-ab1c-fe8254c3d751"
        },
        "warnafter":1686510847
    },
    "nbf":1686507240,
    "sub":"system:serviceaccount:demo-comp-123:default"
}
"""

