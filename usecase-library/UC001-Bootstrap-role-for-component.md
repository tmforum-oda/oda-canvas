# Bootstrap role for component use-case

This use-case describes how a component can master its roles, and automatically synchronize these roles into the Identity Management (IDM) system.

It uses the following assumptions:

* The IDM will master the users, and associate users with roles. This removes the need for a Component to include identity management as part of its scope.
* The Bootstrap process will create a system user for the component. This user can be used for all subsequent API calls from the Component. The clientId/secret for this user is stored in a Kubernetes secret to be used by the component.
* The Bootstrap process will also assign the Canvas `seccon` user to the Admin role. This user can be used for all subsequent API calls from the Canvas. The `seccon` user was created as part of the Canvas setup.
* Once the bootstrap process is complete, when clients of the component call the components exposed Open-APIs, the Canvas will perform the initial authorization and include the Role information in the API call (using HTTP headders and following open standards like SAML or OAuth2). The component can use this to perform access control on the data it masters.

![securitySequenceKeycloak](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/pumlFiles/securitySequenceKeycloak.puml)
[plantUML code](pumlFiles/securitySequenceKeycloak.puml)
