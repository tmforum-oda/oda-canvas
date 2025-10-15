# Live-Demo Dependent API Resolution in a Multi-Canvas Scenario

## Setup Environment

### Cluster IHC-DT-A (green)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-a
set DOMAIN=ihc-dt-a.cluster-2.de
set COMPREG_EXTNAME=compreg-a
set TLS_SECRET_NAME=domain-tls-secret
tmfihcdta
```

### Cluster IHC-DT-B (magenta)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt-b
set DOMAIN=ihc-dt-b.cluster-2.de
set COMPREG_EXTNAME=compreg-b
set TLS_SECRET_NAME=domain-tls-secret
tmfihcdtb
```

### Cluster IHC-DT (blue)

```
set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt
set DOMAIN=ihc-dt.cluster-2.de
tmfihcdt
```

as canvas was deinstalled reinstall the canvas component-gateway standalone

```
helm upgrade --install component-gateway -n canvas --create-namespace %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service/helm/canvas-somponent-gateway
```


## Install Collectors

### [green] - IHC-DT-A

```
# [green] - IHC-DT-A
	cd %USERPROFILE%\git\oda-canvas
	cd source/services/ComponentRegistry/custom-resource-collector
helm upgrade --install collector -n canvas --create-namespace helm/custom-resource-collector 
```


### [magenta] - IHC-DT-B

```
# [magenta] - IHC-DT-B
cd %USERPROFILE%\git\oda-canvas
cd source/services/ComponentRegistry/custom-resource-collector
helm upgrade --install collector -n canvas --create-namespace helm/custom-resource-collector 
```



## Cleanup

### [blue] - IHC-DT

```
# [blue] - IHC-DT
helm uninstall -n compreg global-compreg
helm uninstall -n compreg upup-compreg
```

### [green] - IHC-DT-A

```
# [green] - IHC-DT-A
helm uninstall -n components r-cat
kubectl rollout restart -n canvas deployment canvas-depapi-op
```

### [magenta] - IHC-DT-B

```
# [green] - IHC-DT-B
helm uninstall -n components f-cat
kubectl rollout restart -n canvas deployment canvas-depapi-op
```

unregister global-compreg

```
curl -X DELETE https://canvas-compreg.ihc-dt-a.cluster-2.de/registries/global-compreg -H "accept: application/json"
curl -X DELETE https://canvas-compreg.ihc-dt-b.cluster-2.de/registries/global-compreg -H "accept: application/json"
curl -X DELETE https://global-compreg.ihc-dt.cluster-2.de/registries/compreg-a -H "accept: application/json"
curl -X DELETE https://global-compreg.ihc-dt.cluster-2.de/registries/compreg-b -H "accept: application/json"
curl -X DELETE https://global-compreg.ihc-dt.cluster-2.de/registries/localdev -H "accept: application/json"
```



## Show state of IHC-DT-A [GREEN]

```
helm list -A
```

plain canvas installation (from branch)

```
kubectl get deployments -n canvas
```

new: canvas-compreg

```
kubectl canvaslogs depapi
```

new: `COMPONENT_REGISTRY_URL=http://canvas-compreg.canvas.svc.cluster.local`

```
kubectl get vs -n canvas
```

additional public routes have been installed to expose internal services

* https://canvas-compreg.ihc-dt-a.cluster-2.de
* https://canvas-info.ihc-dt-a.cluster-2.de/api-docs/

### show COMPREG-A

https://canvas-compreg.ihc-dt-a.cluster-2.de

Show info:

