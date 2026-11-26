#!/bin/bash
set -e

# Configuration
OPERATOR_NAMESPACE="canvas"
TEST_NAMESPACE="pdb-perf-test"
RESULTS_DIR="performance-results-$(date +%Y%m%d-%H%M%S)"
METRICS_PORT=8443

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Create results directory
mkdir -p $RESULTS_DIR

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $RESULTS_DIR/test.log
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $RESULTS_DIR/test.log
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $RESULTS_DIR/test.log
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a $RESULTS_DIR/test.log
}

# Function to print header
print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}║              PDB Management Operator - Performance Testing        ║${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Pre-flight checks
preflight_check() {
    log "Running pre-flight checks..."

    # Check if operator is running
    if ! kubectl get deployment -n $OPERATOR_NAMESPACE pdb-management-controller-manager &>/dev/null; then
        error "PDB operator not found in namespace $OPERATOR_NAMESPACE"
        exit 1
    fi

    # Check if operator is ready
    READY=$(kubectl get deployment -n $OPERATOR_NAMESPACE pdb-management-controller-manager -o jsonpath='{.status.readyReplicas}')
    if [ "$READY" -lt 1 ]; then
        error "PDB operator is not ready"
        exit 1
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        error "jq is required but not installed"
        exit 1
    fi

    log "Pre-flight checks passed"
}

# Collect baseline metrics
collect_baseline() {
    log "Collecting baseline metrics..."

    # Get operator resource usage
    kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager > $RESULTS_DIR/baseline-resources.txt 2>/dev/null || true

    # Get current metrics with better error handling
    log "Collecting metrics from operator..."
    kubectl port-forward -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager $METRICS_PORT:8443 &
    PF_PID=$!
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Try to collect metrics with retry (using HTTP, not HTTPS)
    for attempt in {1..3}; do
        if curl -s http://localhost:$METRICS_PORT/metrics --connect-timeout 10 > $RESULTS_DIR/baseline-metrics.txt 2>/dev/null; then
            log "Metrics collected successfully"
            break
        else
            warning "Metrics collection attempt $attempt failed, retrying..."
            sleep 2
        fi
    done
    
    # Clean up port-forward
    kill $PF_PID 2>/dev/null || true
    wait $PF_PID 2>/dev/null || true

    log "Baseline collected"
}

# Test 1: Basic Performance Test
basic_performance_test() {
    log "Starting Basic Performance Test..."
    local DEPLOYMENT_COUNT=${1:-100}
    local START_TIME=$(date +%s)

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create deployments
    log "Creating $DEPLOYMENT_COUNT deployments..."
    for i in $(seq 1 $DEPLOYMENT_COUNT); do
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perf-test-$i
  namespace: $TEST_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
    oda.tmforum.org/componentName: "perf-component-$i"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: perf-$i
  template:
    metadata:
      labels:
        app: perf-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
          limits:
            cpu: 20m
            memory: 32Mi
EOF
    done

    # Wait for PDBs to be created
    log "Waiting for PDB creation..."
    EXPECTED_PDBS=$DEPLOYMENT_COUNT
    TIMEOUT=300  # 5 minutes
    ELAPSED=0

    while true; do
        CURRENT_PDBS=$(kubectl get pdb -n $TEST_NAMESPACE --no-headers 2>/dev/null | wc -l)
        if [ $CURRENT_PDBS -eq $EXPECTED_PDBS ]; then
            log "All $EXPECTED_PDBS PDBs created successfully!"
            break
        fi

        if [ $ELAPSED -gt $TIMEOUT ]; then
            error "Timeout waiting for PDBs. Created: $CURRENT_PDBS/$EXPECTED_PDBS"
            break
        fi

        info "PDBs created: $CURRENT_PDBS/$EXPECTED_PDBS"
        sleep 5
        ELAPSED=$((ELAPSED + 5))
    done

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Collect post-test metrics
    log "Collecting post-test metrics..."
    collect_metrics "post-test"

    # Save results
    echo "Basic Performance Test Results:" > $RESULTS_DIR/basic-performance-results.txt
    echo "Deployments: $DEPLOYMENT_COUNT" >> $RESULTS_DIR/basic-performance-results.txt
    echo "Total Duration: $DURATION seconds" >> $RESULTS_DIR/basic-performance-results.txt
    echo "Average time per PDB: $((DURATION / DEPLOYMENT_COUNT)) seconds" >> $RESULTS_DIR/basic-performance-results.txt
    echo "PDBs Created: $CURRENT_PDBS" >> $RESULTS_DIR/basic-performance-results.txt
    echo "Success Rate: $((CURRENT_PDBS * 100 / DEPLOYMENT_COUNT))%" >> $RESULTS_DIR/basic-performance-results.txt

    log "Basic performance test completed"
}

# Test 2: Cache Performance Test
cache_performance_test() {
    log "Starting Cache Performance Test..."
    
    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create policy for cache test
    kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: cache-test-policy
  namespace: $TEST_NAMESPACE
spec:
  availabilityClass: standard
  componentSelector:
    matchLabels:
      cache: test
    namespaces:
    - $TEST_NAMESPACE
  priority: 100
EOF

    # Create many deployments that use the same policy
    log "Creating 50 deployments to test policy cache..."
    for i in {1..50}; do
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-test-$i
  namespace: $TEST_NAMESPACE
  labels:
    cache: test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cache-$i
  template:
    metadata:
      labels:
        app: cache-$i
        cache: test
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
    done

    # Wait for reconciliation
    sleep 30

    # Check cache metrics with better error handling
    log "Collecting cache performance metrics..."
    kubectl port-forward -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager $METRICS_PORT:8443 &
    PF_PID=$!
    sleep 5

    # Try to collect cache metrics with retry (using HTTP, not HTTPS)
    for attempt in {1..3}; do
        if curl -s http://localhost:$METRICS_PORT/metrics --connect-timeout 10 | grep -E "pdb_management_cache_(hits|misses)_total" > $RESULTS_DIR/cache-metrics.txt 2>/dev/null; then
            log "Cache metrics collected successfully"
            break
        else
            warning "Cache metrics collection attempt $attempt failed, retrying..."
            sleep 2
        fi
    done

    # Clean up port-forward
    kill $PF_PID 2>/dev/null || true
    wait $PF_PID 2>/dev/null || true

    log "Cache performance test completed"
}

# Test 3: Advanced Performance Test with Metrics
advanced_performance_test() {
    log "Starting Advanced Performance Test..."
    local TEST_DURATION=${1:-600}  # 10 minutes

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Apply scale test policy
    kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: perf-test-policy
  namespace: $TEST_NAMESPACE
spec:
  availabilityClass: high-availability
  componentSelector:
    matchLabels:
      test: performance
    namespaces:
    - $TEST_NAMESPACE
  priority: 100
EOF

    # Start background load generator
    (
        while true; do
            # Randomly create/update/delete deployments
            ACTION=$((RANDOM % 3))
            DEPLOYMENT_NUM=$((RANDOM % 50 + 1))

            case $ACTION in
                0) # Create
                    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-test-$DEPLOYMENT_NUM
  namespace: $TEST_NAMESPACE
  labels:
    test: performance
spec:
  replicas: $((RANDOM % 5 + 2))
  selector:
    matchLabels:
      app: load-$DEPLOYMENT_NUM
  template:
    metadata:
      labels:
        app: load-$DEPLOYMENT_NUM
        test: performance
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
EOF
                    ;;
                1) # Update
                    kubectl scale deployment load-test-$DEPLOYMENT_NUM -n $TEST_NAMESPACE --replicas=$((RANDOM % 5 + 2)) 2>/dev/null
                    ;;
                2) # Delete
                    kubectl delete deployment load-test-$DEPLOYMENT_NUM -n $TEST_NAMESPACE --ignore-not-found=true 2>/dev/null
                    ;;
            esac

            sleep $((RANDOM % 5 + 1))
        done
    ) &
    LOAD_PID=$!

    # Collect metrics during test
    log "Starting $TEST_DURATION second performance test..."
    START_TIME=$(date +%s)

    for i in $(seq 1 $((TEST_DURATION / 60))); do
        sleep 60
        collect_metrics "Minute $i"
    done

    # Stop load generator
    kill $LOAD_PID 2>/dev/null || true

    # Final metrics
    END_TIME=$(date +%s)
    collect_metrics "Final"

    # Generate report
    echo "=== Advanced Performance Test Report ===" > $RESULTS_DIR/advanced-performance-report.txt
    echo "Test Duration: $((END_TIME - START_TIME)) seconds" >> $RESULTS_DIR/advanced-performance-report.txt
    echo "Namespace: $TEST_NAMESPACE" >> $RESULTS_DIR/advanced-performance-report.txt

    # Count final state
    echo "Final PDB count: $(kubectl get pdb -n $TEST_NAMESPACE --no-headers 2>/dev/null | wc -l)" >> $RESULTS_DIR/advanced-performance-report.txt
    echo "Final Deployment count: $(kubectl get deployment -n $TEST_NAMESPACE --no-headers 2>/dev/null | wc -l)" >> $RESULTS_DIR/advanced-performance-report.txt

    log "Advanced performance test completed"
}

