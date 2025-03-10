# Notes for OAuth2 EnvoyFilter Operator

## Prerequisites

Credentials-Manager-Operator has to be deployed.

```
helm upgrade --install canvas-credman-op -n canvas charts/credentialsmanagement-operator --set=credentials.client_id=credentialsmanagement-operator --set=credentials.client_secret=IDH98gtmd6UXBFUkuY6IOaLqp5wveIqD
```


## Installation

```
helm upgrade --install canvas-oauth2-op -n canvas charts/oauth2-envoyfilter-operator
```

# deploy

The build and release process for docker images is described here:
[docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md)

