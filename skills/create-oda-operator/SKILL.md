---
name: create-oda-operator
description: Guide for creating Kubernetes operators for the ODA Canvas using the Python KOPF framework. Covers handler patterns, CRD watching, logging, error handling, Dockerfile construction, Helm chart deployment, and RBAC configuration. Use this skill when building or modifying Canvas operators.
---

# Create ODA Operator — Skill Instructions

## Technology

Many ODA Canvas operators use the **KOPF** (Kubernetes Operator Pythonic Framework) for Python. Other frameworks are also available and `pdb-management` operator uses Go/kubebuilder.

### Dependencies

```
kopf
kubernetes
pykube-ng
pyyaml
```

Additional per-operator: `python-json-logger`, `cloudevents`, `requests`.

## Directory Structure

```
source/operators/<domain>/
  <operatorName>.py           # Main operator file
  log_wrapper.py              # Structured logging (if needed)
  <operatorName>-dockerfile   # Dockerfile (no .ext)
  requirements.txt            # Optional, per-operator deps
```

The matching Helm chart lives at `charts/<operator-chart-name>/`.

## Constants Pattern

Define CRD coordinates and HTTP codes at the top of every operator file:

```python
GROUP = "oda.tmforum.org"
VERSION = "v1"
COMPONENTS_PLURAL = "components"          # or "exposedapis", "dependentapis", etc.
HTTP_CONFLICT = 409
HTTP_NOT_FOUND = 404
```

## Startup Hook

Always configure watcher timeout to prevent stale connections:

```python
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60
```

## Handler Patterns

### Triple-Stacked Handlers (resume + create + update)

The standard pattern for handling a CRD lifecycle — stack all three decorators on one function:

```python
@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def coreAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    # Handler implementation
    pass
```

### Field-Triggered Handlers

Use when reacting to specific status transitions:

```python
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL,
    field="status.summary/status.deployment_status",
    value="In-Progress-IDConfOp", retries=5)
async def identityConfig(meta, spec, status, body, namespace, labels, name, old, new, **kwargs):
    pass
```

### Delete Handlers

```python
@kopf.on.delete(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def componentDelete(meta, spec, status, namespace, name, **kwargs):
    pass
```

## Error Handling

Always distinguish KOPF retryable errors from unexpected exceptions:

```python
try:
    result = await process_resource(spec, namespace, name)
except kopf.TemporaryError as e:
    raise kopf.TemporaryError(e)  # allow operator to retry
except Exception as e:
    logw.error(f"Unhandled exception {e}: {traceback.format_exc()}")
    return []
```

- `kopf.TemporaryError(msg, delay=N)` — retry after N seconds
- `kopf.PermanentError(msg)` — stop retrying
- Never swallow exceptions silently

## Kubernetes API Calls

Use the Python `kubernetes` client:

```python
custom_objects_api = kubernetes.client.CustomObjectsApi()

# GET
try:
    resource = custom_objects_api.get_namespaced_custom_object(
        group=GROUP, version=VERSION,
        namespace=namespace, plural=PLURAL, name=resource_name)
except ApiException as e:
    if e.status == HTTP_NOT_FOUND:
        # create resource
        pass
    else:
        raise kopf.TemporaryError(e)

# CREATE
custom_objects_api.create_namespaced_custom_object(
    group=GROUP, version=VERSION,
    namespace=namespace, plural=PLURAL, body=resource_body)

# PATCH
custom_objects_api.patch_namespaced_custom_object(
    group=GROUP, version=VERSION,
    namespace=namespace, plural=PLURAL, name=resource_name, body=patch)
```

## Logging (LogWrapper)

Use the structured `LogWrapper` for consistent log output:

```python
from log_wrapper import LogWrapper

logw = LogWrapper(handler_name="coreAPIs", function_name="processExposedAPIs")
logw.info("subject", "Processing exposed APIs")
logw.error("subject", f"Failed: {error}")
```

Format: `[componentName|resourceName|handlerName|functionName] subject: message`

## Segment Configuration (Data-Driven)

For operators processing multiple component segments, use a registry:

```python
SEGMENT_CONFIG = {
    "coreAPIs": {
        "spec_path": "coreFunction",
        "status_key": "coreAPIs",
        "segment": "coreFunction"
    },
    "managementAPIs": {
        "spec_path": "managementFunction",
        "status_key": "managementAPIs",
        "segment": "managementFunction"
    },
}
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `COMPONENT_NAMESPACE` | `"components"` | Namespace(s) to monitor |
| `LOGGING` | `logging.INFO` | Log level |
| `COMPONENTNAME_LABEL` | `"oda.tmforum.org/componentName"` | Component label |
| `CICD_BUILD_TIME` | — | Build timestamp (set in Docker) |
| `GIT_COMMIT_SHA` | — | Git commit (set in Docker) |

## Dockerfile Pattern

```dockerfile
FROM python:3.12-alpine
RUN pip install kopf==1.37.2 \
    && pip install kubernetes==27.2.0 \
    && pip install python-json-logger==2.0.7 \
    && pip install PyYAML
COPY ./<operatorName>.py /operator/
COPY ./log_wrapper.py /operator/
ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME $CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA $GIT_COMMIT_SHA
CMD kopf run --namespace=$COMPONENT_NAMESPACE --verbose /operator/<operatorName>.py
```

## Helm Chart for Operator

Every operator needs a Helm chart in `charts/<chart-name>/`:

```
charts/<chart-name>/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml     # Runs kopf with namespace args
    rbac.yaml           # ServiceAccount + ClusterRole + ClusterRoleBinding
    configMap.yaml      # Environment variables
    _helpers.tpl        # Name, labels, Docker image helpers
```

### Key _helpers.tpl Patterns

- Docker image construction: `registry/image:version[-prereleaseSuffix]`
- Force `imagePullPolicy: Always` when prereleaseSuffix is set
- Convert comma-separated namespaces to CLI flags: `"ns1,ns2"` → `"-n ns1 -n ns2"`

### RBAC Requirements

Operators need ClusterRole permissions for:
- KOPF peering: `zalando.org` (clusterkopfpeerings, kopfpeerings)
- CRD management: `apiextensions.k8s.io` (customresourcedefinitions)
- ODA resources: `oda.tmforum.org` (components, exposedapis, etc.)
- Core K8s: pods, services, deployments, configmaps, events, namespaces
- Networking: gateway APIs (Kong, APISIX, Istio) as applicable

## API-Management Operators

API-management operators have a different pattern:
- Watch `exposedapis` CRD (not `components`)
- Handlers may be **synchronous** (not async)
- Create gateway-specific resources (HTTPRoutes, VirtualServices, ApisixRoutes)
- Use additional environment variables: `API_CONNECT_TIMEOUT`, `API_READ_TIMEOUT`, `API_WRITE_TIMEOUT`

## Testing

- Run locally: `kopf run --namespace=components --standalone <operatorName>.py`
- Unit tests: `pytest` in operator directory
- Integration: BDD features in `feature-definition-and-test-kit/`

## Do

- Use triple-stacked handlers (resume + create + update)
- Always set `retries=5` on handlers
- Use `kopf.TemporaryError` for retryable failures
- Use structured logging via LogWrapper
- Load namespace configuration from environment variables
- Use `python:3.12-alpine` as base Docker image

## Don't

- Don't hard-code namespace references
- Don't swallow exceptions without logging
- Don't use synchronous handlers if making multiple API calls (use async)
- Don't duplicate CRD field updates across handlers — use status sub-resource
- Don't edit the `pdb-management` operator as if it were Python/KOPF (it's Go)
