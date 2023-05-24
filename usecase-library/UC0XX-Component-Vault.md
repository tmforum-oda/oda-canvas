# Private Vault for Component

This use-case describes how a component can manage its secrets in a private vault, which is exclusively accessible from the component.

## Problem

The biggest issue is where to store bootstrap credentials for authenticating against 
a Canvas-Vault (or other systems).
This problem is hard to solve in a secure manner. 
So, every component can benefit from a solution provided on canvas level.

## Solution Idea

One of the stable features since Kubernetes 1.21 is to act as a JWT/OIDC provider.
This allows us to use the Kubernetes cluster itself to act as an authority which proves 
the identity of ServiceAccounts and PODs running in the cluster.

## Workflow

Maybe some steps are not 100% correct, but the general idea should get clear. 

* The canvas manages a central vault (Canvas-Vault).
* When the Canvas-Vault is setup, a trust relation to the Kubernetes-Cluster CA is configured.
* When a new component is deployed, the Component-Operator decides - based on the information 
  provided in the component.yaml (envelope/manifest) - whether a private vault is requested or not.
* If no private vault is requested, the workflow comes to an end here   :-)
* For the next steps we need a unique string to identify the component instance.
  Therefore a step creating a Component-Instance-ID "&lt;CIID&gt;" was added in the 
  sequence diagram. Maybe there exists already something like this, 
  then this step can be skipped.
* A dedicated Key-Value-Store named "privatevault-&lt;CIID&gt;" is created in the Canvas-Vault. 
  This is the private vault for the component instance.
* At the same time a dedicated Kubernetes ServiceAccount for this component, 
  named "sa-&lt;CIID&gt;", is created.
* The Canvas-Vault is configured to grant the newly created ServiceAccount full permissions 
  to the newly created Key-Value-Store.
* If a component POD is started, which requires access to the private vault, 
  a Private-Vault-SideCar is injected. This is a container running in the same POD as the 
  Component-Implementation.
* The SideCar is provided and configured by the Component-Operator to have all necessary 
  information to login to the private vault. The SideCar gets a JWT mount identifying 
  the ServiceAccount, the URL to the Canvas-Vault and the private vault name.
* The Component-Implementation communicates via localhost with the SideCar using a simple API.
  It needs no knowledge about JWT, &lt;CIID&gt; and Canvas-Vault-URL.
* An optional token negotiation was added to secure the localhost communication.
  Any other auth method might serve as well.
  The purpose is to avoid grabbing the secret from a container shell by calling the localhost 
  endpoint of the SideCar.


## Sequence Diagram

### Private Vault Initialization and Usage

![componentVaultBootstrapAndUsage](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ferenc-hechler/oda-canvas/master/usecase-library/pumlFiles/componentVault-bootstrap-and-usage.puml)
[plantUML code](pumlFiles/componentVault-bootstrap-and-usage.puml)


## Technical Details

Detailed information, how the JWT Authentication works can be found here:

https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes

Even if this documentation is from Hashicorp Vault, it also applies to other Vaults, which support JWT/OIDC authentication, e.g. CyberArk Conjur.

## Possible Improvements

The JWT payload contains not only the ServiceAccount information, it also contains information 
about the POD and Namespace:

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

It is possible to use this additional information to sharpen the requirements for the JWT auth in Canvas Vault.


# Disclaimer

As stated above, the workflow is not 100% correct.
It will be updated as soon as a reference implementation was made.


