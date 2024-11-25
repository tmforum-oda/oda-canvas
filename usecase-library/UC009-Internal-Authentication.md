# Internal authentication use-case

When one deployed component wants to call an API exposed by another component (internal system user), this use-case describes how they Authenticate and get a token*. The use case uses the following assumptions with component 1 as the caller and component 2 as the provider of the API.
* The component 2 is deployed in the same canvas as component 1 (otherwise use the external authentication use-case).
* The component 1 deployment bootstraps the system user that will be used to call the API ([UC005](UC005-Configure-Users-and-Roles.md)).
* The componnet 2 deployment bootstraps the roles relating to the APIs that it exposes ([UC003](UC003-Configure-Exposed-APIs.md)).
* The component 1 deployment declares its dependency for the API exposed by component 2, and the Operations team have configured access for this dependency ([UC007](UC007-Configure-Dependent-APIs.md)).
* The authentication is performed using a Service Mesh or API Gateway: If an external API Gateway is used, the recommendation is to use a Service Mesh for this internal authentication. If the API Gateway is part of the Canvas cluster, then the API Gateway could be used for both internal and external authentication. Some API Gateways now use a micro-gateway pattern with the Gateway implemented as a sidecar container in the same pod as the component. In this case, the recommendation is to use the API Gateway for both internal and external authentication.



*Refer to [Which OAuth2 flow should I use](https://auth0.com/docs/get-started/authentication-and-authorization-flow/which-oauth-2-0-flow-should-i-use)
## Authentication

![authentication-internal-system](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/authentication-internal-system.puml)
[plantUML code](pumlFiles/authentication-internal-system.puml)
