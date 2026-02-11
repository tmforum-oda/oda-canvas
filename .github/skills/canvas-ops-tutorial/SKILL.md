---
name: canvas-ops-tutorial
description: Interactive tutorial for learning and exploring the ODA Canvas on Kubernetes. Guides users through architecture concepts, CRD schemas, component deployment, API inspection, dependency resolution, observability, and BDD testing via context-aware menus. Use when a user wants to understand, explore, or operate an ODA Canvas cluster.
---

# ODA Canvas Kubernetes Tutorial

An interactive, guided tutorial for learning and operating the ODA Canvas on Kubernetes. Present the **main menu** below when activated using `ask_questions` and let the user choose an action.

| # | Action | Reference |
|---|--------|-----------|
| 1 | **About ODA Canvas** — Learn the architecture, CRDs, operators, and how components are decomposed | [references/01-about-oda-canvas.md](references/01-about-oda-canvas.md) |
| 2 | **Install ODA Canvas** — Check prerequisites, choose a gateway (Istio/Kong/APISIX), and install or troubleshoot a Canvas | [references/02-install-oda-canvas.md](references/02-install-oda-canvas.md) |
| 3 | **Manage ODA Components** — Deploy, view, and inspect Component custom resources | [references/03-deploy-component.md](references/03-deploy-component.md), [references/04-view-components.md](references/04-view-components.md) |
| 4 | **View APIs** — Inspect ExposedAPI and DependentAPI custom resources and their status | [references/05-view-exposedapis.md](references/05-view-exposedapis.md), [references/06-view-dependentapis.md](references/06-view-dependentapis.md) |
| 5 | **View Observability Data** — Access Prometheus, Grafana, and Jaeger UIs | [references/07-view-observability.md](references/07-view-observability.md) |
| 6 | **Manage Identities** — View IdentityConfig resources, access Keycloak UI, and create external clients for API access | [references/08-manage-identities.md](references/08-manage-identities.md) |
| 7 | **Run BDD Feature Tests** — Execute Behaviour-Driven Design test scenarios | [references/09-run-bdd-tests.md](references/09-run-bdd-tests.md) |

Read the corresponding reference file(s) before executing the user's chosen action. For consolidated items (3 and 4), present a sub-menu using `ask_questions` so the user can pick the specific action (e.g., deploy vs. view components, or ExposedAPIs vs. DependentAPIs), then read the relevant reference file.

## Tutorial Interaction Rules

Follow these rules throughout every interaction:

### Menu Presentation
- **On activation**: Always present the 7-item main menu above using `ask_questions` so the user can pick interactively.
- **After every action**: Present a **contextual sub-menu** of 2–4 suggested next steps relevant to what was just done, with **"Return to main menu"** always as the last option. Use `ask_questions` for these sub-menus too.
- **On "Return to main menu"**: Re-present the full 7-item main menu.

### Educational Explanations
- After running any command or showing any output, **explain what the output means** in the context of the ODA Canvas architecture: what the resources are, which operator manages them, and how they fit into the component lifecycle.
- **Show CRD schema context** when relevant — use one or more of the three CRD sources described below to show users the actual resource structure.
- **Show the reproducible commands** — always display the `kubectl` or `helm` commands used, formatted as copyable code blocks, so the user can repeat them independently.

### CRD Education — Three Sources

When explaining resource structures, reference these sources:

| Source | When to use | How |
|--------|------------|-----|
| **Live cluster** | Interactive exploration | `kubectl explain component.spec`, `kubectl get crd <name> -o yaml` |
| **CRD Helm templates** | Show authoritative schema | Read from `charts/oda-crds/templates/` — see file table below |
| **Example components** | Show concrete YAML | Read from `feature-definition-and-test-kit/testData/` — see directory table below |

**CRD template files** (in `charts/oda-crds/templates/`):

| File | Resource | v1 schema location |
|------|----------|-------------------|
| `oda-component-crd.yaml` | Component | ~line 1858 |
| `oda-exposedapi-crd.yaml` | ExposedAPI | ~line 337 |
| `oda-dependentapi-crd.yaml` | DependentAPI | ~line 176 |
| `oda-identityconfig-crd.yaml` | IdentityConfig | ~line 66 |
| `oda-secretsmanagement-crd.yaml` | SecretsManagement | ~line 150 |
| `oda-publishednotification-crd.yaml` | PublishedNotification | ~line 231 |
| `oda-subscribednotification-crd.yaml` | SubscribedNotification | ~line 237 |

**Example component directories** (in `feature-definition-and-test-kit/testData/`):

| Directory | Demonstrates |
|-----------|-------------|
| `productcatalog-v1/` | Base component: core, management, and security functions |
| `productcatalog-dependendent-API-v1/` | Declaring dependent APIs |
| `productcatalog-static-roles-v1/` | Static `componentRole` definitions |
| `productcatalog-v1-sman/` | `secretsManagement` sidecar config |
| `productcatalog-dynamic-roles-v1/` | MCP API type + gatewayConfiguration |
| `productinventory-v1/` | Product Inventory component |

The rendered component template is in each directory's `templates/component-productcatalog.yaml`. Show these to users as concrete examples of Component specifications.

## Prerequisites

Verify cluster access before running any commands:

```bash
kubectl cluster-info
```

If this fails, inform the user that a valid kubeconfig and cluster connection are required.

### Shell Compatibility

