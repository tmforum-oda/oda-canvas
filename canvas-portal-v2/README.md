# Canvas Portal v2

A web management portal for an ODA Canvas. It is the successor to the Spring Boot + Vue portal in `canvas-portal/`.

| Part | Stack | Role |
|---|---|---|
| `frontend/` | React 18, Vite, TypeScript, Ant Design, React Query, `keycloak-js`, d3/dagre | The UI. Served by nginx in production. |
| `backend/` | FastAPI, `kubernetes` client, JWT validation | The API. It reads and writes the cluster. |
| `helm/canvas-portal/` | Helm chart | Deploys both parts, plus RBAC, volumes and a Keycloak init job. |

## Features

- **Components:** list ODA Components with status, pods, APIs and events (`/api/components`).
- **APIs:** browse exposed and dependent APIs, with an API relationship graph and resource map.
- **Gateway:** view Istio, Kong or APISIX resources. The backend detects the gateway at startup from the deployment names in the `canvas` namespace.
- **Operators and pods:** view operators and pods, with live log streaming.
- **Helm** (admins only): manage chart repositories, then install, uninstall and view history and values for releases. Installs are limited to configured namespaces and, optionally, allowed chart sources.
- **Conformance** (admins only): run the Canvas BDD tests from the repo, view logs, and download the cucumber and HTML reports.
- **Model gateway:** create, edit and delete `ModelGatewayService` resources, and proxy chat requests through them.
- **Cluster overview and observability:** a cluster summary, plus Grafana and Prometheus links if configured.
- **Authentication:** Keycloak or Entra ID (`IDM_PROVIDER`). The backend validates the JWT and the browser keeps a refresh cookie.

## Prerequisites

