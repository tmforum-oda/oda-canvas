# Current tests

## DEMO

### set default namespace to "components"

```
kubectl config set-context --current --namespace=components
```

### open CMD with componentoperator logfile

```
kubectl logs -n canvas deployment/componentvault-operator --tail 1 -f
```

### show empty HashiCorp Vault GUI


https://canvas-vault-hc.ihc-dt.cluster-3.de


### PPT Folie xxx

Explain what will be done next.


### deploy demo-a

```
cd git/oda-canvas-component-vault
helm upgrade --install demo-a -n components --create-namespace source/component-vault/custom/productcatalog-v1beta3-compvault
```

### show HashiCorp Vault GUI


### restart prodcatapi

```
kubectl rollout restart deployment demo-a-prodcatapi
```

(15 sec to start sidecar)

### conenct to prodcatapi shell 

```
kubectl get pods

kubectl exec -it demo-a-prodcatapi-XXXXXXXXXXXXXX -- /bin/bash
```

### Open Swagger GUI

https://developer.telekom.de/swagger-editor/

--> Create Secret as CURL

```
curl -X 'POST' \
  'http://127.0.0.1:5000/secret' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "key": "password",
  "value": "H37c5bza+d9.de89"
}'
```

### paste into demo-a

### Open Swagger GUI

show new password

--> get Secret as cURL

### paste into demo-a

### start second instance

cmd window sbottom right

```
kubectl scale deployment demo-a-prodcatapi --replicas=2
```

(15 sec)

connect to second instance

```
kubectl get pods

kubectl exec -it demo-a-prodcatapi-XXXXXXXXXXXXXX -- /bin/bash
```

### copy curl command from swagger

### paste into 2nd demo-a window

### close demo-a window, start new cmd bottom right

### install demo-b

```
cd git/oda-canvas-component-vault
helm upgrade --install demo-b -n components --create-namespace source/component-vault/custom/productcatalog-v1beta3-compvault
```

### restart demo-b prodcatapi 

```
kubectl rollout restart deployment demo-b-prodcatapi
```

### log into demo-b prodcatapi

```
kubectl get pods

kubectl exec -it demo-a-prodcatapi-XXXXXXXXXXXXXX -- /bin/bash
```

### copy curl from swagger

### explain X in PPT

### copy CREATE curl from swagger with other value

### curl with get (arrow-up)

### Explain demo-b arrow to own componentvault

### in demo-a curl with get --> other value

### open Vault, show new password


## undepoly demo-a

```
helm uninstall demo-a
```

--> show componentvault logs

--> show in HC Vault







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

# ComponentVault Operator

## deploy ComponentVault Operator

```
helm upgrade --install componentvault-operator -n canvas --create-namespace source/component-vault/operators/componentvaultoperator-hc/helmcharts/cvop
```


## undeploy ComponentVault Operator

```
helm uninstall -n canvas componentvault-operator
```
