# Run a local demo Canvas

This how-to builds a complete ODA Canvas on one machine, with [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker). Use it to learn the Canvas, try a component, or give a demo. By the end you have:

- the Canvas, with Istio as the API gateway;
- the Product Catalog reference component, with its APIs answering at `https://127.0.0.1/...`;
- the Canvas Portal v2, at `http://localhost:8090`.

It follows the full [installation guide](README.md), with the extra steps a local cluster needs. Each step was tested on 20 November 2026 with kind 0.29 (Kubernetes 1.33), Istio 1.30.8, `canvas-oda` 1.2.6-rc9 and the Portal chart 0.1.0, on Docker Desktop on Windows 11.

## Before you start

You need:

- Docker, with at least 4 CPUs and 16 GB of memory available to it (see [hardware requirements](README.md#hardware-requirements));
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), [kubectl](https://kubernetes.io/docs/tasks/tools/) and [Helm 3](https://helm.sh/docs/intro/install/);
- a bash shell: Linux, macOS, WSL or Git Bash. In Git Bash, run `export MSYS_NO_PATHCONV=1` first, so that it doesn't rewrite the container paths in the commands below.

The steps take about 15 minutes, most of it waiting for the Canvas to start.

## 1. Create the cluster

```bash
kind create cluster --name oda-demo
```

kind switches your `kubectl` context to `kind-oda-demo`. Check it with `kubectl config current-context` before each step if you use other clusters.

## 2. Install Istio

```bash
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update
kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system
helm install istiod istio/istiod -n istio-system --wait
kubectl create namespace istio-ingress
kubectl label namespace istio-ingress istio-injection=enabled
helm install istio-ingress istio/gateway -n istio-ingress \
  --set labels.app=istio-ingress --set labels.istio=ingressgateway
```

## 3. Give the ingress gateway an address

kind has no load balancer, so the `istio-ingress` service never gets an external address. The Canvas needs one, **before** you install the Canvas or any component:

- the Canvas chart's pre-install check fails without it;
- the API operator builds each API's URL from it when the component is installed. A component installed before the gateway has an address stays at `In-Progress-CompCon` with empty URLs, even after the address arrives ([#621](https://github.com/tmforum-oda/oda-canvas/issues/621)).

Set the address to your own machine:

```bash
kubectl patch svc istio-ingress -n istio-ingress --subresource=status --type=merge \
  -p '{"status":{"loadBalancer":{"ingress":[{"ip":"127.0.0.1"}]}}}'
kubectl get svc istio-ingress -n istio-ingress
```

`EXTERNAL-IP` now shows `127.0.0.1`. To reach the gateway at that address, step 5 forwards ports 80 and 443 to it.

Alternatively, run [cloud-provider-kind](https://github.com/kubernetes-sigs/cloud-provider-kind), which gives LoadBalancer services a real address. The release test workflow uses it.

## 4. Install the Canvas

```bash
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas
helm repo update
helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace --devel --timeout 15m
```

- **Don't add `--wait`.** The chart's post-install hooks create the certificates and secrets that several pods need. With `--wait`, Helm waits for those pods before running the hooks, and the install never finishes.
- `--devel` installs the latest release candidate, which matches the `main` branch and the Portal v2 in step 7. Leave it out to install the latest stable release.
- The defaults install Istio as the API operator, plus Keycloak, HashiCorp Vault, cert-manager and the other Canvas operators.

The command takes about five minutes. Then check that everything is running:

```bash
kubectl get pods -A | grep -v -E "Running|Completed"
```

Only the header line should be left. An `Error` pod for a post-install hook, such as `canvas-vault-hc-post-install-hook-...`, is normal if a later run of the same hook shows `Completed`: the first run can time out while Vault starts.

## 5. Forward the gateway ports

In a separate terminal, and leave it running:

```bash
kubectl port-forward -n istio-ingress svc/istio-ingress 80:80 443:443
```

On Linux, ports below 1024 need root: run it with `sudo -E`. If the ports are already in use (for example by Docker Desktop's own Kubernetes), free them first, or use cloud-provider-kind instead (step 3).

## 6. Install a component

Install the Product Catalog reference component into the `components` namespace, which the Canvas created:

```bash
helm repo add oda-components https://tmforum-oda.github.io/reference-example-components
helm repo update
helm install demo oda-components/productcatalog -n components
kubectl get components -n components -w
```

The status moves through `In-Progress-CompCon` and `In-Progress-IDConfOp` to `Complete`, in one to two minutes. Press Ctrl+C, then list the APIs the Canvas exposed:

```bash
kubectl get exposedapis -n components
```

Each has an `API_ENDPOINT` under `https://127.0.0.1/demo-productcatalogmanagement/`. Call one (`-k` because the gateway's certificate is self-signed):

```bash
curl -k https://127.0.0.1/demo-productcatalogmanagement/tmf-api/productCatalogManagement/v4/catalog
```

A new component has no catalogs yet, so the answer is `[]`.

The [reference example components](https://github.com/tmforum-oda/reference-example-components) repository has six other components to try in the same way.

## 7. Install the Canvas Portal v2

The [Canvas Portal v2](../canvas-portal-v2/README.md) is a web UI for the Canvas. It isn't part of the `canvas-oda` chart yet, so it is installed from the `oda-canvas` repository.

### Build the images

The Portal images aren't published to Docker Hub yet, so build them and load them into the kind cluster:

```bash
git clone -c core.autocrlf=input https://github.com/tmforum-oda/oda-canvas.git
cd oda-canvas/canvas-portal-v2
docker build -t tmforumodacanvas/canvas-portal:frontend-0.1.0 frontend
docker build -t tmforumodacanvas/canvas-portal:backend-0.1.0 backend
kind load docker-image --name oda-demo \
  tmforumodacanvas/canvas-portal:frontend-0.1.0 tmforumodacanvas/canvas-portal:backend-0.1.0
```

The tags match the chart's defaults. `core.autocrlf=input` matters on Windows: with Windows line endings in its start-up script, the frontend container fails with `30-runtime-config.sh: not found`.

### Set up Keycloak

The Portal logs users in through the Canvas's Keycloak, in the `odari` realm. It needs two clients, an admin group and a user. Choose a user name and password, then run this from the same shell:

```bash
PORTAL_USER=demo
PORTAL_PASSWORD='choose-a-password'

kcadm() {
  kubectl exec -n canvas canvas-keycloak-0 -- \
    /opt/bitnami/keycloak/bin/kcadm.sh "$@" --config /tmp/kcadm.config
}

# Log in as the Keycloak admin, with the password the Canvas chart stored
kcadm config credentials --server http://localhost:8083/auth --realm master --user admin \
  --password "$(kubectl get secret canvas-keycloak -n canvas -o jsonpath='{.data.admin-password}' | base64 -d)"

# The login client: public, with direct access grants (the Portal backend uses a password grant)
kcadm create clients -r odari -s clientId=canvas-portal -s publicClient=true \
  -s directAccessGrantsEnabled=true -s standardFlowEnabled=false

# The admin client: confidential, with a service account that can manage users
kcadm create clients -r odari -s clientId=canvas-portal-admin -s publicClient=false \
  -s serviceAccountsEnabled=true -s standardFlowEnabled=false
kcadm add-roles -r odari --uusername service-account-canvas-portal-admin \
  --cclientid realm-management --rolename manage-users --rolename view-users --rolename query-users

# The Portal's admin group, and a user in it
kcadm create groups -r odari -s name=canvas-admin
kcadm create users -r odari -s username="$PORTAL_USER" -s enabled=true \
  -s email="$PORTAL_USER@example.com" -s emailVerified=true -s firstName=Demo -s lastName=User \
  -s 'groups=["canvas-admin"]' \
  -s "credentials=[{\"type\":\"password\",\"value\":\"$PORTAL_PASSWORD\",\"temporary\":false}]"

# The admin client's secret, for the Portal chart
CLIENT_ID=$(kcadm get clients -r odari -q clientId=canvas-portal-admin --fields id --format csv --noquotes | tr -d '\r')
PORTAL_ADMIN_SECRET=$(kcadm get clients/$CLIENT_ID/client-secret -r odari --fields value --format csv --noquotes | tr -d '\r')
```

Only members of the `canvas-admin` group can install Helm charts and run conformance tests from the Portal. Other users can view the Canvas.

### Install the chart

Write the settings for a local cluster to a values file. Both services are `ClusterIP`, because kind has no load balancer, and the access rules name only the `components` namespace, because the chart's other default namespaces don't exist in this Canvas.

```bash
cat > portal-values.yaml <<'EOF'
backend:
  service:
    type: ClusterIP
  env:
    KEYCLOAK_URL: http://canvas-keycloak-headless.canvas.svc.cluster.local:8083/auth
    CORS_ORIGINS:
      - http://localhost:8090
frontend:
  service:
    type: ClusterIP
  nginx:
    keycloakUpstream: http://canvas-keycloak-headless.canvas.svc.cluster.local:8083/auth
keycloak:
  init:
    enabled: false
rbac:
  canvasInstallAccess:
    targetNamespaces: [components]
  modelGatewayAccess:
    targetNamespaces: [components]
  canvasConformanceAccess:
    targetNamespaces: [components]
EOF

helm install canvas-portal ./helm/canvas-portal -n canvas -f portal-values.yaml \
  --set backend.secretEnv.KEYCLOAK_ADMIN_CLIENT_SECRET="$PORTAL_ADMIN_SECRET"
```

The chart's Keycloak init job is turned off, because the commands above already did its work.

### Open the Portal

When both Portal pods are running (`kubectl get pods -n canvas | grep portal`), forward the frontend in another terminal:

```bash
kubectl port-forward -n canvas svc/canvas-portal-frontend 8090:80
```

Open `http://localhost:8090` and log in with the user you created. The dashboard shows the Product Catalog component and its four exposed APIs.

## 8. Add observability (optional)

To see the component's metrics and traces in Prometheus, Grafana and Jaeger, follow the [Observability tutorial](https://tmforum-oda.github.io/oda-ca-docs/docs/Observability-Tutorial/README.html). It installs the [observability stack](../charts/observability-stack/README.md) into this cluster.

## Clean up

Delete the whole cluster:

```bash
kind delete cluster --name oda-demo
```

## If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `helm install canvas` fails with `BackoffLimitExceeded` in a pre-install job | The ingress gateway has no address. Do step 3, then install again. |
| `helm install canvas` never finishes | It was run with `--wait`. Uninstall, then install again without it. |
| A component stays at `In-Progress-CompCon` and its exposed APIs have no URL | It was installed before the gateway had an address. Do step 3, then uninstall and reinstall the component. |
| `curl` can't connect to `127.0.0.1` | The port-forward from step 5 isn't running. |
| Portal pods show `ErrImagePull` | The images weren't loaded into kind. Build and load them as in step 7. |
| The Portal frontend restarts with `30-runtime-config.sh: not found` | The image was built from a Windows checkout with Windows line endings. Clone with `-c core.autocrlf=input` and build again. |
| The Portal says "Invalid credentials" | Check the user and password in Keycloak's `odari` realm. Users in other realms, such as `master`, can't log in. |

For other problems, see the [installation guide's troubleshooting section](README.md#troubleshooting) and the [Troubleshooting guide](https://tmforum-oda.github.io/oda-ca-docs/docs/TroubleshootingGuide/index.html).
