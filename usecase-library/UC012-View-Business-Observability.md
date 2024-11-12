# View business observability use-case

When a component is deployed, you should be able to view the busines metrics for that component. The business metrics will 
be specific to each component implementation. For example, the *TMFC002 product order capture &
validation* component might expose a metric for the number of orders. 

The use case uses the following assumptions:

* The component implementation will expose the business metrics using a standard API (e.g. OpenMetrics).
* The component specification will describe the details of the business metrics - these are used to automatically configure the observability platform to integrate to the API provided by the component implmentation.

![Technical Observability](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/technical-observability.puml)
[plantUML code](pumlFiles/technical-observability.puml)