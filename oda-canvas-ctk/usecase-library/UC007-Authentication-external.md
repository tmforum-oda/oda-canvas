# External authentication use-case

When an external client (either system or human) wants to call an API exposed by a Component, how they Authenticate and get a token*. The use case uses the following assumptions:

* For system users we use the Client Credentials flow within OAuth2. 
* At runtime, when the client calls an API exposed by a component (using the gateway URL provided by the API Gateway and token provided by the IDM using the Client Credentials Flow), the API Gateway will integrate with the Identity Management System and add a token to the API header that includes details from the Identity Management System (user, roles). 
* For system users their authorization is as the system (and not a passthrough of the actual human end-user). For example, a website displaying a catalog from a product catalog component would authorize as the website, and not as the human end-user that is browsing the website.

*Refer to [Which OAuth2 flow should I use](https://auth0.com/docs/get-started/authentication-and-authorization-flow/which-oauth-2-0-flow-should-i-use)
## System User

![authentication-external-system](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/pumlFiles/authentication-external-system.puml)
[plantUML code](pumlFiles/authentication-external-system.puml)
