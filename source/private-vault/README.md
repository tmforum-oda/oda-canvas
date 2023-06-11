# Installations

## Install Private Vault Custom Resource Definition

```
helm upgrade --install oda-pv installation/oda-pv-crds --namespace oda-pv --create-namespace
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
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault secrets enable -version=2 -path=private-vault kv
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwtk8s jwt
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwtk8s/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-pv jwt
# kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-pv/config oidc_discovery_url=https://kubernetes.default.svc.cluster.local oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## DEBUG: create public route to Canvas-Vault

```
kubectl apply -f installation/canvas-vault-hc/public-route-for-testing.yaml
```

## Test


### Example PrivateVault

```
kubectl apply -f test/privatevault.yaml
kubectl get privatevaults
```


### local tests with Windows

```
set VAULT_ADDR=https://canvas-vault-hc.k8s.feri.ai
vault login
vault kv get -mount=secret -field=password demo
```


# Cleanup

```
helm uninstall -n demo-comp-123 demo-comp-123
helm uninstall -n canvas-vault canvas-vault-hc
kubectl delete -f installation/canvas-vault-hc/public-route-for-testing.yaml
helm uninstall -n oda-pv oda-pv
kubectl delete -f test/privatevault.yaml
kubectl delete ns oda-pv 
kubectl delete ns canvas-vault 
kubectl delete ns demo-comp-123
```