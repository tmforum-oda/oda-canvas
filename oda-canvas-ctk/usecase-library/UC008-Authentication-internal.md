# Internal authentication use-case

When one deployed component wants to call an API exposed by another component (internal system user), this use-case describes how they Authenticate and get a token*. The use case uses the following assumptions with component 1 as the caller and component 2 as the provider of the API.
* The component 2 is deployed in the same canvas as component 1 (otherwise use the external authentication use-case).
* The component 1 deployment bootstraps the system user that will be used to call the API ([UC001](UC001-Bootstrap-role-for-component.md)).
* The componnet 2 deployment bootstraps the roles relating to the APIs that it exposes ([UC002](UC002-Expose-APIs-for-Component.md)).
* The component 1 deployment declares its dependency for the API exposed by component 2, and the Operations team have configured access for this dependency ([UC003](UC003-Discover-dependent-APIs-for-Component.md)).



*Refer to [Which OAuth2 flow should I use](https://auth0.com/docs/get-started/authentication-and-authorization-flow/which-oauth-2-0-flow-should-i-use)
## Authentication

![authentication-internal-system](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/pumlFiles/authentication-internal-system.puml)
[plantUML code](pumlFiles/authentication-internal-system.puml)
