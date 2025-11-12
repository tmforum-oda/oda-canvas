# Deploy ComponentRegistry Helm Charts


## set env

Green

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-a
tmfihcdta
```

Magenta

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-b
tmfihcdtb
```

Blue

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt
tmfihcdt
```


## deploy global compreg:

```
set DOMAIN=ihc-dt.cluster-2.de
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service
helm upgrade --install global-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 

```

```
cd C:\Users\A307131\git\oda-canvas
cd source/services/ComponentRegistry/component-registry-service
helm upgrade --install compreg-a -n compreg-a --create-namespace helm/component-registry
helm upgrade --install compreg-b -n compreg-b --create-namespace helm/component-registry
helm upgrade --install compreg-ab -n compreg-ab --create-namespace helm/component-registry
helm upgrade --install compreg-abup -n compreg-abup --create-namespace helm/component-registry

```


# configure upstream repos

## compreg-a, compreg-b, compreg-ab

```
curl -X 'POST' \
  'https://compreg-a.ihc-dt.cluster-2.de/registries/upstream-from-url' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://compreg-ab.ihc-dt.cluster-2.de"}'

curl -X 'POST' \
  'https://compreg-b.ihc-dt.cluster-2.de/registries/upstream-from-url' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://compreg-ab.ihc-dt.cluster-2.de"}'

curl -X 'POST' \
  'https://compreg-ab.ihc-dt.cluster-2.de/registries/upstream-from-url' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://compreg-abup.ihc-dt.cluster-2.de"}'

```

for windows:



```
curl -X POST https://compreg.ihc-dt.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json"  -d "{\"url\": \"https://global-compreg.ihc-dt.cluster-2.de\"}"
curl -X POST https://compreg.ihc-dt-b.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json"  -d "{\"url\": \"https://global-compreg.ihc-dt.cluster-2.de\"}"
```

```
curl -X POST https://compreg-a.ihc-dt.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json"  -d "{\"url\": \"https://compreg-ab.ihc-dt.cluster-2.de\"}"

curl -X POST https://compreg-b.ihc-dt.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json"  -d "{\"url\": \"https://compreg-ab.ihc-dt.cluster-2.de\"}"

curl -X POST https://compreg-ab.ihc-dt.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json"  -d "{\"url\": \"https://compreg-abup.ihc-dt.cluster-2.de\"}"

```
  



# Install collectors

```
cd C:\Users\A307131\git\oda-canvas
cd source/services/ComponentRegistry/custom-resource-collector
helm upgrade --install collector -n canvas --create-namespace helm/custom-resource-collector 


helm upgrade --install collector-a -n compreg-a --create-namespace helm/custom-resource-collector --set=registryUrl=https://compreg-a.ihc-dt.cluster-2.de --set=registryExternalName=compreg-a --set=monitoredNamespaces=components
helm upgrade --install collector-b -n compreg-b --create-namespace helm/custom-resource-collector --set=registryUrl=https://compreg-b.ihc-dt.cluster-2.de --set=registryExternalName=compreg-b --set=monitoredNamespaces=components

```


# Components

## uninstall old Components

```
helm uninstall -n components r-cat
helm uninstall -n components f-cat
```


# From BDD UC007-F002 (inst) - Configure DependentAPI for single downstream productcatalog component

```
Scenario Outline: Configure DependentAPI for single downstream productcatalog component
  # Install a downstream retail productcatalog component as release r-cat
  Given I install the 'productcatalog-v1' package as release 'r-cat'
  And the 'productcatalogmanagement' component has a deployment status of 'Complete'
  And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway
  # Install the federated productcatalog component that has a dependency on a downstream  productcatalog as release f-cat
  When I install the 'productcatalog-dependendent-API-v1' package as release 'f-cat'
  Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'productcatalogmanagement' component with a ready status
  And the 'productcatalogmanagement' component has a deployment status of 'Complete'
```

## Install a downstream retail productcatalog component as release r-cat

Given I install the 'productcatalog-v1' package as release 'r-cat'

```
cd C:\Users\A307131\git\oda-canvas
helm upgrade --install r-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1

  Release "r-cat" does not exist. Installing it now.
  NAME: r-cat
  LAST DEPLOYED: Sat Oct  4 17:44:05 2025
  NAMESPACE: components
  STATUS: deployed
  REVISION: 1
  TEST SUITE: None
```

And the 'productcatalogmanagement' component has a deployment status of 'Complete'

```
kubectl get component r-cat-productcatalogmanagement -n components

  NAMESPACE     NAME                             DEPLOYMENT_STATUS
  components   r-cat-productcatalogmanagement   Complete
