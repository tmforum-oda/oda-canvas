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
# kubectl apply -f installation/canvas-vault-hc/public-route-for-testing.yaml
kubectl apply -f installation/canvas-vault-hc/canvas-vault-hc-vs.yaml

```

## Configure HashiCorp Vault to accept Kubernetes SerciceAccount Issuer

```
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-pv jwt
sleep 2

# https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes#using-service-account-issuer-discovery
kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated

kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-pv/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## KOPF crds

if the crds or peering crs are already installed the corresponing helm chart will fail with "resource already exists", which is fine.

```
helm upgrade --install kopf-framework-crds operators/privatevaultoperator-hc/helmcharts/kopf-framework-crds --namespace privatevault-system --create-namespace
helm upgrade --install kopf-framework operators/privatevaultoperator-hc/helmcharts/kopf-framework --namespace privatevault-system --create-namespace
```



## Deploy Private-Vault-Operator

```
helm upgrade --install privatevault-operator operators/privatevaultoperator-hc/helmcharts/cvop --namespace privatevault-system --create-namespace
```


## Test


### Example PrivateVaults

These privatevault crs would normally be deployed from the Component-Operator which extracts the corresponding section from the component.yaml.

```
kubectl apply -f test/privatevault-demoa-comp-one.yaml
kubectl apply -f test/privatevault-demob-comp-two.yaml
kubectl get privatevaults -A
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
kubectl exec -it -n demo-comp deployment/demoa-comp-one-sender -- /bin/sh
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
kubectl exec -it -n demo-comp deployment/demoa-comp-one-receiver -- /bin/sh
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
kubectl exec -it -n demo-comp deployment/demob-comp-two -- /bin/sh
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
kubectl delete -f test/privatevault-demoa-comp-one.yaml
kubectl delete -f test/privatevault-demob-comp-two.yaml
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


# Windows CLI

```
set VAULT_ADDR=https://canvas-vault-hc.k8s.cluster3.de
vault login
```

# Troubleshooting

two kopf hooks blocking each other

```
[2023-08-27 18:44:12,991] kopf._core.engines.a [INFO    ] Initial authentication has finished.
[2023-08-27 18:44:13,249] kopf._cogs.clients.w [DEBUG   ] Starting the watch-stream for customresourcedefinitions.v1.apiextensions.k8s.io cluster-wide.
[2023-08-27 18:44:13,253] kopf._kits.webhooks  [DEBUG   ] Generating a self-signed certificate for HTTPS.
[2023-08-27 18:44:13,812] kopf._cogs.clients.w [DEBUG   ] Starting the watch-stream for clusterkopfpeerings.v1.zalando.org cluster-wide.
[2023-08-27 18:44:13,820] kopf._cogs.clients.w [DEBUG   ] Starting the watch-stream for privatevaults.v1alpha1.oda.tmforum.org cluster-wide.
[2023-08-27 18:44:13,885] kopf._core.engines.p [DEBUG   ] Keep-alive in 'default' cluster-wide: ok.
[2023-08-27 18:44:13,887] kopf._kits.webhooks  [DEBUG   ] Listening for webhooks at https://*:9443
[2023-08-27 18:44:13,887] kopf._kits.webhooks  [DEBUG   ] Accessing the webhooks at https://privatevault-operator-svc.privatevault-system.svc:9443
[2023-08-27 18:44:13,888] kopf._core.engines.a [INFO    ] Reconfiguring the validating webhook pv.sidecar.kopf.
[2023-08-27 18:44:13,893] kopf._core.engines.a [INFO    ] Reconfiguring the mutating webhook pv.sidecar.kopf.
[2023-08-27 18:44:22,742] kopf._core.engines.p [INFO    ] Pausing operations in favour of [<Peer root@overcommit-operator-7d444b7477-mm9bz/20230818225741/3uz: priority=100, lifetime=60, lastseen='2023-08-27T18:44:22.622240'>].
[2023-08-27 18:44:22,843] kopf._cogs.clients.w [DEBUG   ] Pausing the watch-stream for privatevaults.v1alpha1.oda.tmforum.org cluster-wide (blockers: default@None).
```

https://github.com/nolar/kopf/issues/734

## solution

use different peering names and not default.

