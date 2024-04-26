# Discover dependent APIs use case

This use-case describes how a component discovers the url and credentials for a dependent API. The use case uses the following assumptions:

* The API Dependency is an explicit part of the ODA Component definition. The Golden Components will include this dependency as part of their definition and the dependency can also be tested by the Component CTK. The dependent APIs can be part of the **core function**, **security** or **management** part of the component definition.
* The component helm chart will include a `values.yaml` file with placeholders for the Operations team to configure the dependencies (e.g. if a Product Configurator component has a dependency on a Product Catalogue API, the helm chart will include a placeholder for the URL of the specific Product Catalogue API implementation. There may be multiple Product Catalogues deployed in any given canvas). The values will be used in the component template as well as in a ConfigMap (so the component implementation can access the values).
* The ODA Components are **not** given raised privileges to query the Canvas to find their dependencies; Instead, the operations team read the requirement from the Component definition and provides details of the dependent APIs back to the component in the `values.yaml` file. For example, in a Kubernetes based Canvas, the Components are **not** given the permission to call the Kubernetes API. This is important from a security perspective as well as from the perspective of not building operational dependencies on management-plane APIs.


![discoverDependentAPI](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/discover-dependent-API.puml)
[plantUML code](pumlFiles/discover-dependent-API.puml)