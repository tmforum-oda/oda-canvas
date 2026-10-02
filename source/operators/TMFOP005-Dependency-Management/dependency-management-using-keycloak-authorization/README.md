# Dependency Management Operator — Keycloak Authorization

## Overview

This operator implements the [TMFOP005 Dependency Management](../README.md) pattern using Keycloak as the authorization policy enforcement point.

When a component's service account is granted a client role in Keycloak, the operator detects the corresponding `CLIENT_ROLE_MAPPING` admin event and automatically resolves the component's API dependencies:

1. Identifies the **user-component** (whose service account receives the role) and the **target-component** (which owns the role's Keycloak client).
2. Lists all `DependentAPI` resources owned by the user-component.
3. For each `DependentAPI`, searches for a matching ready `ExposedAPI` on the target-component, matched by specification URL and `apiType: openapi`.
4. On a match, patches the `DependentAPI` status (`implementation.ready`, `depapiStatus.url`) and creates or updates the corresponding entry in the Canvas Service Inventory.

This approach ties dependency resolution to Keycloak role grants, meaning a component's dependency is only resolved after authorization has been explicitly granted — demonstrating a more production-like environment where API access is policy-controlled.

## Architecture

The operator uses a single startup-managed background polling task. This gives exactly one active loop per operator instance, independent of the number of ODA Component CRD objects in the cluster, without placing a Kopf finalizer on a Helm-managed ConfigMap.

```
Keycloak Admin Events API
        │  CLIENT_ROLE_MAPPING (CREATE / UPDATE / DELETE)
        ▼
keycloak_admin_event_poller (background task)
        │
        ├─ _resolve_event_components()
        │       ├─ user UUID  → service-account username → user-component name
        │       └─ client UUID → clientId                → target-component name
        │
        ├─ _log_role_mapping_event()
        │
        └─ _process_depapi_matches()
                ├─ list DependentAPIs for user-component
                ├─ for each: _find_matching_exposed_api() on target-component
                └─ on match: _set_dependent_api_ready()
                        ├─ _update_service_inventory()  (Canvas Info Service)
                        └─ _patch_dependent_api()       (k8s status patch)
```

## Key Files

| File | Purpose |
|------|---------|
| `dependencyManagementKeycloakAuthzOperator.py` | Main operator — event polling, component resolution, DependentAPI patching |
| `keycloakUtils.py` | Keycloak REST API client (token, admin events, client/user lookup) |
| `service_inventory_client.py` | Canvas Info Service (Service Inventory) REST client |
| `utils.py` | `safe_get()` utility for safe nested dict access |
| `log_wrapper.py` | Structured logging wrapper |
| `templates/create-service-payload.json.jinja2` | Jinja2 template for Service Inventory REST payloads |
| `dependencyManagementKeycloakAuthzOperator-dockerfile` | Dockerfile |
| `requirements.txt` | Python dependencies |

## Configuration

All configuration is injected via Kubernetes ConfigMap and Secret, templated by the Helm chart at `charts/dependency-management-keycloak-authz/`.

| Environment Variable    | Description | Default |
|-------------------------|-------------|---------|
| `KEYCLOAK_BASE`         | Keycloak base URL | *(required)* |
| `KEYCLOAK_REALM`        | Realm to monitor | `odari` |
| `KEYCLOAK_USER`         | Keycloak admin username | *(from Secret)* |
| `KEYCLOAK_PASSWORD`     | Keycloak admin password | *(from Secret)* |
| `POLL_INTERVAL_SECONDS` | Polling interval in seconds | `5` |
| `POD_NAMESPACE`         | Namespace the operator runs in | *(from Downward API)* |
| `CANVAS_INFO_ENDPOINT`  | Canvas Info Service base URL | `http://info.canvas.svc.cluster.local` |
| `LOGGING`               | Python log level (integer) | `20` (INFO) |

## Keycloak Prerequisites

The operator requires admin events to be enabled in the monitored Keycloak realm:

- **Admin Events Enabled**: on
- **Include Representation**: on (required to receive role details in the event payload)

These are configured under **Realm Settings → Events → Admin Events** in the Keycloak admin console, or via the `adminEventsEnabled` / `adminEventsDetailsEnabled` settings in the realm JSON.

The operator verifies these settings at startup and logs a warning if they are not enabled.

## Keycloak Compatibility

Tested against **Keycloak 20**. Notable behaviours:

- `AdminEventRepresentation` has no `id` field — deduplication uses a composite key `(time, operationType, resourcePath)`.
- `dateFrom` accepts date granularity only (`yyyy-MM-dd`), so today's events re-appear on every poll. The composite-key set eliminates replays.
- `resourcePath` format for role mappings: `users/{user-uuid}/role-mappings/clients/{client-uuid}`

## RBAC

The operator's `ClusterRole` (defined in `charts/dependency-management-keycloak-authz/templates/rbac.yaml`) requires:

| Resource | Verbs |
|----------|-------|
| `dependentapis` | `list`, `get`, `patch` |
| `exposedapis` | `list`, `get`, `patch` |

## Build and Deploy

```bash
# Build Docker image
cd source/operators/TMFOP005-Dependency-Management/dependency-management-using-keycloak-authorization
docker build -f dependencyManagementKeycloakAuthzOperator-dockerfile \
  -t tmforumodacanvas/dependency-management-keycloak-authz:0.2.0 .

# Deploy via Helm (as part of canvas-oda umbrella chart)
helm upgrade canvas charts/canvas-oda -n canvas \
  --set dependency-management-keycloak-authz.enabled=true \
  --set dependentapi-simple-operator.enabled=false \
  --no-hooks

# Restart after a local image rebuild (imagePullPolicy: Never)
kubectl rollout restart deployment/dependency-management-keycloak-authz -n canvas
kubectl rollout status deployment/dependency-management-keycloak-authz -n canvas
```

The full build and release process for Docker images is described in [docs/developer/work-with-dockerimages.md](../../../../docs/developer/work-with-dockerimages.md).

## Related Documentation

- [TMFOP005 Dependency Management](../README.md)
- [UC007-Configure-Dependent-APIs](../../../../usecase-library/UC007-Configure-Dependent-APIs.md)
- [Simple Dependency Management Operator](../simple-dependency-management/README.md) — alternative implementation without Keycloak authorization
- [Canvas Design](../../../../Canvas-design.md)
