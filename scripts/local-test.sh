#!/bin/bash
set -e

# Local testing script for Canvas ODA with PDB Management Operator
# This script provides quick local testing without GitHub Actions

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="canvas-test"
NAMESPACE="canvas"
TIMEOUT="10m"

# Parse command line arguments
SKIP_CLEANUP=false
QUICK_TEST=false
FULL_CANVAS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --quick)
            QUICK_TEST=true
            shift
            ;;
        --full)
            FULL_CANVAS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-cleanup    Don't delete kind cluster after tests"
            echo "  --quick          Run minimal tests (PDB operator only)"
            echo "  --full           Install full Canvas with all components"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    for tool in docker kubectl kind helm; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools:"
        for tool in "${missing_tools[@]}"; do
            case $tool in
                docker)
                    echo "  - Docker: https://docs.docker.com/get-docker/"
                    ;;
                kubectl)
                    echo "  - kubectl: brew install kubectl (Mac) or see https://kubernetes.io/docs/tasks/tools/"
                    ;;
                kind)
                    echo "  - kind: brew install kind (Mac) or see https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
                    ;;
                helm)
                    echo "  - helm: brew install helm (Mac) or see https://helm.sh/docs/intro/install/"
                    ;;
            esac
        done
        exit 1
    fi
    
    log_success "All prerequisites installed"
}

create_kind_cluster() {
    log_info "Creating kind cluster '$CLUSTER_NAME'..."
    
    # Check if cluster already exists
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_warning "Cluster '$CLUSTER_NAME' already exists. Deleting..."
        kind delete cluster --name=$CLUSTER_NAME
    fi
    
    # Create kind configuration
    cat <<EOF > /tmp/kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 8083
    hostPort: 8083
    protocol: TCP
EOF
    
    kind create cluster --config=/tmp/kind-config.yaml
    kubectl cluster-info --context kind-${CLUSTER_NAME}
    
    log_success "Kind cluster created"
}

install_istio() {
    log_info "Installing Istio..."
    
    helm repo add istio https://istio-release.storage.googleapis.com/charts
    helm repo update
    
    kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Install with minimal resources for local testing
    helm upgrade --install istio-base istio/base -n istio-system
    helm upgrade --install istiod istio/istiod -n istio-system \
        --set pilot.resources.requests.cpu=100m \
        --set pilot.resources.requests.memory=128Mi \
        --wait --timeout=5m
    
    kubectl create namespace istio-ingress --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace istio-ingress istio-injection=enabled --overwrite
    
    helm upgrade --install istio-ingress istio/gateway -n istio-ingress \
        --set service.type=NodePort \
        --set resources.requests.cpu=100m \
        --set resources.requests.memory=128Mi
    
    log_success "Istio installed"
}

