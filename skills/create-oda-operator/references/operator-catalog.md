# ODA Canvas Operator Catalog

All Python/KOPF operators live under `source/operators/`. The Go-based operators
(`pdb-management/`, `oauth2EnvoyfilterOperator/`) are outside the scope of this skill.

---

## Component Management Operator

**Location:** `source/operators/TMFOP001-Component-Management/component-management/componentOperator.py`  
**Helm chart:** `charts/component-operator/`  
**CRDs watched:** `components.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/component-operator`

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.resume/create/update` × 6 handlers (coreAPIs, managementAPIs, securityAPIs, coreDependentAPIs, managementDependentAPIs, securityDependentAPIs)
- `@kopf.on.update` — watches child resources to propagate status up to parent component
- `@kopf.on.resume/create` — adopts existing K8s child resources (Services, Deployments, PVCs, Jobs, StatefulSets, CronJobs, ConfigMaps, Secrets, ServiceAccounts, Roles, RoleBindings)
- `@kopf.on.field` — responds to component status field changes

**Key patterns:**
- **Data-driven `SEGMENT_CONFIG` dict** — maps handler name to spec path and status key, allowing one function body to service all six segment handlers
- **`kopf.adopt()`** — sets ownerReferences so child resources are deleted with the component
- **Child → parent status propagation** — `@kopf.on.update` on child CRDs reads child status and patches the parent component's status
- **Creates `ExposedAPI` and `DependentAPI` custom resources** as children of `Component`
- **`safe_get(default, dict, *paths)` helper** — safely navigates nested dicts without KeyError
- **`quick_get_comp_name(body)` helper** — extracts component name from `oda.tmforum.org/componentName` label

**Use as template when:**
- Building an operator that decomposes a top-level CRD into multiple child CRDs
- Implementing status rollup from child resources to parent
- Managing many resource types as children of a single parent

---

## API Management — Kong

**Location:** `source/operators/TMFOP002-API-Management/kong/apiOperatorKong.py`  
**Helm chart:** `charts/kong-gateway/`  
**CRDs watched:** `exposedapis.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/api-operator-kong`

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.resume/create/update` — ExposedAPI lifecycle
- `@kopf.on.delete` — cleanup routing rules and plugins

**Key patterns:**
- Creates **`HTTPRoute`** (Gateway API) resources referencing the component's Service
- Creates **`ReferenceGrant`** to allow cross-namespace HTTPRoute → Service references
- Creates **`KongPlugin`** resources for rate limiting, API key verification, CORS
- Timeout values expressed in **milliseconds** format (Kong-specific)
- Mix of sync and async handlers

**Use as template when:**
- Building an API gateway integration using standard Kubernetes Gateway API (HTTPRoute)
- Managing Kong-specific plugin configuration alongside routing rules

---

## API Management — Apache APISIX

**Location:** `source/operators/TMFOP002-API-Management/apache-apisix/apiOperatorApisix.py`  
**Helm chart:** `charts/apisix-gateway/`  
**CRDs watched:** `exposedapis.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/api-operator-apisix`

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.resume/create/update` — ExposedAPI lifecycle
- `@kopf.on.delete` — cleanup
- `@kopf.on.field` — watches `status.apiStatus` and `status.implementation`

**Key patterns:**
- Creates **`ApisixRoute`** and **`ApisixPluginConfig`** resources
- Template-based plugin generation for policies
- Timeout values in **string format** (e.g., `"60s"`, `"900s"`) — APISIX-specific

**Use as template when:**
- Building an operator that creates APISIX-specific routing and plugin resources
- Implementing field-watching to respond to status transitions set by another operator

---

## API Management — Istio

**Location:** `source/operators/TMFOP002-API-Management/istio/apiOperatorIstio.py`  
**Helm chart:** `charts/api-operator-istio/`  
**CRDs watched:** `exposedapis.oda.tmforum.org`, `endpointslices.discovery.k8s.io`  
**Docker image:** `tmforumodacanvas/api-operator-istio`

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.create/update` — ExposedAPI and EndpointSlice lifecycle
- `@kopf.on.field` — watches `status.apiStatus` and `status.implementation`