# Test 4: Circuit Breaker Test
circuit_breaker_test() {
    log "Starting Circuit Breaker Test..."
    
    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create a network policy to simulate API server issues
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-api-server
  namespace: $OPERATOR_NAMESPACE
spec:
  podSelector:
    matchLabels:
      control-plane: controller-manager
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: $TEST_NAMESPACE
    ports:
    - protocol: TCP
      port: 443
EOF

    log "Network policy applied. Creating deployments..."

    # Create deployments that should trigger circuit breaker
    for i in {1..20}; do
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: circuit-test-$i
  namespace: $TEST_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: circuit-$i
  template:
    metadata:
      labels:
        app: circuit-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
    done

    # Monitor operator logs for circuit breaker events
    log "Monitoring operator logs for circuit breaker activity..."
    kubectl logs -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager --tail=100 | \
        jq -c 'select(.msg | contains("circuit"))' | \
        jq -r '"\(.ts) \(.msg)"' > $RESULTS_DIR/circuit-breaker-events.txt

    # Cleanup network policy
    kubectl delete networkpolicy block-api-server -n $OPERATOR_NAMESPACE 2>/dev/null || true

    log "Circuit breaker test completed"
}

# Test 5: RBAC Debug Test
rbac_debug_test() {
    log "Starting RBAC Debug Test..."
    
    echo "=== RBAC Debugging Commands ===" > $RESULTS_DIR/rbac-debug-report.txt

    # 1. List all ClusterRoles for pdb-management
    echo -e "\n1. All ClusterRoles for pdb-management:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl get clusterroles | grep pdb-management >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "No pdb-management cluster roles found" >> $RESULTS_DIR/rbac-debug-report.txt

    # 2. Describe the manager ClusterRole to see its permissions
    echo -e "\n2. Manager ClusterRole permissions:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl describe clusterrole pdb-management-manager-role >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "ClusterRole not found" >> $RESULTS_DIR/rbac-debug-report.txt

    # 3. Check ClusterRoleBinding
    echo -e "\n3. ClusterRoleBinding details:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl get clusterrolebinding pdb-management-manager-rolebinding -o yaml >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "ClusterRoleBinding not found" >> $RESULTS_DIR/rbac-debug-report.txt

    # 4. Check the ServiceAccount
    echo -e "\n4. ServiceAccount in canvas namespace:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl get sa -n $OPERATOR_NAMESPACE | grep pdb-management >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "ServiceAccount not found" >> $RESULTS_DIR/rbac-debug-report.txt

    # 5. Test specific permissions for the ServiceAccount
    echo -e "\n5. Testing ServiceAccount permissions:" >> $RESULTS_DIR/rbac-debug-report.txt
    echo "Can list namespaces?" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl auth can-i list namespaces --as=system:serviceaccount:$OPERATOR_NAMESPACE:pdb-management-controller-manager >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "Permission check failed" >> $RESULTS_DIR/rbac-debug-report.txt

    echo "Can list deployments?" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl auth can-i list deployments --all-namespaces --as=system:serviceaccount:$OPERATOR_NAMESPACE:pdb-management-controller-manager >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "Permission check failed" >> $RESULTS_DIR/rbac-debug-report.txt

    echo "Can list availabilitypolicies?" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl auth can-i list availabilitypolicies --all-namespaces --as=system:serviceaccount:$OPERATOR_NAMESPACE:pdb-management-controller-manager >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "Permission check failed" >> $RESULTS_DIR/rbac-debug-report.txt

    # 6. Check what permissions the ServiceAccount actually has
    echo -e "\n6. All permissions for the ServiceAccount:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl auth can-i --list --as=system:serviceaccount:$OPERATOR_NAMESPACE:pdb-management-controller-manager | grep -E "(namespaces|deployments|availabilitypolicies|poddisruptionbudgets)" >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "Permission list failed" >> $RESULTS_DIR/rbac-debug-report.txt

    # 7. Get the current pod logs to see the exact error
    echo -e "\n7. Current pod errors:" >> $RESULTS_DIR/rbac-debug-report.txt
    kubectl logs -n $OPERATOR_NAMESPACE -l control-plane=controller-manager --tail=5 | grep -i "forbidden" >> $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "No forbidden errors found" >> $RESULTS_DIR/rbac-debug-report.txt

    log "RBAC debug test completed"
}

