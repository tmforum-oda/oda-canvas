# OAuth2 EnvoyFilter Demo


## set default namespace to "components"

```
kubectl config set-context --current --namespace=components
```


## deploy echo target

```
helm upgrade --install targetcomp source/operators/oauth2EnvoyfilterOperator/helm/echotarget

helm upgrade --install jedionlytarget source/operators/oauth2EnvoyfilterOperator/helm/jedionlytarget

helm upgrade --install proxy-extecho source/operators/oauth2EnvoyfilterOperator/helm/proxy-extecho
```

## deploy echo client

```
helm upgrade --install clientcomp source/operators/oauth2EnvoyfilterOperator/helm/echoclient
```


## Assign jedi role

```
https://canvas-keycloak.ihc-dt.cluster-1.de/auth/admin/master/console/#/odari/users/
```

## Prerequisites

### Install Credentials-Management-Operator


find client-secret for client "credentialsmanagement-operator" in realm "odari":

https://canvas-keycloak.ihc-dt.cluster-1.de/


install Credentials-Manager-Operator using helm

```
helm upgrade --install canvas-credman-op -n canvas charts/credentialsmanagement-operator --set=credentials.client_secret=IDH98****eIqD
```

after a minute take a look at the logs

```
kubectl canvaslogs deployment credentialsmanagement-operator
```

The secrets now exist:

```
kubectl get secret demo-b-productcatalogmanagement-secret -oyaml
```

extract secret

```
kubectl get secret demo-b-productcatalogmanagement-secret -ojsonpath='{.data.client_secret}' | base64 -d
```

### show running pods

```
kubectl get pods -Lapp -Limpl
```

### log into pod prodcatapi

```
#PRODCATAPI_POD=$(kubectl get pods -limpl=demo-b-prodcatapi -o=jsonpath="{.items[*].metadata.name}")
TARGETCOMP_POD=$(kubectl get pods -limpl=targetcomp-echoservice -o=jsonpath="{.items[*].metadata.name}")
echo $TARGETCOMP_POD
kubectl exec -it $TARGETCOMP_POD -- /bin/bash

```





## Installation

```
helm upgrade --install canvas-oauth2-op -n canvas charts/experimental/oauth2-envoyfilter-operator
```

### alte objekt löschen


```
kubectl get serviceentry,envoyfilter,destinationrule,secret -n components
```

```
helm uninstall clientcomp
helm uninstall targetcomp
helm uninstall jedionlytarget
helm uninstall extecho


kubectl delete exposedapi externalapi-productcatalogmanagement
kubectl delete serviceentry add-https
kubectl delete destinationrule demo-b-productcatalogmanagement-downstreamproductcatalog-add-https
kubectl delete destinationrule clientcomp-echoclient-downstreamproductcatalog-add-https
kubectl delete destinationrule clientcomp-echoclient-echotarget-add-https
kubectl delete destinationrule clientcomp-echoclient-jedionlytarget-add-https
kubectl delete secret envoy-oauth2-secrets 
kubectl delete envoyfilter demo-b-productcatalogmanagement-envoyfilter-oauth2
kubectl delete envoyfilter clientcomp-echoclient-envoyfilter-oauth2
kubectl delete configmap deps-clientcomp-echoclient
```


## Deployment of ExposedAPI

```
helm upgrade --install demo-a -n components feature-definition-and-test-kit/testData/productcatalog-v1
```

Alternative: external Wrapper

```
kubectl apply -f source/operators/oauth2EnvoyfilterOperator/docker/manual_test/testdata/yamls/externalapi-productcatalogmanagement-echoservice.yaml
```

```
kubectl apply -f source/operators/oauth2EnvoyfilterOperator/docker/manual_test/testdata/yamls/externalapi-productcatalogmanagement-echo-beepceptor.yaml
```



## Testdeployment of component with dependency

```
helm upgrade --install demo-b -n components feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1  --set=add_dependency_envvars=true
```

check if dependencies are injected (requires waiting and restart)

