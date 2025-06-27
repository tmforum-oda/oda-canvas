# Configure Clients and Roles use case

This use-case describes:
* How a client is created in the Identity Management System (IDM) for each ODA Component. This separates the roles and client for each ODA Component. 
* how an ODA Component can master its roles, and automatically synchronize these roles into the Identity Management (IDM) system. There are options for static roles (defined in the ODA Component) and dynamic roles (exposed by the ODA Component through an API as part of the ODA Components Security Function).

It uses the following assumptions:

* The IDM will master the clients, and associate clients with roles. This removes the need for a Component to include identity management as part of its scope.
* The Bootstrap process will create a system client for the ODA Canvas. This client can be used for all subsequent API calls from the Component. The clientId/secret for this client is stored in a Kubernetes secret to be used by the ODA Component.
* The Bootstrap process will also assign the Canvas `canvassystem` client to the Admin role. This client can be used for all subsequent API calls from the Canvas. The `canvassystem` client was created as part of the Canvas setup.
* Once the bootstrap process is complete, when clients of the ODA Component call the ODA Components exposed Open-APIs, the Canvas will perform the initial authorization and include the Role information in the API call (using HTTP headders and following open standards like SAML or OAuth2). The ODA Component can use this to perform access control on the data it masters.

![configure-clients-and-roles](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/configure-clients-and-roles.puml)
[plantUML code](pumlFiles/configure-clients-and-roles.puml)
