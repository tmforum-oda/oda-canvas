# View ExposedAPIs

## Table of Contents
- [What is an ExposedAPI?](#what-is-an-exposedapi)
- [Default Namespace](#default-namespace)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Understanding the CRD Schema](#understanding-the-crd-schema)
- [Drill-Down](#drill-down)
- [Contextual Next Steps](#contextual-next-steps)

## What is an ExposedAPI?

An `ExposedAPI` is a **child Custom Resource** created by the Component Operator when it decomposes a Component. For every API entry in `spec.coreFunction.exposedAPIs[]`, `spec.managementFunction.exposedAPIs[]`, and `spec.securityFunction.exposedAPIs[]`, the Component Operator creates a corresponding ExposedAPI resource.

The **API Operator** then watches these ExposedAPI resources and configures the API Gateway (e.g., Istio, Kong, APISIX) to:
- Create a route from the public path to the backend service
- Apply gateway policies: CORS, rate limiting, API key verification, OAS validation, quotas
- Report the public URL and readiness status back to the ExposedAPI's `.status`

**Key concepts:**
- The `segment` field (coreFunction / managementFunction / securityFunction) indicates which section of the parent Component this API came from
- The `apiType` determines how the API is handled: `openapi` (REST), `prometheus`/`openmetrics` (metrics scraping), `mcp` (AI Model Context Protocol)
- The `gatewayConfiguration` sub-fields (CORS, rateLimit, quota, OASValidation, apiKeyVerification) are optional non-functional policies applied at the gateway level

To explore the ExposedAPI CRD schema:
```bash
kubectl explain exposedapi.spec
```

The CRD definition is in `charts/oda-crds/templates/oda-exposedapi-crd.yaml` (v1 schema starts around line 337).

## Default Namespace

Use `components` as the default namespace.

## Commands

Follow the same dual-output pattern (raw + structured):

```bash
# Summary table
kubectl get exposedapis -n components

# Structured summary using helper script
kubectl get exposedapis -n components -o json | python <scripts>/parse_exposedapis.py

# Detail for a specific ExposedAPI
kubectl describe exposedapi <name> -n components
```

## Key Fields

The raw `kubectl get` output already shows useful columns: `API_ENDPOINT` and `IMPLEMENTATION_READY`.

| Field | JSON Path | Description |
|-------|-----------|-------------|
| Name | `.metadata.name` | ExposedAPI resource name |
| Namespace | `.metadata.namespace` | Namespace |
| Parent Component | `.metadata.ownerReferences[0].name` | Owning Component name |
| API Type | `.spec.apiType` | e.g., `openapi` (note: camelCase) |
| TMF ID | `.spec.id` | TMF Forum API identifier, e.g., `TMF620` |
| Segment | `.spec.segment` | One of: `coreFunction`, `managementFunction`, `securityFunction` |
| Implementation | `.spec.implementation` | Backend service name |
| Path | `.spec.path` | API path |
| Port | `.spec.port` | Backend port |
| Ready | `.status.implementation.ready` | Boolean, is the implementation ready |
| URL | `.status.apiStatus.url` | Published API URL |
| Developer UI | `.status.apiStatus.developerUI` | Swagger/docs URL |

## Drill-Down

After the concise list, offer to drill into a specific ExposedAPI:

```bash
kubectl get exposedapi <name> -n components -o json | python <scripts>/parse_exposedapi_drilldown.py
```

This shows:

- Full `.spec` including: implementation service, path, port, API specification URL
- `.spec.CORS` — CORS configuration (enabled, allowOrigins, handlePreflightRequests)
- `.spec.rateLimit` — Rate limiting configuration (enabled, limit, interval, identifier)
- `.spec.apiKeyVerification` — API key verification settings
- `.spec.OASValidation` — OpenAPI specification validation settings
- `.spec.specification[]` — Links to the OpenAPI specification documents
- Full `.status` (apiStatus, implementation details)

After drill-down, explain what each section means:
- **Implementation + Port** — the Kubernetes Service and port that the API Operator routes traffic to through the gateway
- **Path** — the public URL path segment, typically `/<release>-<componentname>/tmf-api/<apiName>/v4`
- **CORS / rateLimit / quota** — non-functional policies the API Operator configures at the API Gateway level
- **specification[]** — links to the OpenAPI/Swagger JSON documents that define the API contract
- **status.apiStatus.url** — the fully qualified URL where this API is accessible externally
- **status.implementation.ready** — whether the backend pod is running and the gateway route is configured

You can also view the raw YAML to see the complete ExposedAPI resource:

```bash
kubectl get exposedapi <name> -n components -o yaml
```

## Understanding the CRD Schema

Offer to explore the ExposedAPI schema in depth:

**Live cluster exploration:**
```bash
kubectl explain exposedapi.spec
kubectl explain exposedapi.spec.CORS
kubectl explain exposedapi.spec.rateLimit
kubectl explain exposedapi.spec.OASValidation
```

**Key v1 schema properties** (from `charts/oda-crds/templates/oda-exposedapi-crd.yaml`):

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | API name (required) |
| `apiType` | enum: openapi, prometheus, openmetrics, mcp | How the API is handled (required) |
| `implementation` | string | Backend Kubernetes Service name (required) |
| `path` | string | URL path for the API (required) |
| `port` | integer | Backend service port (required) |
| `segment` | enum: coreFunction, managementFunction, securityFunction | Which component section it came from |
| `specification[]` | array of {url, version} | Links to API specification documents |
| `CORS` | object | Cross-origin resource sharing policy |
| `rateLimit` | object | Rate limiting: enabled, identifier, limit, interval |
| `quota` | object | Request quota: identifier, limit |
| `OASValidation` | object | OpenAPI spec validation for requests/responses |
| `apiKeyVerification` | object | API key verification: enabled, location |
| `template` | string | Pre-configured gateway policy template |

**Example from test data** — the `productcatalog-v1` component declares these ExposedAPIs (see `feature-definition-and-test-kit/testData/productcatalog-v1/templates/component-productcatalog.yaml`):
- **Core function**: `productcatalogmanagement` (openapi, port 8080) — the TMF620 Product Catalog Management API
- **Management function**: `metrics` (prometheus, port 4000) — Prometheus metrics endpoint
- **Security function**: `partyrole` (openapi, port 8080) — TMF669 Party Role Management API

## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **Drill into a specific ExposedAPI** — See CORS, rate limits, specification URLs, and full status |
| 2 | **View the parent component** — See the Component that owns these ExposedAPIs |
| 3 | **View observability data** — Explore Prometheus metrics (especially for prometheus/openmetrics ExposedAPIs) |
| 4 | **View DependentAPIs** — See which APIs other components depend on |
| 5 | **Return to main menu** |
