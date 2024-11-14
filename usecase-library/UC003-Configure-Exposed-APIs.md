# Configure Exposed APIs use-case

This use-case describes how each Exposed APIs is configured in the API Gateway and/or Service Mesh. The Exposed API resources are created by the Component Operator When a component is deployed, updated or deleted. This use-case describes how the Canvas integrates with the Service Mesh and/or API Gateway to configure and expose the API Endpoints. The use case uses the following assumptions:

* The APIs to be exposed are an explicit part of the ODA Component definition. The Golden Components will include this as part of their definition and the API exposure can also be tested by the Component CTK. The exposed APIs can be part of the **coreFunction**, **security** or **management** part of the component definition.
* The ODA Components are **not** given raised privileges to expose their APIs directly; Instead, the API Management operator in the Canvas reads the Exposed API definition and configure the Service Mesh and/or API Gateway on behalf of the component. This model allows the component vendor to express their requirement for exposing APIs in the component definition, and allows the SRE (Site Reliability Team) to determine how the APIs are exposed. 
* This Canvas reference implementation will provide a number of `API Management Operators`; We anticipate a large number of different organisations will implementent their own API Management Operator to configure their chosen API Gateway and/or Service Mesh. This could be hyperscale cloud providers building operators for their API Management services, API Gateway vendors developing operators for their own API Gateway, or open-source communities building operators for their open srouce API Gateways. The Exposed API resource provides a standard vendor-neutral way to express their API requirements.

## Create Exposed API

![exposed-API-create](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/exposed-API-create.puml)
[plantUML code](pumlFiles/exposed-API-create.puml)

## Update Exposed API

![exposed-API-update](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/exposed-API-update.puml)
[plantUML code](pumlFiles/exposed-API-update.puml)

## Delete Exposed API 

![exposed-API-delete](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/exposed-API-delete.puml)
[plantUML code](pumlFiles/exposed-API-delete.puml)

