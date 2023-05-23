# Component Vault (WIP)

This use-case describes how a component can manage it secrets in a private component vault which is exclusively accessible from the own component.

## Problem

The biggest issue is where to store some kind of bootstrap credentials for authenticating against the Canvas Vault.
This leads to possible attack vectors and if this burden is solved by the component, why not store all other secrets in the same way...

## Solution Idea

One of the stable features since Kubernetes 1.21 is to act as a JWT/OIDC provider if in the kube-api-server the `service-account-issuer` flag is set.
This allows us to use the Kubernetes Cluster itself to act as an autority which proves the identity of PODs running in the cluster.

### Info

from https://developer.hashicorp.com/vault/docs/auth/jwt/oidc-providers/kubernetes

> Kubernetes can function as an OIDC provider such that Vault can validate its service account tokens using JWT/OIDC auth.

Even if this documentation is from Hashicorp Vault, it also applies to other Vaults, which support JWT/OIDC authentication, e.g. CyberArk Conjur.

## Workflow

Maybe some steps are not 100% correct, but the general idea should get clear. After doing a reference implementation the workflow will be sharpened.

* The idea is, that the Kubernetes Cluster issues JWTs for ServiceAccounts which are signed by the Cluster CA.
* The Canvas Vault has to be configured to trust the cluster CA.
* When a component is created the Component Operator creates a role in the Canvas Vault which has full access to a path unique for this component.
* The Usage could be simplified by deploying a sidecar container, which does the communication with the Canvas-Vault and is accessible using a localhost API.
* Next to the service account also the namespace and POD name is part of the JWT. This information is really unique and can be used to further limit the authentication to exactly one instance.

### Examnple JWT format

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


## Sequence Diagram

@startuml

participant Canvas as "Canvas"
entity Component
participant "Component Operator" as ComponentOperator
participant "Kubernetes API" as KubernetesAPI
participant "Component Implementation" as ComponentImplementation
participant CanvasVault as "Canvas Vault"


group Canvas Vault Setup 
    ...
	Canvas -> CanvasVault : setup jwt endpoint for oidc_discovery with secrets/kubernetes.io/serviceaccount/ca.crt
	...
end group

group Bootstrap - component deployment
	Component -> ComponentOperator : on.create
	ComponentOperator -> ComponentOperator : create unique Component-ID <CID>
	ComponentOperator -> KubernetesAPI : create ServiceAccount <SA-CID> for Component
	ComponentOperator -> CanvasVault : create Key-Value store /kv-<CID>
	ComponentOperator -> CanvasVault : Setup JWT role for <SA-CID> with full access to path /kv-<CID>
	...
	ComponentOperator -> ComponentImplementation : inject ServiceAccountToken & <CID>
	note right
	  add volume .../secrets/kubernetes.io/serviceaccount/token
	    ...
	      sources:
	      - serviceAccountToken:
	          expirationSeconds: 3607
	          path: token
	    ...
	  The token is a JWT signed by the cluster ca
    end note
end group

group Runtime - component running
	ComponentImplementation -> CanvasVault : login using JWT of <SA-CID>
	ComponentImplementation -> CanvasVault : create secret(key, value) in /kv-<CID>
	...
	ComponentImplementation -> CanvasVault : read secret(key) from /kv-<CID>
	ComponentImplementation  <-- CanvasVault : return secret-value
end group

@enduml



@startuml

participant Canvas as "Canvas"
entity Component
participant "Component Operator" as ComponentOperator
participant "Kubernetes API" as KubernetesAPI
participant ComponentImplementation [
	=Component POD
	----
	Component Implementation
]
participant ComponentVaultSideCar [
	=Component POD
	----
	Component Vault SideCar
]
participant CanvasVault as "Canvas Vault"


group Canvas Vault Setup 
    ...
	Canvas -> CanvasVault : setup jwt endpoint for oidc_discovery with secrets/kubernetes.io/serviceaccount/ca.crt
	...
end group

group Bootstrap - component deployment
	Component -> ComponentOperator : on.create
	ComponentOperator -> ComponentOperator : create unique Component-ID <CID>
	ComponentOperator -> KubernetesAPI : create ServiceAccount <SA-CID> for Component
	ComponentOperator -> CanvasVault : create Key-Value store /kv-<CID>
	ComponentOperator -> CanvasVault : Setup JWT role for <SA-CID> with full access to path /kv-<CID>
	ComponentOperator -> ComponentImplementation ** : inject SideCar container with ServiceAccountToken & <CID>
	ComponentImplementation <-[#ff0000]-> ComponentVaultSideCar ** : started together
	ComponentVaultSideCar -> CanvasVault : login using JWT of <SA-CID>
	...
end group

...
note over ComponentImplementation : some time later
...

group Runtime - component running
	...
	...
	ComponentImplementation -> ComponentVaultSideCar : create secret(key, value)
	ComponentVaultSideCar -> CanvasVault : create secret(key, value) in /kv-<CID>
	...
	ComponentImplementation -> ComponentVaultSideCar : read secret(key)
	ComponentVaultSideCar -> CanvasVault : read secret(key) in /kv-<CID>
	ComponentVaultSideCar  <-- CanvasVault : return secret-value
	ComponentImplementation <-- ComponentVaultSideCar : return secret-value 
end group

@enduml


As stated above, the workflow is not 100% correct, but will be updated as soon as new insights were gained.
