# Installations

## Install Private Vault Custom Resource Definition

```
helm upgrade --install oda-pv-crd installation/oda-pv-crds --namespace privatevault-system --create-namespace
```

## Install HashiCorp Vault in DEV mode

not for production!

```
## install canvas-vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc hashicorp/vault --version 0.24.0 --namespace canvas-vault --create-namespace --values installation/canvas-vault-hc/values.yaml
```

## DEBUG: create public route to Canvas-Vault

```
kubectl apply -f installation/canvas-vault-hc/public-route-for-testing.yaml
```

## Configure HashiCorp Vault to accept Kubernetes SerciceAccount Issuer

```
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-pv jwt
sleep 2
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-pv/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## KOPF crds

```
helm upgrade --install kopf-framework operators/privatevaultoperator-hc/helmcharts/kopf-framework --namespace privatevault-system --create-namespace
```



## Private-Vault-Operator

```
helm upgrade --install privatevault-operator operators/privatevaultoperator-hc/helmcharts/pvop --namespace privatevault-system --create-namespace
```


## Test


### Example PrivateVault

```
kubectl apply -f test/privatevault-dc123.yaml
kubectl apply -f test/privatevault-dc124.yaml
kubectl get privatevaults
```

### deploy demo components with privatevault=sidecar annotation

```
helm upgrade --install demo-comp test/helm-charts/democomp -n demo-comp --create-namespace
```

to PODs get the sidecar injected, demo-comp-one and demo-comp-two.
demo-comp-three fails the pattern check, because it is annotated with 
"demo-comp-123" and "privatevault-demo-comp-123" defines the 
podSelector name="demo-comp-one-*" which does not match the actual
"demo-comp-three-fcn938l9"

The pod-name selector is only validated inside the WebHook, while namespace and serviceaccount
are validated in HashiCorp Vault auth.


### log into component one

```
kubectl exec -it -n demo-comp deployment/demo-comp-one -- /bin/sh
```

access private vault using localhost

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

now open a second shell in component two:

```
kubectl exec -it -n demo-comp deployment/demo-comp-two -- /bin/sh
export KEY=testpw1
# CreateSecret
curl -s -X "POST" "http://localhost:5000/api/v3/secret" -H "accept: application/json" -H "Content-Type: application/json" -d "{\"key\":\"$KEY\",\"value\":\"comp-two-value-$KEY\"}"
# GetSecretByKey
curl -s -X GET http://localhost:5000/api/v3/secret/$KEY -H "accept: application/json"
```

short check in the other shell for component one:

```
# GetSecretByKey
curl -s -X GET http://localhost:5000/api/v3/secret/$KEY -H "accept: application/json"
```

The secret does not exist in component-one, because both sidecats have different secrets mounts.


# Cleanup

```
kubectl delete -f test/privatevault.yaml
# if delete hangs, finalizer of privatevault cr have to be removed.
helm uninstall -n demo-comp demo-comp
helm uninstall -n canvas-vault canvas-vault-hc
helm uninstall -n privatevault-system privatevault-operator 
helm uninstall -n privatevault-system oda-pv-crd
helm uninstall -n privatevault-system kopf-framework 
kubectl delete ns demo-comp
kubectl delete ns privatevault-system 

### keep letsencrypt cert
#kubectl delete -f installation/canvas-vault-hc/public-route-for-testing.yaml
#kubectl delete ns canvas-vault  
```
