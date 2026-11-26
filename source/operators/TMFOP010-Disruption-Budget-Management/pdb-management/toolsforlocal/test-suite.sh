#!/bin/bash
set -e

# Configuration
OPERATOR_NAMESPACE="pdb-management-system"
TEST_NAMESPACE="pdb-stress-test"
RESULTS_DIR="test-results-$(date +%Y%m%d-%H%M%S)"
PROMETHEUS_PORT=9090
METRICS_PORT=8080

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

    log "Pre-flight checks passed"
}

# Collect baseline metrics
collect_baseline() {
    log "Collecting baseline metrics..."

    # Get operator resource usage
    kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager > $RESULTS_DIR/baseline-resources.txt

    # Get current metrics
    kubectl port-forward -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager $METRICS_PORT:8080 &
    PF_PID=$!
    sleep 3

    curl -s http://localhost:$METRICS_PORT/metrics > $RESULTS_DIR/baseline-metrics.txt
    kill $PF_PID 2>/dev/null || true

    log "Baseline collected"
}

# Test 1: Scale Test
scale_test() {
    log "Starting Scale Test..."
    local DEPLOYMENT_COUNT=200
    local BATCH_SIZE=50

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create policy for scale test
    kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: scale-test-policy
  namespace: $TEST_NAMESPACE
spec:
  availabilityClass: standard
  componentSelector:
    matchLabels:
      test: scale
    namespaces:
    - $TEST_NAMESPACE
  priority: 100
EOF

    START_TIME=$(date +%s%N)

    # Create deployments in batches
    for batch in $(seq 1 $((DEPLOYMENT_COUNT/BATCH_SIZE))); do
        log "Creating batch $batch..."
        for i in $(seq $((($batch-1)*BATCH_SIZE+1)) $(($batch*BATCH_SIZE))); do
            kubectl apply -f - <<EOF &
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scale-test-$i
  namespace: $TEST_NAMESPACE
  labels:
    test: scale
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scale-$i
  template:
    metadata:
      labels:
        app: scale-$i
        test: scale
    spec:
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
EOF
        done
        wait
        sleep 2
    done

    # Wait for all PDBs
    log "Waiting for PDB creation..."
    TIMEOUT=300
    ELAPSED=0
    while [ $(kubectl get pdb -n $TEST_NAMESPACE --no-headers 2>/dev/null | wc -l) -lt $DEPLOYMENT_COUNT ]; do
        if [ $ELAPSED -gt $TIMEOUT ]; then
            error "Timeout waiting for PDBs"
            break
        fi
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        echo -n "."
    done
    echo

    END_TIME=$(date +%s%N)
    DURATION=$(( ($END_TIME - $START_TIME) / 1000000000 ))

    # Collect results
    log "Scale Test Results:"
    echo "Deployments: $DEPLOYMENT_COUNT" > $RESULTS_DIR/scale-test-results.txt
    echo "Duration: $DURATION seconds" >> $RESULTS_DIR/scale-test-results.txt
    echo "Average per deployment: $(( $DURATION / $DEPLOYMENT_COUNT )) seconds" >> $RESULTS_DIR/scale-test-results.txt

    kubectl get pdb -n $TEST_NAMESPACE --no-headers | wc -l >> $RESULTS_DIR/scale-test-results.txt

    # Collect metrics
    kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager >> $RESULTS_DIR/scale-test-resources.txt

    # Cleanup
    kubectl delete namespace $TEST_NAMESPACE --wait=false
    sleep 10
}

