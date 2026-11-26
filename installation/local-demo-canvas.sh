#!/usr/bin/env bash
#
# Builds a complete local demo Canvas on kind: Istio, the Canvas, the Product
# Catalog reference component and the Canvas Portal v2.
#
# See local-demo-canvas.md for what each step does and why.
#
# Usage:
#   ./installation/local-demo-canvas.sh
#
# Settings (environment variables):
#   CLUSTER_NAME       kind cluster name                      (default: oda-demo)
#   HTTP_PORT          host port for the API gateway's HTTP   (default: 80)
#   HTTPS_PORT         host port for the API gateway's HTTPS  (default: 443)
#   PORTAL_PORT        host port for the Canvas Portal        (default: 8090)
#   CANVAS_VERSION     canvas-oda chart version               (default: latest release candidate)
#   ISTIO_VERSION      Istio chart version                    (default: latest)
#   GATEWAY_API_VERSION  Kubernetes Gateway API CRDs version  (default: v1.0.0)
#   INSTALL_COMPONENT  install the Product Catalog component  (default: true)
#   INSTALL_PORTAL     install the Canvas Portal v2           (default: true)
#   PORTAL_USER        Portal user name                       (default: demo)
#   PORTAL_PASSWORD    Portal password                        (default: generated, and printed at the end)
#
# The script can be run again on the same cluster: it skips or upgrades what is
# already there.

set -euo pipefail

CLUSTER_NAME=${CLUSTER_NAME:-oda-demo}
HTTP_PORT=${HTTP_PORT:-80}
HTTPS_PORT=${HTTPS_PORT:-443}
PORTAL_PORT=${PORTAL_PORT:-8090}
CANVAS_VERSION=${CANVAS_VERSION:-}
ISTIO_VERSION=${ISTIO_VERSION:-}
GATEWAY_API_VERSION=${GATEWAY_API_VERSION:-v1.0.0}
INSTALL_COMPONENT=${INSTALL_COMPONENT:-true}
INSTALL_PORTAL=${INSTALL_PORTAL:-true}
PORTAL_USER=${PORTAL_USER:-demo}
PORTAL_PASSWORD=${PORTAL_PASSWORD:-}

# Git Bash on Windows rewrites arguments that look like paths, such as the
# container paths given to kubectl exec. Turn that off.
export MSYS_NO_PATHCONV=1

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
CONTEXT="kind-$CLUSTER_NAME"
WORK_DIR=$(mktemp -d)
# On Windows, give Windows programs such as kind.exe and git.exe paths they can read
if command -v cygpath >/dev/null; then
  WORK_DIR=$(cygpath -m "$WORK_DIR")
  REPO_DIR=$(cygpath -m "$REPO_DIR")
fi
trap 'rm -rf "$WORK_DIR"' EXIT
START=$SECONDS

# Every kubectl and helm call names the kind cluster's context, so the script
# never acts on another cluster, whatever the current context is.
k() { kubectl --context "$CONTEXT" "$@"; }
h() { helm --kube-context "$CONTEXT" "$@"; }

step() { printf '\n\033[1m==> [%d:%02d] %s\033[0m\n' $(((SECONDS - START) / 60)) $(((SECONDS - START) % 60)) "$*"; }
fail() { printf '\033[31mError: %s\033[0m\n' "$*" >&2; exit 1; }

version_flag() { if [ -n "$1" ]; then echo "--version $1"; fi; }

# ---------------------------------------------------------------------------
step "Checking the tools"
for tool in docker kind kubectl helm curl; do
  command -v "$tool" >/dev/null || fail "$tool isn't installed. See local-demo-canvas.md, 'Before you start'."
done
if [ "$INSTALL_PORTAL" = true ]; then
  command -v git >/dev/null || fail "git is needed to build the Portal images (or set INSTALL_PORTAL=false)."
fi
docker info >/dev/null 2>&1 || fail "Docker isn't running."

