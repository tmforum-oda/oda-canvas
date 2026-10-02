# AGENTS.md — charts/

Helm charts for deploying ODA Canvas operators, services, and infrastructure components to Kubernetes.

## Architecture

- **Umbrella chart**: `canvas-oda/` — aggregates all sub-charts as dependencies
- **Operator charts**: `component-operator/`, `api-operator-istio/`, `identityconfig-operator-keycloak/`, etc.
- **Gateway charts**: `kong-gateway/`, `apisix-gateway/`, `apigee-gateway/`
- **Infrastructure**: `canvas-vault/`, `cert-manager-init/`, `observability-stack/`, `canvas-namespaces/`
- **CRDs**: `oda-crds/` — Custom Resource Definitions
- **Webhook**: `oda-webhook/` — CRD conversion webhook

## Chart Structure Pattern

Each sub-chart follows:

```
<chart-name>/
  Chart.yaml          # apiVersion: v2, type: application, semver version
  values.yaml         # Chart-specific configuration
  templates/
    deployment.yaml
    rbac.yaml
    _helpers.tpl
    ...
  README.md
```

## Conventions

### Versioning

- Charts use SemVer: `MAJOR.MINOR.PATCH` with optional suffixes (e.g., `-rc1`, `-LT5`)
- `appVersion` in Chart.yaml tracks the CRD spec version (e.g., `"v1"`)
- Version changelog is maintained as **comments in Chart.yaml** — update these when bumping versions

### Dependencies

- Sub-charts reference each other via `repository: 'file://../<subchart>'` in `Chart.yaml`
- External dependencies use repository URLs (e.g., `https://charts.bitnami.com/bitnami`)
- Sub-charts are conditionally enabled via `condition: <chart-name>.enabled` in the umbrella chart

### Values

- Global values use `global.*` pattern (e.g., `global.image.registry`, `global.imagePullSecrets`)
- Umbrella chart `canvas-oda/values.yaml` (~630 lines) contains configuration for all sub-charts
- `canvas-oda/values.schema.json` validates values

### Templates

- Namespaces are **never hardcoded** — use `{{ .Release.Namespace }}` or Helm template variables
- Image references use `{{ .Values.global.image.registry }}` prefix
- Use `_helpers.tpl` for reusable template snippets

## Do

- Run `helm dependency update` on `canvas-oda/` after modifying any sub-chart
- Bump the chart version in `canvas-oda/Chart.yaml` for any sub-chart change
- Regenerate `.tgz` archives in `canvas-oda/charts/` after sub-chart changes
- Add a version changelog comment in `Chart.yaml` when bumping versions
- Use `helm lint` to validate chart changes
- Use template variables for all namespace references

## Don't

- Do not change default values in `values.yaml` without asking first
- Do not hardcode namespace references — always use Helm template variables
- Do not add sub-charts to the umbrella without adding a `condition:` toggle in `canvas-oda/values.yaml`
- Do not forget to update the packaged `.tgz` dependencies

## Commands

```bash
# Lint a chart
helm lint charts/canvas-oda
helm lint charts/component-operator

# Update umbrella chart dependencies
cd charts/canvas-oda
helm dependency update

# Template render (dry-run)
helm template my-release charts/canvas-oda

# Install Canvas
helm install oda-canvas charts/canvas-oda

# Validate a component YAML
kubectl apply --dry-run=client -f path/to/component.yaml
```