# Test 2: Churn Test
churn_test() {
    log "Starting Churn Test..."
    local DURATION=300  # 5 minutes
    local DEPLOYMENTS=50

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create initial deployments
    for i in $(seq 1 $DEPLOYMENTS); do
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-test-$i
  namespace: $TEST_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: churn-$i
  template:
    metadata:
      labels:
        app: churn-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
    done

    # Start churn process
    START_TIME=$(date +%s)
    OPERATIONS=0

    (
        while [ $(($(date +%s) - START_TIME)) -lt $DURATION ]; do
            # Random operation
            OP=$((RANDOM % 4))
            DEP=$((RANDOM % DEPLOYMENTS + 1))

            case $OP in
                0) # Scale up
                    kubectl scale deployment churn-test-$DEP -n $TEST_NAMESPACE --replicas=$((RANDOM % 5 + 2)) 2>/dev/null
                    ;;
                1) # Scale down
                    kubectl scale deployment churn-test-$DEP -n $TEST_NAMESPACE --replicas=1 2>/dev/null
                    ;;
                2) # Update annotation
                    CLASS=$([[ $((RANDOM % 2)) -eq 0 ]] && echo "high-availability" || echo "standard")
                    kubectl annotate deployment churn-test-$DEP -n $TEST_NAMESPACE \
                        oda.tmforum.org/availability-class=$CLASS --overwrite 2>/dev/null
                    ;;
                3) # Delete and recreate
                    kubectl delete deployment churn-test-$DEP -n $TEST_NAMESPACE --ignore-not-found=true 2>/dev/null
                    sleep 1
                    kubectl apply -f - <<EOF 2>/dev/null
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-test-$DEP
  namespace: $TEST_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: churn-$DEP
  template:
    metadata:
      labels:
        app: churn-$DEP
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
                    ;;
            esac

            OPERATIONS=$((OPERATIONS + 1))
            sleep 0.5
        done

        echo $OPERATIONS > $RESULTS_DIR/churn-operations.txt
    ) &
    CHURN_PID=$!

    # Monitor during churn
    log "Monitoring during churn test..."
    for i in $(seq 1 5); do
        sleep 60
        log "Minute $i - PDBs: $(kubectl get pdb -n $TEST_NAMESPACE --no-headers | wc -l)"
        kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager >> $RESULTS_DIR/churn-test-resources.txt
    done

    wait $CHURN_PID
    OPERATIONS=$(cat $RESULTS_DIR/churn-operations.txt)

    log "Churn Test Results:"
    echo "Duration: $DURATION seconds" > $RESULTS_DIR/churn-test-results.txt
    echo "Operations: $OPERATIONS" >> $RESULTS_DIR/churn-test-results.txt
    echo "Operations/second: $(( $OPERATIONS / $DURATION ))" >> $RESULTS_DIR/churn-test-results.txt

    # Check for errors
    ERROR_COUNT=$(kubectl logs -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager --since=5m | grep -i error | wc -l)
    echo "Errors during test: $ERROR_COUNT" >> $RESULTS_DIR/churn-test-results.txt

    # Cleanup
    kubectl delete namespace $TEST_NAMESPACE --wait=false
    sleep 10
}

# Test 3: Policy Complexity Test
policy_test() {
    log "Starting Policy Complexity Test..."

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Create multiple overlapping policies
    for i in {1..10}; do
        kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: policy-test-$i
  namespace: $TEST_NAMESPACE
spec:
  availabilityClass: $([[ $((RANDOM % 2)) -eq 0 ]] && echo "standard" || echo "high-availability")
  componentSelector:
    matchLabels:
      tier: $([[ $((i % 3)) -eq 0 ]] && echo "frontend" || echo "backend")
    matchExpressions:
    - key: priority
      operator: In
      values: ["high", "medium"]
    componentFunctions:
    - $([[ $((i % 2)) -eq 0 ]] && echo "core" || echo "security")
    namespaces:
    - $TEST_NAMESPACE
  priority: $((i * 10))
  maintenanceWindows:
  - start: "0$i:00"
    end: "0$i:30"
    timezone: "UTC"
    daysOfWeek: [0, 6]
EOF
    done

    # Create deployments that match multiple policies
    START_TIME=$(date +%s%N)

    for i in {1..100}; do
        kubectl apply -f - <<EOF &
apiVersion: apps/v1
kind: Deployment
metadata:
  name: policy-test-$i
  namespace: $TEST_NAMESPACE
  labels:
    tier: $([[ $((i % 2)) -eq 0 ]] && echo "frontend" || echo "backend")
    priority: $([[ $((i % 3)) -eq 0 ]] && echo "high" || echo "medium")
  annotations:
    oda.tmforum.org/component-function: $([[ $((i % 3)) -eq 0 ]] && echo "security" || echo "core")
spec:
  replicas: 2
  selector:
    matchLabels:
      app: policy-$i
  template:
    metadata:
      labels:
        app: policy-$i
        tier: $([[ $((i % 2)) -eq 0 ]] && echo "frontend" || echo "backend")
        priority: $([[ $((i % 3)) -eq 0 ]] && echo "high" || echo "medium")
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
    done
    wait

    # Wait for policy evaluation
    sleep 30

    END_TIME=$(date +%s%N)
    DURATION=$(( ($END_TIME - $START_TIME) / 1000000000 ))

    log "Policy Test Results:"
    echo "Policies: 10" > $RESULTS_DIR/policy-test-results.txt
    echo "Deployments: 100" >> $RESULTS_DIR/policy-test-results.txt
    echo "Duration: $DURATION seconds" >> $RESULTS_DIR/policy-test-results.txt

    # Check policy status
    kubectl get availabilitypolicy -n $TEST_NAMESPACE -o wide >> $RESULTS_DIR/policy-test-results.txt

    # Cleanup
    kubectl delete namespace $TEST_NAMESPACE --wait=false
    sleep 10
}

