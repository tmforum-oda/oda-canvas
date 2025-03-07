# API Management Operators

Each ODA Component includes a declarative definition of its requirements for exposing its APIs. The APIs can be for the core function of the component, or for managing and securing the component itself. 

A Canvas platform can use any API Gateway and/or Service Mesh to expose these APIs in a secure and controlled way. API Operators automate the configuration of the API Gateways and Services Meshes.

The Component Operator takes the `Component` custom resource and extracts each Exposed API in the coreFunction, managementFunction and securityFunction and creates an `ExposedAPI` custom resource. The API Operator is a class of Canvas Operator then manages the lifecycle of these `ExposedAPI` resources. In a given Canvas implementation, you can implement any API Gateway and/or Service Mesh by installing the corresponding API Management operator as part of the Canvas installation. The Canvas platform team can implement their organizations policies on how APIs are exposed and secured. For example, a zero-trust implementation could use a Service Mesh to control traffic between Components within the Canvas and use an API Gateway to expose APIs to external clients. 

At present, there are API Operators for the following API Gateways/Service Meshes:

* [Apache APISIX](./apache-apisix/README.md): Operator for the Apache APISIX open source API Gateway (https://apisix.apache.org/).
* [Kong](./kong/README.md): Operator for the Kong open source API Gateway (https://konghq.com/products/kong-gateway).
* [Istio](./istio/README.md): Operator for the Istio Service Mesh (https://istio.io/).
* [Azure API Management](azure-apim/README.md): Operator for the Azure API Gateway (https://azure.microsoft.com/en-gb/products/api-management/).
* [Google Apigee](apigee/README.md): Operator for the Google Apigee API Gateway (https://cloud.google.com/apigee).
* [Whale Cloud API Management](whalecloud-apim/README.md): Operator for the Whale Cloud API Gateway (https://online.iwhalecloud.com/).


## ExposedAPI Data Model

The `ExposedAPI` resource describes the API that a component would like to configure in the Service Mesh and/or API Gateway for other components or external clients to call. The first example below shows a minimal `ExposedAPI` resource with only mandatory properties. The second example adds all the optional properties for requirements like rate limiting.


Minimal example with only mandatory properties.

```yaml
apiVersion: oda.tmforum.org/v1
kind: ExposedAPI
metadata:
  name: r1-productcatalogmanagement-productcatalogmanagement # Kubernetes resource name for the instance of the ExposedAPI
spec:
  name: productcatalogmanagement # Name of the API as defined by the Component
  specification:
    - "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json" # URL to the specification of the API, if required. e.g. URL to the swagger file for Open API.
  apiType: openapi # The type of API specification. Currently only OpenAPI (swagger) and OpenMetrics APIs are supported.
  implementation: r1-prodcatapi # The name of the Kubernetes service where the implementation of the API is found
  path: "/r1-productcatalogmanagement/tmf-api/productCatalogManagement/v4" # The path to the root of the API
  developerUI: "/r1-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs" # (optional) The path to the developer User Interface for the API
  port: 8080 # The port where the API is exposed
```

Example with all optional properties.

```yaml
apiVersion: oda.tmforum.org/v1
kind: ExposedAPI
metadata:
  name: r1-productcatalogmanagement-productcatalogmanagement # Kubernetes resource name for the instance of the ExposedAPI
spec:
  name: productcatalogmanagement # Name of the API as defined by the Component
  specification:
    - "https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json" # URL to the specification of the API, if required. e.g. URL to the swagger file for Open API.
  apiType: openapi # The type of API specification. Currently only OpenAPI (swagger) and OpenMetrics APIs are supported.
  apiSDO: TMForum # (optional) The Standards Development Organization that defines the API
  implementation: r1-prodcatapi # The name of the Kubernetes service where the implementation of the API is found
  path: "/r1-productcatalogmanagement/tmf-api/productCatalogManagement/v4" # The path to the root of the API
  developerUI: "/r1-productcatalogmanagement/tmf-api/productCatalogManagement/v4/docs" # (optional) The path to the developer User Interface for the API
  port: 8080 # The port where the API is exposed
  apiKeyVerification:
    enabled: true # (default: false) Enforce verification of API key
    location: header # (optional) Name of variable where API key value is expected
  rateLimit:
    enabled: true # (default: false)
    identifier: IP # Limit requests by this identifier when enforcing the rate limit
    limit: "100" # The limit (count) of requests to allow for each identifier
    interval: pm # (default: ps) The interval when enforcing the rate limit (ps or pm)
  quota:
    identifier: test-identifier # Identifier used for each quota counter
    limit: "1000" # Quota counter limit to enforce for each identifier
  OASValidation:
    requestEnabled: true # (default: false) Enable for the incoming request
    responseEnabled: true # (default: false) Enable for the response
    allowUnspecifiedHeaders: false # (default: false) (request only) Allow for headers that are not explicitly referenced in the OAS
    allowUnspecifiedQueryParams: false # (default: false) (request only) Allow for query parameters that are not explicitly referenced in the OAS
    allowUnspecifiedCookies: false # (default: false) (request only) Allow for cookies that are not explicitly referenced in the OAS
  CORS:
    enabled: true # (default: false)
    allowCredentials: true # (default: false) Indicates whether the client is allowed to send the actual request (not the preflight request) using credentials. Translates to the Access-Control-Allow-Credentials header
    allowOrigins: "https://allowed-origin.com, https://another-allowed-origin.com" # (default: *) CSV of origins allowed to access the resource. The Access-Control-Allow-Origin header will include the matched origin
    handlePreflightRequests:
      enabled: true # (default: true) Indicates whether the API should handle OPTIONS preflight requests by generating a compliant response
      allowHeaders: "Origin, Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers" # (default: Origin, Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers) CSV of HTTP headers that can be used. Translates to the Access-Control-Allow-Headers header
      allowMethods: "GET, POST, PUT, DELETE" # (default: GET, POST, HEAD, OPTIONS) CSV of HTTP methods allowed for the resource. Translates to the Access-Control-Allow-Methods header
      maxAge: 3600 # (default: 1800) Specifies how long (in seconds) a client should cache the values of the Access-Control-Allow-Headers and Access-Control-Allow-Methods headers for each resource
```


## Sequence diagram

The diagram below describes how each Exposed APIs is configured in the API Gateway and/or Service Mesh. The `ExposedAPI` resources are created by the Component Operator When a component is deployed, updated or deleted. The sequence diagram shows how the API Operator manages the Service Mesh and/or API Gateway to configure and expose the API Endpoints. There are more details and diagrams for update and delete operations in [Use case UC003 - Configure Exposed APIs](../../../usecase-library/UC003-Configure-Exposed-APIs.md).

![exposed-API-create](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/exposed-API-create.puml)

