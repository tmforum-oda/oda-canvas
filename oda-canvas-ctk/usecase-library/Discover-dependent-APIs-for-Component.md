# Discover dependent APIs for Component use-case

This use-case describes how a component discovers the url and credentials for a dependent API. The use case uses the following assumptions:

* The API Dependency is an explicit part of the ODA Component definition. The Golden Components will include this dependency as part of their dfinition and the dependency can also be tested by the Component CTK.
* The ODA Components are **not** given raised privelages to query the Canvas to find their dependencies; Instead, the Canvas reads the requirement from the Component definition and provides details of the dependent APIs back to the component. For example, in a Kubernetes based Canvas, the Components are **not** given the permission to call the Kubernetes API. This is important from a security perspective as well as from the perspective of not building operational dependencies on management-plane APIs.
* Whilst the reference implementation will provide a reference `API Discovery Operator`, in typical implementations this will be custom to the Operations team that is running their Canvas, and will link to their internal process for authorizing access to APIs.


![discoverDependentAPI](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/canvasUseCasesandBDD/usecase-library/Discover-dependent-API-for-component/discoverDependenAPI.puml)
[plantUML code](Discover-dependent-API-for-component/discoverDependenAPI.puml)