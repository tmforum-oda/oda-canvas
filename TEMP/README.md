# Build Component-Operator

```
./TEMP/build/build-component-operator.sh
```

Image: `mtr.devops.telekom.de/magenta_canvas/public:component-istiocontroller-0.4.0-compvault`

# deploy patched canvas from local filesystem 

```
cd ~/git/oda-canvas-component-vault-ODAA26
cd charts/cert-manager-init
helm dependency update
helm dependency build
cd ../../charts/controller
helm dependency update
helm dependency build
cd ../../charts/canvas-oda
helm dependency update
helm dependency build
cd ../..
helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set=controller.configmap.loglevel=10 --set=controller.deployment.imagePullPolicy=Always
```

# product catalog with component vault

## deploy PRODCAT

```
helm upgrade --install prodcat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1beta3-compvault
```

## undeploy PRODCAT

```
helm uninstall prodcat -n components 
```

# ComponentVault Operator

## build ComponentVault Operator

```
cd ./git/oda-canvas-component-vault-ODAA26
git pull
./source/operators/componentvaultoperator-hc/docker/build.sh
```

## deploy ComponentVault Operator

```
helm upgrade --install componentvault-operator -n canvas --create-namespace --set=logLevel=10 source/operators/componentvaultoperator-hc/helmcharts/cvop
```


## undeploy ComponentVault Operator

```
helm uninstall -n canvas componentvault-operator
```

# HashiCorp Vault

## install Vault

```
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc --namespace canvas-vault --create-namespace --version 0.28.0 --values TEMP/canvas-vault/values.yaml hashicorp/vault --wait 

kubectl apply -n canvas-vault -f TEMP/canvas-vault/canvas-vault-hc-vs.yaml

kubectl exec -n canvas-vault canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-cv jwt
# see: https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes#using-service-account-issuer-discovery
kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated
```


### install Vault WIN

```
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc --namespace canvas-vault --create-namespace --version 0.28.0 --values TEMP/canvas-vault/values.yaml hashicorp/vault --wait 

kubectl apply -n canvas-vault -f TEMP/canvas-vault/canvas-vault-hc-vs-VPS2.yaml

kubectl exec -n canvas-vault canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-cv jwt
set ISSUER=https://kubernetes.default.svc.cluster.local
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-cv/config oidc_discovery_url=%ISSUER% oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```
## uninstall Vault

```
helm uninstall -n canvas-vault canvas-vault-hc
kubectl delete -n canvas-vault -f TEMP/canvas-vault/canvas-vault-hc-vs.yaml
kubectl delete ns canvas-vault
```
