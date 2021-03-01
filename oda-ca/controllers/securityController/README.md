# Notes

Keycloak setup

Relm = whole organisation
Client (within Relm) = 1 App or component

Roles can be scoped at relm or client level
Users can be scoped at relm or client level



# Tasks to set up development environment (tested on Docker for Windows)

Install keycloak and set Environmnet variables for username and password (from https://www.keycloak.org/getting-started/getting-started-kube)

```
kubectl create -f https://raw.githubusercontent.com/keycloak/keycloak-quickstarts/latest/kubernetes-examples/keycloak.yaml
```

Keycloak is created with a Service exposed at `http://localhost:8080/auth/`


To run python module standalone:

1. Ensure url's `kcBaseURL` and `prBaseURL` are set correctly in keycloaktestapp.py
2. Install required python modules with `pip install -r .\requirements.txt`
3. Run `python keycloaktestapp.py`
4. Set the environment variables for login to keycloak

```
$env:KEYCLOAK_USER = "admin"
$env:KEYCLOAK_PASSWORD = "admin"
```

5. Configure a new relm `myrealm` in keycloak.
6. Configure a new client `r1-productcatalog` in the `myrealm` relm.


# Testing KOPF module

Run: `kopf run --namespace=components --standalone .\securityController-keycloak.py`