# ---------------------------------------------------------------------------
step "Creating the kind cluster '$CLUSTER_NAME'"
# The node's ports 30080, 30443 and 30090 are mapped to the host. The gateway
# and the Portal use them as fixed node ports, so no port-forward is needed.
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  echo "The cluster already exists."
else
  cat > "$WORK_DIR/kind.yaml" <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - { containerPort: 30080, hostPort: $HTTP_PORT, listenAddress: 127.0.0.1 }
      - { containerPort: 30443, hostPort: $HTTPS_PORT, listenAddress: 127.0.0.1 }
      - { containerPort: 30090, hostPort: $PORTAL_PORT, listenAddress: 127.0.0.1 }
EOF
  kind create cluster --name "$CLUSTER_NAME" --config "$WORK_DIR/kind.yaml" --wait 2m \
    || fail "kind couldn't create the cluster. If a port is already in use, set HTTP_PORT, HTTPS_PORT or PORTAL_PORT."
fi

# ---------------------------------------------------------------------------
step "Installing Istio"
helm repo add istio https://istio-release.storage.googleapis.com/charts --force-update >/dev/null
helm repo add oda-canvas https://tmforum-oda.github.io/oda-canvas --force-update >/dev/null
helm repo add oda-components https://tmforum-oda.github.io/reference-example-components --force-update >/dev/null
helm repo update >/dev/null

# The Kubernetes Gateway API CRDs. Istio doesn't need them, but the Portal's
# Gateway, Service Mesh and Policies pages fail without them, and Kong needs them.
k apply -f "https://github.com/kubernetes-sigs/gateway-api/releases/download/$GATEWAY_API_VERSION/standard-install.yaml" >/dev/null

k create namespace istio-system --dry-run=client -o yaml | k apply -f - >/dev/null
k create namespace istio-ingress --dry-run=client -o yaml | k apply -f - >/dev/null
k label namespace istio-ingress istio-injection=enabled --overwrite >/dev/null
# shellcheck disable=SC2046
h upgrade --install istio-base istio/base -n istio-system $(version_flag "$ISTIO_VERSION") >/dev/null
# shellcheck disable=SC2046
h upgrade --install istiod istio/istiod -n istio-system $(version_flag "$ISTIO_VERSION") --wait >/dev/null

cat > "$WORK_DIR/gateway.yaml" <<'EOF'
labels:
  app: istio-ingress
  istio: ingressgateway
service:
  type: LoadBalancer
  ports:
    - { name: status-port, port: 15021, protocol: TCP, targetPort: 15021 }
    - { name: http2, port: 80, protocol: TCP, targetPort: 80, nodePort: 30080 }
    - { name: https, port: 443, protocol: TCP, targetPort: 443, nodePort: 30443 }
EOF
# No --wait: Helm would wait for the LoadBalancer service to get an address,
# which kind never gives it. The next step sets one.
# shellcheck disable=SC2046
h upgrade --install istio-ingress istio/gateway -n istio-ingress $(version_flag "$ISTIO_VERSION") \
  -f "$WORK_DIR/gateway.yaml" >/dev/null

# ---------------------------------------------------------------------------
step "Giving the ingress gateway the address 127.0.0.1"
# kind has no load balancer. The Canvas needs the gateway to have an address
# before the Canvas and any component are installed (see #621).
k patch svc istio-ingress -n istio-ingress --subresource=status --type=merge \
  -p '{"status":{"loadBalancer":{"ingress":[{"ip":"127.0.0.1"}]}}}' >/dev/null
k rollout status deployment/istio-ingress -n istio-ingress --timeout=5m
k get svc istio-ingress -n istio-ingress

# ---------------------------------------------------------------------------
step "Installing the Canvas (about five minutes)"
# No --wait: the post-install hooks create what several pods need, so --wait
# never finishes. Helm still waits for the hooks.
if h status canvas -n canvas >/dev/null 2>&1; then
  echo "The Canvas is already installed."
else
  if [ -n "$CANVAS_VERSION" ]; then canvas_version="--version $CANVAS_VERSION"; else canvas_version="--devel"; fi
  # shellcheck disable=SC2086
  h install canvas oda-canvas/canvas-oda -n canvas --create-namespace $canvas_version --timeout 15m >/dev/null
