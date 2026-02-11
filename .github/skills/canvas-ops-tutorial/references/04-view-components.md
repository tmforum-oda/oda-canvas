# View Deployed ODA Components

## Table of Contents
- [What is an ODA Component?](#what-is-an-oda-component)
- [Default Namespace](#default-namespace)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Deployment Status Progression](#deployment-status-progression)
- [Understanding the CRD Schema](#understanding-the-crd-schema)
- [Drill-Down](#drill-down)
- [Contextual Next Steps](#contextual-next-steps)

## What is an ODA Component?

A `Component` is the **top-level Custom Resource** in the ODA Canvas. It is the single artifact that a software vendor creates to describe their entire application to the Canvas. When you deploy a Component, the **Component Operator** reads its spec and decomposes it into child resources:

- **ExposedAPIs** — one per API listed in `coreFunction.exposedAPIs[]`, `managementFunction.exposedAPIs[]`, and `securityFunction.exposedAPIs[]`
- **DependentAPIs** — one per dependency in `coreFunction.dependentAPIs[]`, etc.
- **IdentityConfig** — from `securityFunction.canvasSystemRole` and `componentRole[]`
- **SecretsManagement** — from `securityFunction.secretsManagement` (if declared)
- **PublishedNotifications** — from `eventNotification.publishedEvents[]`
- **SubscribedNotifications** — from `eventNotification.subscribedEvents[]`

Each child resource is then processed by its specialist operator (API Operator, Identity Operator, etc.). The Component Operator tracks the aggregate status of all children and reports the overall `deployment_status`.

To see a real example of a Component YAML, look at the test data:
```
feature-definition-and-test-kit/testData/productcatalog-v1/templates/component-productcatalog.yaml
```

To explore the Component CRD schema on a live cluster:
```bash
kubectl explain component.spec
kubectl explain component.spec.coreFunction.exposedAPIs
```

The authoritative CRD definition is in `charts/oda-crds/templates/oda-component-crd.yaml` (v1 schema starts around line 1858).

## Default Namespace

Use `components` as the default namespace unless the user specifies otherwise.

## Commands

Offer both raw `kubectl` output and a structured summary.

**Raw output (show to user):**

```bash
# Summary table — shows NAME and DEPLOYMENT_STATUS columns
kubectl get components -n components

# Detailed view for a specific component
kubectl describe component <name> -n components
```

Note: `-o wide` does not show additional columns for Components — use `-o json` for full details instead.

**Structured summary (parse and present):**

```bash
kubectl get components -n components -o json | python <scripts>/parse_components.py
```

Replace `<scripts>` with the absolute path to `.github/skills/canvas-k8s-ops/scripts/`.

## Key Fields

Parse the JSON output and present a table with these fields per component:

| Field | JSON Path | Description |
|-------|-----------|-------------|
| Name | `.metadata.name` | Component name |
| Namespace | `.metadata.namespace` | Deployment namespace |
| Deployment Status | `.status['summary/status'].deployment_status` | One of: `In-Progress-CompCon`, `In-Progress-IDConfOp`, `In-Progress-SecretMan`, `In-Progress-DepApi`, `Complete` |
| Core APIs | `.status.coreAPIs` (count + readiness) | Number of core ExposedAPIs and how many are ready |
| Management APIs | `.status.managementAPIs` (count + readiness) | Number of management ExposedAPIs and how many are ready |
| Security APIs | `.status.securityAPIs` (count + readiness) | Number of security ExposedAPIs and how many are ready |
| Core Dependent APIs | `.status.coreDependentAPIs` (count + readiness) | Number of core DependentAPIs and how many are ready |
| Published Events | `.status.publishedEvents` (count) | Number of published event notifications |
| Subscribed Events | `.status.subscribedEvents` (count) | Number of subscribed event notifications |

## Deployment Status Progression

The `deployment_status` follows this state machine, where each state corresponds to a different operator completing its work:

1. `In-Progress-CompCon` — The **Component Operator** is creating ExposedAPI child resources and waiting for the **API Operator** to configure API Gateway routes and report them as ready
2. `In-Progress-IDConfOp` — All ExposedAPIs are ready; the **Identity Operator** is now configuring Keycloak roles and listeners from the IdentityConfig resource
3. `In-Progress-SecretMan` — Identity is configured; the **Secrets Operator** is processing the SecretsManagement resource (if declared) to configure vault sidecar injection
4. `In-Progress-DepApi` — Secrets are done; the **Dependency Operator** is resolving DependentAPI resources by discovering matching ExposedAPIs from other components
5. `Complete` — All operators have finished; the component is fully operational

If a component stays in a status for a long time, check the logs of the corresponding operator:

```bash
# Check which operator based on the stuck status:
# In-Progress-CompCon → component operator or api operator
kubectl logs -l app=oda-controller-componentoperator -n canvas --tail=50
kubectl logs -l app=oda-controller-apioperator -n canvas --tail=50

# In-Progress-IDConfOp → identity operator
kubectl logs -l app=oda-controller-identityoperator -n canvas --tail=50

# In-Progress-DepApi → dependency operator
kubectl logs -l app=oda-controller-dependentapi -n canvas --tail=50
```

## Understanding the CRD Schema

After viewing the component list, offer to show the CRD schema for deeper understanding. Use one of these approaches:

**Live cluster exploration:**
```bash
kubectl explain component.spec.componentMetadata
kubectl explain component.spec.coreFunction
kubectl explain component.spec.securityFunction
```

**Read from the CRD template** — show relevant sections from `charts/oda-crds/templates/oda-component-crd.yaml`. Key v1 schema sections:

- `spec.componentMetadata` — TMFC ID, name, version, functional block, maintainers, owners
- `spec.coreFunction.exposedAPIs[]` — required fields: `name`, `apiType` (enum: openapi|mcp|a2a|sse), `implementation`, `path`, `port`
- `spec.coreFunction.dependentAPIs[]` — required fields: `name`, `apiType`
- `spec.securityFunction.canvasSystemRole` — role granted to Canvas controllers
- `spec.securityFunction.componentRole[]` — static roles defined by the component

**Show a concrete example** — read `feature-definition-and-test-kit/testData/productcatalog-v1/templates/component-productcatalog.yaml` and highlight the key sections.

## Drill-Down

After showing the summary, offer to drill into a specific component:

```bash
kubectl get component <name> -n components -o json | python <scripts>/parse_component_drilldown.py
```

This shows:

- `.status['summary/status']` — full summary including API URL summaries and developer UI URLs
- `.status.coreAPIs[]` — each API's name, url, developerUI, ready status
- `.status.identityConfig` — identity provider and listener status
- `.status.securitySecretsManagement` — secrets ready status

After the drill-down, explain what each status section means:
- **Core APIs with URLs** — these are the ExposedAPIs that the API Operator has configured through the API Gateway. The URL is the public-facing endpoint.
- **Management APIs** — typically the Prometheus metrics endpoint (`apiType: prometheus`) used by the observability stack.
- **Security APIs** — the Party Role Management API used by the Identity Operator to manage roles.
- **Identity Config** — shows which identity provider (e.g., Keycloak) is configured and whether the webhook listener is registered.

You can also view the raw YAML to see the full Component spec and status:

```bash
kubectl get component <name> -n components -o yaml
```

## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **Drill into a specific component** — See detailed API URLs, identity config, and secrets status |
| 2 | **View ExposedAPIs** — See all APIs exposed by these components through the API Gateway |
| 3 | **View DependentAPIs** — Check if any cross-component dependencies are declared and resolved |
| 4 | **Deploy another component** — Add a component to explore the decomposition lifecycle |
| 5 | **Return to main menu** |