# Function to collect metrics
collect_metrics() {
    local phase=$1
    log "=== Metrics for phase: $phase ==="

    # Operator resource usage
    echo "=== Operator Resource Usage ===" > $RESULTS_DIR/metrics-$phase.txt
    kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager >> $RESULTS_DIR/metrics-$phase.txt 2>/dev/null || true

    # Reconciliation metrics
    kubectl port-forward -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager $METRICS_PORT:8443 &
    PF_PID=$!
    sleep 2

    echo -e "\n=== PDB Management Metrics ===" >> $RESULTS_DIR/metrics-$phase.txt
    curl -s http://localhost:$METRICS_PORT/metrics | grep -E \
        "pdb_management_(reconciliation|cache|operator)" >> $RESULTS_DIR/metrics-$phase.txt 2>/dev/null || true

    echo -e "\n=== Controller Runtime Metrics ===" >> $RESULTS_DIR/metrics-$phase.txt
    curl -s http://localhost:$METRICS_PORT/metrics | grep -E \
        "controller_runtime_(reconcile|workqueue)" >> $RESULTS_DIR/metrics-$phase.txt 2>/dev/null || true

    echo -e "\n=== Go Runtime Metrics ===" >> $RESULTS_DIR/metrics-$phase.txt
    curl -s http://localhost:$METRICS_PORT/metrics | grep -E \
        "go_(goroutines|threads|gc)" >> $RESULTS_DIR/metrics-$phase.txt 2>/dev/null || true

    kill $PF_PID 2>/dev/null || true
}

