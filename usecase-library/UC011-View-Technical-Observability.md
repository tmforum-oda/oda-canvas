# View technical observability use-case

When a component is deployed, you should be able to view the baseline technical metrics such as HTTP Requests per second, CPU, Memory etc. using the observability service management dashboard that comes with the Canvas implementation. 

The use case uses the following assumptions:

* As part of the Canvas installation, the Service Mesh is configured to capture the technical observability metrics and make them available to the observability service. 
* As part of the Canvas installation, the the cloud platform is configured to make the underlying compute metrics (CPU, Memory etc.) available to the observability service. 
* The requirement si for the ODA Canvas to correctly configure the Service Mesh and the cloud platform to based on the meta-data described in the Component specification. This is described in use case [UC003](UC003-Configure-Exposed-APIs.md)



![Technical Observability](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/technical-observability.puml)
[plantUML code](pumlFiles/technical-observability.puml)