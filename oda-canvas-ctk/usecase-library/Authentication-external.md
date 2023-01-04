# External authentication use-case

When an external client wants to call an API exposed by a Component, how they Authenticate and get a token. The use case uses the following assumptions:

* The API Gateway will generate an API key for the external client. This key will map to a system identity in the Identity Management System.
* At runtime, when the client calls an API exposed by a component (using the gateway URL provided by the API Gateway), the API Gateway will integrate with the Identity Management System and add a token to the API header that includes details from the Identity Management System (user, roles). 


## Install component

![authentication-external](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/pumlFiles/authentication-external.puml)
[plantUML code](pumlFiles/authentication-external.puml)



