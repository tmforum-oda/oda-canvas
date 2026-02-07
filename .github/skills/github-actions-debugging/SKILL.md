---
name: github-actions-debugging
description: Guide for debugging and working with GitHub Actions CI/CD workflows in the ODA Canvas project. Covers Docker build workflows, chart release pipeline, PR test pipeline, linting, common debugging commands, and the auto-generated workflow system. Use this skill when troubleshooting CI failures, modifying workflows, or understanding the build pipeline.
---

# GitHub Actions Debugging — Skill Instructions

## Workflow Inventory

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `dockerbuild-prerelease-*.yml` (×15) | Push to `feature/*`, `odaa-*` | Build + push prerelease Docker images |
| `dockerbuild-release-*.yml` (×15) | Push to `main` (tags) | Build + push release Docker images |
| `Chart-Releaser-ReleasedChartTester-TrivyScanner.yml` | Push to `main` | Release Helm charts + integration test + security scan |
| `trigger_tests.yml` | PR to `main` + manual | Full BDD test suite on Kind cluster |
| `local-test.yml` | Manual | Local testing helper |
| `lint-python-code.yml` | PR to `main` | Python formatting with Black |
| `check-no-prerelease-suffixes-in-PR.yml` | PR to `main` | Ensure no prerelease suffixes in release |

## Auto-Generated Docker Workflows

**CRITICAL**: The 30 Docker build workflows are AUTO-GENERATED. Do not edit them directly.

- **Config**: `automation/generators/dockerbuild-workflow-generator/dockerbuild-config.yaml`
- **Generator**: `automation/generators/dockerbuild-workflow-generator/dockerbuild_workflow_generator.py` (uses Jinja2)
- **To modify**: Edit the config YAML or Jinja2 templates, then regenerate

### Docker Build Pipeline Steps

1. Read image name/version from `charts/canvas-oda/values.yaml` using `yq`
2. Validate version format:
   - Prerelease: `<n>.<n>.<n>-<suffix>` (e.g., `1.2.5-LT5`)
   - Release: `<n>.<n>.<n>` (e.g., `1.2.5`)
3. Check release image doesn't already exist (prevents overwriting)
4. Build multi-arch: `linux/amd64,linux/arm64`
5. Inject build args: `SOURCE_DATE_EPOCH`, `GIT_COMMIT_SHA`, `CICD_BUILD_TIME`
6. Push to Docker Hub with `latest` and version tags

## PR Test Pipeline (`trigger_tests.yml`)

### Skip Mechanisms

- `[skip tests]` in PR title or commit message
- If only `values.yaml` changed with empty prereleaseSuffix removals

### Pipeline Steps (334 lines)

1. **Kind cluster** (Kubernetes v1.30.0) + cloud-provider-kind
2. **Istio install** (pinned versions)
3. **Helm dependency update** on all sub-charts
4. **Install Canvas** from local source: `helm install canvas charts/canvas-oda`
5. **Port-forward** Keycloak (8083) and Resource Inventory (8639)
6. **Install test components** in `components` and `odacompns-1` namespaces
7. **Run BDD tests**: `cd feature-definition-and-test-kit && npm start`
8. **Upload artifacts**: operator logs, test results, cucumber.json
9. **Generate badges**: Parse cucumber JSON for pass/fail/skip counts

### Common Failure Points

| Symptom | Likely Cause | Debug Command |
|---------|-------------|---------------|
| Pod not ready | Image pull failure | `kubectl describe pod <name> -n canvas` |
| CRD not found | Helm dependency not updated | `helm dependency update charts/canvas-oda` |
| Test timeout | Operator crash loop | `kubectl -n canvas logs deployment/component-operator` |
| Port-forward fail | Service not yet ready | `kubectl get svc -n canvas` |
| Istio errors | Version mismatch | Check Istio install step version pins |

## Chart Release Pipeline

**Trigger**: Push to `main`

1. `helm dependency update` on all charts
2. `helm/chart-releaser-action` — package and publish to GitHub Pages
3. Verify charts available in Helm repo
4. Integration test on Kind cluster:
   - Install from published charts: `helm install canvas oda-canvas/canvas-oda --devel`
   - Install test component
   - Verify component status reaches `Complete`
5. **Trivy security scan** on deployed images
6. Upload scan results as artifacts

## Python Linting (`lint-python-code.yml`)

Uses `psf/black` formatter on:
- `automation/generators/dockerbuild-workflow-generator/`
- `source/operators/component-management/`
- `source/operators/api-management/istio/`
- `source/operators/dependentApiSimpleOperator/`
- `source/operators/secretsmanagementOperator-hc/`

## Debugging Commands

### Cluster State

```bash
kubectl get all -n canvas
kubectl get all -n components
kubectl get components -n components
kubectl get exposedapis -n components
kubectl get dependentapis -n components
```

### Operator Logs

```bash
kubectl -n canvas logs deployment/component-operator
kubectl -n canvas logs deployment/api-operator-istio
kubectl -n canvas logs deployment/identity-operator-keycloak
```

### Helm State

```bash
helm list --all-namespaces
helm status canvas -n canvas
helm get values canvas -n canvas
```

### Component Debugging

```bash
kubectl describe component <name> -n components
kubectl get events -n components --sort-by=.lastTimestamp
kubectl get component <name> -n components -o yaml
```

## Local Testing

### Using Act (GitHub Actions Locally)

```bash
# Run with act
scripts/run-with-act.sh

# Or directly
cd feature-definition-and-test-kit
npm install
npm start
```

### Local Operator Development

```bash
kopf run --namespace=components --standalone source/operators/<path>/<operator>.py
```

## Version Management in CI

| File | Field | Prerelease | Release |
|------|-------|-----------|---------|
| `charts/canvas-oda/values.yaml` | `compopVersion` | `1.2.5` | `1.2.5` |
| `charts/canvas-oda/values.yaml` | `compopPrereleaseSuffix` | `LT5` | `""` |
| `charts/<chart>/Chart.yaml` | `version` | `1.2.5-LT5` | `1.2.5` |

The prerelease check workflow (`check-no-prerelease-suffixes-in-PR.yml`) ensures no prerelease suffixes remain when merging to main.

## Artifact Uploads

CI uploads these artifacts for post-mortem analysis:
- **Component operator logs**: `component-operator-logs`
- **API operator logs**: `api-operator-istio-logs`
- **Test results**: `test-results`
- **Cucumber JSON**: `cucumber-report` (machine-readable test results)
- **Trivy scan**: `trivy-results` (security findings)

## Do

- Edit Docker workflow config YAML, not generated workflow files
- Use `[skip tests]` in commit messages for documentation-only changes
- Check operator logs first when BDD tests fail
- Run `helm dependency update` after modifying sub-chart versions
- Use Kind cluster for local integration testing

## Don't

- Don't edit `dockerbuild-*.yml` files directly — they're auto-generated
- Don't push prerelease suffixes to main branch
- Don't skip the prerelease suffix check workflow
- Don't ignore Trivy security findings in release pipeline
- Don't hard-code Kubernetes or Istio versions — use the pinned versions from workflows