# Test 4: Memory Leak Test
memory_test() {
    log "Starting Memory Leak Test..."
    local DURATION=600  # 10 minutes

    kubectl create namespace $TEST_NAMESPACE 2>/dev/null || true

    # Record initial memory
    INITIAL_MEMORY=$(kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager --no-headers | awk '{print $3}' | sed 's/Mi//')
    log "Initial memory: ${INITIAL_MEMORY}Mi"

    # Create and delete deployments continuously
    START_TIME=$(date +%s)
    CYCLE=0

    while [ $(($(date +%s) - START_TIME)) -lt $DURATION ]; do
        CYCLE=$((CYCLE + 1))

        # Create 20 deployments
        for i in {1..20}; do
            kubectl apply -f - <<EOF &
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-test-$i
  namespace: $TEST_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: memory-$i
  template:
    metadata:
      labels:
        app: memory-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
        done
        wait

        sleep 10

        # Delete all deployments
        kubectl delete deployment --all -n $TEST_NAMESPACE --wait=false

        sleep 10

        # Record memory every 5 cycles
        if [ $((CYCLE % 5)) -eq 0 ]; then
            CURRENT_MEMORY=$(kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager --no-headers | awk '{print $3}' | sed 's/Mi//')
            log "Cycle $CYCLE - Memory: ${CURRENT_MEMORY}Mi"
            echo "Cycle $CYCLE: ${CURRENT_MEMORY}Mi" >> $RESULTS_DIR/memory-test-results.txt
        fi
    done

    # Final memory check
    sleep 30
    FINAL_MEMORY=$(kubectl top pod -n $OPERATOR_NAMESPACE -l control-plane=controller-manager --no-headers | awk '{print $3}' | sed 's/Mi//')

    log "Memory Test Results:"
    echo "Initial Memory: ${INITIAL_MEMORY}Mi" >> $RESULTS_DIR/memory-test-results.txt
    echo "Final Memory: ${FINAL_MEMORY}Mi" >> $RESULTS_DIR/memory-test-results.txt
    echo "Memory Growth: $((FINAL_MEMORY - INITIAL_MEMORY))Mi" >> $RESULTS_DIR/memory-test-results.txt

    # Cleanup
    kubectl delete namespace $TEST_NAMESPACE --wait=false
}

# Generate final report
generate_report() {
    log "Generating test report..."

    cat > $RESULTS_DIR/test-report.md <<EOF
        # PDB Operator Stress Test Report
        Generated: $(date)

        ## Test Summary

        ### Scale Test
        $(cat $RESULTS_DIR/scale-test-results.txt 2>/dev/null || echo "Not run")

        ### Churn Test
        $(cat $RESULTS_DIR/churn-test-results.txt 2>/dev/null || echo "Not run")

        ### Policy Test
        $(cat $RESULTS_DIR/policy-test-results.txt 2>/dev/null || echo "Not run")

        ### Memory Test
        $(cat $RESULTS_DIR/memory-test-results.txt 2>/dev/null || echo "Not run")

        ## Operator Logs Summary
        Errors: $(kubectl logs -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager --tail=10000 | grep -i error | wc -l)
        Warnings: $(kubectl logs -n $OPERATOR_NAMESPACE deployment/pdb-management-controller-manager --tail=10000 | grep -i warn | wc -l)

        ## Recommendations
        - Review any memory growth patterns
        - Check error logs for repeated issues
        - Verify cache hit rates are optimal
        - Ensure circuit breaker is functioning correctly
EOF

    log "Report generated at: $RESULTS_DIR/test-report.md"
}

# Main execution
main() {
    log "Starting PDB Operator Comprehensive Test Suite"

    preflight_check
    collect_baseline

    # Run tests
    scale_test
    churn_test
    policy_test
    memory_test

    # Generate report
    generate_report

    log "All tests completed. Results in: $RESULTS_DIR"
}

# Run main
main