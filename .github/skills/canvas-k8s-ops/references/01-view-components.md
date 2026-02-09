# View Deployed ODA Components

## Table of Contents
- [Default Namespace](#default-namespace)
- [Commands](#commands)
- [Key Fields](#key-fields)
- [Deployment Status Progression](#deployment-status-progression)
- [Drill-Down](#drill-down)

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

The `deployment_status` follows this state machine:

1. `In-Progress-CompCon` — APIs being configured by component operator
2. `In-Progress-IDConfOp` — All ExposedAPIs ready; waiting for identity config
3. `In-Progress-SecretMan` — Identity configured; waiting for secrets management
4. `In-Progress-DepApi` — Secrets done; waiting for dependent APIs
5. `Complete` — All subsystems ready

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
