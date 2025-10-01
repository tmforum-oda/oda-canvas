# Deploy ComponentRegistry Helm Charts

```
cd C:\Users\A307131\git\oda-canvas
cd source/services/ComponentRegistry/component-registry-service
helm upgrade --install compreg-a -n compreg-a --create-namespace helm/component-registry
helm upgrade --install compreg-b -n compreg-b --create-namespace helm/component-registry
helm upgrade --install compreg-ab -n compreg-ab --create-namespace helm/component-registry
```


# Install collector

```
cd C:\Users\A307131\git\oda-canvas
cd source/services/ComponentRegistry/custom-resource-collector
helm upgrade --install collector-a -n compreg-a --create-namespace helm/custom-resource-collector --set=registryUrl=https://compreg-a.ihc-dt.cluster-2.de --set=registryExternalName=compreg-a --set=monitoredNamespaces=odacompns-a
helm upgrade --install collector-b -n compreg-b --create-namespace helm/custom-resource-collector --set=registryUrl=https://compreg-b.ihc-dt.cluster-2.de --set=registryExternalName=compreg-b --set=monitoredNamespaces=odacompns-b
```


# Components

## uninstall old Components

```
helm uninstall demo-a -n odacompns-a
helm uninstall demo-b -n odacompns-b
```

## deploy exposed api

```
cd C:\Users\A307131\git\oda-canvas
helm upgrade --install demo-a -n odacompns-a --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1
```

## query deployed services

```
curl -sX GET   https://canvas-info.ihc-dt.cluster-2.de/service -H "accept:application/json"   | jq -r ".[].id"
```

## deploy consumer (component with dependency to exposed api)

```
helm upgrade --install demo-b -n odacompns-b --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```


## configure upstream repo

in compreg-a

```
curl -X 'POST' \
  'https://compreg-a.ihc-dt.cluster-2.de/registries' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "compreg-ab",
  "url": "https://compreg-ab.ihc-dt.cluster-2.de",
  "type": "upstream",
  "labels": {
    "description": "Registry compreg-ab for Kubernetes ODA Components"
  }
}'
```

in compreg-b

```
curl -X 'POST' \
  'https://compreg-b.ihc-dt.cluster-2.de/registries' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "compreg-ab",
  "url": "https://compreg-ab.ihc-dt.cluster-2.de",
  "type": "upstream",
  "labels": {
    "description": "Registry compreg-ab for Kubernetes ODA Components"
  }
}'
```

in localhost

```
curl -X 'POST' \
  'http://localhost:8080/registries' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "compreg-ab",
  "url": "https://compreg-ab.ihc-dt.cluster-2.de",
  "type": "upstream",
  "labels": {
    "description": "Registry compreg-ab for Kubernetes ODA Components"
  }
}'
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





# Undeploy Component Registries

```
helm uninstall -n compreg-b collector-b
helm uninstall -n compreg-a collector-a

helm uninstall -n compreg-b compreg-b
helm uninstall -n compreg-a compreg-a

kubectl delete namespace compreg-b compreg-a
```

