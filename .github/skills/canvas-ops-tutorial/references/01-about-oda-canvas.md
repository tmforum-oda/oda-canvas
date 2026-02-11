# About ODA Canvas

## Table of Contents
- [What is the ODA Canvas?](#what-is-the-oda-canvas)
- [The Kubernetes Operator Pattern](#the-kubernetes-operator-pattern)
- [ODA Custom Resource Definitions](#oda-custom-resource-definitions)
- [Component Decomposition](#component-decomposition)
- [Exploring the CRD Schemas](#exploring-the-crd-schemas)
- [Three Sources of CRD Knowledge](#three-sources-of-crd-knowledge)
- [Contextual Next Steps](#contextual-next-steps)

## What is the ODA Canvas?

The TM Forum **Open Digital Architecture (ODA) Canvas** is an execution environment for ODA Components running on Kubernetes. It follows the **Kubernetes Operator Pattern** — a set of controllers watch for ODA custom resources and reconcile them into the desired state by configuring infrastructure services like API Gateways, Identity Management, Service Meshes, and Observability stacks.

Think of the Canvas as the "operating system" for telecom software components. A vendor packages their software as an **ODA Component** (a Kubernetes Custom Resource), and the Canvas reads that specification to automatically:

- Expose APIs through the API Gateway
- Register the component with Identity Management
- Configure secrets access
- Resolve dependencies on other components' APIs
- Set up event notification channels
- Enforce availability policies

## The Kubernetes Operator Pattern

Each concern is handled by an independent **operator** (a controller running in the `canvas` namespace):

| Operator | Watches | Configures |
|----------|---------|------------|
| **Component Operator** | `Component` | Decomposes into child resources; tracks overall status |
| **API Operator** | `ExposedAPI` | API Gateway / Service Mesh routes, CORS, rate limits |
| **Identity Operator** | `IdentityConfig` | Keycloak roles, listeners, party role APIs |
| **Secrets Operator** | `SecretsManagement` | Vault sidecar injection, pod selectors |
| **Dependency Operator** | `DependentAPI` | Discovers upstream ExposedAPIs, resolves URLs |


## ODA Custom Resource Definitions

All ODA resources belong to the API group `oda.tmforum.org`. List them on a live cluster:

```bash
kubectl get crd | grep oda.tmforum.org
```

| CRD | Kind | Short Names | Purpose |
|-----|------|-------------|---------|
| `components.oda.tmforum.org` | `Component` | — | Top-level component specification |
| `exposedapis.oda.tmforum.org` | `ExposedAPI` | — | API exposed through the gateway |
| `dependentapis.oda.tmforum.org` | `DependentAPI` | `depapi`, `depapis` | API dependency on another component |
| `identityconfigs.oda.tmforum.org` | `IdentityConfig` | — | Identity and role configuration |
| `secretsmanagements.oda.tmforum.org` | `SecretsManagement` | `sman`, `smans` | Secrets vault sidecar configuration |
| `publishednotifications.oda.tmforum.org` | `PublishedNotification` | — | Outbound event notification channel |
| `subscribednotifications.oda.tmforum.org` | `SubscribedNotification` | — | Inbound event subscription |
| `availabilitypolicies.oda.tmforum.org` | `AvailabilityPolicy` | — | Pod disruption budget policies |

The Canvas currently serves versions **v1** (current), **v1beta4**, and **v1beta3**, with webhook-based conversion between them. Check which versions are active:

```bash
kubectl get crd components.oda.tmforum.org -o jsonpath='{.spec.versions[?(@.served==true)].name}'
```

## Component Decomposition

When you create a `Component` custom resource, the **Component Operator** reads its spec and decomposes it into child resources. Each child resource is then handled by its specialist operator:

```
Component (top-level custom resource)
├── spec.componentMetadata          → identity & catalog metadata (TMFC ID, version, etc.)
├── spec.coreFunction
│   ├── exposedAPIs[]               → creates ExposedAPI CRs (segment: coreFunction)
│   └── dependentAPIs[]             → creates DependentAPI CRs
├── spec.eventNotification
│   ├── publishedEvents[]           → creates PublishedNotification CRs
│   └── subscribedEvents[]          → creates SubscribedNotification CRs
├── spec.managementFunction
│   ├── exposedAPIs[]               → creates ExposedAPI CRs (segment: managementFunction)
│   └── dependentAPIs[]             → creates DependentAPI CRs
└── spec.securityFunction
    ├── canvasSystemRole            → creates IdentityConfig CR
    ├── componentRole[]             → included in IdentityConfig CR
    ├── secretsManagement           → creates SecretsManagement CR
    ├── exposedAPIs[]               → creates ExposedAPI CRs (segment: securityFunction)
    └── dependentAPIs[]             → creates DependentAPI CRs
```

This decomposition is the core of the ODA Canvas architecture. You define everything in one `Component` YAML, and the Canvas breaks it apart so each operator can independently manage its domain.

## Exploring the CRD Schemas

Use `kubectl explain` to interactively explore any CRD schema on a live cluster:

```bash
# Top-level Component spec
kubectl explain component.spec

# Drill into specific sections
kubectl explain component.spec.componentMetadata
kubectl explain component.spec.coreFunction
kubectl explain component.spec.coreFunction.exposedAPIs
kubectl explain component.spec.securityFunction

# Other resource types
kubectl explain exposedapi.spec
kubectl explain dependentapi.spec
kubectl explain identityconfig.spec
kubectl explain secretsmanagement.spec
kubectl explain publishednotification.spec
kubectl explain subscribednotification.spec
```

## Three Sources of CRD Knowledge

When explaining CRD structures, reference these three sources:

### 1. Live cluster — `kubectl explain`

Best for interactive exploration. Shows the schema of the version currently stored in the cluster.

### 2. CRD Helm templates — `charts/oda-crds/templates/`

The authoritative schema definitions. Key files:

| File | Resource | v1 schema starts at |
|------|----------|---------------------|
| `oda-component-crd.yaml` | Component | ~line 1858 |
| `oda-exposedapi-crd.yaml` | ExposedAPI | ~line 337 |
| `oda-dependentapi-crd.yaml` | DependentAPI | ~line 176 |
| `oda-identityconfig-crd.yaml` | IdentityConfig | ~line 66 |
| `oda-secretsmanagement-crd.yaml` | SecretsManagement | ~line 150 |
| `oda-publishednotification-crd.yaml` | PublishedNotification | ~line 231 |
| `oda-subscribednotification-crd.yaml` | SubscribedNotification | ~line 237 |

Read the relevant section to show users the exact OpenAPI v3 schema properties, types, enums, and required fields.

### 3. Example components — `feature-definition-and-test-kit/testData/`

Real component YAML files used in BDD tests. Key examples:

| Directory | What it demonstrates |
|-----------|---------------------|
| `productcatalog-v1/` | Base component with core, management, and security functions |
| `productcatalog-dependendent-API-v1/` | Component declaring dependent APIs |
| `productcatalog-static-roles-v1/` | Static `componentRole` definitions in securityFunction |
| `productcatalog-v1-sman/` | `secretsManagement` with sidecar configuration |
| `productcatalog-dynamic-roles-v1/` | MCP API type + gatewayConfiguration on all APIs |
| `productinventory-v1/` | A different component type (Product Inventory) |

The rendered component template is in each directory's `templates/component-productcatalog.yaml`. Show users these files as concrete examples of ODA Component specifications.

## Contextual Next Steps

Present these options to the user:

| # | Next Step |
|---|-----------|
| 1 | **Deploy a component** — Install a reference example to explore hands-on |
| 2 | **View deployed components** — See what's already running on the cluster |
| 3 | **Return to main menu** |
