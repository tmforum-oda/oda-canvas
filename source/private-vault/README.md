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

## Configure HashiCorp Vault to accept Kubernetes SerciceAccount Issuer

```
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-pv jwt
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-pv/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## DEBUG: create public route to Canvas-Vault

```
kubectl apply -f installation/canvas-vault-hc/public-route-for-testing.yaml
```


## Private-Vault-Operator

```
helm upgrade --install pvop operators/privatevaultoperator-hc/helmcharts/pvop --namespace privatevault-system --create-namespace
```


## Test


### Example PrivateVault

```
kubectl apply -f test/privatevault.yaml
kubectl get privatevaults
```

### test sidecar

```
helm upgrade --install demo-comp-123 test/helm-charts/democomp -n demo-comp-123 --create-namespace
```



### local tests with Windows

```
set VAULT_ADDR=https://canvas-vault-hc.k8s.feri.ai
vault login
vault kv get -mount=secret -field=password demo
```


# Cleanup

```
kubectl delete -f test/privatevault.yaml
helm uninstall -n demo-comp-123 demo-comp-123
kubectl delete -f installation/canvas-vault-hc/public-route-for-testing.yaml
helm uninstall -n canvas-vault canvas-vault-hc
helm uninstall -n privatevault-system oda-pv-crd
helm uninstall -n privatevault-system pvop 
helm uninstall -n privatevault-system kopf-framework 
kubectl delete ns demo-comp-123
kubectl delete ns canvas-vault 
kubectl delete ns privatevault-system 
```
