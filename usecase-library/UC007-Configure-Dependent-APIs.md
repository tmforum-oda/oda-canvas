# Configure dependent APIs use case

This use-case describes how a component discovers the url and credentials for a dependent API. The use case uses the following assumptions:

* The API Dependency is an explicit part of the ODA Component definition. The Golden Components will include this dependency as part of their definition and the dependency can also be tested by the Component CTK. The dependent APIs can be part of the **core function**, **security function** or **management function** part of the component definition.

* The ODA Components are **not** given raised privileges to query the Canvas to find their dependencies; Instead, the component must call an API Service at a fixed url `info.canvas.svc.cluster.local`. The service implements the [Service Inventory API](https://www.tmforum.org/resources/standard/tmf638-service-inventory-api-user-guide-v5-0-0/) API and should return to each component just the dependent APIs that the component has been authorized to call.

The use case below shows a **Product Inventory** with a dependency on a downstream **Product Catalog**. In the use case there are two product catalog APIs provided for a **Retail Catalog** and a **Wholesale Catalog**. 

![discoverDependentAPI](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/usecase-library/pumlFiles/discover-dependent-API.puml)
[plantUML code](pumlFiles/discover-dependent-API.puml)


The Service Inventory payload for a dependent API with name `downstreamproductcatalog` will look like the example below:

``` JSON
{
	"serviceType": "API",
	"name": "Acme partner catalog",
	"description": "Implementation of TMF620 Product Catalog Management Open API",
	"state": "active",
	"serviceCharacteristic": [
		{
			"name": "componentName",
			"valueType": "string",
			"value": "acme-productinventory",
			"@type": "StringCharacteristic"
		},
		{
			"name": "dependencyName",
			"valueType": "string",
			"value": "downstreamproductcatalog",
			"@type": "StringCharacteristic"
		},
		{
			"name": "url",
			"valueType": "string",
			"value": "http://localhost/acme-productcatalogmanagement/tmf-api/productCatalogManagement/v4",
			"@type": "StringCharacteristic"
		},
		{
			"name": "OAS Specification",
			"valueType": "string",
			"value": "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json",
			"@type": "StringCharacteristic"
		}
	],
	"serviceSpecification": {
		"id": "1",
		"name": "API",
		"version": "1.0.0",
		"@type": "ServiceSpecification",
		"specCharacteristic": [
			{
				"name": "componentName",
				"valueType": "string",
				"description": "The name of the component which wants to consume the API service. The component name is normally available in the environment vaiable COMPONENT_NAME",
				"@type": "StringCharacteristic"
			},
			{
				"name": "dependencyName",
				"valueType": "string",
				"description": "The dependency name that this API service matches. The dependency name is set in the Component Specification",
				"@type": "StringCharacteristic"
			},
			{
				"name": "url",
				"valueType": "string",
				"description": "The url the the API root endpoint",
				"@type": "StringCharacteristic"
			},
			{
				"name": "OAS Specification",
				"valueType": "string",
				"description": "The url to the Open API Speciofication for this API",
				"@type": "StringCharacteristic"
			}
		]
	},
	"@type": "Service"
}
```