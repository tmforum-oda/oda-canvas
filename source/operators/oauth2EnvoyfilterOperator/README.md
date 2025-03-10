# Notes for OAuth2 EnvoyFilter Operator

## Prerequisites

Credentials-Manager-Operator has to be deployed.

```
helm upgrade --install canvas-credman-op -n canvas charts/credentialsmanagement-operator --set=credentials.client_id=credentialsmanagement-operator --set=credentials.client_secret=IDH9****eIqD
```


## set default namespace to "components"

```
kubectl config set-context --current --namespace=components
```



## Installation

```
helm upgrade --install canvas-oauth2-op -n canvas charts/oauth2-envoyfilter-operator
```


## Deployment of ExposedAPI

```
helm upgrade --install demo-a -n components feature-definition-and-test-kit/testData/productcatalog-v1
```

Alternative: external Wrapper

```
kubectl apply -f source/operators/oauth2EnvoyfilterOperator/docker/manual_test/testdata/yamls/externalapi-echo-depapi.yaml
```


## Testdeployment of component with dependency

```
helm install demo-b -n components feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```


# deploy

The build and release process for docker images is described here:
[docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md)

