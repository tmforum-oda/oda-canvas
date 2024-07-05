# Secrets Management for Component

This use-case describes how a component can manage its secrets in a local secrets management, 
which is exclusively accessible for the component itself.

## Problem

Handling of sensitive information is always difficult.
There are solutions for storing the secrets in a kind of password safe.
But still there is the issue, where where to store the bootstrap credentials 
for initially authenticating against the password safe.
This problem is hard to solve in a secure manner. 
So, every component can benefit from a solution provided on canvas level.

## Solution Idea

One of the stable features since Kubernetes 1.21 is to act as a JWT/OIDC provider.
This allows us to use the Kubernetes cluster itself to act as an authority which proves 
the identity of ServiceAccounts and PODs running in the cluster.

## Workflow

* The ODA-Canvas manages a central vault (Canvas-Vault) to store secrets in a secure way.
  In the reference implementation this will be HashiCorp Vault.
* When the Canvas-Vault is setup, a trust relation to the Kubernetes-Cluster CA is configured.
* When a new component is deployed, the Secrets-Management-Operator decides - based on the information 
  provided in the component.yaml (envelope/manifest) - whether a secrets management is requested or not.
* If no secrets management is requested, the workflow comes to an end here   :-)
* If Secrets-Management is requested, the configuration contains information, 
  which PODs of the ODA-Component need access. The POD selector can filter for
  information stored in the JWT token, issued for the POD. That are namespace, name and serviceaccount. 
* For the next steps we need a unique string to identify the component instance.
  Therefore a step creating a Component-Instance-ID "&lt;CIID&gt;" was added in the 
  sequence diagram. In [ODAA-48](https://projects.tmforum.org/jira/browse/ODAA-48) there
  was a decision to construct the Component-Instance-ID from the label "oda.tmforum.org/componentName" 
  and the namespace of the component.yaml. Multi-Cloud setups can cause conflicts, so additional a cluster 
  specific configurable prefix can be added.
* A dedicated Key-Value-Store named "kv-sman-&lt;CIID&gt;" is created in the Canvas-Vault. 
  This is the secrets management exclusively accessible for this component instance 
  (and maybe admins of the Canvas-Vault).
* Optional a dedicated Kubernetes ServiceAccount for this component can be created. 
* The Canvas-Vault is configured to grant PODs matching the selector above full permissions 
  to the newly created Key-Value-Store.
* If a component POD is started, which requires access to the secrets management, 
  a Secrets-Management-SideCar is injected. This is a container running in the same POD as the 
  Core-Implementation.
* The SideCar is provided and configured by the Secrets-Management-Operator to have all necessary 
  information to login to the KV-Store. The SideCar gets a JWT mount identifying 
  the POD, the URL to the Canvas-Vault and the KV-Store name and the associated role for this component instance.
* The Core-Implementation communicates via localhost with the SideCar using a Secrets CRUD API.
  It needs no knowledge about JWT, &lt;CIID&gt; and Canvas-Vault-URL.
* An optional token negotiation was added to secure the localhost communication.
  Any other auth method might serve as well.
  The purpose is to avoid grabbing the secret from a container shell by calling the localhost 
  endpoint of the SideCar.


## Sequence Diagram

### Secrets Management Initialization and Usage

![secretsManagementBootstrapAndUsage](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ODA-CANVAS-FORK/oda-canvas-component-vault/odaa-26/usecase-library/pumlFiles/secretsManagement-bootstrap-and-usage.puml)
[plantUML code](pumlFiles/secretsManagement-bootstrap-and-usage.puml)


## Technical Details

Detailed information, how the JWT Authentication works can be found here:

https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes

Even if this documentation is from Hashicorp Vault, it also applies to other Vaults, which support JWT/OIDC authentication, e.g. CyberArk Conjur.

## Example JWT Payload

An example JWT payload looks like this:

```
{
  "aud": [ "https://kubernetes.default.svc.cluster.local" ],
  "exp": 1716375009,
  "iat": 1684839009,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "kubernetes.io": {
    "namespace": "comps",
    "pod": {
      "name": "component-abc-0",
      "uid": "9367907f-d33c-471d-97ff-64ada8df28df"
    },
    "serviceaccount": {
      "name": "sa-component-abc",
      "uid": "02690546-0611-40af-b2e4-8b9ca77c3fe3"
    },
    "warnafter": 1684842616
  },
  "nbf": 1684839009,
  "sub": "system:serviceaccount:comps:sa-component-abc"
}
```


## Extension of the Component.yaml

```
apiVersion: oda.tmforum.org/v1beta3
kind: Component
metadata:
  labels:
    oda.tmforum.org/componentName: demo-a-productcatalogmanagement
  namespace: components
spec:
  ...
  securityFunction:  
    ...
    secretsManagement:
      type: sideCar
      sideCar:
        port: 5000
      podSelector:
        name: "demo-a-*"
        namespace: "components"
        serviceaccount: "default"
  ...
```

If there exists a structure "spec.securityFunction.secretsManagement" the Secrets-Management-Operator will create 
a KV-Store for this component. 

## Limitations

The current setup only allows one configuration for gaining full access (read & write) and only one set of POD selectors.
In the future we should support multiple POD selectors with fine grained policies.
