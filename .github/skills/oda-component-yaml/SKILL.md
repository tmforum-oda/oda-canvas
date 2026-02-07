---
name: oda-component-yaml
description: Guide for writing ODA Component YAML specifications following the TM Forum standard. Covers the v1 CRD schema, required fields, segment structure (coreFunction, managementFunction, securityFunction), ExposedAPIs, DependentAPIs, events, security roles, and test data conventions. Use this skill when creating or validating ODA Component definitions.
---

# ODA Component YAML — Skill Instructions

## API Version and Kind

```yaml
apiVersion: oda.tmforum.org/v1
kind: Component
```

Supported versions: `v1` (current), `v1beta4`, `v1beta3`. Always target `v1` for new components.

## Top-Level Structure

```yaml
apiVersion: oda.tmforum.org/v1
kind: Component
metadata:
  name: <release-name>-<component-name>
  labels:
    oda.tmforum.org/componentName: <release-name>-<component-name>
spec:
  componentMetadata:
    id: <TMFC-id>
    name: <component-name>
    version: "<semver>"
    description: <text>
    functionalBlock: <block-name>
    publicationDate: <ISO-8601>
    status: specified
    maintainers: [...]
    owners: [...]
  coreFunction:
    exposedAPIs: [...]
    dependentAPIs: [...]
  eventNotification:
    publishedEvents: [...]
    subscribedEvents: [...]
  managementFunction:
    exposedAPIs: [...]
    dependentAPIs: [...]
  securityFunction:
    secretsManagement: {...}
    exposedAPIs: [...]
    dependentAPIs: [...]
    canvasSystemRole: <role-name>
    componentRole: [...]
```

## Component Metadata

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | TM Forum component ID (e.g., `TMFC001`) |
| `name` | Yes | Component name (e.g., `productcatalogmanagement`) |
| `version` | Yes | Semantic version string |
| `description` | No | Human-readable description |
| `functionalBlock` | No | TM Forum functional block (e.g., `CoreCommerce`) |
| `publicationDate` | No | ISO 8601 date |
| `status` | No | `specified`, `implemented`, etc. |
| `maintainers` | No | Array of `{name, email}` |
| `owners` | No | Array of `{name, email}` |

## Segments

Components are structured into three segments:

| Segment | Purpose | apiType values |
|---------|---------|---------------|
| `coreFunction` | Core business APIs | `openapi` |
| `managementFunction` | Metrics, health checks | `openapi`, `prometheus` |
| `securityFunction` | Auth, roles, permissions | `openapi` |

## ExposedAPI

### Required Fields

```yaml
- name: productcatalogmanagement
  apiType: openapi
  implementation: <service-name>
  path: /<release>-<component>/tmf-api/<apiPath>/v4
  port: 8080
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | API name |
| `apiType` | Yes | `openapi` or `prometheus` |
| `implementation` | Yes | Kubernetes Service name |
| `path` | Yes | URL path for the API |
| `port` | Yes | Service port number |

### Optional Fields

```yaml
  specification:
    - url: "https://raw.githubusercontent.com/.../TMF620.swagger.json"
      version: v4.0
  apiSDO: TM Forum
  required: true
  developerUI: /ui
  resources:
    - Resource1
    - Resource2
  gatewayConfiguration:
    apiKeyVerification: true
    rateLimit:
      enabled: true
      limit: 100
      period: 60
    quota:
      enabled: true
      limit: 1000
      period: 86400
    OASValidation: true
    CORS:
      enabled: true
    template: <custom-template-name>
```

## DependentAPI

```yaml
dependentAPIs:
  - name: productinventorymanagement
    apiType: openapi
    specification:
      - url: "https://raw.githubusercontent.com/.../TMF637.swagger.json"
        version: v4.0
    resources:
      - ProductInventory
    required: true
```

Required: `name`, `apiType`. Optional: `specification`, `apiSDO`, `resources`, `required`.

## Event Notification

### Published Events

```yaml
eventNotification:
  publishedEvents:
    - name: productCreateEvent
      description: Product catalog create notification
      apiType: openapi
      specification:
        - url: "https://..."
      implementation: <service-name>
      port: 8080
      hub: /hub
```

### Subscribed Events

```yaml
  subscribedEvents:
    - name: productOrderCreateEvent
      description: Product order notification
      apiType: openapi
      specification:
        - url: "https://..."
      implementation: <service-name>
      port: 8080
      callback: /callback
      query: "eventType=ProductOrderCreateEvent"
```

## Security Function

### Canvas System Role

```yaml
securityFunction:
  canvasSystemRole: Admin
```

Grants the Canvas operator system-level access to manage the component.

### Component Roles (Static)

```yaml
  componentRole:
    - name: admin
      description: Full access to all APIs
    - name: reader
      description: Read-only access
```

### Secrets Management

```yaml
  secretsManagement:
    type: sideCar
    sideCar:
      port: 5000
    podSelector:
      namespace: components
      name: <pod-name>
      serviceaccount: <sa-name>
```

## Prometheus Metrics (Management)

```yaml
managementFunction:
  exposedAPIs:
    - name: metrics
      apiType: prometheus
      implementation: <service-name>
      path: /metrics
      port: 8080
```

## Helm Template Conventions

When the component is packaged as a Helm chart:

```yaml
metadata:
  name: {{ .Release.Name }}-{{ .Values.component.name }}
  labels:
    oda.tmforum.org/componentName: {{ .Release.Name }}-{{ .Values.component.name }}
spec:
  componentMetadata:
    id: {{ .Values.component.id }}
    name: {{ .Values.component.name }}
```

### Standard values.yaml

```yaml
component:
  id: TMFC001
  name: productcatalogmanagement
  functionalBlock: CoreCommerce
  version: "0.0.1"
  dependentAPIs:
    enabled: false
  apipolicy:
    apiKeyVerification: {enabled: false}
    rateLimit: {enabled: false}
    CORS: {enabled: false}
security:
  canvasSystemRole: Admin
```

## Test Data Reference

Example component Helm charts in `feature-definition-and-test-kit/testData/`:

| Package | Purpose |
|---------|---------|
| `productcatalog-v1/` | Baseline v1 component |
| `productcatalog-enhanced-v1/` | Enhanced API features |
| `productcatalog-dependendent-API-v1/` | With dependent APIs |
| `productcatalog-dynamic-roles-v1/` | Dynamic roles + MCP server |
| `productcatalog-static-roles-v1/` | Static roles |
| `productcatalog-v1-sman/` | Secrets management |
| `productinventory-v1/` | Different component type |
| `productcatalog-v1beta3/` | Legacy v1beta3 |
| `productcatalog-v1beta4/` | Legacy v1beta4 |

Default release name in tests: `ctk`. Default namespace: `components`.

## Validation

```bash
# Dry-run validation
kubectl apply --dry-run=client -f component.yaml

# Check deployed component status
kubectl get components -n components
kubectl describe component <name> -n components
```

## Do

- Always include all three segments (coreFunction, managementFunction, securityFunction)
- Use `oda.tmforum.org/v1` for new components
- Include the `oda.tmforum.org/componentName` label
- Reference TM Forum specification URLs for standard APIs
- Use Helm templates for release-name and values injection

## Don't

- Don't omit the `canvasSystemRole` in securityFunction
- Don't hard-code release names in metadata — use `{{ .Release.Name }}`
- Don't mix apiType values incorrectly (prometheus only in managementFunction)
- Don't forget `port` on ExposedAPIs — it's required
- Don't create v1beta3/v1beta4 components unless testing backward compatibility
