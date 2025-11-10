# TEST


# Cluster IHC-DT (blue)

```
#set KUBECONFIG=%USERPROFILE%\.kube\config-ihc-dt
set DOMAIN=ihc-dt.cluster-2.de
set COMPREG_EXTNAME=ihc-dt-compreg
set TLS_SECRET_NAME=domain-tls-secret
tmfihcdt
```

# Cleanup

## unregister global-compreg

```
curl -X DELETE https://canvas-compreg.ihc-dt.cluster-2.de/hub/global -H "accept: */*"
```

## undeploy compregs and components

```
helm uninstall -n compreg global-compreg
helm uninstall -n compreg upup-compreg

helm uninstall -n odacompns-a compreg-a
helm uninstall -n odacompns-b compreg-b
kubectl delete ns compreg odacompns-a odacompns-b

helm uninstall -n components r-cat
helm uninstall -n components f-cat
kubectl rollout restart -n canvas deployment canvas-depapi-op
```




# update canvas WINDOWS

```
cd %USERPROFILE%/git/oda-canvas

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

helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace --set keycloak.service.type=ClusterIP --set api-operator-istio.deployment.hostName=*.%DOMAIN% --set api-operator-istio.deployment.credentialName=%TLS_SECRET_NAME% --set api-operator-istio.configmap.publicHostname=components.%DOMAIN% --set=api-operator-istio.deployment.httpsRedirect=false --set=canvas-info-service.serverUrl=https://canvas-info.%DOMAIN%  --set=keycloak.keycloakConfigCli.image.repository=bitnamilegacy/keycloak-config-cli  --set=resource-inventory.serviceType=ClusterIP --set=resource-inventory.serverUrl=https://canvas-resource-inventory.ihc-dt.cluster-2.de/tmf-api/resourceInventoryManagement/v5 --set=component-registry.ownRegistryName=%COMPREG_EXTNAME%  --set=component-registry.domain=%DOMAIN%  --set=component-registry.watchedNamespaces=components
```

optional install canvas-vs

```
helm upgrade --install -n canvas canvas-vs %USERPROFILE%/git/oda-canvas-notes/virtualservices/canvas --set=domain=%DOMAIN%  
```


### URLs

* https://canvas-compreg.ihc-dt.cluster-2.de
* https://canvas-resource-inventory.ihc-dt.cluster-2.de/tmf-api/resourceInventoryManagement/v5/api-docs/



## Install Global Component-Registry

```
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service-tmf639
helm upgrade --install global-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 
```

open in browser:

* http://global-compreg.ihc-dt.cluster-2.de/


### upup

```
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service-tmf639
helm upgrade --install upup-compreg -n compreg --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% 
```

open in browser:

* https://upup-compreg.ihc-dt.cluster-2.de/



### compreg with watcher for namespace odacomns-a

```
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service-tmf639
helm upgrade --install compreg-a -n odacompns-a --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% --set=canvasResourceInventory=http://resource-inventory.canvas.svc.cluster.local/tmf-api/resourceInventoryManagement/v5 --set=watchedNamespaces=odacompns-a
```

open in browser:

* https://compreg-a.ihc-dt.cluster-2.de/


### compreg with watcher for namespace odacomns-b

```
cd %USERPROFILE%/git/oda-canvas/source/services/ComponentRegistry/component-registry-service-tmf639
helm upgrade --install compreg-b -n odacompns-b --create-namespace helm/component-registry-standalone --set=domain=%DOMAIN% --set=canvasResourceInventory=http://resource-inventory.canvas.svc.cluster.local/tmf-api/resourceInventoryManagement/v5 --set=watchedNamespaces=odacompns-b
```

open in browser:

* https://compreg-b.ihc-dt.cluster-2.de/


## Link registries (in Browser)

open in browser

* https://canvas-compreg.ihc-dt-a.cluster-2.de

Klick Register-Upstream-URL: https://global-compreg.ihc-dt.cluster-2.de

For compreg-b use curl to do the same:

### canvas-compreg -> global-compreg

```
curl -X POST https://canvas-compreg.ihc-dt.cluster-2.de/hub -H "accept: application/json" -H "Content-Type: application/json" -d "{\"id\":\"global\",\"callback\":\"https://global-compreg.ihc-dt.cluster-2.de/sync\",\"query\":\"source=ihc-dt-compreg\"}"
```

### compreg-a -> global-compreg

```
curl -X POST https://compreg-a.ihc-dt.cluster-2.de/hub -H "accept: application/json" -H "Content-Type: application/json" -d "{\"id\":\"global\",\"callback\":\"https://global-compreg.ihc-dt.cluster-2.de/sync\",\"query\":\"source=compreg-a\"}"
```

### compreg-b -> global-compreg

```
curl -X POST https://compreg-b.ihc-dt.cluster-2.de/hub -H "accept: application/json" -H "Content-Type: application/json" -d "{\"id\":\"global\",\"callback\":\"https://global-compreg.ihc-dt.cluster-2.de/sync\",\"query\":\"source=compreg-b\"}"
```


### global-compreg -> upup-compreg

```
curl -X POST https://global-compreg.ihc-dt.cluster-2.de/hub -H "accept: application/json" -H "Content-Type: application/json" -d "{\"id\":\"upup\",\"callback\":\"https://upup-compreg.ihc-dt.cluster-2.de/sync\",\"query\":\"source=global-compreg\"}"
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
helm upgrade --install r-cat -n odacompns-a --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1

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
kubectl get component r-cat-productcatalogmanagement -n odacompns-a

  NAMESPACE     NAME                             DEPLOYMENT_STATUS
  components   r-cat-productcatalogmanagement   Complete
```

And I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

```
# [green] IHC-DT-A
kubectl get exposedapi -n odacompns-a

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
helm upgrade --install f-cat -n odacompns-b --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1

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
kubectl get depapis -n odacompns-b   f-cat-productcatalogmanagement-downstreamproductcatalog

  NAMESPACE     NAME                                                      READY   AGE   SVCINVID                               URL
  components   f-cat-productcatalogmanagement-downstreamproductcatalog   true    53s   0e16d068-fc39-4cf5-80a0-5e5826b02d10   https://components.ihc-dt.cluster-2.de/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

And the 'productcatalogmanagement' component has a deployment status of 'Complete'

```
# [magenta] IHC-DT-B
kubectl get components -n odacompns-b   f-cat-productcatalogmanagement

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
  