# Function to show results
show_results() {
    print_header
    log "Performance Test Results Summary"
    
    echo -e "\n${BLUE}Results Directory:${NC} $RESULTS_DIR"
    echo -e "\n${BLUE}Available Reports:${NC}"
    ls -la $RESULTS_DIR/
    
    echo -e "\n${BLUE}Basic Performance Results:${NC}"
    cat $RESULTS_DIR/basic-performance-results.txt 2>/dev/null || echo "No basic performance results"
    
    echo -e "\n${BLUE}Baseline Metrics:${NC}"
    cat $RESULTS_DIR/metrics-baseline.txt 2>/dev/null || echo "No baseline metrics"
    
    echo -e "\n${BLUE}Post-Test Metrics:${NC}"
    cat $RESULTS_DIR/metrics-post-test.txt 2>/dev/null || echo "No post-test metrics"
    
    echo -e "\n${BLUE}Cache Metrics:${NC}"
    cat $RESULTS_DIR/cache-metrics.txt 2>/dev/null || echo "No cache metrics"
    
    echo -e "\n${BLUE}Circuit Breaker Events:${NC}"
    cat $RESULTS_DIR/circuit-breaker-events.txt 2>/dev/null || echo "No circuit breaker events"
    
    echo -e "\n${BLUE}RBAC Debug Report:${NC}"
    cat $RESULTS_DIR/rbac-debug-report.txt 2>/dev/null || echo "No RBAC debug report"
}