fi
echo "Waiting for the Canvas deployments..."
k wait --for=condition=Available deployment --all -n canvas --timeout=10m >/dev/null
k rollout status statefulset/canvas-keycloak -n canvas --timeout=10m >/dev/null
echo "The Canvas is running."

# ---------------------------------------------------------------------------
if [ "$INSTALL_COMPONENT" = true ]; then
  step "Installing the Product Catalog component"
  if h status demo -n components >/dev/null 2>&1; then
    echo "The component is already installed."
  else
    h install demo oda-components/productcatalog -n components >/dev/null
  fi
  printf 'Waiting for the component to reach Complete'
  status=""
  for _ in $(seq 1 60); do
    status=$(k get components -n components demo-productcatalogmanagement --no-headers \
      -o custom-columns=S:.status.summary/status.deployment_status 2>/dev/null || true)
    [ "$status" = Complete ] && break
    printf '.'
    sleep 5
  done
  echo
  [ "$status" = Complete ] || fail "The component is still at '$status' after five minutes. See the troubleshooting table in local-demo-canvas.md."
  k get exposedapis -n components

  echo "Calling the catalog API through the gateway:"
  curl -sSk --retry 5 --retry-delay 2 --retry-all-errors \
    "https://127.0.0.1:$HTTPS_PORT/demo-productcatalogmanagement/tmf-api/productCatalogManagement/v4/catalog"
  echo
fi

# ---------------------------------------------------------------------------
if [ "$INSTALL_PORTAL" = true ]; then
  step "Building the Canvas Portal v2 images"
  # The Portal images aren't published yet. Build them from this checkout's
  # last commit. git archive with core.autocrlf=false gives Unix line endings
  # even on a Windows checkout; Windows line endings break the frontend.
  git -C "$REPO_DIR" -c core.autocrlf=false archive HEAD canvas-portal-v2 | (cd "$WORK_DIR" && tar -x)
  docker build -q -t oda-demo/canvas-portal:frontend "$WORK_DIR/canvas-portal-v2/frontend"
  docker build -q -t oda-demo/canvas-portal:backend "$WORK_DIR/canvas-portal-v2/backend"
  kind load docker-image --name "$CLUSTER_NAME" oda-demo/canvas-portal:frontend oda-demo/canvas-portal:backend

  step "Setting up Keycloak for the Portal"
  kcadm() {
    k exec -n canvas canvas-keycloak-0 -- /opt/bitnami/keycloak/bin/kcadm.sh "$@" --config /tmp/kcadm.config
  }
  csv() { kcadm "$@" --format csv --noquotes | tr -d '\r'; }

  kcadm config credentials --server http://localhost:8083/auth --realm master --user admin \
    --password "$(k get secret canvas-keycloak -n canvas -o jsonpath='{.data.admin-password}' | base64 -d)"

  # The login client: public, with direct access grants (the backend uses a password grant)
  if [ -z "$(csv get clients -r odari -q clientId=canvas-portal --fields id)" ]; then
    kcadm create clients -r odari -s clientId=canvas-portal -s publicClient=true \
      -s directAccessGrantsEnabled=true -s standardFlowEnabled=false
  fi
  # The admin client: confidential, with a service account that can manage users
  if [ -z "$(csv get clients -r odari -q clientId=canvas-portal-admin --fields id)" ]; then
    kcadm create clients -r odari -s clientId=canvas-portal-admin -s publicClient=false \
      -s serviceAccountsEnabled=true -s standardFlowEnabled=false
  fi
  kcadm add-roles -r odari --uusername service-account-canvas-portal-admin \
    --cclientid realm-management --rolename manage-users --rolename view-users --rolename query-users

  # The Portal's admin group, with a realm role of the same name mapped onto
  # it. The role is what reaches the user's token (in realm_access.roles), so
  # members get the Portal's admin features.
  if [ -z "$(csv get groups -r odari -q search=canvas-admin -q exact=true --fields id)" ]; then
    kcadm create groups -r odari -s name=canvas-admin
  fi
  if ! kcadm get roles/canvas-admin -r odari >/dev/null 2>&1; then
    kcadm create roles -r odari -s name=canvas-admin -s 'description=Canvas Portal: Helm and conformance access'
  fi
  kcadm add-roles -r odari --gname canvas-admin --rolename canvas-admin
  if [ -z "$PORTAL_PASSWORD" ]; then
    PORTAL_PASSWORD=$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9')
    PORTAL_PASSWORD=${PORTAL_PASSWORD:0:16}
  fi
  user_id=$(csv get users -r odari -q username="$PORTAL_USER" -q exact=true --fields id)
  if [ -z "$user_id" ]; then
    kcadm create users -r odari -s username="$PORTAL_USER" -s enabled=true \
      -s email="$PORTAL_USER@example.com" -s emailVerified=true -s firstName=Demo -s lastName=User \
      -s 'groups=["canvas-admin"]' \
      -s "credentials=[{\"type\":\"password\",\"value\":\"$PORTAL_PASSWORD\",\"temporary\":false}]"
  else
    echo "The user '$PORTAL_USER' already exists: setting its password."
    kcadm set-password -r odari --userid "$user_id" --new-password "$PORTAL_PASSWORD"
  fi

  client_id=$(csv get clients -r odari -q clientId=canvas-portal-admin --fields id)
  admin_secret=$(csv get "clients/$client_id/client-secret" -r odari --fields value)

  step "Installing the Canvas Portal v2"
  keycloak_url=http://canvas-keycloak-headless.canvas.svc.cluster.local:8083/auth
  cat > "$WORK_DIR/portal.yaml" <<EOF
