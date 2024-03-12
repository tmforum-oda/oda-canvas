# Current tests

## Canvas

### deploy Canvas from modified charts

```
helm dependency update charts/cert-manager-init
helm dependency update charts/canvas-oda

# helm upgrade --install canvas -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set controller.deployment.compconImage=mtr.devops.telekom.de/magenta_canvas/public:component-istio-controller-0.4.0-compvault --set controller.deployment.imagePullPolicy=Always --set=controller.configmap.loglevel=10 --values=source/component-vault/custom/virtualservices/component-gateway-tls-values.yaml charts/canvas-oda

helm upgrade --install canvas -n canvas --create-namespace --values source/component-vault/custom/patched-oda-canvas/values.yaml charts/canvas-oda
```

### deploy Canvas from public charts

```
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update

helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set=controller.configmap.loglevel=10
```

### uninstall Canavs

```
helm uninstall canvas -n canvas 
```

## ODA Component ProducCatalogManagement

### install prodcat component with component vault

```
helm upgrade --install prodcat -n components --create-namespace source/component-vault/custom/productcatalog-v1beta3-compvault
```

### install public prodcat component 

```
helm repo add oda-components https://tmforum-oda.github.io/reference-example-components
helm repo update
helm install prodcat -n components --create-namespace oda-components/productcatalog
```

### uninstall prodcat component 

```
helm uninstall prodcat -n components 
```

# Deploy ComponentVault Operator

```
helm upgrade --install componentvault-operator -n canvas --create-namespace source/component-vault/operators/componentvaultoperator-hc/helmcharts/cvop
```