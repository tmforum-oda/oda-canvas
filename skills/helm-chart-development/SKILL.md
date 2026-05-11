---
name: helm-chart-development
description: Guide for developing Helm charts in the ODA Canvas project. Covers umbrella chart architecture, sub-chart conventions, _helpers.tpl patterns, values.yaml structure, RBAC templates, Docker image construction, versioning with prerelease suffixes, and dependency management. Use this skill when creating or modifying Helm charts.
---

# Helm Chart Development — Skill Instructions

## Architecture

The ODA Canvas uses an **umbrella chart** pattern:

- `charts/canvas-oda/` — Main umbrella chart, aggregates all sub-charts
- `charts/<sub-chart>/` — Individual operator/service charts

Sub-charts are referenced as local dependencies in the umbrella `Chart.yaml`.

## Chart.yaml Conventions

```yaml
apiVersion: v2
name: <chart-name>
description: <one-line description>
type: application
version: <semver>           # e.g., 1.2.5 or 1.2.5-LT5 (prerelease)
appVersion: "v1"            # tracks CRD spec version
```

- **Version changelog**: Maintain as comments in `Chart.yaml` — each version with date and description
- **Prerelease suffix**: Author initials (e.g., `-LT5`, `-JS3`). Clear for releases.

## Dependency Management

### Local Sub-Chart Dependencies

```yaml
dependencies:
  - name: cert-manager-init
    version: "1.1.2"
    repository: 'file://../cert-manager-init'
```

### External Dependencies

```yaml
  - name: keycloak
    version: "13.0.3"
    repository: 'https://charts.bitnami.com/bitnami'
    condition: keycloak.enabled
```

Always use `condition:` for optional dependencies so they can be toggled in `values.yaml`.

### Updating Dependencies

```bash
cd charts/canvas-oda
helm dependency update
```

## Sub-Chart Directory Structure

```
charts/<chart-name>/
  Chart.yaml
  values.yaml
  templates/
    deployment.yaml
    rbac.yaml              # ServiceAccount + ClusterRole + ClusterRoleBinding
    configMap.yaml         # Environment variables
    _helpers.tpl           # Standard template helpers
```

## values.yaml Patterns

### Global Values (Umbrella Chart)

```yaml
global:
  image:
    registry: ""                    # Docker registry prefix (include trailing /)
  imagePullSecrets: []
  certificate:
    appName: "compcrdwebhook"
  hookImages:
    kubectl: bitnamilegacy/kubectl:latest
    kubectlCurl: tmforumodacanvas/baseimage-kubectl-curl:1.30.5
```

### Sub-Chart Toggles (Umbrella)

```yaml
oda-crds:
  enabled: true
canvas-namespaces:
  enabled: true
component-operator:
  compopImage: tmforumodacanvas/component-operator
  compopVersion: "1.2.5"
  compopPrereleaseSuffix: ""        # Set to initials for prerelease
```

### Operator values.yaml

```yaml
compopImage: tmforumodacanvas/component-operator
compopVersion: "1.2.5"
compopPrereleaseSuffix: ""
monitoredNamespaces: "components"
```

## _helpers.tpl Standard Patterns

### Docker Image Construction

```go
{{- define "<chart>.DockerImage" -}}
{{ include "docker.registry" . }}{{ .Values.image }}:{{ .Values.version }}
{{- if .Values.prereleaseSuffix -}}-{{ .Values.prereleaseSuffix }}{{- end -}}
{{- end }}
```

### Image Pull Policy

```go
{{- define "<chart>.ImagePullPolicy" -}}
{{- if .Values.prereleaseSuffix -}}Always{{- else -}}IfNotPresent{{- end -}}
{{- end }}
```

### Docker Registry (Global)

```go
{{- define "docker.registry" -}}
{{- if .Values.global -}}{{- if .Values.global.image -}}{{- if .Values.global.image.registry -}}
{{ .Values.global.image.registry }}
{{- end -}}{{- end -}}{{- end -}}
{{- end -}}
```

### Namespace CLI Conversion

Convert comma-separated namespaces to KOPF CLI flags:

```go
{{- define "<chart>.monitoredNamespacesCLIOpts" -}}
{{- $namespaces := splitList "," .Values.monitoredNamespaces -}}
{{- range $namespaces }} -n {{ . }}{{- end -}}
{{- end }}
```

### Standard Labels

```go
{{- define "<chart>.labels" -}}
helm.sh/chart: {{ include "<chart>.chart" . }}
{{ include "<chart>.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

## Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "<chart>.fullname" . }}
  namespace: {{ .Release.Namespace }}      # NEVER hardcode
  labels:
    {{- include "<chart>.labels" . | nindent 4 }}
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "<chart>.selectorLabels" . | nindent 6 }}
  template:
    spec:
      serviceAccountName: {{ .Values.serviceAccountName }}
      {{- with .Values.global.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          image: {{ include "<chart>.DockerImage" . }}
          imagePullPolicy: {{ include "<chart>.ImagePullPolicy" . }}
          envFrom:
            - configMapRef:
                name: {{ include "<chart>.fullname" . }}-config
```

## RBAC Template

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Values.serviceAccountName }}
  namespace: {{ .Release.Namespace }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "<chart>.fullname" . }}
rules:
  # KOPF peering
  - apiGroups: [zalando.org]
    resources: [clusterkopfpeerings, kopfpeerings]
    verbs: [list, watch, patch, get]
  # ODA resources
  - apiGroups: [oda.tmforum.org]
    resources: [components, components/status, exposedapis, exposedapis/status]
    verbs: [list, watch, patch, get, create, update, delete]
  # Core K8s
  - apiGroups: [""]
    resources: [pods, services, configmaps, events, namespaces]
    verbs: [list, watch, get, create, update, delete]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {{ include "<chart>.fullname" . }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {{ include "<chart>.fullname" . }}
subjects:
  - kind: ServiceAccount
    name: {{ .Values.serviceAccountName }}
    namespace: {{ .Release.Namespace }}
```

## Versioning Workflow

1. During development: set `prereleaseSuffix: LT5` (your initials + iteration)
2. Docker images built as `<image>:<version>-<suffix>` with `imagePullPolicy: Always`
3. For release: clear `prereleaseSuffix: ""`, image uses `IfNotPresent`
4. Bump `version` in `Chart.yaml` with changelog comment

## Validation

```bash
# Lint chart
helm lint charts/<chart-name>

# Dry-run install
helm install --dry-run --debug test charts/<chart-name>

# Template rendering
helm template test charts/<chart-name>
```

## Do

- Use `{{ .Release.Namespace }}` — never hard-code namespaces
- Include version changelog comments in `Chart.yaml`
- Use `condition:` for optional umbrella dependencies
- Construct Docker images via `_helpers.tpl` helper templates
- Use `global.imagePullSecrets` for registry authentication
- Follow standard labels (`helm.sh/chart`, `app.kubernetes.io/*`)

## Don't

- Don't edit umbrella `Chart.yaml` dependencies without running `helm dependency update`
- Don't use `latest` tags for operator images
- Don't hard-code Docker registry paths — use `global.image.registry`
- Don't forget RBAC — KOPF needs cluster-wide permissions for peering
- Don't add prerelease suffixes in PRs to main
