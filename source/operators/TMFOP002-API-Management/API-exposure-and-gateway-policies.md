# API exposure and gateway policies

This page explains how the Canvas exposes a component's APIs through an API gateway or service mesh, and how a component asks for policies such as rate limiting, API key verification and CORS. It also says which API operator applies which policy, because they don't all apply the same ones.

It is for component developers, who declare the APIs and policies, and for Canvas platform teams, who choose the gateway. The design is in [use case UC003, Configure Exposed APIs](../../../usecase-library/UC003-Configure-Exposed-APIs.md).

## How an API is exposed

1. **The component declares its APIs.** Each entry in `exposedAPIs`, in the component's `coreFunction`, `managementFunction` or `securityFunction`, gives the API's name, specification, path, implementation service and port, and optionally a `gatewayConfiguration` with policies.
2. **The Component Management operator creates one `ExposedAPI` resource per API version.** An API with a v4 and a v5 specification becomes two `ExposedAPI` resources, named `<component>-<api>-v4` and `<component>-<api>-v5`. The operator copies the `gatewayConfiguration` fields into the `ExposedAPI`'s spec.
3. **The API operator configures the gateway.** The Canvas runs one API operator, chosen when it is installed. It routes the API's path to the implementation service, applies the policies it supports, and writes two things back to the `ExposedAPI`'s status:
   - `apiStatus.url`: the public URL, built from the gateway's external address (or a fixed public hostname, if one is set) and the API's path;
   - `implementation.ready`: `true` once the implementation answers its health check.
4. **The component becomes `Complete`** when every exposed API has a URL and a ready implementation.

The component never configures the gateway itself, and gets no permissions to do so. The component developer says what the API needs, and the platform team decides, by choosing the API operator, how that is done.

To see the result:

```bash
kubectl get exposedapis -n components
kubectl get exposedapi <name> -n components -o yaml
```

The [Canvas Portal v2](../../../canvas-portal-v2/README.md) shows the same information: the **Gateway** page lists each API's route, and the **Policies** page lists the policies the gateway enforces for it.

### API types

`apiType` controls more than documentation:

| `apiType` | What the API operator does |
|---|---|
| `openapi` | Routes the API's path through the gateway. |
| `openmetrics`, `prometheus` | Creates a Prometheus `ServiceMonitor` for the metrics endpoint, as well as the route. See the [observability design](../../../Observability-design.md). |
| `mcp`, `a2a` | Routes the API's path. Kong and APISIX use longer timeouts for these, because MCP and A2A connections stay open. |

## Declaring gateway policies

Policies go in the API's `gatewayConfiguration`. This example is from the Product Catalog [reference component](https://github.com/tmforum-oda/reference-example-components), which declares every policy but leaves them all turned off:

```yaml
coreFunction:
  exposedAPIs:
    - name: productcatalogmanagement
      id: TMF620
      apiType: openapi
      path: /demo-productcatalogmanagement/tmf-api/productCatalogManagement/v4
      implementation: demo-prodcatapi
      port: 8080
      specification:
        - url: https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json
      gatewayConfiguration:
        apiKeyVerification:
          enabled: false
          location: header
        rateLimit:
          enabled: false
          identifier: IP
          limit: "6"
          interval: pm
        quota:
          identifier: ""
          limit: ""
        OASValidation:
          requestEnabled: false
          responseEnabled: false
          allowUnspecifiedHeaders: false
          allowUnspecifiedQueryParams: false
          allowUnspecifiedCookies: false
        CORS:
          enabled: false
          allowCredentials: false
          allowOrigins: "https://allowed-origin.com"
          handlePreflightRequests:
            enabled: false
            allowHeaders: "Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
            allowMethods: "GET, POST"
            maxAge: 36000
        template: ""
```

A `gatewayConfiguration` can also go inside an entry in `specification`, to give one API version different policies. It then replaces the API-level `gatewayConfiguration` for that version as a whole: the two aren't merged.

| Field | Asks the gateway to |
|---|---|
| `apiKeyVerification` | Reject requests without a valid API key. `location` names where the key is expected. |
| `rateLimit` | Limit the requests per `identifier` (for example per client IP) to `limit` per `interval`: `ps` (per second) or `pm` (per minute). |
| `quota` | Limit the total requests per `identifier` to `limit`. It has no `enabled` flag: setting both fields turns it on. |
| `OASValidation` | Check requests, responses or both against the API's OpenAPI specification. |
| `CORS` | Answer cross-origin requests from `allowOrigins`, including `OPTIONS` preflight requests if `handlePreflightRequests.enabled` is set. |
| `template` | Apply a gateway-specific set of policies, named or downloaded from a URL. The format depends on the API operator. |