```

And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

```
kubectl get exposedapi -n components

  NAME                                                      API_ENDPOINT                                                                                                IMPLEMENTATION_READY
  r-cat-productcatalogmanagement-metrics                    https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/metrics                               true
  r-cat-productcatalogmanagement-partyrole                  https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/partyRoleManagement/v4        true
  r-cat-productcatalogmanagement-productcatalogmanagement   https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4   true
```


## Install the federated productcatalog component that has a dependency on a downstream  productcatalog as release f-cat

When I install the 'productcatalog-dependendent-API-v1' package as release 'f-cat'

```
cd C:\Users\A307131\git\oda-canvas
helm upgrade --install f-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1

  Release "f-cat" does not exist. Installing it now.
  NAME: f-cat
  LAST DEPLOYED: Sat Oct  4 20:52:52 2025
  NAMESPACE: components
  STATUS: deployed
  REVISION: 1
  TEST SUITE: None
```


Then I should see the 'downstreamproductcatalog' DependentAPI resource on the 'productcatalogmanagement' component with a ready status

```
kubectl get depapis -n components   f-cat-productcatalogmanagement-downstreamproductcatalog

  NAMESPACE     NAME                                                      READY   AGE   SVCINVID                               URL
  components   f-cat-productcatalogmanagement-downstreamproductcatalog   true    53s   0e16d068-fc39-4cf5-80a0-5e5826b02d10   https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

And the 'productcatalogmanagement' component has a deployment status of 'Complete'

```
kubectl get components -n components   f-cat-productcatalogmanagement

  NAME                             DEPLOYMENT_STATUS
  f-cat-productcatalogmanagement   Complete
```


# From BDD UC007-F002 (data) - Populate and verify data in federated product catalog

```
Scenario Outline: Populate and verify data in federated product catalog
  # Populate the retail product catalog with sample data
  Given the 'productcatalogmanagement' component in the 'r-cat' release has the following 'category' data:
    | name                      | description                                       |
    | Internet line of product  | Fiber and ADSL broadband products                 |
    | Mobile line of product    | Mobile phones and packages                        |
    | IoT line of product       | IoT devices and solutions                         |
  # Verify that the federated product catalog exposes the populated catalogs
  When I query the 'productcatalogmanagement' component in the 'f-cat' release for 'category' data:
  Then I should see the following 'category' data in the federated product catalog:
    | name                      | description                                       |
    | Internet line of product  | Fiber and ADSL broadband products                 |
    | Mobile line of product    | Mobile phones and packages                        |
    | IoT line of product       | IoT devices and solutions                         |   
```

## Populate the retail product catalog with sample data

Given the 'productcatalogmanagement' component in the 'r-cat' release has the following 'category' data:

| name                      | description                                       |
| ------------------------- | ------------------------------------------------- |
| Internet line of product  | Fiber and ADSL broadband products                 |
| Mobile line of product    | Mobile phones and packages                        |
| IoT line of product       | IoT devices and solutions                         |

```
curl -X POST "http://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" \
     -H  "accept: application/json;charset=utf-8" \
     -H  "Content-Type: application/json;charset=utf-8" \
     -d "{  \"name\": \"Internet line of product\",  \"description\": \"Fiber and ADSL broadband products\"  }"

curl -X POST "http://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" \
     -H  "accept: application/json;charset=utf-8" \
     -H  "Content-Type: application/json;charset=utf-8" \
     -d "{  \"name\": \"Mobile line of product\",  \"description\": \"Mobile phones and packages\"  }"

curl -X POST "http://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" \
     -H  "accept: application/json;charset=utf-8" \
     -H  "Content-Type: application/json;charset=utf-8" \
     -d "{  \"name\": \"IoT line of product\",  \"description\": \"IoT devices and solutions\"  }"
```


##  Verify that the federated product catalog exposes the populated catalogs

When I query the 'productcatalogmanagement' component in the 'f-cat' release for 'category' data:  
Then I should see the following 'category' data in the federated product catalog:
  
| name                      | description                                       |
| ------------------------- | ------------------------------------------------- |
| Internet line of product  | Fiber and ADSL broadband products                 |
| Mobile line of product    | Mobile phones and packages                        |
| IoT line of product       | IoT devices and solutions                         |   

```
curl -X GET "http://components.ihc-dt.cluster-2.de/f-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" | jq .
```


# show access of r-cat in f-cat logs:

```
kubectl logs deployment/f-cat-prodcatapi -n components

  ...
  listCategory :: GET /f-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category components.ihc-dt.cluster-2.de
  utils/downstreamAPI/listFromDownstreamAPI :: resourceType =  category
  utils/downstreamAPI/getDownstreamAPIs :: returning 1 downstream APIs
  utils/downstreamAPI/listFromDownstreamAPI :: getting data from downstream API at https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category
  utils/downstreamAPI/listFromDownstreamAPI :: received 5 records
```