* NAME "compreg-a"
* Component-Registries (only self)
* Registered Components (empty
* Links - Swagger-UI



## Show state of IHC-DT-B [MAGENTA]

same as ihc-dt-a

https://canvas-compreg.ihc-dt-b.cluster-2.de



## Show state of IHC-DT [BLUE]

```
helm list -A
```



## Install Global Component-Registry

```
# [blue] - IHC-DT
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service
helm upgrade --install global-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 
```

open in browser:

* http://global-compreg.ihc-dt.cluster-2.de/



## Link registries (in Browser)

open in browser

* https://canvas-compreg.ihc-dt-a.cluster-2.de

Klick Register-Upstream-URL: https://global-compreg.ihc-dt.cluster-2.de

For compreg-b use curl to do the same:

```
curl -X POST https://canvas-compreg.ihc-dt-b.cluster-2.de/registries/upstream-from-url -H "accept: application/json" -H "Content-Type: application/json" -d "{\"url\":\"https://global-compreg.ihc-dt.cluster-2.de\"}"
```



## Manually run BDD UC007-F002

https://github.com/tmforum-oda/oda-canvas/blob/feature/384_mainly_simple_dependent_operator/feature-definition-and-test-kit/features/UC007-F002-Dependent-APIs-Configure-Dependent-APIs-Single-Downstream.feature

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

### Split actions into ODA Canvas IHC-DT-A and IHC-DT-B

r-cat --> ihc-dt-a [green]
f-cat --> ihc-dt-b [magenta]


# BDD UC007-F002

## [green] Install a downstream retail productcatalog component as release r-cat

Given I install the 'productcatalog-v1' package as release 'r-cat'

```
# [green] IHC-DT-A
cd %USERPROFILE%\git\oda-canvas
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
# [green] IHC-DT-A
kubectl get component r-cat-productcatalogmanagement -n components

  NAMESPACE     NAME                             DEPLOYMENT_STATUS
  components   r-cat-productcatalogmanagement   Complete
```

And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

```
# [green] IHC-DT-A
kubectl get exposedapi -n components

  NAME                                                      API_ENDPOINT                                                                                                IMPLEMENTATION_READY
  r-cat-productcatalogmanagement-metrics                    https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/metrics                               true
  r-cat-productcatalogmanagement-partyrole                  https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/partyRoleManagement/v4        true
  r-cat-productcatalogmanagement-productcatalogmanagement   https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4   true
```


## [MAGENTA] Install the federated productcatalog component that has a dependency on a downstream  productcatalog as release f-cat

When I install the 'productcatalog-dependendent-API-v1' package as release 'f-cat'

```
# [magenta] IHC-DT-B
cd %USERPROFILE%\git\oda-canvas
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
# [magenta] IHC-DT-B
kubectl get depapis -n components   f-cat-productcatalogmanagement-downstreamproductcatalog

  NAMESPACE     NAME                                                      READY   AGE   SVCINVID                               URL
  components   f-cat-productcatalogmanagement-downstreamproductcatalog   true    53s   0e16d068-fc39-4cf5-80a0-5e5826b02d10   https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

And the 'productcatalogmanagement' component has a deployment status of 'Complete'

```
# [magenta] IHC-DT-B
kubectl get components -n components   f-cat-productcatalogmanagement

  NAME                             DEPLOYMENT_STATUS
  f-cat-productcatalogmanagement   Complete
```


# From BDD UC007-F002 (data) -  [green] Populate and [magenta] verify data in federated product catalog

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

## [green] Populate the retail product catalog with sample data

Given the 'productcatalogmanagement' component in the 'r-cat' release has the following 'category' data:

| name                      | description                                       |
| ------------------------- | ------------------------------------------------- |
| Internet line of product  | Fiber and ADSL broadband products                 |
| Mobile line of product    | Mobile phones and packages                        |
| IoT line of product       | IoT devices and solutions                         |

```
# [green] IHC-DT-A
curl -sX POST "http://components.ihc-dt-a.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" -H  "Content-Type: application/json;charset=utf-8" -d "{  \"name\": \"Internet line of product\",  \"description\": \"Fiber and ADSL broadband products\"  }" | jq .

curl -sX POST "http://components.ihc-dt-a.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" -H  "Content-Type: application/json;charset=utf-8" -d "{  \"name\": \"Mobile line of product\",  \"description\": \"Mobile phones and packages\"  }" | jq .

curl -sX POST "http://components.ihc-dt-a.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" -H  "Content-Type: application/json;charset=utf-8" -d "{  \"name\": \"IoT line of product\",  \"description\": \"IoT devices and solutions\"  }" | jq .

```



## [magenta] Verify that the federated product catalog exposes the populated catalogs

When I query the 'productcatalogmanagement' component in the 'f-cat' release for 'category' data:  
Then I should see the following 'category' data in the federated product catalog:
  
| name                      | description                                       |
| ------------------------- | ------------------------------------------------- |
| Internet line of product  | Fiber and ADSL broadband products                 |
| Mobile line of product    | Mobile phones and packages                        |
| IoT line of product       | IoT devices and solutions                         |   

```
# [magenta] IHC-DT-B
curl -sX GET "http://components.ihc-dt-b.cluster-2.de/f-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category" -H  "accept: application/json;charset=utf-8" | jq .

```


# [magenta] show access of r-cat in f-cat logs:

```
# [magenta] IHC-DT-B
kubectl logs deployment/f-cat-prodcatapi -n components

  ...
  listCategory :: GET /f-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category components.ihc-dt.cluster-2.de
  utils/downstreamAPI/listFromDownstreamAPI :: resourceType =  category
  utils/downstreamAPI/getDownstreamAPIs :: returning 1 downstream APIs
  utils/downstreamAPI/listFromDownstreamAPI :: getting data from downstream API at https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4/category
  utils/downstreamAPI/listFromDownstreamAPI :: received 5 records
```


## [magenta] look into Dependent-API Operator logs

```
kubectl canvaslogs depapi
```




## Create an Up-Upstream compreg

```
# [blue] - IHC-DT
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service
helm upgrade --install upup-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 
```

manually register in gloabl-compreg and sync

### [green] undeploy r-cat

```
# [green] - IHC-DT-A
helm uninstall -n components r-cat
```

show after 1 min disappears in upup-compreg




# Links

* this document:
  https://github.com/tmforum-oda/oda-canvas/blob/c0643cf463facf6b24dba8816e25dd5541a87921/source/services/ComponentRegistry/component-registry-service/INFO/ELEVATE-DEMO.md
* GitHub Issue #384:
  https://github.com/tmforum-oda/oda-canvas/issues/384
* Clusters in GCP
  https://console.cloud.google.com/kubernetes/list/overview?project=tmforum-oda-component-cluster
* COMPREG-A
  https://canvas-compreg.ihc-dt-a.cluster-2.de
* COMPREG-B
  https://canvas-compreg.ihc-dt-b.cluster-2.de
* GLOBAL COMPREG
  https://global-compreg.ihc-dt.cluster-2.de
* Canvas-Info_Service IHC-DT-B
  https://canvas-info.ihc-dt-b.cluster-2.de/api-docs/
* UC007-F002
  https://github.com/tmforum-oda/oda-canvas/blob/feature/384_mainly_simple_dependent_operator/feature-definition-and-test-kit/features/UC007-F002-Dependent-APIs-Configure-Dependent-APIs-Single-Downstream.feature
* GitHub Copilot Benefits
  https://github.com/tmforum-oda/oda-canvas/blob/feature/384_mainly_simple_dependent_operator/source/services/ComponentRegistry/images/upstream-sync-compreg.png
* service-discovery switch in Dependent-API-Operator
  https://github.com/tmforum-oda/oda-canvas/blob/feature/384_mainly_simple_dependent_operator/source/operators/dependentApiSimpleOperator/docker/src/dependentApiSimpleOperator.py#L175-L179
  
