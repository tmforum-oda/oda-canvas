# Component Vault for Component

This use-case describes how a component can manage its secrets in a component vault, which is exclusively accessible from the component.


## Problem

The biggest issue is where to store bootstrap credentials for authenticating against 
a Canvas-Vault (or other systems).
This problem is hard to solve in a secure manner. 
So, every component can benefit from a solution provided on canvas level.


## Solution Idea

There exists software, like HashiCorp Vault, CyberArk Conjur, ... which manages secrets in a secure manner.
For an ODA-Component it is hard to bundle such a software by itself, because there is always some kind of
Master-Key (Unseal-Key(s), Data-Key) which has to be stored outside the cluster in a secure place.
So, there is a recursion. To setup a software managing secrets you need another place to store the master secret.

Because the ODA Components can not rely on any specific infrastructure, it is up to the ODA Canvas to 
manage a Secrets Management software and ensure the security.
There is no standard for accessing the differen implementations, so a very lean abstraction layer is needed.

This abstraction are the Component Vault Supporting Functions. 
The API can be requested by an ODA Component in its manifest.
The API contains simple CRUD methods for secrets and can be used like any other REST API.

Each ODA Component can only access its own secrets. 
Secrets of other ODA Components are not accessible.
So, the Component Vault of an ODA Component is isolated from each other ODA Components.


## Workflow

This description is quite high-level and implementation independent.
There are reference Workflows which rely on specific Authentication Methods or Software,
which follow this generic Workflow.

* The canvas manages a central vault (Canvas-Vault), which not necessarily has to be in the cluster.
  The Canvas-Vault can be an external system as well.
* The Canvas-Vault has to be configured to provide a Kubernetes Authenticator.
  As an underlying technique [Service-Account JWTs](https://developer.hashicorp.com/vault/docs/auth/kubernetes) 
  issued from the Kubernetes cluster can be used.
  But there are other autentication methods possible, 
  like [certificate based authentication](https://docs.conjur.org/latest/en/content/integrations/k8s-ocp/k8s-k8s-authn.htm).
  In this generic Workflow, it does not matter HOW the authentication happens, 
  it is only important THAT Pods are able to authenticate against the Canvas Vault.
* When a new component is deployed, the Component-Operator decides - based on the information 
  provided in the component.yaml (envelope/manifest) - whether a component vault is requested or not.
* If no component vault is requested, the workflow comes to an end here   :-)
* For the next steps we need a unique string to identify the component instance.
  Therefore a step creating a Component-Instance-ID "&lt;CIID&gt;" was added in the 
  sequence diagram. Maybe there exists already something like this, 
  then this step can be skipped.
* To follow the Kubernetes Operator principle, for components, which request a Component-Vault 
  a ComponentVault Custom-Resource is created.
* The ComponentVaultOperator is triggered and creates a new component vault role inside the Canvas-Vault,
  which is only accessible for PODs which authenticate from this Component-Instance.
  For this role access to an exclusive secret store which is initially empty is granted.
* If a component POD is started, which requires access to the component vault, 
  a Component-Vault-SideCar is injected. This is a container running in the same POD as the 
  Component-Implementation.
* The SideCar is provided and configured by the Component-Vault-Operator to have all necessary 
  information to authenticate with the component-instance component-vault role against the Canvas-Vault.
* The Component-Implementation communicates via localhost with the SideCar using a simple API.
  It needs no knowledge about the Canvas-Vault and the authentication process.
* The localhost communication should be secured with a token, which is negotiated in the POD startup phase.
  The purpose is to avoid grabbing the secret from a container shell by calling the localhost 
  endpoint of the SideCar.


## Sequence Diagram

### Component Vault Initialization and Usage

![componentVaultGenericWorkflow](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/ODA-CANVAS-FORK/oda-canvas-component-vault/master/usecase-library/pumlFiles/componentVault-generic-workflow.puml)
[plantUML code](pumlFiles/componentVault-generic-workflow.puml)


## Component-Vault Request

The request for a component vault has to be defined in the component.yaml. 
Not every POD of an ODA Component needs access to the component vault.
A selector can be used to limit the number of PODs with access to the Component-Vault.
The Selector can be defined on "namespace", "pod-name", "service-account-name".
> To be clarified: Is each ODA Component running in an own namespace?


For example:

```
security:
  ...
  componentVault:
    type: SideCar
    selector: 
      podnames:
      - component-main
      - banking-service
````

# Reference Workflows

* [UC0XX-Component-Vault-JWT-based.md](UC0XX-Component-Vault-JWT-based.md)


# Feedback from ODA-Workshop 22.6.2023

## Allow other kind of Secret access

The current description only describes the access via an local API, which needs a sidecar `type: sidcar`.
For some standard components it might not be possible to access the secrets in this way.
Therefore other access methods should be possible:

* `type: sidecar` the secrets are accessible via a local API as described above
* `type: file` the secrets are injected into a memory filesystem by an init-container
* `type: file-update` the secrets are injected and updated into a memory filesystem by a sidecar
* `type: env` the secrets are injected and updated by the ComponentVault-Operator as Environment variables in the POD (POD manifest contains plain values)
* `type: env-entrypoint` the POD gets an entrypoint injected, which sets the environment variables (maybe technically difficult)
* `type: k8s-secret` the secrets are made available in the namespace as kubernetes secrets at POD starting time 
* `type: k8s-secret-update` the secrets are made available in the namespace and updated regularly

## Allow to define PODS with readonly access to ComponentVault

In the current concept, only one role with Full-Access to the ComponentVault Keystore is created.
It might be good to define more fine granular permissions, like PODs which are allowed to read, but not to write secrets.

Thinking more about this, it could be solved by a generic definition of roles with own settings

```
security:
  ...
  componentVault:
    - name: admin
      permissions: ["create", "read", "update", "delete", "list", "patch"]
      selector: 
        podnames:
        - db-mgmt
    - name: read
      permissions: ["read"]
      selector: 
        podnames:
        - db-server
        - db-client
    - name: setup
      permissions: ["create"]
      selector: 
        podnames:
        - db-init
````

## Allow initial creation of Secrets

It should be possible to generate secrets with an initial value.
So, nowhere in the code the secret is visible, but on initial deploy time a value is generated and can be used on server and client side

## Key Rotation

Allow periodic key rotations. 


## Conjur Support

As DT is using CyberArk Conjur and not HashiCorp Vault, a reference Implementation for Conjur would also be appreciated.
