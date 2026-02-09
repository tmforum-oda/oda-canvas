# View ExposedAPIs

## Table of Contents
- [Default Namespace](#default-namespace)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Drill-Down](#drill-down)

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
