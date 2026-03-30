---
name: create-oda-operator
description: >
  Guide for creating Kubernetes operators for the ODA Canvas using the Python KOPF framework.
  Use this skill whenever you are building or modifying any Canvas operator, adding a kopf handler to existing code, creating a CRD watcher, implementing component lifecycle management, writing any Python Kubernetes controller, working with files in source/operators/, or answering questions like "how do I watch a CRD", "how do I update status", "how should I structure my operator chart", or "how do I add a health check to my operator".
  Also use for questions about operator peering, admission webhooks, timer/periodic handlers, or any kopf framework question.
---

# Create ODA Operator

## Technology

Most ODA Canvas operators use **KOPF** — [Kubernetes Operators Framework for Python](https://docs.kopf.dev/en/stable/).

The Go-based operators (`pdb-management/`, `oauth2EnvoyfilterOperator/`) are outside this skill's scope.

**Core dependencies (pinned versions used by this project):**
```
kopf==1.37.2
kubernetes==27.2.0
python-json-logger==2.0.7
PyYAML
requests              # for external HTTP calls
```
Additional per-operator: `cloudevents`, `jinja2`, `hvac` (HashiCorp Vault), `google-auth`.

**References:**
- [`references/kopf-docs.md`](references/kopf-docs.md) — curated kopf documentation links by topic
- [`references/operator-catalog.md`](references/operator-catalog.md) — all existing operators with file paths and patterns

## Quick Reference: Existing Operators

Before writing new code, check if an existing operator matches your use case:

| Use case | Reference operator |
|---|---|
| Component/CRD lifecycle, sub-resource management | `source/operators/TMFOP001-Component-Management/component-management/` |
| API gateway integration (HTTPRoute, Kong plugins) | `source/operators/TMFOP002-API-Management/kong/` |
| Service mesh integration (VirtualService, EndpointSlice) | `source/operators/TMFOP002-API-Management/istio/` |
| External identity service integration + health timers | `source/operators/TMFOP003-Identity-Config/keycloak/` |
| Pod sidecar injection, admission webhooks | `source/operators/TMFOP007-Secrets-Management/vault/` |
| Cross-resource URL discovery, dependency resolution | `source/operators/TMFOP005-Dependency-Management/simple-dependency-management/` |
| Field-triggered handler, Kubernetes Secret creation | `source/operators/TMFOP004-Credentials-Management/credentials-management/` |

See `references/operator-catalog.md` for kopf decorators used and detailed patterns in each.

## Directory Structure

Operators are organised under `source/operators/` in two-level directories:

```
source/operators/TMFOP###-<Domain>/
  <implementation>/
    <operatorName>.py           # Main operator file
    log_wrapper.py              # Structured logging shared helper
                                #  (copy from TMFOP001-Component-Management/component-management/)
    <operatorName>-dockerfile   # Dockerfile (no extension)
    requirements.txt            # Optional per-operator deps
```

The matching Helm chart lives at `charts/<operator-chart-name>/`.

## Constants & Startup

Define CRD coordinates and HTTP codes at the top of every operator:

```python
GROUP = "oda.tmforum.org"
VERSION = "v1"
COMPONENTS_PLURAL = "components"   # or "exposedapis", "dependentapis", "identityconfigs", etc.
HTTP_CONFLICT = 409
HTTP_NOT_FOUND = 404
```

Always configure the watcher timeout in a startup hook to recover from stale watch connections:

```python
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60  # recover from broken watchers every 60s
    # Optional — see https://docs.kopf.dev/en/stable/configuration/
    # settings.posting.level = logging.WARNING    # reduce K8s event verbosity
    # settings.peering.priority = 100             # set if running alongside other operators
```

## Handler Patterns

### Create / Resume / Update (triple-stacked)

The standard CRD lifecycle pattern — one function handles all three events. `resume` fires when
the operator starts and finds pre-existing objects, ensuring continuity after restarts.

```python
@kopf.on.resume(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
@kopf.on.update(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def coreAPIs(meta, spec, status, body, namespace, labels, name, **kwargs):
    pass
```

Docs: https://docs.kopf.dev/en/stable/handlers/

### Delete Handlers

```python
@kopf.on.delete(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def componentDelete(meta, spec, status, namespace, name, **kwargs):
    pass
```

Kopf adds a finalizer so the object isn't fully deleted until this handler succeeds.
Pass `optional=True` if the handler shouldn't block object deletion.

### Field Handlers

React to specific field changes. Use a `when=` callback to conditionally filter to avoid
re-processing unchanged states:

```python
def is_status_changed(status, **kwargs):
    return status.get("identityConfig") != "In-Progress-Done"

@kopf.on.field(GROUP, VERSION, COMPONENTS_PLURAL,
               field="status.identityConfig",
               when=is_status_changed, retries=5)
async def identityConfig(meta, spec, status, old, new, namespace, **kwargs):
    pass
```

Docs: https://docs.kopf.dev/en/stable/filters/

### Timer Handlers

Run periodically as long as the object exists — useful for health polling and reconciliation.
`idle` waits for the resource to stabilise before first invocation:

```python
@kopf.timer(GROUP, VERSION, "identityconfigs", interval=300.0, idle=30.0)
async def healthProbe(spec, status, namespace, name, **kwargs):
    # Periodic reconciliation / external service health check
    pass
```

Docs: https://docs.kopf.dev/en/stable/timers/

### Health Check Probes

Expose a health endpoint Kubernetes liveness probes can call:

```python
@kopf.on.probe(id="http-check")
def check_http_connection(**kwargs) -> str:
    resp = requests.get(SERVICE_URL, timeout=10)
    resp.raise_for_status()
    return "ok"
```

Docs: https://docs.kopf.dev/en/stable/probing/

### Low-Level Event Watching

Watch raw watch-stream events without kopf storing handler state — useful for mirroring changes
from another operator's CRDs or for lightweight reactive logic:

```python
@kopf.on.event(GROUP, VERSION, "exposedapis")
def onExposedAPIEvent(event, body, **kwargs):
    if event["type"] in (None, "ADDED", "MODIFIED"):
        pass  # react to changes; no retry/status tracking by kopf
```

Docs: https://docs.kopf.dev/en/stable/handlers/#event-watching-handlers

### Admission / Mutation Webhooks

Intercept resource creation/updates before they reach the cluster — the secretsmanagement
operator uses this to inject a Vault sidecar into pods:

```python
@kopf.on.mutate("", "v1", "pods", operation="CREATE")
async def inject_sidecar(patch, spec, namespace, **kwargs):
    if should_inject(spec):
        patch.spec.setdefault("containers", []).append(SIDECAR_CONTAINER)
```

Requires a webhook server configured in startup. In-cluster, use a `ServiceTunnel` so Kubernetes
calls back via the operator's Service DNS name. For simpler cases kopf can manage the webhook
configuration automatically:

```python
@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, **_):
    settings.admission.server = kopf.WebhookServer(addr="0.0.0.0", port=8080)
    settings.admission.managed = "auto.kopf.dev"
    settings.peering.priority = 200  # ensure admission operator has highest priority
```

See `source/operators/TMFOP007-Secrets-Management/vault/docker/` for the full `ServiceTunnel` implementation.
Docs: https://docs.kopf.dev/en/stable/admission/

### Sub-Handlers

Process a list of items with per-item kopf lifecycle (retries, status, logging):

```python
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL)
async def processAPIs(spec, **_):
    for api in spec.get("coreFunction", {}).get("exposedAPIs", []):
        @kopf.subhandler(id=api["name"])
        def handle_api(api=api, **kwargs):
            pass
```

Docs: https://docs.kopf.dev/en/stable/handlers/#sub-handlers

## Error Handling

Three error categories — pick the right one to control retry behaviour:

```python
# Transient failure — kopf will retry after delay (default delay is 60s)
raise kopf.TemporaryError("External service not ready", delay=30)

# Permanent failure — stop retrying, mark handler as failed
raise kopf.PermanentError("Invalid spec: field X is required")

# Configure error mode per handler (default is TEMPORARY = retry forever)
@kopf.on.create(GROUP, VERSION, PLURAL,
                errors=kopf.ErrorsMode.PERMANENT,
                retries=5,
                backoff=30)
async def handler(**_): ...
```

Always handle `ApiException` explicitly when calling the Kubernetes client:

```python
from kubernetes.client.rest import ApiException

try:
    resource = custom_api.get_namespaced_custom_object(...)
except ApiException as e:
    if e.status == HTTP_NOT_FOUND:
        pass  # create it
    else:
        raise kopf.TemporaryError(str(e), delay=30)
```

Docs: https://docs.kopf.dev/en/stable/errors/

## Status Updates & Results Delivery

A handler's return value is automatically written to `status.<handler_id>`. Use a dict to
store structured results:

```python
@kopf.on.create(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
async def coreAPIs(name, **kwargs):
    result = await processAPIs(...)
    return {"apiCount": len(result), "status": "Active"}  # → status.coreAPIs = {...}
```

Docs: https://docs.kopf.dev/en/stable/results/

## Kubernetes API Calls

```python
import kubernetes

# Custom resources (CRDs)
coa = kubernetes.client.CustomObjectsApi()

# Idempotent create-or-update pattern
try:
    coa.get_namespaced_custom_object(GROUP, VERSION, namespace, PLURAL, name)
    coa.patch_namespaced_custom_object(GROUP, VERSION, namespace, PLURAL, name, body)
except ApiException as e:
    if e.status == HTTP_NOT_FOUND:
        coa.create_namespaced_custom_object(GROUP, VERSION, namespace, PLURAL, body)
    else:
        raise kopf.TemporaryError(str(e), delay=30)

# Core Kubernetes resources
core_v1 = kubernetes.client.CoreV1Api()
core_v1.create_namespaced_secret(namespace, secret_body)

# List cluster-wide resources for cross-resource discovery
all_apis = coa.list_cluster_custom_object(GROUP, VERSION, "exposedapis")

# Watch non-CRD resources (e.g. EndpointSlice for service implementation discovery)
@kopf.on.create("discovery.k8s.io", "v1", "endpointslices", retries=5)
@kopf.on.update("discovery.k8s.io", "v1", "endpointslices", retries=5)
async def onEndpointSlice(meta, spec, namespace, name, **kwargs):
    pass
```

Docs: https://docs.kopf.dev/en/stable/idempotence/

## Resource Hierarchies

Use `kopf.adopt()` to set `ownerReferences` on child resources so they are deleted with the
parent (cascaded deletion):

```python
child = {"apiVersion": "oda.tmforum.org/v1", "kind": "ExposedAPI", ...}
kopf.adopt(child)   # sets ownerReferences, namespace, and labels from current handler context
coa.create_namespaced_custom_object(GROUP, VERSION, namespace, "exposedapis", child)
```

Individual hierarchy helpers when you need fine-grained control:

```python
kopf.label(objs, {"oda.tmforum.org/componentName": name})   # add labels
kopf.harmonize_naming(objs, name, strict=True)               # align name to parent
kopf.adjust_namespace(objs, namespace, forced=True)          # set namespace
```

Docs: https://docs.kopf.dev/en/stable/hierarchies/

## Async vs Sync

- Use `async def` for handlers that make multiple Kubernetes or external HTTP API calls — keeps the event loop unblocked so other resources are handled concurrently
- Sync handlers are fine for lightweight single-purpose logic (many API-management operators use sync)
- If you have many sync handlers, scale the worker pool: `settings.execution.max_workers = 20`

Docs: https://docs.kopf.dev/en/stable/async/

## Logging

Use the shared `LogWrapper` for consistent structured log output across all operators:

```python
from log_wrapper import LogWrapper

logging_level = os.environ.get("LOGGING", logging.INFO)
logger = logging.getLogger("OperatorName")
logger.setLevel(int(logging_level))
LogWrapper.set_defaultLogger(logger)

logw = LogWrapper(handler_name="coreAPIs", function_name="processExposedAPIs")
logw.set(component_name=name, resource_name=api_name)
logw.info("Processing", f"Found {len(apis)} APIs")
logw.error("Failed", f"{e}: {traceback.format_exc()}")
```

Log format: `[componentName|resourceName|handlerName|functionName] subject: message`

Simple operators (e.g. `credentials-management`) may use standard `logging` without `LogWrapper`.

## Segment Configuration (Data-Driven)

For operators processing multiple named segments of a Component spec, use a registry to avoid
duplicating handler logic. The component-management operator uses this pattern for six segments:

```python
SEGMENT_CONFIG = {
    "coreAPIs":       {"spec_path": "coreFunction",       "status_key": "coreAPIs"},
    "managementAPIs": {"spec_path": "managementFunction", "status_key": "managementAPIs"},
    "securityAPIs":   {"spec_path": "securityFunction",   "status_key": "securityAPIs"},
}

# One implementation driven by SEGMENT_CONFIG[kwargs["handler"].id]
```

## Peering Configuration

When multiple operators run in the same cluster watching overlapping resources, set distinct
priorities. Higher priority wins; equal priority causes both operators to freeze.

```python
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.peering.priority = 200      # secretsmanagement: 200 (highest)
    settings.peering.name = "default"    # uses ClusterKopfPeering named "default"
    settings.watching.server_timeout = 1 * 60
```

ODA Canvas priority conventions:
- Most operators: leave unset (priority=0, auto-standalone if no peering object found)
- `secretsmanagement-operator`: 200 (admission webhooks must stay responsive)
- `dependentapi-operator`: 110 (uses custom named peering object `"dependentapi"`)

Docs: https://docs.kopf.dev/en/stable/peering/

## Admission Webhooks (Advanced)

The `secretsmanagementOperator` uses a custom `ServiceTunnel` class so the Kubernetes API server
calls the webhook via the operator's in-cluster Service DNS name:

```python
class ServiceTunnel:
    async def __call__(self, fn: kopf.WebhookFn) -> AsyncIterator[kopf.WebhookClientConfig]:
        namespace = os.environ.get("WEBHOOK_SERVICE_NAMESPACE")
        svc_name  = os.environ.get("WEBHOOK_SERVICE_NAME")
        yield kopf.WebhookClientConfigService(name=svc_name, namespace=namespace, path="/")
        await asyncio.Event().wait()

@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, **_):
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = "auto.kopf.dev"
    settings.peering.priority = 200
```

Requires RBAC for `admissionregistration.k8s.io` (`mutatingwebhookconfigurations` with verbs
`create`, `patch`).

Docs: https://docs.kopf.dev/en/stable/admission/

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `COMPONENT_NAMESPACE` | `"components"` | Namespace(s) to monitor (comma-separated) |
| `LOGGING` | `logging.INFO` | Log level integer |
| `COMPONENTNAME_LABEL` | `"oda.tmforum.org/componentName"` | Label key for component name |
| `CICD_BUILD_TIME` | — | Build timestamp injected via Dockerfile `ARG` |
| `GIT_COMMIT_SHA` | — | Git commit injected via Dockerfile `ARG` |

API-management operators additionally use: `API_CONNECT_TIMEOUT`, `API_READ_TIMEOUT`, `API_WRITE_TIMEOUT`, plus gateway-specific variables (hostnames, credentials).

## Dockerfile Pattern

```dockerfile
FROM python:3.12-alpine
RUN pip install kopf==1.37.2 \
    && pip install kubernetes==27.2.0 \
    && pip install python-json-logger==2.0.7 \
    && pip install PyYAML requests
COPY ./<operatorName>.py /operator/
COPY ./log_wrapper.py /operator/
ARG CICD_BUILD_TIME
ENV CICD_BUILD_TIME=$CICD_BUILD_TIME
ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA
CMD kopf run --namespace=$COMPONENT_NAMESPACE --verbose /operator/<operatorName>.py
```

Docs: https://docs.kopf.dev/en/stable/docker/

## Helm Chart for Operator

Every operator needs a chart in `charts/<chart-name>/`. See `charts/component-operator/` as the
canonical example.

### Standard Structure
```
charts/<chart-name>/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml   # Runs kopf with namespace CLI args
    rbac.yaml         # ServiceAccount + ClusterRole + ClusterRoleBinding
    configMap.yaml    # Non-sensitive env vars (log level, namespaces, URLs)
    _helpers.tpl      # dockerimage, labels, monitoredNamespacesCLIOpts helpers
```

Add `secret.yaml` for credentials. Add `certificate.yaml` for webhook TLS via cert-manager.

### Shared Helpers (always reuse from umbrella chart)

The umbrella chart `charts/canvas-oda/templates/_helpers.tpl` provides two helpers that every
operator chart must reuse — do not reimplement them:

- **`docker.registry`** — registry prefix with trailing slash, or empty string
- **`image-pull-secrets`** — `imagePullSecrets:` block from `global.imagePullSecrets`

In your `_helpers.tpl`:
```yaml
{{- define "myoperator.dockerimage" -}}
  {{ include "docker.registry" . }}{{ .Values.deployment.image }}:{{ .Values.deployment.version -}}
  {{- if .Values.deployment.prereleaseSuffix }}-{{ .Values.deployment.prereleaseSuffix }}{{- end -}}
{{- end -}}

{{/* Converts "ns1,ns2" → "-n ns1 -n ns2" for kopf run CLI */}}
{{- define "myoperator.monitoredNamespacesCLIOpts" -}}
{{- printf "-n %s" .Values.deployment.monitoredNamespaces | replace "," " -n " }}
{{- end -}}
```

When `prereleaseSuffix` is set, force `imagePullPolicy: Always`. In `deployment.yaml`:
```yaml
image: {{ include "myoperator.dockerimage" . }}
imagePullPolicy: {{ if .Values.deployment.prereleaseSuffix }}Always{{ else }}{{ .Values.deployment.imagePullPolicy }}{{ end }}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- include "image-pull-secrets" . | nindent 6 }}
{{- end }}
```

### RBAC Requirements

All kopf operators need `ClusterRole` permissions for:
- Kopf peering: `kopf.dev` (`clusterkopfpeerings`, `kopfpeerings`)
- K8s events: `""` and `events.k8s.io` (create, patch, get)
- CRD discovery: `apiextensions.k8s.io` (`customresourcedefinitions`, list/watch/get)
- ODA resources: `oda.tmforum.org` — specific plurals (components, exposedapis, etc.)
- Gateway-specific CRDs for API-management operators (Kong, APISIX, Istio)

Operators creating namespace-scoped resources (Secrets, ConfigMaps) also add a `Role` + `RoleBinding`.

Docs: https://docs.kopf.dev/en/stable/deployment/

## API-Management Operators

API-management operators follow a distinct sub-pattern:
- Watch `exposedapis` CRD (not `components`)
- Create gateway-specific routing resources (HTTPRoute, VirtualService, ApisixRoute)
- Watch `EndpointSlice` or `Service` resources to discover service implementation details
- Some use synchronous handlers (single Kubernetes API call per handler is fine without async)
- Each gateway lives in its own directory under `source/operators/TMFOP002-API-Management/`

See `references/operator-catalog.md` for details on each gateway implementation.

## Testing

Run locally during development:
```bash
# Standalone mode — no peering object required, good for local dev
kopf run --namespace=components --standalone <operatorName>.py

# Multiple namespaces with wildcard (how the Helm chart deploys it)
kopf run -n components -n odacompns-* --verbose <operatorName>.py
```

Integration testing with `kopf.testing.KopfRunner`:
```python
from kopf.testing import KopfRunner
import subprocess, time

def test_operator():
    with KopfRunner(["run", "--standalone", "-n", "default", "myoperator.py"]) as runner:
        subprocess.run("kubectl apply -f test-component.yaml", shell=True, check=True)
        time.sleep(2)
        subprocess.run("kubectl delete -f test-component.yaml", shell=True, check=True)
        time.sleep(1)
    assert runner.exit_code == 0
    assert runner.exception is None
```

BDD integration tests are in `feature-definition-and-test-kit/`.
Docs: https://docs.kopf.dev/en/stable/testing/

## Do

- Use triple-stacked handlers (resume + create + update) for CRD lifecycle
- Always set `retries=5` on handlers; use `kopf.TemporaryError(delay=N)` for appropriate backoff
- Set `settings.watching.server_timeout = 1 * 60` in the startup hook
- Use `kopf.PermanentError` when the failure is definitively unrecoverable
- Use structured logging via `LogWrapper`
- Load namespace configuration from environment variables, never hard-code
- Use `kopf.adopt()` to link child resources to their parent for cascaded deletion
- Use `python:3.12-alpine` as the Dockerfile base image
- Reuse shared Helm helpers (`docker.registry`, `image-pull-secrets`) from the umbrella chart

## Don't

- Don't hard-code namespace references — use Helm template variables and env vars
- Don't swallow exceptions without logging (`except Exception: pass` is forbidden)
- Don't block the event loop with synchronous I/O inside `async def` handlers — use `await` or `asyncio.to_thread()`
- Don't duplicate CRD status field updates across handlers — use status sub-resource + field handlers to propagate changes
- Don't add a new operator-managed CRD field without updating `source/webhooks/` conversion logic
- Don't edit `pdb-management/` or `oauth2EnvoyfilterOperator/` as if they were Python/KOPF (they're Go/kubebuilder)

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