**Key patterns:**
- **Watches `EndpointSlice` resources** (`discovery.k8s.io/v1`) alongside custom CRDs — used to discover service implementation details (pod IPs, ports)
- Creates Istio **`VirtualService`** resources for service mesh routing
- Discovers public hostname/IP from the `istio-ingressgateway` Service
- Supports multiple observability implementations: ServiceMonitor, PrometheusAnnotation, DataDogAnnotation via environment variable switch

**Use as template when:**
- Building an operator that watches non-CRD Kubernetes resources (EndpointSlice, Services, Pods) alongside custom resources
- Integrating with Istio service mesh
- Implementing observability configuration alongside routing

---

## API Management — Apigee

**Location:** `source/operators/TMFOP002-API-Management/apigee/apiOperatorApigee.py`  
**Helm chart:** `charts/apigee-gateway/`  
**CRDs watched:** `exposedapis.oda.tmforum.org`

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.create` — create Apigee API proxy
- `@kopf.on.delete` — remove Apigee API proxy

**Key patterns:**
- Creates Apigee API proxies with spike arrest, API key verification, CORS policies
- Template-based policy generation
- Google Cloud authentication via `google-auth` library

**Use as template when:** Building an operator that provisions resources in an external cloud API management platform.

---

## Identity Config Operator (Keycloak)

**Location:** `source/operators/TMFOP003-Identity-Config/keycloak/identityConfigOperatorKeycloak.py`  
**Helm chart:** `charts/identityconfig-operator-keycloak/`  
**CRDs watched:** `identityconfigs.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/identityconfig-operator-keycloak`  
**Deployment:** Dual-container (operator + Keycloak listener sidecar on port 5000)

**kopf decorators used:**
- `@kopf.on.startup()`
- `@kopf.on.resume/create/update` — IdentityConfig lifecycle
- `@kopf.on.delete` — deregister Keycloak client
- **`@kopf.timer(GROUP, VERSION, "identityconfigs", interval=300.0, idle=30.0)`** — periodic health probe / reconciliation
- **`@kopf.on.probe(id="keycloak-check")`** — Kubernetes liveness health check

**Key patterns:**
- **Timer handler** fires every 5 minutes to reconcile identity configuration and verify external service connectivity
- **Probe handler** exposes a health endpoint that Kubernetes liveness probes call
- External HTTP API integration via `requests` library (Keycloak REST API)
- Global **listener registry dictionary** shared between handlers for the same resource
- Dual-container: main kopf operator + a separate listener web service deployed as sidecar in the same pod

**Use as template when:**
- Building an operator that integrates with an external service API
- Implementing periodic reconciliation (timer) alongside event-driven handlers
- Exposing custom Kubernetes health check probes
- Deploying operator alongside a sidecar service in the same pod

---

## Secrets Management Operator (HashiCorp Vault)

**Location:** `source/operators/TMFOP007-Secrets-Management/vault/docker/secretsmanagementOperatorHC.py`  
**Helm chart:** `charts/secretsmanagement-operator/`  
**CRDs watched:** `secretsmanagements.oda.tmforum.org`, `pods` (via admission webhook)  
**Docker image:** `tmforumodacanvas/secretsmanagement-operator-hc`  
**Scope:** `--all-namespaces`

**kopf decorators used:**
- `@kopf.on.startup()` — configures peering priority=200, custom ServiceTunnel, admission
- **`@kopf.on.mutate("", "v1", "pods", operation="CREATE")`** — mutating admission webhook
- `@kopf.on.resume/create/update` — SecretsManagement CRD lifecycle
- `@kopf.on.delete` — Vault policy cleanup
- `@kopf.on.field` — field watchers

**Key patterns:**
- **Mutating admission webhook** intercepts pod CREATE events and injects a sidecar container (vault-agent) with volume mounts
- **Custom `ServiceTunnel` class** implements `kopf.WebhookFn` protocol to configure the webhook server as an in-cluster Kubernetes Service, so the Kubernetes API server calls back into the operator pod via a stable Service DNS name
- **`settings.peering.priority = 200`** — highest priority in ODA Canvas, ensuring admission webhook is never blocked
- **`settings.admission.managed = "auto.kopf.dev"`** — kopf automatically creates/updates `MutatingWebhookConfiguration`
- Multiple Vault token configuration methods: plaintext, encrypted, or Kubernetes Secret references
- Pod selector matching by name patterns, namespace, and service account

**Use as template when:**
- Building an operator with admission webhooks (pod mutation/injection)
- Implementing in-cluster webhook service using a custom tunnel class
- Integrating with HashiCorp Vault
- Building an operator that needs the highest execution priority

---

## Dependent API Simple Operator

**Location:** `source/operators/TMFOP005-Dependency-Management/simple-dependency-management/docker/src/dependentApiSimpleOperator.py`  
**Helm chart:** `charts/dependentapi-simple-operator/`  
**CRDs watched:** `dependentapis.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/dependentapi-simple-operator`

**kopf decorators used:**
- `@kopf.on.startup()` — configures peering priority=110, peering name="dependentapi"
- `@kopf.on.resume/create/update` — DependentAPI lifecycle
- `@kopf.on.delete` — cleanup service inventory entry

**Key patterns:**
- **`settings.peering.priority = 110`** — mid-range priority
- **`settings.peering.name = "dependentapi"`** — operator uses a named peering object (not the default), preventing collision with other operators' peering
- **Cross-resource discovery**: calls `list_cluster_custom_object()` on `ExposedAPIs` to find matching APIs and resolve their URLs
- Updates TMF Service Inventory API with resolved dependency URLs
- Uses `Jinja2` templating for resource body construction

**Use as template when:**
- Building an operator that needs to discover and cross-reference other CRDs cluster-wide (dependency resolution)
- Implementing named peering to isolate operator coordination
- Integrating with an external service inventory or catalogue

---

## Credentials Management Operator

**Location:** `source/operators/TMFOP004-Credentials-Management/credentials-management/credentialsManagementOperator.py`  
**Helm chart:** `charts/credentialsmanagement-operator/`  
**CRDs watched:** `identityconfigs.oda.tmforum.org`  
**Docker image:** `tmforumodacanvas/credentials-management-operator`

**kopf decorators used:**
- `@kopf.on.startup()`
- **`@kopf.on.field(GROUP, VERSION, "identityconfigs", field="status.identityConfig", when=is_status_changed)`** — field handler with `when=` callback filter

**Key patterns:**
- **Field handler with `when=` callback** — only fires when `status.identityConfig` changes to a specific value (avoids spurious re-processing)
- Retrieves Keycloak client credentials via REST API
- Creates a `kubernetes.client.V1Secret` using `CoreV1Api`
- **`kopf.adopt(secret)`** — makes the Secret owned by the IdentityConfig (cascaded deletion)
- Uses standard Python `logging` (not `LogWrapper`) — simpler operators can skip `LogWrapper`

**Use as template when:**
- Building an operator that reacts only to specific status field transitions
- Creating Kubernetes Secrets from external service credential retrieval
- Writing a lightweight operator watching a CRD owned by another operator

---

## Helm Chart Conventions

### Standard Chart Structure
```
charts/<operator-name>/
  Chart.yaml            # name, version, appVersion (operator version)
  values.yaml           # deployment image/version/prerelease, namespaces, loglevel
  templates/
    deployment.yaml     # Operator pod, image, env, command
    rbac.yaml           # ServiceAccount + ClusterRole + ClusterRoleBinding (+ Role/RoleBinding for namespaced ops)
    configMap.yaml      # Non-sensitive config (log level, namespace, service URLs)
    _helpers.tpl        # dockerimage, selectorLabels, labels, monitoredNamespacesCLIOpts