The [ExposedAPI data model](README.md#exposedapi-data-model) lists every field and its default.

## What each API operator applies

A policy only takes effect if the Canvas's API operator implements it. **The default Canvas uses the Istio API operator, which applies none of them.** Check the table for the operator your Canvas runs.

| Policy | Istio (default) | Kong | Apache APISIX | Google Apigee | Azure API Management | Whale Cloud |
|---|---|---|---|---|---|---|
| `apiKeyVerification` | No | JWT, not an API key (see below) | Yes, `key-auth` | Yes, `VerifyAPIKey` | Always JWT (see below) | No |
| `rateLimit` | No | Per minute only | Per second only | Yes, `SpikeArrest` | Always on (see below) | No |
| `quota` | No | No | Yes, `limit-count` per minute | No | No | No |
| `OASValidation` | No | No | No (needs the commercial API7 plugin) | No | No | No |
| `CORS` | No | One origin only | Yes, `cors` | Yes | Always on (see below) | No |
| `template` | No | URL of `KongPlugin` resources | URL of an `ApisixPluginConfig` | Name of an Apigee template | No | No |

These were checked against the operators' source on `main` in November 2026. The Istio behaviour was also tested on a local kind cluster with `canvas-oda` 1.2.6-rc9: with `rateLimit` turned on at 6 a minute, the setting reached the `ExposedAPI`, but the route didn't change and 10 calls in a few seconds all succeeded.

### Istio

The [Istio operator](istio/README.md) creates one `VirtualService` per API, on the `canvas/component-gateway` gateway, that routes the API's path prefix to the implementation service. It ignores `gatewayConfiguration`. To enforce policies with Istio, configure them in Istio yourself (for example with `AuthorizationPolicy` or `EnvoyFilter` resources), or install Kong or APISIX in front of it.

### Kong

The [Kong operator](kong/README.md) creates an `HTTPRoute` per API and one `KongPlugin` per policy, and attaches them to the route with the `konghq.com/plugins` annotation:

- `rateLimit` becomes the `rate-limiting` plugin, with `limit` requests **per minute** and the `local` policy. `interval` and `identifier` are ignored.
- `apiKeyVerification` becomes the `jwt` plugin, with fixed settings: the token can be sent as a bearer token, the `jwt` query parameter or the `token` cookie, its `iss` claim identifies the Kong consumer, and `exp` is checked. `location` is ignored. The operator doesn't create Kong consumers or their JWT credentials, so set those up in Kong.
- `CORS` becomes the `cors` plugin. `allowOrigins` is passed as a single origin, so give one origin: a comma-separated list doesn't match any request's origin.
- `template` is the URL of a YAML file of `KongPlugin` resources. The operator applies them and attaches them to the route.

### Apache APISIX

The [APISIX operator](apache-apisix/README.md) creates an `ApisixRoute` per API, and one `ApisixPluginConfig` named `combined-apisixpluginconfig-<api>` with all its policies:

- `rateLimit` becomes the `limit-req` plugin, with `limit` requests **per second** and no burst. `interval` is ignored. `identifier` is used as the plugin's key, so give an APISIX variable such as `remote_addr` (the default).
- `quota` becomes the `limit-count` plugin, with `limit` requests per 60 seconds per `identifier`, rejecting with HTTP 429.
- `apiKeyVerification` becomes the `key-auth` plugin, reading the key from the header named in `location`.
- `CORS` becomes the `cors` plugin.
- `OASValidation` only logs an error: the `oas-validator` plugin is part of API7, a commercial extension of APISIX.
- `template` is the URL of an `ApisixPluginConfig` YAML file. Its plugins are added to the ones above.

### Google Apigee and Azure API Management

These operators configure a cloud API gateway, and aren't part of the `canvas-oda` chart.

- The Apigee operator (in the `apigee` folder, which has no README yet) builds an API proxy with a `SpikeArrest` policy for `rateLimit` (for example `100pm`), a `VerifyAPIKey` policy at `location`, and CORS. It reads `rateLimit` and `apiKeyVerification` without defaults, so every API must declare both, even if they are turned off.
- The [Azure API Management operator](azure-apim/README.md) applies the same policy to every API: JWT validation against Microsoft Entra ID, a rate limit of `rateLimit.limit` calls (100 if not set) per 60 seconds per client IP, and CORS. It does this whether or not `enabled` is set. It reads `allowMethods` and `allowHeaders` from `CORS` itself, not from `handlePreflightRequests`.

### Whale Cloud API Management

The [Whale Cloud operator](whalecloud-apim/README.md) registers the API's route in the Whale Cloud API gateway. It doesn't read `gatewayConfiguration`.

## Choosing the API operator

The `canvas-oda` chart installs one API operator: Istio by default, or Kong or APISIX instead. Only one can be enabled. For example, to use Kong:

```bash
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace \
  --set api-operator-istio.enabled=false \
  --set kong-gateway-install.enabled=true
```

Kong needs the Kubernetes Gateway API CRDs. See the [installation guide](../../../installation/README.md) for the full steps for each gateway.

If none of these fits your organisation's policies, you can write your own API operator for your gateway. It needs to watch `ExposedAPI` resources and write `apiStatus.url` and `implementation.ready` to their status. See [Canvas operators](../README.md).

## Related pages

- [TMFOP002 API Management operators](README.md), with the `ExposedAPI` data model and sequence diagrams
- [UC003 Configure Exposed APIs](../../../usecase-library/UC003-Configure-Exposed-APIs.md)
- [UC010 External Authentication](../../../usecase-library/UC010-External-Authentication.md), for authenticating API clients with the Canvas identity platform
- [A component is stuck at In-Progress](https://tmforum-oda.github.io/oda-ca-docs/docs/TroubleshootingGuide/Component-Stuck-In-Progress.html), if an API never gets a URL
