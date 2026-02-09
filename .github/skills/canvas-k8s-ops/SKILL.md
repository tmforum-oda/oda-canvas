---
name: canvas-k8s-ops
description: Interact with a live ODA Canvas on Kubernetes — view Components, ExposedAPIs, DependentAPIs, observability data, deploy components, and run BDD tests.
---

# ODA Canvas Kubernetes Interaction

Interact with a live ODA Canvas deployment on Kubernetes. Present the menu below when activated and ask the user which action to perform.

| # | Action | Reference |
|---|--------|-----------|
| 1 | **View deployed ODA Components** — List and inspect Component custom resources | [references/01-view-components.md](references/01-view-components.md) |
| 2 | **View ExposedAPIs** — List and inspect ExposedAPI custom resources | [references/02-view-exposedapis.md](references/02-view-exposedapis.md) |
| 3 | **View DependentAPIs** — Inspect dependency resolution status | [references/03-view-dependentapis.md](references/03-view-dependentapis.md) |
| 4 | **View Observability Data** — Access Prometheus, Grafana, and Jaeger UIs | [references/04-view-observability.md](references/04-view-observability.md) |
| 5 | **Deploy an ODA Component** — Install a reference example component from Helm | [references/05-deploy-component.md](references/05-deploy-component.md) |
| 6 | **Run BDD Feature Tests** — Execute Behaviour-Driven Design test scenarios | [references/06-run-bdd-tests.md](references/06-run-bdd-tests.md) |

Read the corresponding reference file before executing the user's chosen action.

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
| `poll_component_status.py` | Deployment status check | `kubectl get components -n components -o json \| python <scripts>/poll_component_status.py [name]` |
| `check_bdd_deps.py` | Check BDD test dependencies | `python <scripts>/check_bdd_deps.py <path-to-feature-definition-and-test-kit>` |
| `exercise_catalog_api.py` | Generate TMF620 API metrics | `python <scripts>/exercise_catalog_api.py <api-base-url> [--rounds N] [--cleanup]` |

These scripts work on both bash and PowerShell. For custom parsing beyond what these provide, create a temporary `.py` file, pipe to it, and delete it when done.

## Do

- Verify cluster access with `kubectl cluster-info` before running commands
- Default to the `components` namespace for ODA resources
- Present both raw kubectl output and structured summaries; offer drill-down after summaries
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

- Do not assume the observability stack or ServiceMonitor CRDs are installed — check first
- Do not run BDD tests without verifying dependencies (all 5 utility packages + main)
- Do not hard-code IP addresses or external URLs for services
- Do not leave port-forward processes or BDD test components running without offering cleanup
- Do not run all BDD tests at once without user confirmation (full suite can take over an hour)
- Do not deploy components without confirming chart selection with the user
- Do not skip `helm repo update` — stale indexes return no results
- Do not print Kubernetes secrets or credentials in plain text unless required
- Do not use bash-only syntax without PowerShell alternatives
````