- A running ODA Canvas. The `canvas` namespace must exist for gateway detection.
- A Keycloak realm with a `canvas-portal` client and a `canvas-portal-admin` service client. The chart does not create the realm or the clients. Its `keycloak.init` job (which needs the Keycloak master admin password) creates the admin group and realm role (see [Admin access](#admin-access)) and grants the `canvas-portal-admin` service account its permissions.
- Persistent storage: 5Gi for the backend (Helm repo catalog and conformance runs) and 1Gi for the frontend.

## Deploy with Helm

```bash
helm install canvas-portal ./helm/canvas-portal -n <ns> \
  --set keycloak.init.adminPassword=... \
  --set backend.env.KEYCLOAK_URL=https://<keycloak>/auth \
  --set frontend.nginx.keycloakUpstream=https://<keycloak>/auth
```

Images default to `tmforumodacanvas/canvas-portal` (tags `frontend-0.1.0` and `backend-0.1.0`). Review these defaults in `helm/canvas-portal/values.yaml` before installing, because several look environment-specific:

- `KEYCLOAK_URL` and `frontend.nginx.keycloakUpstream` default to a hardcoded IP.
- `keycloak.init.adminUser` defaults to `testadminpo.`.
- `CORS_ORIGINS` includes the placeholder `http://xx.xx.xx.xx`.
- `rbac.*.targetNamespaces` defaults to `components`, `odacompns-1` and `temp-namespace`. Add any namespace you want to install into or run conformance tests in, then run `helm upgrade`.
- Both Services are `LoadBalancer` by default.
- `backend.auth.cookieSecure` is `false`. Set it to `true` when serving over HTTPS.
- The Keycloak realm defaults to `odari` in the chart, but to `canvas` in `frontend/.env.example` and the frontend entrypoint.

## Build the images

```bash
docker build -t <repo>:frontend-0.1.0 frontend
docker build -t <repo>:backend-0.1.0  backend
```

Then set `frontend.image.*` and `backend.image.*` in the chart values.

## Authentication

Login goes through the backend, not through `keycloak-js`.

1. The login page posts `{username, password}` to `POST /auth/login`. The backend runs a Keycloak password grant against the `canvas-portal` client.
2. The access token is returned in the response body and held **in memory only** by `frontend/src/lib/auth.ts`. The refresh token goes into an `httpOnly` cookie (`canvas_portal_refresh`, path `/auth`, `Secure` and `SameSite` set by `backend.auth.*`).
3. On a page reload, `main.tsx` calls `POST /auth/refresh` to turn the cookie into a new access token. `useSessionManager` shows a warning before expiry. `client.ts` retries on a 401.
4. `POST /auth/logout` revokes the refresh token at Keycloak and clears the cookie.
5. Every `/api/*` route uses the `get_current_user` dependency. It verifies the bearer JWT (RS256, signature via the realm JWKS, `exp` and `iss`) and builds an `AuthUser` from `preferred_username`, `email`, `groups` and `sub`.

First-login flow: if Keycloak answers "Account is not fully set up", `/auth/login` returns 409. The UI then asks for a new password and calls `/auth/set-initial-password`. The backend uses the `canvas-portal-admin` service client (`KEYCLOAK_ADMIN_CLIENT_SECRET`) to clear required actions and reset the password. `GET /auth/security-status` warns when the Canvas default `admin`/`adpass` credentials still work in the `odari` realm.

`frontend/src/lib/keycloak.ts` (a `keycloak-js` redirect flow) exists but is not imported by the login path.

Entra ID is selectable with `IDM_PROVIDER=entraid`, but `/auth/login`, `/auth/refresh` and `set-initial-password` use the Keycloak token endpoint only. With Entra ID, only bearer-token validation on the API is covered.

### Admin access

`/api/helm/*` and `/api/conformance/*` require the user to hold one of the names in `backend.auth.adminGroups` (env `AUTHZ_ADMIN_GROUPS`, a JSON list, default `["canvas-admin"]`). Everyone else gets 403.

- With Keycloak, the backend checks both the `groups` claim and the realm roles (`realm_access.roles`). A leading `/` in group paths is ignored, so `/canvas-admin` matches `canvas-admin`.
- On install and upgrade, the `keycloak.init` job creates a group **and** a realm role for each name (top-level names only), and gives the group that role. It does not assign users.
- To grant access, add the user to the `canvas-admin` group or assign them the `canvas-admin` realm role. Realm roles are in the access token by default, so no extra Keycloak mapper is needed.
- The check fails closed: an empty `adminGroups` list denies everyone.
- `backend.auth.allowAllAuthenticated: true` (env `AUTHZ_ALLOW_ALL_AUTHENTICATED`) turns the check off, so any logged-in user can use Helm and conformance again.
- **Upgrading an existing install:** after the upgrade, Helm and conformance return 403 until users are in the group or have the role. To keep the old behaviour, set `backend.auth.allowAllAuthenticated: true`.
- The UI does not hide these pages from other users. They see an error when the API returns 403.

### Security notes

- **Role check on Helm and conformance only.** See [Admin access](#admin-access). All other routes (components, gateway, pods, operators, model gateway and so on) are open to any authenticated user.
- **Backend service account for everything.** `get_impersonated_client()` ignores the user and returns the shared backend client. Kubernetes audit logs show the portal service account, not the person. The Helm router logs the username.
- **TLS verification is off for Keycloak.** The backend calls Keycloak with `httpx.AsyncClient(verify=False)`, and the `keycloak-init` job disables certificate checks.
- **Audience is not verified** (`verify_aud` is false), so tokens issued to any client in the realm are accepted.
- **Out-of-cluster mode** disables TLS verification to the API server if `K8S_REMOTE_CA_CERT` is empty.

## RBAC model

The backend runs as one ServiceAccount, and the chart grants it these permissions.

| Template | Scope | Grants |
|---|---|---|
| `backend-gateway-read-clusterrole.yaml` (`rbac.backendGatewayReadAccess`) | Cluster-wide, read-only | `get/list/watch` on nodes, pods, pods/log, services, events, namespaces, deployments, ODA `components`/`exposedapis`/`modelgatewayservices`, Gateway API, Kong, APISIX and Istio resources. `get` on the `modelgatewayservices` CRD. |
| `canvas-install-rbac.yaml` (`rbac.canvasInstallAccess`) | Per namespace in `targetNamespaces` | A `RoleBinding` of the ClusterRole named by `clusterRoleName` (default `admin`) to the backend ServiceAccount. A ClusterRole aggregated into `admin` adds `oda.tmforum.org/*`. |
| `backend-model-gateway-rbac.yaml` (`rbac.modelGatewayAccess`) | Per namespace | Write access on `modelgatewayservices.oda.tmforum.org`. |
| `backend-conformance-rbac.yaml` (`rbac.canvasConformanceAccess`) | Cluster roles plus per-namespace roles | What the BDD runner needs. |

How this fits together:

- `INSTALL_TARGET_NAMESPACES_JSON` in the backend ConfigMap comes from `rbac.canvasInstallAccess.targetNamespaces`. The Helm install and uninstall routes return 403 for other namespaces if the list is non-empty, so the app check and the RoleBindings stay in sync.
- To allow a new namespace, add it to `targetNamespaces` and run `helm upgrade`. With `createNamespaces: false` it must already exist.
- `create_namespace` in the install request only works if the service account may create namespaces. The error handler hints at this.
- The namespaced `admin` role is powerful inside those namespaces (secrets, workloads, RBAC). Only users with the admin role can reach the Helm routes (see [Admin access](#admin-access)), so keep that role to people you would trust with those namespaces.

## Helm install flow

Helm operations run by shelling out to the `helm` v3.15.4 binary baked into the backend image (`backend/k8s/helm/installer.py`).

1. **Repositories** (`/api/helm/repos`) are kept in a JSON catalog on the PVC (`/app/data/helm-repositories.json`). `POST /repos` adds one and `POST /repos/{name}/sync` refreshes its chart index. The portal does not rely on the container's `helm repo` state.
2. **Browse and configure.** The UI lists charts and versions from the catalog and fetches default values with `GET /api/helm/values`.
3. **Install** (`POST /api/helm/install`):
   - It checks the namespace against `INSTALL_TARGET_NAMESPACES_JSON`.
   - It checks `repo_url` or `oci://`/`http(s)://` chart refs against `backend.helm.allowedChartSources`. An empty list allows any source.
   - It writes a temporary kubeconfig that uses the service account token. In-cluster this is the mounted token and CA. Out-of-cluster it is `K8S_REMOTE_*`.
   - It runs `helm upgrade --install <release> <chart> -n <ns> --wait --timeout <1-60>m [--create-namespace] [--version] [--repo] -f <values>`, so installing an existing release name upgrades it. Values come from `values_yaml` or `values`.
   - On failure it returns 500 with the Helm error plus a hint for known RBAC problems.
4. **Manage.** `GET /releases`, `GET /history`, `GET /releases/values` and `DELETE /uninstall` cover the lifecycle. The frontend modals are `HelmInstallModal`, `HelmHistoryModal` and `HelmReleaseManagementModals`. nginx gives `/api/` a 10-minute read timeout because installs use `--wait`.

## Deploying the portal itself

On `helm install` or `helm upgrade`, a `post-install`/`post-upgrade` hook Job (`keycloak-init`) runs a Python script. It logs in to Keycloak's `master` realm as `keycloak.init.adminUser`, creates a group and a realm role for each `backend.auth.adminGroups` entry (if missing) and maps the role onto the group, finds the `canvas-portal-admin` client's service account, and grants it `manage-users`, `view-users` and `query-users` from `realm-management`. It retries 5 times and warns if the client is missing.

Order of work:

1. Create the Keycloak realm and clients first. The init job does not create them.
2. Fill in the Keycloak URL, realm, `KEYCLOAK_ADMIN_CLIENT_SECRET` and `keycloak.init.adminPassword`. The chart fails to render if `KEYCLOAK_URL` is empty.
3. List every namespace you will install into in the `rbac.*.targetNamespaces` values.
4. After install, check `kubectl get svc` for the frontend external IP, then add that origin to `backend.env.CORS_ORIGINS`.
5. Verify with `GET /health`. It returns the detected `canvasType` and the IDM provider.

The frontend gets its runtime settings (`APP_API_BASE_URL`, `APP_KEYCLOAK_*`) from `config.js`, which the nginx entrypoint writes at container start. nginx proxies `/api/*` and the session endpoints to `BACKEND_UPSTREAM`, and Keycloak paths under `/auth/realms|resources|js|admin` to `KEYCLOAK_UPSTREAM`.

## Local development

The backend only needs a Kubernetes API URL and a token, so you can run the backend and frontend on your machine against any cluster.

1. **Make a service account for the portal.** Reuse the chart's RBAC by installing the chart once, then read the backend service account's token:
   ```bash
   kubectl -n <ns> create token <backend-serviceaccount> --duration=8h
   kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.server}'
   kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'
   ```
   `K8S_REMOTE_CA_CERT` takes the base64 value as printed.
2. **Install `helm`** locally (v3). The Helm routes call it, and all other features work without it.
3. **Run the backend** from `backend/` with the variables below, plus `HELM_REPOSITORY_CATALOG_PATH=./data/helm-repositories.json` and the other paths in `config.py`:
   ```bash
   APP_ENV=development K8S_MODE=outofcluster \
   K8S_REMOTE_API_URL=<server> K8S_REMOTE_SA_TOKEN=<token> K8S_REMOTE_CA_CERT=<b64-ca> \
   KEYCLOAK_URL=<keycloak-url>/auth KEYCLOAK_REALM=<realm> \
   AUTH_COOKIE_SECURE=false CORS_ORIGINS='["http://localhost:3000"]' \
   INSTALL_TARGET_NAMESPACES_JSON='["components"]' \
   CONFORMANCE_RUN_STORE_PATH=./data/conformance-runs.json \
   CONFORMANCE_WORK_DIR=./data/conformance-work \
   CONFORMANCE_SCRATCH_DIR=./data/conformance-scratch \
   uvicorn main:app --port 8080 --reload
   ```
   The `CONFORMANCE_*` defaults point at `/app/data` and `/var/conformance-scratch`, which only exist in the container.
   Settings come from environment variables or a `.env` file (see `backend/config.py`). With `APP_ENV=development`, Swagger is served at `/docs`. To use the Helm and conformance pages, log in as a user with the admin role (see [Admin access](#admin-access)), or set `AUTHZ_ALLOW_ALL_AUTHENTICATED=true` for local testing.
4. **Run the frontend** from `frontend/`:
   ```bash
   cp .env.example .env   # set VITE_KEYCLOAK_*, VITE_DEV_KEYCLOAK_PROXY_TARGET; remove VITE_API_URL
   npm ci && npm run dev  # http://localhost:3000
   ```
   The production nginx image is configured instead with `APP_*` variables, which its entrypoint writes into `config.js`.
5. **Gotchas.**
   - The Vite dev server proxies `/api`, `/health` and all `/auth/*` session endpoints to the backend (`VITE_DEV_BACKEND_URL`, default `http://localhost:8080`), and `/auth/realms|resources|js|admin` to Keycloak (`VITE_DEV_KEYCLOAK_PROXY_TARGET`). Leave `VITE_API_URL` unset in dev so requests stay same-origin and the cookie works.
   - The refresh cookie has `SameSite=strict` and path `/auth`. For a cross-origin dev setup, use `AUTH_COOKIE_SAMESITE=lax` or run both on `localhost`.
   - A port-forward also works: `kubectl port-forward svc/<backend-svc> 8080:8080` lets you run only the frontend locally.
   - The Keycloak realm must be reachable from the backend host.

## Tests

Backend unit tests use `pytest`:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```
