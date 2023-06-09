# Private-Vault Quickstart


```
## install demo-vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install demo-vault hashicorp/vault --version 0.24.0 --namespace demo-vault --create-namespace --values vault/values.yaml

## setup demo-vault
kubectl exec -n demo-vault -it demo-vault-0 -- /bin/sh
```

in demo-vault-0 shell:

```
vault secrets enable -version=2 -path=comp-secrets kv
vault auth enable -path jwtk8s jwt
vault write auth/jwtk8s/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

## create policy
export CIID=123
vault policy write comp-$CIID-policy - <<EOF
path "comp-secrets/data/component/$CIID/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

## create role
vault write auth/jwtk8s/role/comp-$CIID-role \
   role_type="jwt" \
   bound_audiences="https://kubernetes.default.svc.cluster.local" \
   user_claim="sub" \
   bound_subject="system:serviceaccount:demo-comp:serviceaccount-democomp-$CIID" \
   policies="comp-$CIID-policy" \
   ttl="1h"

exit
```

in local shell:

```
helm upgrade --install democomp --namespace demo-comp --create-namespace helm-charts/democomp
kubectl config set-context --current --namespace=demo-comp  
kubectl get pods -n demo-comp  
```

```
set DEMOCOMPPOD=democomp-78f6c4497b-6ljjn
```

```
kubectl logs -c private-vault-sidecar %DEMOCOMPPOD%
kubectl exec -it %DEMOCOMPPOD%  -- /bin/sh
```

in demo-comp shell:

```
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


## Notes

```
kubectl config set-context --current --namespace=demo-vault
kubectl config set-context --current --namespace=demo-comp
kubectl port-forward -n demo-vault svc/demo-vault 8200:8200
vault write auth/jwtk8s/login role=comp-123-role jwt=%JWT%
curl -H "X-Vault-Request: true" -H "X-Vault-Token: $TOKEN" http://demo-vault.demo-vault.svc.cluster.local:8200/v1/comp-secrets/data/component/123/test
```


## Cleanup

```
cd git\oda-canvas-FORK\source\sidecars\private-vault
helm uninstall -n demo-comp democomp
helm uninstall -n demo-vault demo-vault 
kubectl delete ns demo-comp
kubectl delete ns demo-vault
```



 
