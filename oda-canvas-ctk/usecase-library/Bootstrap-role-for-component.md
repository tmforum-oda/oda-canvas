# Bootstrap role for component use-case

This use-case describes how a component can master its roles, and automatically synchronize these roles into the Canvas Identity Management (IDM) system.

It uses the following assumptions:

* The Canvas IDM will master the users, and associate users with roles. This removes the need for a Component to include identity management as part of its scope.
* The Bootstrap process will also setup a `seccon` bootstrap user that can be used for all subsequent API calls from the Canvas.
* Once the bootstrap process is complete, when clients of the component call the components exposed Open-APIs, the Canvas will perform the initial authorization and include the Role information in the API call (using HTTP headders and following open standards like SAML or OAuth2). The component can use this to perform access control on the data it masters.

![securitySequenceKeycloak](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/Bootstrap-role-for-component/securitySequenceKeycloak.puml)
[plantUML code](Bootstrap-role-for-component/securitySequenceKeycloak.puml)