```
kubectl exec -it demo-b-prodcatapi-XXXXXXXXX -- /bin/sh -c "echo $DEPENDENCY_URL_DOWNSTREAMPRODUCTCATALOG"
```

## test oauth2 injection

```
curl -XPOST http://echoservice.ihc-dt.cluster-1.de/echo
{"echo_body":"","echo_header":{"Accept":"*/*","Authorization":"Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ0c2dUWVVVeFBSSkVSN3g0VHdHb1N5YzdISzNZWl9JWG13YXVrY2RkZkpzIn0.eyJleHAiOjE3NDE2MDM3MTIsImlhdCI6MTc0MTYwMzQxMiwianRpIjoiODlkNzI2ZjktOGUwOC00OTdhLWFhYjItN2ZjYmNlZGQ5Njg1IiwiaXNzIjoiaHR0cDovL2NhbnZhcy1rZXljbG9hay5jYW52YXMuc3ZjLmNsdXN0ZXIubG9jYWw6ODA4My9hdXRoL3JlYWxtcy9vZGFyaSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI3ZjM5ZmQ1NS03M2JkLTQwOWItOTUzMy01NDg4NmU1YmUxZDUiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJkZW1vLWItcHJvZHVjdGNhdGFsb2dtYW5hZ2VtZW50IiwiYWNyIjoiMSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1vZGFyaSJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsImNsaWVudEhvc3QiOiIxMC45Mi4xLjExOSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiY2xpZW50SWQiOiJkZW1vLWItcHJvZHVjdGNhdGFsb2dtYW5hZ2VtZW50IiwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LWRlbW8tYi1wcm9kdWN0Y2F0YWxvZ21hbmFnZW1lbnQiLCJjbGllbnRBZGRyZXNzIjoiMTAuOTIuMS4xMTkifQ.lD_2q8WZ2yuUTVi_mlRAxlmiSsRbbNLWiCRT1lx81_Zvcr4B98i8sAnWaHZupgkj3YGyQJl4fg6AapD1Xbeq0RUStCtkRXPMzxmCD__2deO7VP1o2s8leZosFGXBDVVliRYYbhcEDfDL8EqqBWc6sa6qvoZ4AselCOZoaWXI-kCkX5ejWCt6zQdzUs66u7ImwLOG2lEBcNMnfL0_NfYmOfGZF-zVYDM3QehdidfXDIvW6Rb9usIs_IrpF2-v-qDePW2vj-JPyGeJ1lmD98Sye2391Bwn4GNh5xPPs301ajG3RNRewj5KI6AeHVS3iJOwQZBqOk-bHJzPfzHg9PXBJw","Content-Length":"0","Host":"echoservice.ihc-dt.cluster-1.de","User-Agent":"curl/7.64.0","X-Envoy-Attempt-Count":"1","X-Envoy-Internal":"true","X-Forwarded-Client-Cert":"By=spiffe://cluster.local/ns/echoservice/sa/default;Hash=640a4234426843626e304d5e5238a328766999d3767a6c8c6eaf6c08ec314954;Subject=\"\";URI=spiffe://cluster.local/ns/istio-ingress/sa/istio-ingress","X-Forwarded-For":"10.92.1.1","X-Forwarded-Proto":"http","X-Request-Id":"bdc84a0f-0f23-4911-be16-41dc83b590f0"},"timestamp":"2025-03-10T10:43:56.561749"}
```

inject error at token generation:

```
root@demo-b-prodcatapi-6675466b75-nrgtl:/src# curl http://echo.free.beeceptor.com/echo
Failed to inject credential.root@demo-b-prodcatapi-6675466b75-nrgtl:/src# curl http://echo.free.beeceptor.com/echo
```

# error analysis

## log istiod


```
kubectl logs -n istio-system deployment/istiod
```

