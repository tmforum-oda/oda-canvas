# Expose APIs for Component use-case

This use-case describes how a component exposes its APIs for other components and/or clients to use.  When a component is deployed, updated or deleted, this use-case describes how the Canvas integrates with the Service Mesh and/or API Gateway to configure and expose the API Endpoints. The use case uses the following assumptions:

* The APIs to be exposed are an explicit part of the ODA Component definition. The Golden Components will include this as part of their definition and the API exposure can also be tested by the Component CTK. The exposed APIs can be part of the **coreFunction**, **security** or **management** part of the component definition.
* The ODA Components are **not** given raised privelages to expose their APIs directly; Instead, software operators in the Canvas read the Component definition and configure the Service Mesh and/or API Gateway on behalf of the component. This model allows the component vendor to express their requirement for exposing APIs in the component definition, and allows the SRE (Site Reliability Team) for the operator to determine how the APIs are exposed. 
* Whilst the reference implementation will provide a reference `API Exposure Operator`, in typical implementations this will be specific to the Operations team that is running their Canvas, and will link to their own standards and policies. It is also possible that API Gateway vendors (or open-source communities) develop standard `API Exposure Operators` for their own API Gateway.


![exposeAPIs](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/expose-API-for-component/exposeAPI.puml)
[plantUML code](Expose-API-for-component/exposeAPI.puml)