# VAULT

## Setup JWT

linux

```
export VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
export JWT_AUTH=jwtdemo
vault login
export ISSUER="$(kubectl get --raw /.well-known/openid-configuration | jq -r '.issuer')"
vault auth enable -path $JWT_AUTH jwt
vault write auth/$JWT_AUTH/config oidc_discovery_url=$ISSUER
```



## setup component vault

### Enable KV v2 engine

```
export CV_NAME=demo
export CV_SECRETBASE=sidecar
export POLICY=cv-$CV_NAME-policy
export ROLE=cv-$CV_NAME-role
export KV=kv-$CV_NAME

# enable KV v2 engine 
# https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?
vault secrets enable -version=2 -path=$KV kv

# check
vault secrets list
vault read sys/mounts/$KV
```

### Create Policy

```
# create policy
# https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
vault policy write $POLICY -<<EOF
path "$KV/data/$CV_SECRETBASE/*" {
  capabilities = ["create", "read", "update", "delete", "patch"]
}
EOF

# check
vault policy list
vault policy read $POLICY
```

### Create Role

```
# create role
# https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#create-role

vault write auth/$JWT_AUTH/role/$ROLE - <<EOF
{
  "role_type": "jwt",
  "bound_audiences": ["$ISSUER"],
  "user_claim": "sub",
  "bound_claims_type": "glob",
  "bound_claims": {
    "/kubernetes.io/namespace": "components"
  },
  "token_policies": [ "$POLICY" ],
  "token_ttl": "3600",
  "allowed_redirect_uris": [ "http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback" ]
}
EOF

# check
vault list auth/$JWT_AUTH/role
vault read -format=json auth/$JWT_AUTH/role/$ROLE
```



## login with JWT

```
export VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
export JWT=$(kubectl run vaulttest -it --image=hashicorp/vault --restart=Never -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)
kubectl delete pod vaulttest
echo $JWT
echo
vault write auth/$JWT_AUTH/login role=$ROLE jwt=$JWT
```

```
export VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
export JWT=eyJ...e4g
echo $JWT
echo
TEST_JWT_AUTH=jwt-k8s-cv
TEST_ROLE=cv-demo-a-productcatalogmanagement-role
TEST_JWT_AUTH=$JWT_AUTH
TEST_ROLE=$ROLE
vault write auth/$TEST_JWT_AUTH/login role=$TEST_ROLE jwt=$JWT
```

# Test POD

get JWT

```
export JWT=$(kubectl run vaulttest -it --image=hashicorp/vault --restart=Never -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)
kubectl delete pod vaulttest
echo $JWT
echo ""
```


## VAULT cli Pod:

```
apiVersion: v1
kind: Pod
metadata:
 name: vaulttest
spec:
 containers:
 - name: vaulttest
   image: hashicorp/vault
   command: ['/bin/sh', '-c', 'echo "JWT:";
     echo "----------------------------";
     cat /var/run/secrets/kubernetes.io/serviceaccount/token;
     echo "";
     echo "----------------------------";
     echo "finished']
```