```
2025-03-04T14:59:32.399396Z     info    delta   ADS: new delta connection for node:demo-a-prodcatapi-5988ff6d7-q8rr2.components-22
2025-03-04T14:59:32.400608Z     info    delta   CDS: PUSH request for node:demo-a-prodcatapi-5988ff6d7-q8rr2.components resources:69 removed:0 size:68.4kB cached:64/65 filtered:0
2025-03-04T14:59:32.401170Z     info    delta   EDS: PUSH request for node:demo-a-prodcatapi-5988ff6d7-q8rr2.components resources:48 removed:0 size:11.3kB empty:0 cached:47/48 filtered:0
2025-03-04T14:59:32.404255Z     info    delta   LDS: PUSH request for node:demo-a-prodcatapi-5988ff6d7-q8rr2.components resources:49 removed:0 size:96.6kB filtered:0
2025-03-04T14:59:32.405000Z     info    delta   RDS: PUSH request for node:demo-a-prodcatapi-5988ff6d7-q8rr2.components resources:23 removed:0 size:26.7kB cached:22/23 filtered:0
2025-03-04T14:59:32.434877Z     warn    delta   ADS:LDS: ACK ERROR demo-a-prodcatapi-5988ff6d7-q8rr2.components-22 Internal:Error adding/updating listener(s) 0.0.0.0_10259: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_9100: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_10255: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_80: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_15010: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_9093: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.239.83_8443: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.239.83_443: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.235.169_443: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_10249: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_8080: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_8083: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.233.239_80: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_9153: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_10257: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_2381: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.236.245_5000: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_15014: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.227.205_15021: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
10.164.15.198_4194: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
34.118.228.114_443: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_9090: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist
0.0.0.0_4000: paths must refer to an existing path in the system: '/envoy_secrets/oauth2secs/demo-a-productcatalogmanagement.yaml' does not exist

2025-03-04T15:01:45.404272Z     info    delta   ADS: "10.92.1.125:45926" demo-b-prodcatapi-76c69fbd6f-lwxsw.components-12 terminated
2025-03-04T15:01:45.589392Z     info    delta   ADS: new delta connection for node:demo-b-prodcatapi-76c69fbd6f-lwxsw.components-23
2025-03-04T15:01:45.590569Z     info    delta   CDS: PUSH request for node:demo-b-prodcatapi-76c69fbd6f-lwxsw.components resources:69 removed:0 size:68.4kB cached:64/65 filtered:0
2025-03-04T15:01:45.591012Z     info    delta   EDS: PUSH request for node:demo-b-prodcatapi-76c69fbd6f-lwxsw.components resources:48 removed:0 size:11.3kB empty:0 cached:47/48 filtered:0
2025-03-04T15:01:45.592895Z     info    delta   LDS: PUSH request for node:demo-b-prodcatapi-76c69fbd6f-lwxsw.components resources:49 removed:0 size:83.0kB filtered:0
2025-03-04T15:01:45.593584Z     info    delta   RDS: PUSH request for node:demo-b-prodcatapi-76c69fbd6f-lwxsw.components resources:23 removed:0 size:26.7kB cached:22/23 filtered:0
```


## log sidecar

```
kubectl logs -n components demo-b-prodcatapi-7d8c788c77-v7b9h istio-proxy
```

```
...
2025-03-04T15:35:56.042168Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/token_provider.cc:111       onGetAccessTokenFailure: Failed to get access token      thread=12
2025-03-04T15:35:56.042254Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/oauth_client.cc:74  Oauth response code: 404        thread=12
2025-03-04T15:35:56.042263Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/oauth_client.cc:75  Oauth response body: {"error":"Realm does not exist"}   thread=12
2025-03-04T15:35:56.042266Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/token_provider.cc:111       onGetAccessTokenFailure: Failed to get access token      thread=12
2025-03-04T15:35:56.042356Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/oauth_client.cc:74  Oauth response code: 404        thread=12
2025-03-04T15:35:56.042370Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/oauth_client.cc:75  Oauth response body: {"error":"Realm does not exist"}   thread=12
2025-03-04T15:35:56.042372Z     error   envoy credential_injector external/envoy/source/extensions/http/injected_credentials/oauth2/token_provider.cc:111       onGetAccessTokenFailure: Failed to get access token      thread=12
```


# deploy

The build and release process for docker images is described here:
[docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md)

