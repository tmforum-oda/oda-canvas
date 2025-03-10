# Notes for OAuth2 EnvoyFilter Operator

## Prerequisites

Credentials-Manager-Operator has to be deployed.

```
helm upgrade --install canvas-credman-op -n canvas charts/credentialsmanagement-operator --set=credentials.client_id=credentialsmanagement-operator --set=credentials.client_secret=IDH9****eIqD
```


## Installation

```
helm upgrade --install canvas-oauth2-op -n canvas charts/oauth2-envoyfilter-operator
```


## Deployment of ExposedAPI

```
helm upgrade --install demo-a -n components feature-definition-and-test-kit/testData/productcatalog-v1
```


## Testdeployment of component with dependency

```
helm install democlient -n components feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```


# deploy

The build and release process for docker images is described here:
[docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md)

