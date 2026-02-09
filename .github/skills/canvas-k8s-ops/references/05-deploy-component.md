# Deploy an ODA Component

## Table of Contents
- [Step 1: Ensure Helm Repo](#step-1-ensure-helm-repo)
- [Step 1b: Check Existing Releases](#step-1b-check-existing-releases)
- [Step 2: List Available Charts](#step-2-list-available-charts)
- [Step 3: Optional Overrides](#step-3-optional-overrides)
- [Step 4: Install](#step-4-install)
- [Step 5: Monitor Deployment](#step-5-monitor-deployment)
- [Uninstall](#uninstall)

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
kubectl get components -n components -o json | python <scripts>/poll_component_status.py [component-name]
```

The script reports progress:
- `In-Progress-CompCon` → "Configuring APIs..."
- `In-Progress-IDConfOp` → "Configuring identity..."
- `In-Progress-SecretMan` → "Configuring secrets..."
- `In-Progress-DepApi` → "Resolving dependent APIs..."
- `Complete` → "Component deployed successfully!"

If status does not reach `Complete` within 10 minutes, suggest:

```bash
kubectl describe component <name> -n components
kubectl get events -n components --sort-by='.lastTimestamp'
```

## Uninstall

```bash
helm delete <release-name> -n components
```
