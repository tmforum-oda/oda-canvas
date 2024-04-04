# Configure Users and Roles use case

This use-case describes:
* How a client is created in the Identity Management System (IDM) for each ODA Component. This separates the roles and users for each ODA Component. 
* How the system user is generated for each ODA Component (used to authenticate the ODA Component for outbound API calls).
* how an ODA Component can master its roles, and automatically synchronize these roles into the Identity Management (IDM) system. There are options for static roles (defined in the ODA Component) and dynamic roles (exposed by the ODA Component through an API as part of the ODA Components Security Function).

It uses the following assumptions:

* The IDM will master the users, and associate users with roles. This removes the need for a Component to include identity management as part of its scope.
* The Bootstrap process will create a system user for the ODA Component. This user can be used for all subsequent API calls from the Component. The clientId/secret for this user is stored in a Kubernetes secret to be used by the ODA Component.
* The Bootstrap process will also assign the Canvas `seccon` user to the Admin role. This user can be used for all subsequent API calls from the Canvas. The `seccon` user was created as part of the Canvas setup.
* Once the bootstrap process is complete, when clients of the ODA Component call the ODA Components exposed Open-APIs, the Canvas will perform the initial authorization and include the Role information in the API call (using HTTP headders and following open standards like SAML or OAuth2). The ODA Component can use this to perform access control on the data it masters.

![configure-users-and-roles](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/configure-users-and-roles.puml)
[plantUML code](pumlFiles/configure-users-and-roles.puml)
