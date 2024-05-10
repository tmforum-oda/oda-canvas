# Build

## Build Component Operator

```
cd ~
cd git/oda-canvas-component-vault_ODAA26
git pull
./TEMP/build/build-component-operator.sh
```

## Build ComponentVault Operator

```
cd ~
cd git/oda-canvas-component-vault_ODAA26
git pull
./TEMP/build/build-componentvault-operator.sh
```


## Build ComponentVault Sidecar

```
cd ~
cd git/oda-canvas-component-vault_ODAA26
git pull
./TEMP/build/build-componentvault-sidecar.sh
```



# deploy canvas from local filesystem 

```
cd ~/git/oda-canvas-component-vault-ODAA26
cd charts/cert-manager-init
helm dependency update
helm dependency build
cd ../../charts/controller
helm dependency update
helm dependency build
cd ../../charts/componentvault-operator
helm dependency update
helm dependency build
cd ../../charts/canvas-oda
helm dependency update
helm dependency build
cd ../..
helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP  --set=controller.configmap.loglevel=10 --set=controller.deployment.imagePullPolicy=Always --set=controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istiocontroller-0.4.0-compvault --set=componentvault-operator.logLevel=10
```

## patch api operator

```
kubectl patch configmap/canvas-controller-configmap -n canvas --type merge -p "{\"data\":{\"APIOPERATORISTIO_PUBLICHOSTNAME\":\"components.ihc-dt.cluster-3.de\"}}"
kubectl rollout restart deployment -n canvas oda-controller-ingress
```


## patch component gateway

```
kubectl edit gateway -n components component-gateway

...
spec:
  ...
  - hosts:
[*] - '*.ihc-dt.cluster-3.de'
...
[+++]
  - hosts:
    - '*.ihc-dt.cluster-3.de'
    port:
      name: https
      number: 443
      protocol: HTTPS
    tls:
      credentialName: wc-ihc-dt-cluster-3-de-tls
      mode: SIMPLE
```


# install HashiCorp vault

with WSL:

```
TEMP/installation/setup_CanvasVault.sh
```

with Windows:

```
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc --namespace canvas-vault --create-namespace --version 0.28.0 --values TEMP/installation/canvas-vault-hc/values.yaml hashicorp/vault --wait 

kubectl apply -f TEMP\installation\canvas-vault-hc\canvas-vault-hc-vs-GCP.yaml

kubectl exec -n canvas-vault canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-cv jwt

kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated

kubectl get --raw /.well-known/openid-configuration
set ISSUER=https://container.googleapis.com/v1/projects/tmforum-oda-component-cluster/locations/europe-west3/clusters/ihc-dt
echo "ISSUER=%ISSUER%"
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-cv/config oidc_discovery_url=%ISSUER% 
```




## Deploy Component with component vault

```
helm upgrade --install prodcat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1beta3-compvault
```


# Uninstall

## Undeploy Component PRODCAT

```
helm uninstall prodcat -n components
```

# ComponentVault Operator

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

kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated

echo "wait 15 seconds for Vault to startup"
sleep 15

kubectl exec -n canvas-vault canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-cv jwt
# see: https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes#using-service-account-issuer-discovery

ISSUER="$(kubectl get --raw /.well-known/openid-configuration | jq -r '.issuer')"
echo "ISSUER=$ISSUER"
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-cv/config oidc_discovery_url=$ISSUER oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```


### install Vault WIN

```
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install canvas-vault-hc --namespace canvas-vault --create-namespace --version 0.28.0 --values TEMP/canvas-vault/values.yaml hashicorp/vault --wait 

kubectl apply -n canvas-vault -f TEMP/canvas-vault/canvas-vault-hc-vs-VPS2.yaml

kubectl create clusterrolebinding oidc-reviewer  --clusterrole=system:service-account-issuer-discovery --group=system:unauthenticated

kubectl exec -n canvas-vault canvas-vault-hc-0 -- vault auth enable -path jwt-k8s-cv jwt
set ISSUER=https://kubernetes.default.svc.cluster.local
kubectl exec -n canvas-vault -it canvas-vault-hc-0 -- vault write auth/jwt-k8s-cv/config oidc_discovery_url=%ISSUER% oidc_discovery_ca_pem=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

## uninstall Vault

```
helm uninstall -n canvas-vault canvas-vault-hc
kubectl delete -n canvas-vault -f TEMP/canvas-vault/canvas-vault-hc-vs.yaml
kubectl delete clusterrolebinding oidc-reviewer  
kubectl delete ns canvas-vault
```