```
Some charts add: `secret.yaml` (credentials), `certificate.yaml` (cert-manager), `webhook.yaml`.

### Shared Umbrella Helpers

The `charts/canvas-oda/templates/_helpers.tpl` defines two shared helpers referenced by **all** operator charts:

- **`docker.registry`** — returns the Docker registry prefix with trailing slash, or empty string if no registry is set via `global.dockerRegistry`
- **`image-pull-secrets`** — renders `imagePullSecrets:` block from `global.imagePullSecrets` (supports both string names and full secret objects)

Reference them in your operator `_helpers.tpl`:
```yaml
{{- define "myoperator.dockerimage" -}}
  {{ include "docker.registry" . }}{{ .Values.deployment.image }}:{{ .Values.deployment.version -}}
  {{- if .Values.deployment.prereleaseSuffix }}-{{ .Values.deployment.prereleaseSuffix }}{{- end -}}
{{- end -}}
```

In `deployment.yaml`:
```yaml
image: {{ include "myoperator.dockerimage" . }}
imagePullPolicy: {{ if .Values.deployment.prereleaseSuffix }}Always{{ else }}{{ .Values.deployment.imagePullPolicy }}{{ end }}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- include "image-pull-secrets" . | nindent 6 }}
{{- end }}
```

### Namespace CLI Options Helper

Converts comma-separated namespace list to kopf CLI flags:
```yaml
{{- define "myoperator.monitoredNamespacesCLIOpts" -}}
{{- printf "-n %s" .Values.deployment.monitoredNamespaces | replace "," " -n " }}
{{- end -}}
```
`"components,odacompns-*"` → `-n components -n odacompns-*`

Used in deployment command:
```yaml
command: ["/bin/sh"]
args: ["-c", "kopf run $COMPONENT_NAMESPACES_CLI --verbose /operator/myoperator.py"]
```

### ConfigMap vs Secret vs Inline Env Vars

| Type | Use for | Helm encoding |
|---|---|---|
| **ConfigMap** | Non-sensitive config: log level, namespaces, service URLs | Plain values, `envFrom.configMapRef` |
| **Secret** | Credentials: passwords, client_id/secret, tokens, Vault keys | `b64enc`, `envFrom.secretRef` |
| **Inline `env`** | Simple values, field references (`metadata.namespace`), conditional | Direct `value:` or `valueFrom.fieldRef` |

### Multi-Container Deployment Pattern (identityconfig-operator-keycloak)
```yaml
containers:
  - name: identityconfig-operator
    image: {{ include "identityconfig.dockerimage" . }}
    command: ["/bin/sh"]
    args: ["-c", "kopf run $COMPONENT_NAMESPACES_CLI --verbose /identityConfigOperator/identityConfigOperatorKeycloak.py"]
    envFrom:
      - configMapRef:
          name: {{ include "identityconfig.fullname" . }}-config
  - name: identityconfig-listener
    image: {{ include "identityconfig-listener.dockerimage" . }}
    ports:
      - containerPort: 5000
```

### RBAC Minimums for All Kopf Operators

Every operator needs these in its ClusterRole:
```yaml
rules:
  # KOPF peering (required by kopf framework)
  - apiGroups: [kopf.dev]
    resources: [clusterkopfpeerings]
    verbs: [list, watch, patch, get]
  - apiGroups: [kopf.dev]
    resources: [kopfpeerings]
    verbs: [list, watch, patch, get]
  # K8s events (kopf posts events on handled objects)
  - apiGroups: ["", "events.k8s.io"]
    resources: [events]
    verbs: [create, patch, get]
  # CRD management (kopf discovers CRDs at startup)
  - apiGroups: [apiextensions.k8s.io]
    resources: [customresourcedefinitions]
    verbs: [list, watch, get]
  # ODA resources this operator manages
  - apiGroups: [oda.tmforum.org]
    resources: [components, exposedapis, dependentapis, ...]
    verbs: [list, watch, get, create, update, patch, delete]
```

Add gateway-specific CRD permissions (Kong, APISIX, Istio) for API-management operators.  
Operators that create namespace-scoped resources (Secrets, ConfigMaps) need a `Role` + `RoleBinding` in addition to the `ClusterRole`.
