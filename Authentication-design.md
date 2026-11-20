# Authentication design

This document describes the design of authentication and authorization in the ODA Canvas. It is part of the [overall ODA Canvas design](Canvas-design.md).

This video is part 3 of the [ODA Canvas training videos](https://tmforum-oda.github.io/oda-ca-docs/docs/training-videos/index.html). It explains the design, then runs a complete example with three components on a real Canvas:

[![Authentication and Authorization in the ODA Canvas](https://img.youtube.com/vi/a6j6tUDTS80/0.jpg)](https://youtu.be/a6j6tUDTS80)

## Components declare, the Canvas implements

Traditionally, every application ships with its own identity management, and operations teams have to integrate each one and manage users and roles in many places. An ODA Component does not implement identity management at all. Instead, the `securityFunction` section of its YAML specification declares the roles it supports, and the Canvas configures those roles in one shared identity platform.

When a component is deployed, the [Component Management](source/operators/TMFOP001-Component-Management/README.md) operator copies its security requirements into an `IdentityConfig` resource. An [Identity Config](source/operators/TMFOP003-Identity-Config/README.md) operator then configures the identity platform to match. The Reference Implementation has operators for Keycloak and for Microsoft Entra ID, and any other identity platform can be supported with its own operator, using the same `IdentityConfig` resource.

## Every component gets its own client

The Identity Config operator creates a client in the identity platform for each component. The client is the component's own identity. When the component calls another component's API, it uses this client to get an access token (the OAuth 2.0 client credentials flow), so every call between components carries the identity of the caller.

The [Credentials Management](source/operators/TMFOP004-Credentials-Management/README.md) operator provides the component with its client credentials. It watches `IdentityConfig` resources, creates a Kubernetes secret (named `<client id>-secret`) holding the client ID and secret, and deletes the secret when the component is removed.

## The Canvas system role

The Canvas has its own identity too, the `canvassystem` client. Every component must name one of its roles as its Canvas system role, in `securityFunction.canvasSystemRole`. When the component is deployed, that role is granted to the Canvas system client, which gives the Canvas permission to call the component's management and security APIs.

`canvasSystemRole` was called `controllerRole` before the `v1beta4` component specification. See the [release notes](release-notes/ReleaseNotes.md).

## Static and dynamic roles

A component defines the other roles that can be granted to users and systems in one of two ways:

* **Static roles** are listed in the component YAML, in `securityFunction.componentRole`. The Identity Config operator adds each one to the component's client.
* **Dynamic roles** are published through a TM Forum Open API. The component exposes the **TMF672 User Roles and Permissions** API and names it in its `securityFunction`. The operator registers for events on that API: when the component creates a `PermissionSpecificationSet`, the matching role is added to the component's client, and when it removes one, the role is removed. For example, a product catalog might add a role for each new partner catalog.

The older **TMF669 Party Role Management** API (`partyRoleAPI` in the `IdentityConfig`) is still supported for dynamic roles, but will be deprecated. New components should use TMF672. The [IdentityConfig data model](source/operators/TMFOP003-Identity-Config/README.md) has an example of each option.

## Granting a role resolves a dependency

Roles are how access is granted: users, other systems and other components are given roles on a component's client. The Reference Implementation can go one step further. The [Dependency Management](source/operators/TMFOP005-Dependency-Management/README.md) operator has a [Keycloak authorization](source/operators/TMFOP005-Dependency-Management/dependency-management-using-keycloak-authorization/README.md) implementation, which watches Keycloak for role grants. When a component's service account is granted a role on another component's client, the operator connects the first component's `DependentAPI` to the matching `ExposedAPI` of the second. So a component can only discover an API that it has been allowed to call.

The simple Dependency Management implementation resolves dependencies without waiting for a grant. Only one of the two is installed in a Canvas.

## Authentication between components

Each call between components should carry an access token from the caller's client. The [OAuth2 Config](source/operators/TMFOP008-OAuth2-Config/README.md) operator is a prototype of how the Canvas can do this for a component, by intercepting its outgoing traffic in the Istio service mesh and adding the token. It uses an Envoy extension that is still work in progress, so use it as a reference rather than in production. See [UC009 Internal Authentication](usecase-library/UC009-Internal-Authentication.md).

## API gateway policies

Callers from outside the Canvas reach a component's APIs through the API gateway. As well as exposing each API, a component can ask for policies in its `ExposedAPI` definitions, and the [API Management](source/operators/TMFOP002-API-Management/README.md) operator configures them in the gateway:

| Policy | What it does |
|---|---|
| `apiKeyVerification` | Requires an API key on each request. |
| `rateLimit` | Limits the number of requests per second or per minute, for each caller. |
| `quota` | Limits the total number of requests for each caller. |
| `OASValidation` | Validates requests and responses against the API's OpenAPI specification. |
| `CORS` | Sets the cross-origin rules for browser clients. |

The Kong, Apache APISIX and Google Apigee API operators implement these policies; each operator's README says which ones it supports. See [UC010 External Authentication](usecase-library/UC010-External-Authentication.md).

## Clean-up

When a component is uninstalled, the Identity Config operator deletes its client from the identity platform, along with every role the component defined. The grants of those roles, to the Canvas system client and to other components, are removed with them, so no orphaned identities or permissions are left behind.

## Operators

| Operator | Role in authentication and authorization |
|---|---|
| [TMFOP002 API Management](source/operators/TMFOP002-API-Management/README.md) | Exposes APIs through the gateway, with policies such as API keys and rate limits. |
| [TMFOP003 Identity Config](source/operators/TMFOP003-Identity-Config/README.md) | Creates each component's client and roles in the identity platform. |
| [TMFOP004 Credentials Management](source/operators/TMFOP004-Credentials-Management/README.md) | Provides each component with its client credentials. |
| [TMFOP005 Dependency Management](source/operators/TMFOP005-Dependency-Management/README.md) | Connects dependent APIs, optionally only after a role has been granted. |
| [TMFOP008 OAuth2 Config](source/operators/TMFOP008-OAuth2-Config/README.md) | Prototype: adds access tokens to calls between components. |

## Use cases

The authentication use cases are documented in the [use case library](usecase-library/README.md) as follows:

* [UC002-Manage-Components](usecase-library/UC002-Manage-Components.md)
* [UC003-Configure-Exposed-APIs](usecase-library/UC003-Configure-Exposed-APIs.md)
* [UC005-Configure-Clients-and-Roles](usecase-library/UC005-Configure-Clients-and-Roles.md)
* [UC007-Configure-Dependent-APIs](usecase-library/UC007-Configure-Dependent-APIs.md)
* [UC009-Internal-Authentication](usecase-library/UC009-Internal-Authentication.md)
* [UC010-External-Authentication](usecase-library/UC010-External-Authentication.md)