frontend:
  image: { repository: oda-demo/canvas-portal, tag: frontend, pullPolicy: Never }
  service: { type: NodePort }
  nginx:
    keycloakUpstream: $keycloak_url
backend:
  image: { repository: oda-demo/canvas-portal, tag: backend, pullPolicy: Never }
  service: { type: ClusterIP }
  env:
    KEYCLOAK_URL: $keycloak_url
    CORS_ORIGINS:
      - http://localhost:$PORTAL_PORT
keycloak:
  init:
    enabled: false
rbac:
  canvasInstallAccess: { targetNamespaces: [components] }
  modelGatewayAccess: { targetNamespaces: [components] }
  canvasConformanceAccess: { targetNamespaces: [components] }
EOF
  h upgrade --install canvas-portal "$WORK_DIR/canvas-portal-v2/helm/canvas-portal" -n canvas \
    -f "$WORK_DIR/portal.yaml" --set backend.secretEnv.KEYCLOAK_ADMIN_CLIENT_SECRET="$admin_secret" >/dev/null
  # Fix the frontend's node port, which kind maps to PORTAL_PORT on the host
  k patch svc canvas-portal-frontend -n canvas --type=json \
    -p '[{"op":"replace","path":"/spec/ports/0/nodePort","value":30090}]' >/dev/null
  # Restart the pods, so that a new client secret or image is picked up on a re-run
  k rollout restart deployment/canvas-portal-backend deployment/canvas-portal-frontend -n canvas >/dev/null
  k rollout status deployment/canvas-portal-backend -n canvas --timeout=5m >/dev/null
  k rollout status deployment/canvas-portal-frontend -n canvas --timeout=5m >/dev/null
  echo "The Portal is running."
fi

# ---------------------------------------------------------------------------
step "Done"
https_suffix=""; [ "$HTTPS_PORT" = 443 ] || https_suffix=":$HTTPS_PORT"
cat <<EOF

Your demo Canvas is ready, in the kind cluster '$CLUSTER_NAME' (kubectl context $CONTEXT).

API gateway:    https://127.0.0.1$https_suffix/
EOF
if [ "$INSTALL_COMPONENT" = true ]; then
  cat <<EOF
Catalog API:    curl -k https://127.0.0.1$https_suffix/demo-productcatalogmanagement/tmf-api/productCatalogManagement/v4/catalog
EOF
fi
if [ "$INSTALL_PORTAL" = true ]; then
  cat <<EOF
Canvas Portal:  http://localhost:$PORTAL_PORT
  User:         $PORTAL_USER
  Password:     $PORTAL_PASSWORD
EOF
fi
cat <<EOF

To delete it:   kind delete cluster --name $CLUSTER_NAME
EOF