Commands use bash syntax. On **Windows PowerShell**: replace `grep` with `Select-String`, `2>/dev/null` with `2>$null`, and use `&&` carefully.

### Helper Scripts

PowerShell mangles escaped quotes in inline Python. Use the **pre-built helper scripts** in `scripts/` instead. Replace `<scripts>` with the absolute path to `.github/skills/canvas-k8s-ops/scripts/`.

| Script | Purpose | Usage |
|--------|---------|-------|
| `parse_components.py` | Component list summary | `kubectl get components -n components -o json \| python <scripts>/parse_components.py` |
| `parse_component_drilldown.py` | Component drill-down | `kubectl get component <name> -n components -o json \| python <scripts>/parse_component_drilldown.py` |
| `parse_exposedapis.py` | ExposedAPI list summary | `kubectl get exposedapis -n components -o json \| python <scripts>/parse_exposedapis.py` |
| `parse_exposedapi_drilldown.py` | ExposedAPI drill-down | `kubectl get exposedapi <name> -n components -o json \| python <scripts>/parse_exposedapi_drilldown.py` |
| `parse_dependentapis.py` | DependentAPI resolution status | `kubectl get dependentapis -n components -o json \| python <scripts>/parse_dependentapis.py` |
| `discover_observability.py` | Find observability services | `kubectl get svc -A -o json \| python <scripts>/discover_observability.py` |
| `parse_identityconfigs.py` | IdentityConfig list summary | `kubectl get identityconfigs -n components -o json \| python <scripts>/parse_identityconfigs.py` |
| `parse_identityconfig_drilldown.py` | IdentityConfig drill-down | `kubectl get identityconfig <name> -n components -o json \| python <scripts>/parse_identityconfig_drilldown.py` |
| `manage_keycloak_users.py` | Keycloak user and client management | `python <scripts>/manage_keycloak_users.py --keycloak-url <URL> --admin-password <PASS> --realm odari --action <ACTION>` |
| `poll_component_status.py` | Deployment status check | `kubectl get components -n components -o json \| python <scripts>/poll_component_status.py [name]` |
| `check_bdd_deps.py` | Check BDD test dependencies | `python <scripts>/check_bdd_deps.py <path-to-feature-definition-and-test-kit>` |
| `exercise_catalog_api.py` | Generate TMF620 API metrics | `python <scripts>/exercise_catalog_api.py <api-base-url> [--rounds N] [--cleanup]` |
| `inspect_mcp_server.py` | Inspect MCP server capabilities | `python <scripts>/inspect_mcp_server.py <mcp-endpoint-url>` |
| `generate_postman_collection.py` | Generate Postman collection for authenticated API testing | `python <scripts>/generate_postman_collection.py --keycloak-url <URL> --client-id <ID> --client-secret <SECRET> --api-base-url <URL> --output <FILE>` |

These scripts work on both bash and PowerShell. For custom parsing beyond what these provide, create a temporary `.py` file, pipe to it, and delete it when done.

## Do

- Verify cluster access with `kubectl cluster-info` before running commands
- Default to the `components` namespace for ODA resources
- Present both raw kubectl output and structured summaries; offer drill-down after summaries
- After every action, explain what the output means: what the resources are, which operator manages them, and how they fit into the ODA component lifecycle
- Show relevant CRD schema snippets when explaining resources — use `kubectl explain`, CRD template files, or testData examples as appropriate
- Reference example component YAMLs from `feature-definition-and-test-kit/testData/` when explaining resource structure
- Always show the kubectl/helm commands used so the user can repeat them independently
- Present contextual sub-menus after each action using `ask_questions` with 2–4 relevant next steps plus "Return to main menu"
- Auto-discover observability service locations — do not assume a namespace
- Handle missing observability stack or DependentAPIs gracefully with guidance
- Run port-forward as a background process so UIs remain accessible
- Run `helm repo update oda-components` before `helm search repo`
- Check existing Helm releases with `helm list -n components` before deploying
- Monitor component deployment until `Complete` status or timeout
- Auto-check and install npm dependencies before running BDD tests
- Check for required environment variables based on the specific test
- Highlight the Cucumber Report URL from test output
- Warn that BDD tests deploy their own components (release name `ctk`) and offer cleanup
- Use shell-appropriate commands (bash vs PowerShell) based on the user's environment

## Don't

- Do not show output without explaining what it means and how it relates to the ODA architecture
- Do not assume the observability stack or ServiceMonitor CRDs are installed — check first
- Do not run BDD tests without verifying dependencies (all 5 utility packages + main)
- Do not hard-code IP addresses or external URLs for services
- Do not leave port-forward processes or BDD test components running without offering cleanup
- Do not run all BDD tests at once without user confirmation (full suite can take over an hour)
- Do not deploy components without confirming chart selection with the user
- Do not skip `helm repo update` — stale indexes return no results
- Do not print Kubernetes secrets or credentials in plain text unless required
- Do not use bash-only syntax without PowerShell alternatives
- Do not present menu options as plain text — always use `ask_questions` for interactive selection
- Do not offer to remove or uninstall Istio — all gateway options (Istio, Kong, APISIX) require Istio for internal traffic management inside the cluster; the gateway choice only affects which component handles external API exposure
- Do not create, delete, or modify gateway resources (KongPlugins, HTTPRoutes, KongConsumers, Istio VirtualServices, etc.) directly — all gateway configuration must be done by editing the **Component** or **ExposedAPI** CRDs, and the API Operator translates those to gateway-specific resources automatically
````
