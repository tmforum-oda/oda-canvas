# Run a local demo Canvas

This how-to builds a complete ODA Canvas on one machine, with [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker), using one script. Use it to learn the Canvas, try a component, or give a demo. By the end you have:

- the Canvas, with Istio as the API gateway;
- the Product Catalog reference component, with its APIs answering at `https://127.0.0.1/...`;
- the Canvas Portal v2, at `http://localhost:8090`.

The script was tested on 20 November 2026 with kind 0.29 (Kubernetes 1.33), Istio 1.30.8, `canvas-oda` 1.2.6-rc9 and the Portal chart 0.1.0, on Docker Desktop on Windows 11.

## Before you start

You need:

- Docker, with at least 4 CPUs and 16 GB of memory available to it (see [hardware requirements](README.md#hardware-requirements));
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), [kubectl](https://kubernetes.io/docs/tasks/tools/), [Helm 3](https://helm.sh/docs/intro/install/), git and curl;
- a bash shell: Linux, macOS, WSL or Git Bash;
- ports 80, 443 and 8090 free on your machine. If Docker Desktop's own Kubernetes or another app uses them, choose other ports (see [Settings](#settings)).

## Run the script

From a clone of this repository:

```bash
git clone https://github.com/tmforum-oda/oda-canvas.git
cd oda-canvas
./installation/local-demo-canvas.sh
```

It takes 6 to 10 minutes, most of it waiting for the Canvas to start. At the end it prints the addresses and the Portal login:

```text
Your demo Canvas is ready, in the kind cluster 'oda-demo' (kubectl context kind-oda-demo).

API gateway:    https://127.0.0.1/
Catalog API:    curl -k https://127.0.0.1/demo-productcatalogmanagement/tmf-api/productCatalogManagement/v4/catalog
Canvas Portal:  http://localhost:8090
  User:         demo
  Password:     <generated>
```

kind switches your `kubectl` context to `kind-oda-demo`. Open the Portal and log in: the dashboard shows the Product Catalog component and its four exposed APIs. The catalog API answers `[]`, because a new component has no catalogs yet (`-k` because the gateway's certificate is self-signed).

The [reference example components](https://github.com/tmforum-oda/reference-example-components) repository has six other components to try. Install them into the `components` namespace with Helm.

To see the component's metrics and traces in Prometheus, Grafana and Jaeger, follow the [Observability tutorial](https://tmforum-oda.github.io/oda-ca-docs/docs/Observability-Tutorial/README.html). It installs the [observability stack](../charts/observability-stack/README.md) into this cluster.

### Settings

Set these as environment variables, for example `PORTAL_PORT=18090 ./installation/local-demo-canvas.sh`:

| Variable | Default | Meaning |
|---|---|---|
| `CLUSTER_NAME` | `oda-demo` | The kind cluster's name |
| `HTTP_PORT`, `HTTPS_PORT` | `80`, `443` | The host ports for the API gateway |
| `PORTAL_PORT` | `8090` | The host port for the Portal |
| `CANVAS_VERSION` | the latest release candidate | The `canvas-oda` chart version |
| `ISTIO_VERSION` | the latest | The Istio chart version |
| `INSTALL_COMPONENT` | `true` | Set to `false` to skip the Product Catalog component |
| `INSTALL_PORTAL` | `true` | Set to `false` to skip the Portal |
| `PORTAL_USER`, `PORTAL_PASSWORD` | `demo`, generated | The Portal login |

With other gateway ports, the API URLs the Canvas reports still say `https://127.0.0.1/...`. Add your port when you call them.

You can run the script again on the same cluster: it skips or upgrades what is already there, and sets the Portal user's password again.

### Clean up

```bash
kind delete cluster --name oda-demo
```

## What the script does

The [script](https://github.com/tmforum-oda/oda-canvas/blob/main/installation/local-demo-canvas.sh) follows the full [installation guide](README.md), with the extra steps a local cluster needs. Read it to adapt it, or to do the same on another kind of cluster.

1. **Creates the cluster**, mapping the host ports to fixed node ports (30080, 30443 and 30090). The gateway and the Portal use those node ports, so no `kubectl port-forward` is needed, and the ports keep working after a restart.
2. **Installs Istio**: the `base`, `istiod` and `gateway` charts, with the gateway service named `istio-ingress`.
3. **Gives the ingress gateway the address `127.0.0.1`.** kind has no load balancer, so the gateway never gets an external address by itself. The Canvas needs one **before** you install the Canvas or any component:
   - the Canvas chart's pre-install check fails without it;
   - the API operator builds each API's URL from it when the component is installed. A component installed before the gateway has an address stays at `In-Progress-CompCon` with empty URLs, even after the address arrives ([#621](https://github.com/tmforum-oda/oda-canvas/issues/621)).

   The script sets the address on the service's status:

   ```bash
   kubectl patch svc istio-ingress -n istio-ingress --subresource=status --type=merge \
     -p '{"status":{"loadBalancer":{"ingress":[{"ip":"127.0.0.1"}]}}}'
   ```

   Alternatively, [cloud-provider-kind](https://github.com/kubernetes-sigs/cloud-provider-kind) gives LoadBalancer services a real address. The release test workflow uses it.
4. **Installs the Canvas** with `helm install canvas oda-canvas/canvas-oda -n canvas --create-namespace --devel`:
   - **without `--wait`.** The chart's post-install hooks create the certificates and secrets that several pods need. With `--wait`, Helm waits for those pods before running the hooks, and the install never finishes. Instead, the script waits for the deployments afterwards.
   - `--devel` installs the latest release candidate, which matches the `main` branch and the Portal v2. Set `CANVAS_VERSION` to install a stable release.
   - An `Error` pod for a post-install hook, such as `canvas-vault-hc-post-install-hook-...`, is normal if a later run of the same hook shows `Completed`: the first run can time out while Vault starts.
5. **Installs the Product Catalog component** into the `components` namespace, waits for it to reach `Complete`, and calls its API.
6. **Builds the Portal images and loads them into kind.** The Portal images aren't published to Docker Hub yet. The script builds them from your clone's last commit, with `git archive`, so they get Unix line endings even on Windows. (With Windows line endings in its start-up script, the frontend fails with `30-runtime-config.sh: not found`.)
7. **Sets up Keycloak for the Portal** with `kcadm.sh` in the `canvas-keycloak-0` pod, logging in with the admin password from the `canvas-keycloak` secret. In the `odari` realm, it creates:
   - the `canvas-portal` client: public, with direct access grants, which the Portal backend uses to log users in;
   - the `canvas-portal-admin` client: confidential, with a service account that can manage users;
   - the `canvas-admin` group and the Portal user, in that group. Only members of `canvas-admin` can install Helm charts and run conformance tests from the Portal. Other users can view the Canvas.
8. **Installs the Portal chart** from `canvas-portal-v2/helm/canvas-portal`, with values for a local cluster:
   - the locally built images;
   - the Keycloak address inside the cluster, and the admin client's secret;
   - the chart's own Keycloak init job turned off, because step 7 did its work;
   - access rules for the `components` namespace only, because the chart's other default namespaces don't exist in this Canvas, and the install fails if they're missing.

## If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `kind create cluster` fails with `address already in use` | Another app uses port 80, 443 or 8090. Set `HTTP_PORT`, `HTTPS_PORT` or `PORTAL_PORT`. |
| `helm install canvas` fails with `BackoffLimitExceeded` in a pre-install job | The ingress gateway has no address (step 3). |
| `helm install canvas` never finishes | It was run with `--wait` (step 4). Uninstall, then install again without it. |
| A component stays at `In-Progress-CompCon` and its exposed APIs have no URL | It was installed before the gateway had an address (step 3). Uninstall and reinstall the component. |
| The Portal frontend restarts with `30-runtime-config.sh: not found` | The image was built from a Windows checkout with Windows line endings (step 6). |
| The Portal says "Invalid credentials" | Check the user and password in Keycloak's `odari` realm. Users in other realms, such as `master`, can't log in. Run the script again to set the password again. |

For other problems, see the [installation guide's troubleshooting section](README.md#troubleshooting) and the [Troubleshooting guide](https://tmforum-oda.github.io/oda-ca-docs/docs/TroubleshootingGuide/index.html).