# Function to cleanup
cleanup() {
    log "Cleaning up test environment..."
    
    # Kill any background processes
    pkill -f "kubectl port-forward" 2>/dev/null || true
    
    # Wait for operator to finish processing before deleting namespace
    log "Waiting for operator to finish processing deployments..."
    sleep 10
    
    # Delete deployments first to reduce race conditions
    if kubectl get namespace $TEST_NAMESPACE >/dev/null 2>&1; then
        log "Deleting deployments in $TEST_NAMESPACE..."
        kubectl delete deployment --all -n $TEST_NAMESPACE --wait=false 2>/dev/null || true
        
        # Wait a bit more for operator to process deletions
        sleep 5
        
        # Delete test namespace
        log "Deleting namespace $TEST_NAMESPACE..."
        kubectl delete namespace $TEST_NAMESPACE --wait=false 2>/dev/null || true
    else
        log "Namespace $TEST_NAMESPACE already deleted"
    fi
    
    # Delete network policies
    kubectl delete networkpolicy block-api-server -n $OPERATOR_NAMESPACE 2>/dev/null || true
    
    log "Cleanup completed"
}

# Main function
main() {
    print_header
    
    # Parse arguments
    case "${1:-}" in
        --basic)
            preflight_check
            collect_baseline
            basic_performance_test "${2:-100}"
            show_results
            ;;
        --cache)
            preflight_check
            cache_performance_test
            show_results
            ;;
        --advanced)
            preflight_check
            collect_baseline
            advanced_performance_test "${2:-600}"
            show_results
            ;;
        --circuit-breaker)
            preflight_check
            circuit_breaker_test
            show_results
            ;;
        --rbac)
            preflight_check
            rbac_debug_test
            show_results
            ;;
        --all)
            preflight_check
            collect_baseline
            basic_performance_test 100
            cache_performance_test
            advanced_performance_test 300
            circuit_breaker_test
            rbac_debug_test
            show_results
            ;;
        --cleanup)
            cleanup
            ;;
        --results)
            show_results
            ;;
        --help)
            echo "Usage: $0 [OPTION] [PARAMETER]"
            echo ""
            echo "Options:"
            echo "  --basic [count]        Run basic performance test (default: 100 deployments)"
            echo "  --cache                Run cache performance test"
            echo "  --advanced [seconds]   Run advanced performance test (default: 600 seconds)"
            echo "  --circuit-breaker      Run circuit breaker test"
            echo "  --rbac                 Run RBAC debug test"
            echo "  --all                  Run all tests"
            echo "  --cleanup              Clean up test environment"
            echo "  --results              Show test results"
            echo "  --help                 Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --basic 50          Run basic test with 50 deployments"
            echo "  $0 --advanced 300      Run advanced test for 5 minutes"
            echo "  $0 --all               Run all tests"
            ;;
        *)
            echo "Usage: $0 --help for options"
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 