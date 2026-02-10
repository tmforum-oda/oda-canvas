# View ExposedAPIs

## Table of Contents
- [What is an ExposedAPI?](#what-is-an-exposedapi)
- [Default Namespace](#default-namespace)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Understanding the CRD Schema](#understanding-the-crd-schema)
- [Drill-Down](#drill-down)
- [MCP Server Inspection](#mcp-server-inspection)
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

## MCP Server Inspection

After displaying the ExposedAPI list, check if any ExposedAPIs have `apiType: mcp`. If MCP-type APIs are present, **proactively offer to inspect the MCP server** to discover its tools, resources, and prompts.

### Detecting MCP APIs

When parsing the ExposedAPI list output (either raw or from `parse_exposedapis.py`), look for entries where `API Type` is `mcp`. For each MCP API found, note the **URL** from `.status.apiStatus.url` — this is the MCP server endpoint.

### Inspecting an MCP Server

Use the helper script to inspect the MCP server:

```bash
python <scripts>/inspect_mcp_server.py <mcp-endpoint-url>
```

For example:
```bash
python <scripts>/inspect_mcp_server.py https://localhost/pc1-productcatalogmanagement/mcp
```

The script uses the **MCP Streamable HTTP transport** (the current MCP standard) and performs:

1. **Initialize** — establishes a session, reports server name/version and capabilities
2. **tools/list** — discovers all tools with their names, descriptions, and input schemas
3. **resources/list** — discovers any exposed resources (data the server makes available)
4. **prompts/list** — discovers any prompt templates the server offers

The `requests` Python package is required. If not installed, run `pip install requests` first.

### Explaining MCP Server Results

After showing the inspection output, explain:

- **Server info** — The MCP server name and version correspond to the ODA Component that hosts it. The protocol version (e.g., `2025-03-26`) indicates which MCP specification it implements.
- **Tools** — These are operations an AI agent can invoke on the component. For a Product Catalog component, tools typically map to TMF620 CRUD operations (catalog, category, product specification, product offering, product offering price). Each tool has a JSON Schema `inputSchema` defining its parameters.
- **Resources** — Static or dynamic data the server exposes for reading (e.g., catalog data snapshots, schemas). May be empty if the server only exposes tools.
- **Prompts** — Reusable prompt templates the server offers for common interactions. May be empty if no prompts are defined.
- **Capabilities** — The `capabilities` field returned during initialization declares which MCP features (tools, resources, prompts, subscriptions) the server supports.

### Manual MCP Inspection (curl)

If the helper script is not available, the same inspection can be done with `curl`:

```bash
# Step 1: Initialize session
curl -sk -X POST \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  <mcp-endpoint-url>
# Note the Mcp-Session-Id from the response header

# Step 2: List tools
curl -sk -X POST \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}' \
  <mcp-endpoint-url>

# Step 3: List resources
curl -sk -X POST \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":"3","method":"resources/list","params":{}}' \
  <mcp-endpoint-url>

# Step 4: List prompts
curl -sk -X POST \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":"4","method":"prompts/list","params":{}}' \
  <mcp-endpoint-url>
```

## Contextual Next Steps

Present these options using `ask_questions`.

**If MCP-type ExposedAPIs are present**, include the MCP inspection option:

| # | Next Step |
|---|-------------------------------------------|
| 1 | **Inspect MCP Server** — Discover tools, resources, and prompts exposed by the MCP server |
| 2 | **Drill into a specific ExposedAPI** — See CORS, rate limits, specification URLs, and full status |
| 3 | **View the parent component** — See the Component that owns these ExposedAPIs |
| 4 | **View observability data** — Explore Prometheus metrics (especially for prometheus/openmetrics ExposedAPIs) |
| 5 | **View DependentAPIs** — See which APIs other components depend on |
| 6 | **Return to main menu** |

**If no MCP-type ExposedAPIs are present**, omit option 1 and renumber:

| # | Next Step |
|---|-------------------------------------------|
| 1 | **Drill into a specific ExposedAPI** — See CORS, rate limits, specification URLs, and full status |
| 2 | **View the parent component** — See the Component that owns these ExposedAPIs |
| 3 | **View observability data** — Explore Prometheus metrics (especially for prometheus/openmetrics ExposedAPIs) |
| 4 | **View DependentAPIs** — See which APIs other components depend on |
| 5 | **Return to main menu** |
