# Deploy ComponentRegistry Helm Charts

```
cd fastapi-microservice
helm upgrade --install compreg -n compreg --create-namespace helm/component-registry
```

# run local tests


configure .env file

```
#COMPONENT_REGISTRY_URL=http://localhost:8000
COMPONENT_REGISTRY_URL=https://compreg.ihc-dt.cluster-2.de

# for local tests with proxy
K8S_PROXY=http://sia-lb.telekom.de:8080
```

# test cli

```
c:\dev\venv\py312compreg\Scripts\activate\py312compreg
python cli.py test
```

# deploy components


## deploy exposed api

```
helm upgrade --install demo-a -n components feature-definition-and-test-kit/testData/productcatalog-v1
```

## query dependent services (not yet there)

```
curl -sX GET   https://canvas-info.ihc-dt.cluster-2.de/service -H "accept:application/json"   | jq -r ".[].id"
```

## deploy consumer (component with dependency to exposed api)

```
helm install demo-b -n components feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```

## look dependentapi custom resource

```
kubectl get dependentapis -n components

  NAME                                                           READY   AGE     SVCINVID                               URL
  testdapi-productcatalogmanagement-downstreamproductcatalog     true    5m33s   3b8b010d-d8d0-410e-a256-0afdf84158f8   http://components.ihc-dt.cluster-2.de/ctk-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

## query deployed services

```
curl -sX 'GET'   'https://canvas-info.ihc-dt.cluster-2.de/service'   -H 'accept: application/json' | jq -r '.[].id'

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
