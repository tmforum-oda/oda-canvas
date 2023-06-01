# Private-Vault

Implementation for testing the workflow described in [UC0XX-Component-Vault.md](/usecase-library/UC0XX-Component-Vault.md).

## Deploy Hashicorp Vault

* https://developer.hashicorp.com/vault/docs/platform/k8s/helm
* https://github.com/hashicorp/vault-helm

```
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install demo-vault hashicorp/vault --version 0.24.0 --namespace demo-vault --create-namespace --values vault/values.yaml
kubectl config set-context --current --namespace=demo-vault
```

## Create Key-Value Store "comp-secrets"

```
kubectl exec -it demo-vault-0 -- /bin/sh
vault login
      <roottoken>
vault secrets enable -version=2 -path=comp-secrets kv
```

## Introspect Cluster

```
kubectl proxy
```

in browser:

* http//localhost:8001/.well-known/openid-configuration
* http//localhost:8001/openid/v1/jwks

in vault:

```
cat /var/run/secrets/kubernetes.io/serviceaccount/token | cut -f2 -d. | base64 --decode
```

alternative:

```
cat /var/run/secrets/kubernetes.io/serviceaccount/token 
```

paste output into https://jwt.io


## Setup JWT endpoint 

```
vault auth enable -path jwtk8s jwt
vault write auth/jwtk8s/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```



## Configure Full Access to "component/123" for Component with CIID 123 

create role

```
export CIID=123
vault policy write comp-$CIID-policy - <<EOF
path "comp-secrets/data/component/$CIID" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF
```

## Grant access for JWT with Serviceaccount 123 

```
vault write auth/jwtk8s/role/comp-$CIID-role \
   role_type="jwt" \
   bound_audiences="https://kubernetes.default.svc.cluster.local" \
   user_claim="sub" \
   bound_subject="system:serviceaccount:demo-comp:serviceaccount-democomp-$CIID" \
   policies="comp-$CIID-policy" \
   ttl="1h"
```

## Access Vault UI

```
kubectl port-forward demo-vault-0 8200:8200
```

http://localhost:8200

# SideCar Sources

Use Swagger-Codegen to create skelton in folder ./app from openapi.yaml.

Add implementation in api_secret.go. 
For accessing Hashicorp Vault use the go module "github.com/hashicorp/vault/api".

The app/Dockerfile uses a golang image for building the binary private-vault-service 
and then creates the final image from scratch, only containing the executables.

```
cd ./app
docker build -t private-service-vault .
```

# Deploy Demo-Comp CURL with Private-Vault-SideCar

```
helm upgrade --install democomp --namespace demo-comp --create-namespace helm-charts/democomp
kubectl config set-context --current --namespace=demo-comp  
```

## Login to CURL Container

```
kubectl get pods
kubectl exec -it democomp-XXXXXXXXXX-XXXXXX -- /bin/sh

export KEY=testpw1

# CreateSecret
curl -s -X "POST" "http://localhost:5000/api/v3/secret" -H "accept: application/json" -H "Content-Type: application/json" -d "{\"key\":\"$KEY\",\"value\":\"init-value-$KEY\"}"

# GetSecretByKey
curl -s -X GET http://localhost:5000/api/v3/secret/$KEY -H "accept: application/json"

# UpdateSecret
curl -s -X PUT http://localhost:5000/api/v3/secret/$KEY -H "accept: application/json" -H "Content-Type: application/json" -d "{\"key\":\"$KEY\",\"value\":\"update-value-$KEY\"}"

# GetSecretByKey
curl -s -X GET http://localhost:5000/api/v3/secret/$KEY -H "accept: application/json"

# DeleteSecret
curl -s -X DELETE http://localhost:5000/api/v3/secret/$KEY -H "accept: */*"
```





 
