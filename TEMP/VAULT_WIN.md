# VAULT

## Setup JWT

linux

```
export VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
export JWT_AUTH=jwt3
vault login
export ISSUER="$(kubectl get --raw /.well-known/openid-configuration | jq -r '.issuer')"
vault auth enable -path $JWT_AUTH jwt
vault write auth/$JWT_AUTH/config oidc_discovery_url=$ISSUER
```

win

```
vault login

set JWT_AUTH=jwt2
set ISSUER=https://container.googleapis.com/v1/projects/tmforum-oda-component-cluster/locations/europe-west3/clusters/ihc-dt
vault auth enable -path %JWT_AUTH% jwt
vault write auth/%JWT_AUTH%/config oidc_discovery_url=%ISSUER%
```


## setup component vault

### Enable KV v2 engine

Linux

```
export CV_NAME=abcd
export CV_SECRETBASE=sidecar
export POLICY=cv-$CV_NAME-policy
export ROLE=cv-$CV_NAME-role
export KV=kv-$CV_NAME

# enable KV v2 engine 
# https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?
vault secrets enable -version=2 -path=$KV kv

# check
vault secrets list
vault read sys/mounts/kv-abcd
```

win

```
set CV_NAME=abcd
set CV_SECRETBASE=sidecar
set POLICY=cv-%CV_NAME%-policy
set ROLE=cv-%CV_NAME%-role
set KV=kv-%CV_NAME%

# enable KV v2 engine 
# https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html?highlight=mount#hvac.api.system_backend.Mount.enable_secrets_engine
vault secrets enable -version=2 -path=%KV% kv
```

### Create Policy

Linux

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

win

```
# create policy
# https://hvac.readthedocs.io/en/stable/usage/system_backend/policy.html#create-or-update-policy
echo path "%KV%/data/%CV_SECRETBASE%/*" { > TEMP.pol
echo   capabilities = ["create", "read", "update", "delete", "patch"] >> TEMP.pol
echo } >> TEMP.pol
type TEMP.pol
vault policy write %POLICY% ./TEMP.pol
del TEMP.pol
```

### Create Role

Linux

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
vault read -format=json auth/$JWT_AUTH/role/$ROLE
```

win

```
# create role
# https://hvac.readthedocs.io/en/stable/usage/auth_methods/jwt-oidc.html#create-role


echo { > TEMP.rol
echo   "role_type": "jwt", >> TEMP.rol
echo   "bound_audiences": ["%ISSUER%"], >> TEMP.rol
echo   "user_claim": "sub", >> TEMP.rol
echo   "bound_claims_type": "glob", >> TEMP.rol
echo   "bound_claims": { >> TEMP.rol
echo     "/kubernetes.io/namespace": "components", >> TEMP.rol
REM echo     "/kubernetes.io/pod/name": "%CV_NAME%-*", >> TEMP.rol
REM echo     "/kubernetes.io/serviceaccount/name": "default" >> TEMP.rol
echo   }, >> TEMP.rol
echo   "token_policies": [ "%POLICY%" ], >> TEMP.rol
echo   "token_ttl": "3600", >> TEMP.rol
echo   "allowed_redirect_uris": [ "http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback" ] >> TEMP.rol
echo } >> TEMP.rol

echo   role_type="jwt" > TEMP.rol
echo   bound_audiences="%ISSUER%" >> TEMP.rol
echo   user_claim="sub" >> TEMP.rol
echo   bound_claims_type="glob" >> TEMP.rol
echo   bound_claims={"/kubernetes.io/namespace":"components"} >> TEMP.rol
echo   token_policies=["%POLICY%"] >> TEMP.rol
echo   token_ttl=3600 >> TEMP.rol
echo   allowed_redirect_uris=[ "http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback" ] >> TEMP.rol

echo   role_type="jwt" > TEMP.rol
echo   bound_audiences="%ISSUER%" >> TEMP.rol
echo   user_claim="sub" >> TEMP.rol
echo   bound_claims_type="glob" >> TEMP.rol
echo   bound_claims="/kubernetes.io/namespace=components" >> TEMP.rol
echo   token_policies="%POLICY%" >> TEMP.rol
echo   token_ttl=3600 >> TEMP.rol
echo   allowed_redirect_uris="http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback" >> TEMP.rol


type TEMP.rol
vault write auth/%JWT_AUTH%/role/%ROLE% ./TEMP.rol
del TEMP.rol


# https://developer.hashicorp.com/vault/docs/auth/jwt#jwt-authentication

FIX: see https://github.com/hashicorp/vault-plugin-auth-jwt/issues/68#issuecomment-522075476
###HIERWEITER###
vault write auth/%JWT_AUTH%/role/%ROLE% role_type="jwt" bound_audiences="%ISSUER%" user_claim="sub" bound_claims_type="glob" bound_claims={\"/kubernetes.io/namespace\":\"components\"} token_policies="%POLICY%" token_ttl=3600 allowed_redirect_uris="http://canvas-vault-hc.canvas-vault.svc.cluster.local:8200/jwt-test/callback"
```





# query roles

```
vault list auth/%JWT_AUTH%/role
vault read auth/%JWT_AUTH%/role/cv-demo-a-productcatalogmanagement-role
```


## login with JWT

```
set VAULT_ADDR=https://canvas-vault-hc.ihc-dt.cluster-3.de
set JWT=eyJ...GZQ
set ROLE=cv-demo-a-productcatalogmanagement-role
vault write auth/jwtk8s/login role=$ROLE% jwt=%JWT%
```



