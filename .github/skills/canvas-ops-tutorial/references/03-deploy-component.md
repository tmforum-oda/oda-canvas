# Deploy an ODA Component

## Table of Contents
- [What Happens When You Deploy?](#what-happens-when-you-deploy)
- [Step 1: Ensure Helm Repo](#step-1-ensure-helm-repo)
- [Step 1b: Check Existing Releases](#step-1b-check-existing-releases)
- [Step 2: List Available Charts](#step-2-list-available-charts)
- [Step 3: Optional Overrides](#step-3-optional-overrides)
- [Step 4: Install](#step-4-install)
- [Step 5: Monitor Deployment](#step-5-monitor-deployment)
- [Step 6: Explore the Decomposed Resources](#step-6-explore-the-decomposed-resources)
- [Uninstall](#uninstall)
- [Contextual Next Steps](#contextual-next-steps)

## What Happens When You Deploy?

Deploying an ODA Component triggers a multi-stage lifecycle managed by the Canvas operators:

1. **Helm installs the chart** — this creates Kubernetes Deployments, Services, and a `Component` Custom Resource
2. **Component Operator reads the Component CR** — it decomposes `spec.coreFunction`, `spec.managementFunction`, `spec.securityFunction`, and `spec.eventNotification` into child resources: ExposedAPIs, DependentAPIs, IdentityConfig, SecretsManagement, PublishedNotifications, SubscribedNotifications
3. **API Operator processes each ExposedAPI** — creates API Gateway routes, applies CORS/rate-limit/quota policies, reports readiness
4. **Identity Operator processes the IdentityConfig** — configures Keycloak realm, creates roles, registers webhook listener
5. **Secrets Operator processes SecretsManagement** — configures vault sidecar injection (if declared)
6. **Dependency Operator processes each DependentAPI** — searches for matching ExposedAPIs, writes resolved URLs
7. **Component Operator updates overall status** — progresses through `In-Progress-CompCon` → `In-Progress-IDConfOp` → `In-Progress-SecretMan` → `In-Progress-DepApi` → `Complete`

To see the authoritative Component CRD schema: `charts/oda-crds/templates/oda-component-crd.yaml` (v1 schema starts ~line 1858).

An example component YAML used in testing: `feature-definition-and-test-kit/testData/productcatalog-v1/templates/component-productcatalog.yaml`.

## Step 1: Ensure Helm Repo

The repo index must be updated before searching — stale or missing indexes cause "No results found" errors.

```bash
helm repo add oda-components https://tmforum-oda.github.io/reference-example-components 2>&1
helm repo update oda-components
```

## Step 1b: Check Existing Releases

Before deploying, check what's already installed to avoid name collisions:

```bash
helm list -n components
```

Show any existing releases with chart versions and status.

## Step 2: List Available Charts

```bash
helm search repo oda-components
```

Currently available:

| Chart | Component | Description |
|-------|-----------|-------------|
| `oda-components/productcatalog` | TMFC001 | Product Catalog Management |
| `oda-components/productinventory` | TMFC005 | Product Inventory Management |

Ask the user to select a chart.

### Federated Catalog Scenario

If a `productcatalog` component is already deployed, offer to deploy a **second instance** with dependent APIs enabled to demonstrate cross-component API wiring:

**Important**: Use a short release name (max 5 characters). See [Release Name Constraint](#release-name-constraint) — longer names cause deployment failures.

```bash
helm install pc2 oda-components/productcatalog -n components \
  --set component.dependentAPIs.enabled=true
```

The second instance will declare a DependentAPI on the downstream Product Catalog Management API. The Canvas dependency operator will automatically resolve this against the first instance's ExposedAPI. Use release name `pc2` (or allow user override, max 5 chars). After deployment, suggest viewing DependentAPIs (action 3) to see the resolution status.

## Step 3: Optional Overrides

After chart selection, offer optional `--set` overrides:

| Override | Default | Description |
|----------|---------|-------------|
| `component.dependentAPIs.enabled` | `false` | Enable dependent API declarations |
| `component.MCPServer.enabled` | `false` | Enable MCP Server for AI agent capabilities |

Ask if the user wants to enable any optional features.

## Step 4: Install

Always deploy to the `components` namespace:

```bash
kubectl create namespace components --dry-run=client -o yaml | kubectl apply -f -

helm install <release-name> oda-components/<chart-name> \
  -n components \
  [--set key=value ...]
```

### Release Name Constraint

**Critical**: Kubernetes port names must be 15 characters or fewer. ODA component charts derive port names by combining the release name with internal suffixes (e.g., `<release>-prodinvapi`, `<release>-prodcatapi`). A release name that is too long will cause the Helm install to fail.

**Always use short release names — maximum 5 characters.** Recommended defaults:

| Chart | Default Release Name | Second Instance |
|-------|---------------------|-----------------|
| `productcatalog` | `pc1` | `pc2` |
| `productinventory` | `pi1` | `pi2` |

Allow user override but **reject names longer than 5 characters** with a warning explaining the port name limit. Never use descriptive names like `prodcat`, `prodinv`, or `prodcat2` — they will exceed the 15-character limit when suffixes are appended.

## Step 5: Monitor Deployment

Poll the component status until `Complete` or timeout (10 minutes):

```bash
kubectl get component <component-name> -n components -o yaml
```

Check the `status.summary/status.deployment_status` field in the YAML output. The status progresses through:
- `In-Progress-CompCon` — Configuring APIs...
- `In-Progress-IDConfOp` — Configuring identity...
- `In-Progress-SecretMan` — Configuring secrets...
- `In-Progress-DepApi` — Resolving dependent APIs...
- `Complete` — Component deployed successfully!

Repeat the `kubectl get` command periodically until the status reaches `Complete`.

If status does not reach `Complete` within 10 minutes, suggest:

```bash
kubectl describe component <name> -n components
kubectl get events -n components --sort-by='.lastTimestamp'
```

## Step 6: Explore the Decomposed Resources

Once the component reaches `Complete` (or even while it's progressing), show the user the child resources that the Component Operator created. This helps them understand the decomposition:

```bash
# See all resources created from this component
kubectl get exposedapis -n components -l oda.tmforum.org/componentName=<component-name>
kubectl get dependentapis -n components -l oda.tmforum.org/componentName=<component-name>
kubectl get identityconfigs -n components
kubectl get secretsmanagements -n components
kubectl get publishednotifications -n components
kubectl get subscribednotifications -n components
```

Or see everything at once:

```bash
kubectl get exposedapis,dependentapis,identityconfigs,secretsmanagements -n components
```

Explain each resource type:
- **ExposedAPIs** — one per API in the component's core/management/security functions. The API Operator configured gateway routes for each.
- **DependentAPIs** — only present if `component.dependentAPIs.enabled=true` was set. The Dependency Operator resolves these against other components' ExposedAPIs.
- **IdentityConfig** — created from `securityFunction.canvasSystemRole` and `componentRole[]`. The Identity Operator configured Keycloak with these roles.
- **SecretsManagement** — only present if `securityFunction.secretsManagement` was declared. Configures vault sidecar injection for component pods.

## Uninstall

```bash
helm delete <release-name> -n components
```

After uninstalling, explain that the Component Operator cleans up all child resources (ExposedAPIs, DependentAPIs, IdentityConfig, etc.) through Kubernetes owner references. The API Gateway routes and Identity Management configurations are also removed.

## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **View the deployed component** — Inspect status, APIs, and decomposed resources |
| 2 | **View ExposedAPIs** — See the API Gateway routes created for this component |
| 3 | **View DependentAPIs** — Check if cross-component dependencies are declared and resolved |
| 4 | **View observability data** — Explore Prometheus metrics and Jaeger traces |
| 5 | **Return to main menu** |