## query r-cat categories

```
curl -X GET "http://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8"
```

## query f-cat categories

```
curl -X GET "http://components.ihc-dt.cluster-2.de/f-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8"
```


## 

productcatalog-dependendent-API-v1


{
  "description": "Fiber and ADSL broadband products",
  "name": "Internet line of product"
}

curl -X POST "http://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" -H  "Content-Type: application/json;charset=utf-8" -d "{  \"description\": \"Fiber and ADSL broadband products\",  \"name\": \"Internet line of product\"}"


# Manual tests

## deploy exposed api

```
cd C:\Users\A307131\git\oda-canvas
helm upgrade --install demo-a -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1
```

## query deployed services

```
curl -sX GET   https://canvas-info.ihc-dt.cluster-2.de/service -H "accept:application/json"   | jq -r ".[].id"
```

## deploy consumer (component with dependency to exposed api)

```
helm upgrade --install demo-b -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```



## look dependentapi custom resource

```
kubectl get dependentapis -n components

  NAME                                                           READY   AGE     SVCINVID                               URL
  testdapi-productcatalogmanagement-downstreamproductcatalog     true    5m33s   3b8b010d-d8d0-410e-a256-0afdf84158f8   http://components.ihc-dt.cluster-2.de/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

## query deployed services

```
curl -sX 'GET'   'https://canvas-info.ihc-dt.cluster-2.de/tmf-api/serviceInventoryManagement/v5/service'   -H 'accept: application/json' | jq -r '.[].id'

  3b8b010d-d8d0-410e-a256-0afdf84158f8
```

## Logfile of DependentAPI Operator

```
$ kubectl logs -n canvas deployment/canvas-depapi-op
[2024-09-18 07:50:12,473] DependentApiSimpleOp [INFO    ] Logging set to 20
[2024-09-18 07:50:12,474] DependentApiSimpleOp [INFO    ] CICD_BUILD_TIME=2024-09-18T07:47:18+00:00
[2024-09-18 07:50:12,474] DependentApiSimpleOp [INFO    ] GIT_COMMIT_SHA=94f63d1
[2024-09-18 07:50:12,474] DependentApiSimpleOp [INFO    ] CANVAS_INFO_ENDPOINT=http://info.canvas.svc.cluster.local/tmf-api/serviceInventoryManagement/v5
...
[2024-09-18 09:54:37,370] DependentApiSimpleOp [INFO    ] Create/Update  called with name testdapi-productcatalogmanagement-downstreamproductcatalog in namespace components
[2024-09-18 09:54:37,497] DependentApiSimpleOp [INFO    ] setting implementation status to ready for dependent api components:testdapi-productcatalogmanagement-downstreamproductcatalog
[2024-09-18 09:54:37,649] DependentApiSimpleOp [INFO    ] ServiceInventory: created 3b8b010d-d8d0-410e-a256-0afdf84158f8
[2024-09-18 09:54:37,666] kopf.objects         [INFO    ] [components/testdapi-productcatalogmanagement-downstreamproductcatalog] Handler 'dependentApiCreate' succeeded.
[2024-09-18 09:54:37,667] kopf.objects         [INFO    ] [components/testdapi-productcatalogmanagement-downstreamproductcatalog] Creation is processed: 1 succeeded; 0 failed.
```

## undeploy consumer

```
helm uninstall -n components demo-b
```


### Logfile

```
[2024-09-18 09:55:42,651] DependentApiSimpleOp [INFO    ] Delete         called with name testdapi-productcatalogmanagement-downstreamproductcatalog in namespace components
[2024-09-18 09:55:42,674] DependentApiSimpleOp [INFO    ] deleted ServiceInventory entry: 3b8b010d-d8d0-410e-a256-0afdf84158f8
[2024-09-18 09:55:42,675] kopf.objects         [INFO    ] [components/testdapi-productcatalogmanagement-downstreamproductcatalog] Handler 'dependentApiDelete' succeeded.
[2024-09-18 09:55:42,675] kopf.objects         [INFO    ] [components/testdapi-productcatalogmanagement-downstreamproductcatalog] Deletion is processed: 1 succeeded; 0 failed.
```


## query deployed services

```
curl -sX GET   https://canvas-info.ihc-dt.cluster-2.de/service -H "accept:application/json"   | jq -r ".[].id"
```





# update canvas WINDOWS

```
set DOMAIN=ihc-dt-a.cluster-2.de
set COMPREG_EXTNAME=compreg-a

set DOMAIN=ihc-dt-b.cluster-2.de
set COMPREG_EXTNAME=compreg-b


