# Current tests

## DEMO

Recorded session for DTW Tour Asia (Mumbai):

https://tmf365.sharepoint.com/:v:/r/sites/InnovationHubODAAcceleratorproject/Shared%20Documents/01%20-%20Recordings%20-%20DTW%20Tour%20Asia%20(Mumbai)/ODAA-26_ComponentVault_Showcase.mp4?csf=1&web=1&e=z0hAEf&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D


### set default namespace to "components"

```
kubectl config set-context --current --namespace=components
```

### open CMD with Component-Operator logfile

```
kubectl logs -n canvas deployment/oda-controller-ingress -f
```

### open CMD with ComponentVault-Operator logfile

```
kubectl logs -n canvas deployment/canvas-compvaultop -f
```

### show empty HashiCorp Vault GUI


https://canvas-vault-hc.ihc-dt.cluster-3.de


### PPT Folie xxx

Explain what will be done next.


### deploy demo-a

```
helm upgrade --install demo-a -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1beta3-compvault
```

### show HashiCorp Vault GUI


### conenct to prodcatapi shell 

```
kubectl get pods
PRODCATAPI_POD=$(kubectl get pods -limpl=demo-a-prodcatapi -o=jsonpath="{.items[*].metadata.name}")
echo $PRODCATAPI_POD
kubectl exec -it $PRODCATAPI_POD -- /bin/bash
```

### Open Swagger GUI

https://developer.telekom.de/swagger-editor/

swagger file: https://raw.githubusercontent.com/ODA-CANVAS-FORK/oda-canvas-component-vault/odaa-26/TEMP/swagger/openapi.yaml


--> Create Secret as CURL

```
curl -X 'POST' \
  'http://localhost:5000/api/v3/secret' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "key": "db-password",
  "value": "H37c5bza+d9.de89"
}'
```

### paste into demo-a

### Open Swagger GUI

show new password

--> get Secret as cURL

```
curl -X 'GET' \
  'http://localhost:5000/api/v3/secret/db-password' \
  -H 'accept: application/json'
```

```
{"key":"db-password","value":"H37c5bza+d9.de89"}
```

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

```
curl -X 'GET' \
  'http://localhost:5000/api/v3/secret/db-password' \
  -H 'accept: application/json'
```

```
{"key":"db-password","value":"H37c5bza+d9.de89"}
```


### paste into 2nd demo-a window

### close demo-a window, start new cmd bottom right

### install demo-b

```
cd git/oda-canvas-component-vault-ODAA26
helm upgrade --install demo-b -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1beta3-compvault
```

### log into demo-b prodcatapi

```
kubectl get pods
PRODCATAPI_B_POD=$(kubectl get pods -limpl=demo-b-prodcatapi -o=jsonpath="{.items[*].metadata.name}")
echo $PRODCATAPI_B_POD
kubectl exec -it $PRODCATAPI_B_POD -- /bin/bash
```

### copy curl from swagger


```
curl -X 'GET' \
  'http://localhost:5000/api/v3/secret/db-password' \
  -H 'accept: application/json'
```

```
ERROR 404: key not found
```


### explain X in PPT

### copy CREATE curl from swagger with other value

```
curl -X 'POST' \
  'http://localhost:5000/api/v3/secret' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "key": "db-password",
  "value": "DemoBPassword"
}'
```

### curl with get (arrow-up)

```
curl -X 'GET' \
  'http://localhost:5000/api/v3/secret/db-password' \
  -H 'accept: application/json'
```

```
{"key":"db-password","value":"DemoBPassword"}
```

### Explain demo-b arrow to own componentvault

### in demo-a curl with get --> other value

```
curl -X 'GET' \
  'http://localhost:5000/api/v3/secret/db-password' \
  -H 'accept: application/json'
```

```
{"key":"db-password","value":"H37c5bza+d9.de89"}
```

### open Vault, show new password



## undepoly demo-a

```
helm uninstall demo-a
```

--> show componentvault logs

--> show in HC Vault


## [optional]

show logs of cvsidcar

```
PRODCATAPI_B_POD=$(kubectl get pods -limpl=demo-b-prodcatapi -o=jsonpath="{.items[*].metadata.name}")
kubectl logs $PRODCATAPI_B_POD cvsidecar
```
