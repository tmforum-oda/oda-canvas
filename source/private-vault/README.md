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

## [Optional] create public route to Canvas-Vault

for viewing the changes made by the privatevaultoperator a public route to the vault can be used 
(assumes nginx-ingress-controller and cermanager configured with LetsEncrypt):

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



## Deploy Private-Vault-Operator

```
helm upgrade --install privatevault-operator operators/privatevaultoperator-hc/helmcharts/pvop --namespace privatevault-system --create-namespace
```


## Test


### Example PrivateVaults

These privatevault crs would normally be deployed from the Component-Operator which extracts the corresponding section from the component.yaml.

```
kubectl apply -f test/privatevault-demoa-comp-one.yaml
kubectl apply -f test/privatevault-demob-comp-two.yaml
kubectl get privatevaults
```

### deploy demo components with "oda.tmforum.org/privatevault" annotation

```
helm upgrade --install demoa -n demo-comp --create-namespace test/helm-charts/demoa-comp-one
helm upgrade --install demob -n demo-comp --create-namespace test/helm-charts/demob-comp-two
helm upgrade --install democ -n demo-comp --create-namespace test/helm-charts/democ-comp-three
```

This deployment represents the deployments of three components "one", "two", "three".
Where component "one" has two PODs which want to access the privatevault.
Component "three" can be seen as an try to get illegal access to the privatevault of component "one".

the PODs of components "one" and "two" get the sidecar injected, 
while for component "three" the podSelector does not match and the sidecar is not injected.

Currently the pod-name selector is currently only validated inside the WebHook, 
while namespace and serviceaccount are validated in HashiCorp Vault auth.


### log into component demoa

```
kubectl exec -it -n demo-comp deployment/demo-comp-one-a -- /bin/sh
```

access private vault using localhost with create/read/update/delete

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

To test shared access create a secret:

```
curl -s -X "POST" -d "{\"key\":\"comp-one-secret\",\"value\":\"63H31M\"}" "http://localhost:5000/api/v3/secret" -H "accept: application/json" -H "Content-Type: application/json" 
curl -s -X GET http://localhost:5000/api/v3/secret/comp-one-secret -H "accept: application/json"
```

Now start a second shell in component one-b:

```
kubectl exec -it -n demo-comp deployment/demo-comp-one-b -- /bin/sh
```

and query for the secret created in component one-a:

```
curl -s -X GET http://localhost:5000/api/v3/secret/comp-one-secret -H "accept: application/json"

  {"key":"comp-one-secret","value":"63H31M"}
```

The secret is visbile here.
It can be set to another value and also is changed for component one-a.

Now let´s start a third shell in component two:

```
kubectl exec -it -n demo-comp deployment/demo-comp-two -- /bin/sh
```

again we query for the same secret:

```
curl -s -X GET http://localhost:5000/api/v3/secret/comp-one-secret -H "accept: application/json"

  ERROR 404: key not found
```

it is not there, because component two has another secret mount "demo-comp-124", while 
components one-a and one-b both use "demo-comp-123".


# Cleanup

```
kubectl apply -f test/privatevault-demoa-comp-one.yaml
kubectl apply -f test/privatevault-demob-comp-two.yaml
# if delete hangs (caused by errors in WebHook with retry), finalizer can be removed.
helm uninstall -n demo-comp demoa demob democ
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
