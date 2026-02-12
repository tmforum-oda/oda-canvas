# Install ODA Canvas

## Table of Contents
- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [Step 1: Check Prerequisites](#step-1-check-prerequisites)
- [Step 2: Install Helm](#step-2-install-helm)
- [Step 3: Choose and Install an API Gateway](#step-3-choose-and-install-an-api-gateway)
- [Step 4: Choose Optional Features](#step-4-choose-optional-features)
- [Step 5: Install the ODA Canvas](#step-5-install-the-oda-canvas)
- [Step 6: Verify Installation](#step-6-verify-installation)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)
- [Contextual Next Steps](#contextual-next-steps)

## Overview

The ODA Canvas Reference Implementation is a set of Helm charts deployed on Kubernetes. Before installing, the skill checks what is already in place and guides the user through installing only what is missing.

The installation guide is maintained at: `installation/README.md`.

## Hardware Requirements

Present these to the user before starting:

| Resource | Minimum |
|----------|---------|
| CPU | 4 cores (AMD64; ARM experimental) |
| RAM | 16 GB |
| Storage | 50 GB |
| OS | Any that runs Kubernetes |

## Step 1: Check Prerequisites

Run each check and report results as a summary table. Only flag items that are missing.

### 1a. Kubernetes

```bash
kubectl cluster-info
```

If this fails, the user needs a working Kubernetes cluster. Explain the tested options:

| Distribution | Notes |
|-------------|-------|
| Docker Desktop | Easiest for local development; see `devcontainer.md` |
| Rancher Desktop / k3s | Lightweight local option |
| MiniKube | v1.34.0+; Istio is pre-installed so only gateway chart is needed |
| Microk8s | Enable `metallb` and `hostpath-storage` before installing |
| Kind | Used by the project's CI/CD pipeline |
| AWS EKS | Tested with EKS 1.29 |
| Azure AKS | Tested |
| GCP GKE | Tested |

Ask the user which distribution they have or want to install. Do not install Kubernetes — assist with guidance only since the options are OS/environment-specific.

### 1b. Kubernetes version

```bash
kubectl version --output=json
```

The Canvas v1 supports Kubernetes 1.22–1.30. Warn if the version is outside this range.

### 1c. Kubernetes permissions

Run these checks (equivalent to `installation/precheck.sh`):

```powershell
# Cluster-scoped resources
foreach ($res in @("namespaces","customresourcedefinitions","clusterroles","clusterrolebindings","mutatingwebhookconfigurations","validatingwebhookconfigurations","clusterissuers")) {
  kubectl auth can-i create $res --all-namespaces
}

# Namespace-scoped resources
foreach ($res in @("serviceaccounts","secrets","configmaps","roles","rolebindings","services","deployments","statefulsets","gateways","jobs","certificates","issuers")) {
  kubectl auth can-i create $res
}
```

On bash/Linux use the equivalent from `installation/precheck.sh`.

Report any `no` results and explain what permission is missing. All must be `yes` to proceed.

### 1d. Helm

```bash
helm version
```

Helm 3.0+ is required. If not found, guide the user to install it — see [Step 2](#step-2-install-helm).

### 1e. Existing Canvas installation

```bash
helm list -n canvas
kubectl get crd components.oda.tmforum.org 
```

If this returns an error `"components.oda.tmforum.org" not found` then the canvas is not installed.

If a Canvas is already installed, report the version and ask if the user wants to upgrade or reinstall.

### 1f. Existing Istio installation

```bash
kubectl get namespace istio-system 2>$null
kubectl get pods -n istio-system 2>$null
```

Istio is required for all gateway configurations (it provides the internal service mesh for mTLS and traffic management). If Istio is already present, report it — it will be reused. If Istio is not present, it must be installed regardless of which external API gateway the user selects.

### Summary

After all checks, present a summary table:

```
Prerequisite        Status
──────────────────  ──────
Kubernetes          ✅ v1.29.2 (Docker Desktop)
Kubernetes perms    ✅ All permissions OK
Helm                ✅ v3.14.0
Istio               ❌ Not installed
ODA Canvas          ❌ Not installed
```

Only proceed to install missing items.

## Step 2: Install Helm

Skip if Helm is already installed.

Helm 3.0+ is required. Show platform-specific install:

**Windows (winget):**
```powershell
winget install Helm.Helm
```

**Windows (Chocolatey):**
```powershell
choco install kubernetes-helm
```

**macOS (Homebrew):**
```bash
brew install helm
```

**Linux (snap):**
```bash
sudo snap install helm --classic
```

After installing, install the dependency resolver plugin (needed until Helm 3.12+):

```bash
helm plugin install --version "main" https://github.com/Noksa/helm-resolve-deps.git
```

Add required Helm repos:

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update
```

## Step 3: Choose and Install an API Gateway

**Important:** All three gateway options require **Istio** as the underlying service mesh for internal traffic management (mTLS, sidecar injection, internal routing) inside the cluster. The choice here determines which component handles **external API exposure** for ODA Components' ExposedAPIs. Istio is always installed — never offer to remove it.

Present the three gateway options using `ask_questions`. Explain the trade-offs:

| Option | Gateway | Description |
|--------|---------|-------------|
| **Istio** (default) | Istio Service Mesh | Uses Istio for both internal service mesh and external API gateway (VirtualServices). Full service mesh with mTLS, traffic management, observability. Most commonly used with the ODA Canvas. |
| **Kong** | Kong Gateway | Uses Istio for the internal service mesh + Kong as the external API gateway. Headless API-only gateway with rich plugin ecosystem, rate limiting, authentication. Good for API-centric deployments. **Note:** Kong is a headless gateway — you can optionally install kong-manager for a web UI. |
| **APISIX** | Apache APISIX | Uses Istio for the internal service mesh + APISIX as the external API gateway. High-performance API gateway with dynamic routing, plugin hot-reload. Good for high-throughput scenarios. |

Only one external API gateway can be active at a time. Istio is always present for internal traffic.

### Install Istio (required for all gateway options)

Istio must be installed before the Canvas, regardless of which external API gateway is chosen. Skip this step if Istio is already running.

```bash
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system
helm install istiod istio/istiod -n istio-system --wait
kubectl create namespace istio-ingress
kubectl label namespace istio-ingress istio-injection=enabled
helm install istio-ingress istio/gateway -n istio-ingress --set labels.app=istio-ingress --set labels.istio=ingressgateway --wait
```

Verify:

```bash
kubectl get pods -n istio-system
kubectl get svc -n istio-ingress
```

Confirm that `istiod` is Running and the `istio-ingress` service has an External IP (or `<pending>` on local clusters, which is acceptable for LoadBalancer on Docker Desktop / kind).

### Install Kong prerequisites (if Kong selected as external API gateway)

Kong requires the Gateway API CRDs:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

Kong itself is installed as part of the Canvas Helm chart — no separate installation needed. The Helm values will enable it in [Step 5](#step-5-install-the-oda-canvas).

#### Optional: Install Kong Manager UI

Kong is a headless (API-only) gateway by default. If the user wants a web-based management UI, offer to install **kong-manager** from https://github.com/Kong/kong-manager.

Explain what kong-manager provides:
- Visual dashboard for Kong Gateway configuration
- Browse and manage routes, services, plugins, consumers
- Monitor gateway health and traffic

To install kong-manager after the Canvas is deployed (Kong must be running first):

```bash
# Clone the kong-manager repository
git clone https://github.com/Kong/kong-manager.git
cd kong-manager
```

kong-manager is a Vue.js frontend that connects to the Kong Admin API. Deployment approaches:

**Option A: Run locally for development**
```bash
npm install
npm run dev
```
Configure the Kong Admin API URL in the kong-manager settings to point to the Kong admin service exposed by the Canvas:
```bash
# Find the Kong Admin API service
kubectl get svc -n canvas | Select-String kong
# If using port-forward:
kubectl port-forward svc/canvas-kong-admin -n canvas 8001:8001
```

**Option B: Deploy as a container in Kubernetes**

Build and deploy kong-manager alongside the Canvas. Create a deployment and service for it, pointing the `KONG_ADMIN_API_URL` environment variable to the internal Kong Admin API service address (e.g., `http://canvas-kong-admin.canvas.svc.cluster.local:8001`).

After installation, ask the user if they want to set up port-forwarding to access kong-manager, and run it as a background process.

### Install APISIX prerequisites (if APISIX selected as external API gateway)

APISIX is installed as part of the Canvas Helm chart — no separate prerequisites. The Helm values will enable it in [Step 5](#step-5-install-the-oda-canvas).

## Step 4: Choose Optional Features

Present optional features using `ask_questions` with multi-select:

| Feature | Default | Description |
|---------|---------|-------------|
| **HashiCorp Vault** | Enabled | Secrets management for components that need it. Disable with `canvas-vault.enabled=false` if not needed. Components requesting secrets management will get stuck at `InProgress-SecretsConfig` without it. |
| **Keycloak** | Enabled | Identity management. Required for security function and role management. |
| **Cert-Manager** | Enabled | TLS certificate management. Required for webhook HTTPS. |
| **PDB Management** | Enabled | Pod Disruption Budget operator for availability policies. |
| **Canvas Info Service** | Enabled | TMF638 Service Inventory API. |
| **Resource Inventory** | Enabled | TMF639 Resource Inventory API. |
| **Observability Stack** | Not included | Prometheus, Grafana, Jaeger. Installed separately from `charts/observability-stack`. |

Note: Most users should keep the defaults. Only disable features if there is a specific reason.

### Observability Stack (optional, separate install)

If the user wants observability:

```bash
helm install observability charts/observability-stack -n observability --create-namespace
```

This installs Prometheus, Grafana, and Jaeger for monitoring the Canvas and its components.

## Step 5: Install the ODA Canvas

Build the `helm install` command based on the user's choices from Steps 3 and 4.

### Istio as external API gateway (default)

```bash
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace
```

No extra `--set` flags needed — Istio as both service mesh and external API gateway is the default.

### Kong as external API gateway

Istio remains for internal traffic; Kong handles external API exposure:

```bash
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace \
  --set api-operator-istio.enabled=false \
  --set apisix-gateway-install.enabled=false \
  --set kong-gateway-install.enabled=true
```

### APISIX as external API gateway

Istio remains for internal traffic; APISIX handles external API exposure:

```bash
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace \
  --set api-operator-istio.enabled=false \
  --set apisix-gateway-install.enabled=true \
  --set kong-gateway-install.enabled=false
```

### With optional features disabled

Append any disabled features, e.g.:

```bash
--set canvas-vault.enabled=false
--set pdb-management-operator.enabled=false
```

### Monitor installation

The install can take several minutes. Monitor progress:

```bash
kubectl get pods -n canvas -w
```

Wait for all pods to reach `Running` or `Completed` status. The key pods to watch:

| Pod pattern | Component | Expected state |
|------------|-----------|----------------|
| `compcrdwebhook-*` | CRD Webhook | Running |
| `canvas-keycloak-0` | Keycloak | Running |
| `canvas-postgresql-0` | PostgreSQL (for Keycloak) | Running |
| `*-operator-*` | Canvas operators | Running |
| `job-hook-*` | Pre/post-install hooks | Completed |
| `canvas-keycloak-keycloak-config-cli-*` | Keycloak config | Completed |

## Step 6: Verify Installation

### Check Canvas version

```bash
kubectl get crd components.oda.tmforum.org -o jsonpath='{.spec.versions[?(@.served==true)].name}'
```

Should return `v1beta3 v1beta4 v1` (or similar, showing N-2 version support).

### Check all ODA CRDs

```bash
kubectl get crd | Select-String oda.tmforum.org
```

Expected CRDs: `components`, `exposedapis`, `dependentapis`, `identityconfigs`, `secretsmanagements`, `publishednotifications`, `subscribednotifications`, `availabilitypolicies`.

### Check operators are running

```bash
kubectl get deployments -n canvas
```

All operator deployments should show `READY 1/1` (or `2/2` for the component operator which includes a sidecar).

### Check gateway is accessible

**Istio:**
```bash
kubectl get svc -n istio-ingress
```

**Kong:**
```bash
kubectl get svc -n canvas | Select-String kong
```

**APISIX:**
```bash
kubectl get svc -n canvas | Select-String apisix
```

Present a final summary:

```
ODA Canvas Installation Summary
────────────────────────────────
Canvas version:    v1 (supports v1beta3, v1beta4, v1)
Gateway:           Istio / Kong / APISIX
Vault:             Enabled / Disabled
Keycloak:          Running
Operators:         All running (component, api, identity, secrets, dependency, pdb)
Status:            ✅ Ready
```

## Troubleshooting

### Error: values don't meet the specifications of the schema(s)

More than one external API gateway operator is enabled. Only one of `api-operator-istio`, `kong-gateway-install`, or `apisix-gateway-install` can be `true`. (Istio itself is always required for the internal service mesh.)

### Error: BackoffLimitExceeded (pre-install)

The pre-install hook checks for Istio ingress. Verify:

```bash
kubectl get svc -n istio-ingress
kubectl get crd virtualservices.networking.istio.io
```

- The `istio-ingress` service must have an External IP
- The VirtualService CRD must be present

If using Kong or APISIX instead of Istio, set `preqrequisitechecks.istio` to `false`:

```bash
--set preqrequisitechecks.istio=false
```

### Error: BackoffLimitExceeded (post-install) — Keycloak config

```bash
kubectl get pods -n canvas
kubectl logs -n canvas -l app.kubernetes.io/name=keycloak-config-cli
```

Common causes:
1. **HTTP 403 from Keycloak** — Keycloak requires pod IPs in private ranges (`10.x.x.x`, `192.168.x.x`, `172.16.x.x`). If your cluster uses public IP ranges for pods, Keycloak forces HTTPS.
2. **CrashLoopBackOff on keycloak-0** — Check PostgreSQL: `kubectl logs -n canvas sts/canvas-postgresql`. If "password authentication failed for user bn_keycloak", a previous installation left a PVC. Fix:
   ```bash
   helm uninstall canvas -n canvas
   kubectl delete pvc -n canvas data-canvas-postgresql-0
   # Then reinstall
   ```

### Error: Failed post-install — cert-manager webhook x509

Cert-Manager is not ready. Fix:

```bash
helm uninstall canvas -n canvas
kubectl delete pvc -n canvas data-canvas-postgresql-0
kubectl delete lease cert-manager-cainjector-leader-election -n kube-system
```

Then increase the wait time and reinstall:

```bash
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace \
  --set cert-manager-init.leaseWaitTimeonStartup=100
```

### Pods stuck in Pending

Check for resource constraints:

```bash
kubectl describe pod <pod-name> -n canvas
kubectl get events -n canvas --sort-by='.lastTimestamp'
```

Common causes: insufficient CPU/memory, no storage class available (for PVCs), or missing node selectors.

### Kong-specific: Admin API not reachable

```bash
kubectl get svc -n canvas | Select-String kong
kubectl logs -n canvas -l app.kubernetes.io/name=kong
```

Check that `pg_host` is correct in the values. The default is `canvas-postgresql-kong.canvas.svc.cluster.local`.

### APISIX-specific: etcd not starting

```bash
kubectl get pods -n canvas | Select-String etcd
kubectl logs -n canvas -l app.kubernetes.io/name=etcd
```

etcd requires persistent storage. Ensure a StorageClass is available.

## Uninstall

```bash
helm uninstall canvas -n canvas
```

To clean up completely (including PVCs and namespace):

```bash
kubectl delete pvc --all -n canvas
kubectl delete namespace canvas
```

**Note:** Do not uninstall Istio. Istio is required for internal traffic management regardless of which external API gateway is used (Istio, Kong, or APISIX).

## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **Deploy an ODA Component** — Install a reference example component to test the Canvas |
| 2 | **View deployed components** — Check if any components are already running |
| 3 | **Install observability stack** — Add Prometheus, Grafana, and Jaeger |
| 4 | **About ODA Canvas** — Learn the architecture, CRDs, and operators |
| 5 | **Return to main menu** |