cd %USERPROFILE%/git/oda-canvas

set TLS_SECRET_NAME=domain-tls-secret

helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm dependency update ./charts/cert-manager-init
helm dependency update ./charts/kong-gateway
helm dependency update ./charts/apisix-gateway
helm dependency update ./charts/canvas-vault
helm dependency update ./charts/pdb-management-operator
helm dependency update ./charts/canvas-oda

helm dependency update --skip-refresh ./charts/cert-manager-init
helm dependency update --skip-refresh ./charts/kong-gateway
helm dependency update --skip-refresh ./charts/apisix-gateway
helm dependency update --skip-refresh ./charts/canvas-vault
helm dependency update --skip-refresh ./charts/pdb-management-operator
helm dependency update --skip-refresh ./charts/canvas-oda

helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set api-operator-istio.deployment.hostName=*.%DOMAIN% --set api-operator-istio.deployment.credentialName=%TLS_SECRET_NAME% --set api-operator-istio.configmap.publicHostname=components.%DOMAIN% --set=api-operator-istio.deployment.httpsRedirect=false --set=canvas-info-service.serverUrl=https://canvas-info.%DOMAIN%  --set=keycloak.keycloakConfigCli.image.repository=bitnamilegacy/keycloak-config-cli --set=component-registry.externalName=%COMPREG_EXTNAME%  --set=component-registry.domain=%DOMAIN% --set=resource-inventory.serviceType=ClusterIP


helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set api-operator-istio.deployment.hostName=*.%DOMAIN% --set api-operator-istio.deployment.credentialName=%TLS_SECRET_NAME% --set api-operator-istio.configmap.publicHostname=components.%DOMAIN% --set=api-operator-istio.deployment.httpsRedirect=false --set=canvas-info-service.serverUrl=https://canvas-info.%DOMAIN%  --set=component-registry.ownRegistryName=%COMPREG_EXTNAME%  --set=component-registry.domain=%DOMAIN% --set=resource-inventory.serviceType=ClusterIP --set=resource-inventory.serverUrl=https://canvas-resource-inventory.%DOMAIN%/tmf-api/resourceInventoryManagement/v5
```

optional install canvas-vs

```
helm upgrade --install -n canvas canvas-vs %USERPROFILE%/git/oda-canvas-notes/virtualservices/canvas --set=domain=%DOMAIN%  

```

## Linux

```
cd ~/git/oda-canvas

export TLS_SECRET_NAME=domain-tls-secret

export DOMAIN=ihc-dt.cluster-2.de
export COMPREG_EXTNAME=compreg-a

export DOMAIN=ihc-dt-a.cluster-2.de
export COMPREG_EXTNAME=compreg-a

export DOMAIN=ihc-dt-b.cluster-2.de
export COMPREG_EXTNAME=compreg-b

helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm dependency update ./charts/cert-manager-init
helm dependency update ./charts/kong-gateway
helm dependency update ./charts/apisix-gateway
helm dependency update ./charts/canvas-vault
helm dependency update ./charts/pdb-management-operator
helm dependency update ./charts/canvas-oda

helm dependency update --skip-refresh ./charts/cert-manager-init
helm dependency update --skip-refresh ./charts/kong-gateway
helm dependency update --skip-refresh ./charts/apisix-gateway
helm dependency update --skip-refresh ./charts/canvas-vault
helm dependency update --skip-refresh ./charts/pdb-management-operator
helm dependency update --skip-refresh ./charts/canvas-oda

helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set api-operator-istio.deployment.hostName=*.$DOMAIN --set api-operator-istio.deployment.credentialName=$TLS_SECRET_NAME --set api-operator-istio.configmap.publicHostname=components.$DOMAIN --set=api-operator-istio.deployment.httpsRedirect=false --set=canvas-info-service.serverUrl=https://canvas-info.$DOMAIN  --set=keycloak.keycloakConfigCli.image.repository=bitnamilegacy/keycloak-config-cli --set=component-registry.externalName=$COMPREG_EXTNAME --set=component-registry.domain=$DOMAIN --set=resource-inventory.serviceType=ClusterIP

```

canvas-vs

```
helm upgrade --install -n canvas canvas-vs ~/git/oda-canvas-notes/virtualservices/canvas --set=domain=$DOMAIN
```






# Undeploy Component Registries

```
helm uninstall -n compreg-b collector-b
helm uninstall -n compreg-a collector-a

helm uninstall -n compreg-abup compreg-abup
helm uninstall -n compreg-ab compreg-ab
helm uninstall -n compreg-b compreg-b
helm uninstall -n compreg-a compreg-a

kubectl delete namespace compreg-abup compreg-ab compreg-b compreg-a

```