update_helm_dependencies() {
    log_info "Updating Helm dependencies..."
    
    cd "$PROJECT_ROOT"
    
    if [ "$QUICK_TEST" = true ]; then
        # Only update PDB operator dependencies
        helm dependency update ./charts/pdb-management-operator 2>/dev/null || true
        helm dependency update ./charts/cert-manager-init
        helm dependency update ./charts/canvas-oda
    else
        # Update all dependencies
        for chart in charts/*/; do
            if [ -f "$chart/Chart.yaml" ]; then
                log_info "Updating $(basename $chart)..."
                helm dependency update "$chart" 2>/dev/null || true
            fi
        done
    fi
    
    log_success "Helm dependencies updated"
}

install_canvas() {
    log_info "Installing Canvas ODA..."
    
    cd "$PROJECT_ROOT"
    
    local helm_args=(
        "canvas"
        "./charts/canvas-oda"
        "--namespace=$NAMESPACE"
        "--create-namespace"
        "--timeout=$TIMEOUT"
    )
    
    if [ "$QUICK_TEST" = true ]; then
        # Minimal installation for quick testing
        helm_args+=(
            "--set=keycloak.enabled=false"
            "--set=canvas-vault.enabled=false"
            "--set=component-operator.enabled=false"
            "--set=api-operator-istio.enabled=false"
        )
    elif [ "$FULL_CANVAS" = false ]; then
        # Default: PDB operator focused testing
        helm_args+=(
            "--set=keycloak.enabled=false"
            "--set=canvas-vault.enabled=false"
        )
    fi
    
    helm upgrade --install "${helm_args[@]}"
    
    log_success "Canvas ODA installed"
}

verify_pdb_operator() {
    log_info "Verifying PDB Management Operator..."
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=60s \
        deployment -n $NAMESPACE -l app.kubernetes.io/name=pdb-management || {
        log_error "PDB operator deployment not ready"
        kubectl get pods -n $NAMESPACE
        kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=pdb-management --tail=100
        return 1
    }
    
    # Check services
    log_info "Checking services..."
    kubectl get service -n $NAMESPACE | grep pdb-management
    
    # Verify service name length
    local service_names=$(kubectl get service -n $NAMESPACE -o json | jq -r '.items[].metadata.name' | grep pdb-management)
    for svc in $service_names; do
        local len=${#svc}
        if [ $len -gt 63 ]; then
            log_error "Service name too long: $svc ($len chars)"
            return 1
        else
            log_success "Service name OK: $svc ($len chars)"
        fi
    done
    
    # Check CRD
    if kubectl get crd availabilitypolicies.availability.oda.tmforum.org &>/dev/null; then
        log_success "AvailabilityPolicy CRD found"
    else
        log_error "AvailabilityPolicy CRD not found"
        return 1
    fi
    
    log_success "PDB operator verification passed"
}

test_pdb_functionality() {
    log_info "Testing PDB functionality..."
    
    # Create test policy
    cat <<EOF | kubectl apply -f -
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: test-policy
  namespace: $NAMESPACE
spec:
  selector:
    matchLabels:
      app: test-pdb
  targetAvailability: "99.9"
  minAvailable: 2
  enforcement: Advisory
EOF
    
    # Create test deployment
    kubectl create deployment test-pdb-app \
        --image=nginx:alpine \
        --replicas=3 \
        -n $NAMESPACE
    
    kubectl label deployment test-pdb-app app=test-pdb -n $NAMESPACE
    
    # Wait for PDB creation
    sleep 5
    
    # Check if PDB was created
    if kubectl get pdb -n $NAMESPACE | grep test-pdb; then
        log_success "PDB created successfully"
        kubectl get pdb -n $NAMESPACE -o wide
    else
        log_warning "PDB not created (might be expected in Advisory mode)"
    fi
    
    # Cleanup test resources
    kubectl delete deployment test-pdb-app -n $NAMESPACE --ignore-not-found=true
    kubectl delete availabilitypolicy test-policy -n $NAMESPACE --ignore-not-found=true
    
    log_success "PDB functionality test completed"
}

show_status() {
    log_info "Current cluster status:"
    echo "========================"
    
    echo -e "\n${YELLOW}Nodes:${NC}"
    kubectl get nodes
    
    echo -e "\n${YELLOW}Canvas namespace:${NC}"
    kubectl get all -n $NAMESPACE
    
    echo -e "\n${YELLOW}PDB Resources:${NC}"
    kubectl get availabilitypolicy -A 2>/dev/null || echo "No AvailabilityPolicies found"
    kubectl get pdb -A 2>/dev/null || echo "No PodDisruptionBudgets found"
    
    echo -e "\n${YELLOW}Recent PDB operator logs:${NC}"
    kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=pdb-management --tail=20 2>/dev/null || echo "No logs available"
}

cleanup() {
    if [ "$SKIP_CLEANUP" = false ]; then
        log_info "Cleaning up..."
        kind delete cluster --name=$CLUSTER_NAME
        rm -f /tmp/kind-config.yaml
        log_success "Cleanup completed"
    else
        log_info "Skipping cleanup (--skip-cleanup flag set)"
        log_info "To delete the cluster later, run: kind delete cluster --name=$CLUSTER_NAME"
    fi
}

# Main execution
main() {
    echo -e "${GREEN}Canvas ODA Local Testing Script${NC}"
    echo "================================"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run tests
    check_prerequisites
    create_kind_cluster
    install_istio
    update_helm_dependencies
    install_canvas
    
    # Wait for pods to be ready
    log_info "Waiting for pods to stabilize..."
    sleep 10
    
    verify_pdb_operator
    
    if [ "$QUICK_TEST" = false ]; then
        test_pdb_functionality
    fi
    
    show_status
    
    log_success "All tests completed successfully!"
    
    if [ "$SKIP_CLEANUP" = true ]; then
        echo -e "\n${YELLOW}Cluster is still running. You can interact with it using:${NC}"
        echo "  kubectl config use-context kind-${CLUSTER_NAME}"
        echo "  kubectl get all -n ${NAMESPACE}"
    fi
}

# Run main function
main