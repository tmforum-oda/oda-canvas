#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DEMO_NAMESPACE="pdb-demo-$(date +%s)"
ACTUAL_DEMO_NAMESPACE=""  # Will be set when namespace is created
OPERATOR_NAMESPACE="canvas"
LOG_FILE="demo-logs-$(date +%Y%m%d-%H%M%S).json"

# Function to get the current leader pod
get_leader_pod() {
    kubectl get lease -n $OPERATOR_NAMESPACE oda.tmforum.org.pdb-management -o jsonpath='{.spec.holderIdentity}' | cut -d'_' -f1
}

# Function to print colored output
print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}║                PDB Management Operator - Demo Suite               ║${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to capture logs
capture_logs() {
    local correlation_id=$1
    local description=$2
    local LEADER_POD=$(get_leader_pod)
    echo "Capturing logs for: $description" >> "$LOG_FILE"
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=50 | \
        jq -c --arg id "$correlation_id" 'select(.correlationID == $id)' >> "$LOG_FILE" 2>/dev/null || true
    echo "---" >> "$LOG_FILE"
}

# Function to analyze logs
analyze_logs() {
    local correlation_id=$1
    local description=$2
    local LEADER_POD=$(get_leader_pod)
    print_info "Analyzing logs for: $description"
    
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=100 | \
        jq -c --arg id "$correlation_id" 'select(.correlationID == $id)' | \
        jq -r '"\(.ts | strftime("%H:%M:%S.%3N")) [\(.level | ascii_upcase)] \(.msg)
  └─ Controller: \(.controller.type // "unknown")
  └─ Resource: \(.resource.namespace // ""):\(.resource.name // "")
  └─ Trace: \(.trace.trace_id // "none")
  └─ Details: \(.details | tostring)"' | \
        while IFS= read -r line; do
            if [[ $line == *"[ERROR]"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"[INFO]"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"Audit"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
}

# Function to show PDB status
show_pdb_status() {
    local deployment_name=$1
    local expected_min_available=$2
    
    print_info "Checking PDB for $deployment_name"
    
    local namespace="${ACTUAL_DEMO_NAMESPACE:-$DEMO_NAMESPACE}"
    
    if kubectl get pdb -n "$namespace" ${deployment_name}-pdb &>/dev/null; then
        local actual_min_available=$(kubectl get pdb -n "$namespace" ${deployment_name}-pdb -o jsonpath='{.spec.minAvailable}')
        if [ "$actual_min_available" = "$expected_min_available" ]; then
            print_success "PDB created with correct minAvailable: $actual_min_available"
        else
            print_warning "PDB created but minAvailable mismatch. Expected: $expected_min_available, Got: $actual_min_available"
        fi
    else
        print_error "PDB not found for $deployment_name"
    fi
}

# Function to wait for reconciliation
wait_for_reconciliation() {
    local deployment_name=$1
    local timeout=30
    local elapsed=0
    
    print_info "Waiting for reconciliation of $deployment_name..."
    
    local namespace="${ACTUAL_DEMO_NAMESPACE:-$DEMO_NAMESPACE}"
    
    while [ $elapsed -lt $timeout ]; do
        if kubectl get pdb -n "$namespace" ${deployment_name}-pdb &>/dev/null; then
            print_success "Reconciliation completed for $deployment_name"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    
    print_error "Timeout waiting for reconciliation of $deployment_name"
    return 1
}

# Function to show live logs
show_live_logs() {
    print_header
    print_step "Live Log Monitoring"
    
    echo -e "${MAGENTA}Press Ctrl+C to stop monitoring${NC}"
    echo ""
    
    local LEADER_POD=$(get_leader_pod)
    print_info "Monitoring logs from leader pod: $LEADER_POD"
    
    # First show recent logs, then follow
    echo -e "${BLUE}Recent logs:${NC}"
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=10 | \
        jq -c 'select(.msg | contains("reconciliation") or contains("PDB") or contains("policy"))' 2>/dev/null | \
        jq -r '"\(.ts // "unknown" | tostring | fromdateiso8601? // . | strftime("%H:%M:%S")? // .) [\(.level | ascii_upcase)] \(.msg)
  └─ \(.resource.namespace // ""):\(.resource.name // "")
  └─ Trace: \(.trace.trace_id // "none")"' 2>/dev/null | \
        while IFS= read -r line; do
            if [[ $line == *"[ERROR]"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"[INFO]"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"Audit"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
    
    echo -e "\n${BLUE}Live monitoring (waiting for new logs):${NC}"
    # Monitor logs in real-time with error handling
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD -f | \
        jq -c 'select(.msg | contains("reconciliation") or contains("PDB") or contains("policy"))' 2>/dev/null | \
        jq -r '"\(.ts // "unknown" | tostring | fromdateiso8601? // . | strftime("%H:%M:%S")? // .) [\(.level | ascii_upcase)] \(.msg)
  └─ \(.resource.namespace // ""):\(.resource.name // "")
  └─ Trace: \(.trace.trace_id // "none")"' 2>/dev/null | \
        while IFS= read -r line; do
            if [[ $line == *"[ERROR]"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"[INFO]"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"Audit"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
}

# Function to show trace analysis
show_trace_analysis() {
    local trace_id=$1
    
    print_header
    print_step "Trace Analysis for: $trace_id"
    
    local LEADER_POD=$(get_leader_pod)
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=1000 | \
        jq -c --arg id "$trace_id" 'select(.trace.trace_id == $id)' 2>/dev/null | \
        jq -r '"\(.ts // "unknown" | tostring | fromdateiso8601? // . | strftime("%H:%M:%S.%3N")? // .) [\(.level | ascii_upcase)] \(.msg)
  └─ Controller: \(.controller.type // "unknown")
  └─ Resource: \(.resource.namespace // ""):\(.resource.name // "")
  └─ Span: \(.trace.span_id // "none")
  └─ Details: \(.details | tostring)"' 2>/dev/null | \
        while IFS= read -r line; do
            if [[ $line == *"[ERROR]"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"[INFO]"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"Audit"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
}

# Function to show audit trail
show_audit_trail() {
    print_header
    print_step "Audit Trail"
    
    local LEADER_POD=$(get_leader_pod)
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=100 | \
        jq -c 'select(.msg == "Audit log")' 2>/dev/null | \
        jq -r '"\(.ts // "unknown" | tostring | fromdateiso8601? // . | strftime("%H:%M:%S")? // .) \(.details.action) \(.details.resource) [\(.details.result)]
  └─ Class: \(.details.availabilityClass // "none")
  └─ Policy: \(.details.policy // "none")
  └─ Duration: \(.details.durationMs // "unknown")ms"' 2>/dev/null | \
        while IFS= read -r line; do
            if [[ $line == *"[SUCCESS]"* ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ $line == *"[FAILURE]"* ]]; then
                echo -e "${RED}$line${NC}"
            else
                echo "$line"
            fi
        done
}

# Function to show performance metrics
show_performance_metrics() {
    print_header
    print_step "Performance Metrics"
    
    local LEADER_POD=$(get_leader_pod)
    echo -e "${BLUE}Recent Reconciliation Durations:${NC}"
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=100 | \
        jq -c 'select(.details.durationMs != null)' 2>/dev/null | \
        jq -r '"\(.resource.name // "unknown"): \(.details.durationMs)ms"' 2>/dev/null | \
        tail -10 | \
        while IFS= read -r line; do
            local duration=$(echo "$line" | cut -d':' -f2 | tr -d 'ms')
            if [ "$duration" -gt 1000 ]; then
                echo -e "${YELLOW}$line${NC}"
            elif [ "$duration" -gt 500 ]; then
                echo -e "${BLUE}$line${NC}"
            else
                echo -e "${GREEN}$line${NC}"
            fi
        done
    
    echo -e "\n${BLUE}Cache Performance:${NC}"
    kubectl logs -n $OPERATOR_NAMESPACE pod/$LEADER_POD --tail=100 | \
        jq -c 'select(.msg | contains("cache"))' 2>/dev/null | \
        jq -r '"\(.ts // "unknown" | tostring | fromdateiso8601? // . | strftime("%H:%M:%S")? // .) \(.msg)"' 2>/dev/null | \
        tail -5
}

# Main demo function
run_demo() {
    print_header
    print_step "Setting up demo environment"
    
    # Create demo namespace
    kubectl create namespace $DEMO_NAMESPACE
    ACTUAL_DEMO_NAMESPACE="$DEMO_NAMESPACE"  # Store the actual namespace name
    print_success "Created namespace: $DEMO_NAMESPACE"
    
    # Initialize log file
    echo "PDB Management Operator Demo Logs - $(date)" > "$LOG_FILE"
    echo "================================================" >> "$LOG_FILE"
    
    # Test Case 1: Basic Annotation-Based PDB
    print_header
    print_step "Test Case 1: Basic Annotation-Based PDB"
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: basic-annotation
  namespace: $DEMO_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
    oda.tmforum.org/componentName: "basic-component"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: basic
  template:
    metadata:
      labels:
        app: basic
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "basic-annotation"
    show_pdb_status "basic-annotation" "50%"
    
    # Test Case 2: Security Component Auto-Upgrade
    print_header
    print_step "Test Case 2: Security Component Auto-Upgrade"
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-component
  namespace: $DEMO_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
    oda.tmforum.org/component-function: "security"
    oda.tmforum.org/componentName: "auth-service"
spec:
  replicas: 5
  selector:
    matchLabels:
      app: auth
  template:
    metadata:
      labels:
        app: auth
    spec:
      containers:
        - name: auth
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "security-component"
    show_pdb_status "security-component" "75%"  # Auto-upgraded from 50% to 75%
    
    # Test Case 3: Mission Critical
    print_header
    print_step "Test Case 3: Mission Critical"
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mission-critical
  namespace: $DEMO_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"
spec:
  replicas: 10
  selector:
    matchLabels:
      app: critical
  template:
    metadata:
      labels:
        app: critical
    spec:
      containers:
        - name: critical
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "mission-critical"
    show_pdb_status "mission-critical" "90%"
    
    # Test Case 4: Policy-Based Configuration
    print_header
    print_step "Test Case 4: Policy-Based Configuration"
    
    # Create policy
    kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: demo-policy
  namespace: $DEMO_NAMESPACE
spec:
  availabilityClass: high-availability
  enforcement: flexible
  minimumClass: standard
  componentSelector:
    matchLabels:
      app: policy-demo
    namespaces:
    - $DEMO_NAMESPACE
  priority: 100
EOF
    
    # Create deployment that matches policy
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: policy-based
  namespace: $DEMO_NAMESPACE
  labels:
    app: policy-demo
  annotations:
    oda.tmforum.org/availability-class: "mission-critical"  # Should be accepted
spec:
  replicas: 5
  selector:
    matchLabels:
      app: policy-demo
  template:
    metadata:
      labels:
        app: policy-demo
    spec:
      containers:
        - name: app
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "policy-based"
    show_pdb_status "policy-based" "90%"  # Mission-critical accepted
    
    # Test Case 5: Custom PDB Configuration
    print_header
    print_step "Test Case 5: Custom PDB Configuration"
    
    # Create custom policy
    kubectl apply -f - <<EOF
apiVersion: availability.oda.tmforum.org/v1alpha1
kind: AvailabilityPolicy
metadata:
  name: custom-policy
  namespace: $DEMO_NAMESPACE
spec:
  availabilityClass: custom
  customPDBConfig:
    minAvailable: 2
    unhealthyPodEvictionPolicy: "IfHealthyBudget"
  componentSelector:
    matchLabels:
      app: custom-demo
    namespaces:
    - $DEMO_NAMESPACE
  priority: 200
EOF
    
    # Create deployment for custom policy
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-pdb
  namespace: $DEMO_NAMESPACE
  labels:
    app: custom-demo
spec:
  replicas: 5
  selector:
    matchLabels:
      app: custom-demo
  template:
    metadata:
      labels:
        app: custom-demo
    spec:
      containers:
        - name: app
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "custom-pdb"
    show_pdb_status "custom-pdb" "2"  # Absolute number
    
    # Test Case 6: Maintenance Window
    print_header
    print_step "Test Case 6: Maintenance Window"
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintenance-demo
  namespace: $DEMO_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
    oda.tmforum.org/maintenance-window: "02:00-04:00 UTC"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maintenance
  template:
    metadata:
      labels:
        app: maintenance
    spec:
      containers:
        - name: app
          image: nginx:alpine
EOF
    
    wait_for_reconciliation "maintenance-demo"
    show_pdb_status "maintenance-demo" "75%"
    
    # Test Case 7: Single Replica (No PDB)
    print_header
    print_step "Test Case 7: Single Replica (No PDB)"
    
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: single-replica
  namespace: $DEMO_NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: single
  template:
    metadata:
      labels:
        app: single
    spec:
      containers:
        - name: app
          image: nginx:alpine
EOF
    
    sleep 5
    
    local namespace="${ACTUAL_DEMO_NAMESPACE:-$DEMO_NAMESPACE}"
    
    if kubectl get pdb -n "$namespace" single-replica-pdb &>/dev/null; then
        print_error "PDB should not exist for single replica deployment"
    else
        print_success "No PDB created for single replica (as expected)"
    fi
    
    # Show comprehensive status
    print_header
    print_step "Demo Summary"
    
    local namespace="${ACTUAL_DEMO_NAMESPACE:-$DEMO_NAMESPACE}"
    
    echo -e "${BLUE}Created PDBs:${NC}"
    kubectl get pdb -n "$namespace" -o wide
    
    echo -e "\n${BLUE}Deployments:${NC}"
    kubectl get deployment -n "$namespace" -o wide
    
    echo -e "\n${BLUE}Policies:${NC}"
    kubectl get availabilitypolicy -n "$namespace" -o wide
    
    # Show audit trail
    show_audit_trail
    
    # Show performance metrics
    show_performance_metrics
    
    print_header
    print_step "Interactive Log Analysis"
    
    echo -e "${MAGENTA}Available commands:${NC}"
    echo "1. Show live logs: ./demo-all-features.sh  --live-logs"
    echo "2. Analyze trace: ./demo-all-features.sh  --trace <trace-id>"
    echo "3. Show audit trail: ./demo-all-features.sh  --audit"
    echo "4. Show performance: ./demo-all-features.sh  --performance"
    echo "5. Cleanup demo: ./demo-all-features.sh  --cleanup"
    
    print_info "Demo completed successfully!"
    print_info "Log file saved to: $LOG_FILE"
}

# Function to cleanup
cleanup() {
    print_header
    print_step "Cleaning up demo environment"
    
    # Use actual namespace if available, otherwise try to find it
    local namespace_to_cleanup=""
    if [ -n "$ACTUAL_DEMO_NAMESPACE" ]; then
        namespace_to_cleanup="$ACTUAL_DEMO_NAMESPACE"
    else
        # Try to find demo namespaces
        namespace_to_cleanup=$(kubectl get namespaces -o jsonpath='{.items[?(@.metadata.name=~"pdb-demo-.*")].metadata.name}' 2>/dev/null | head -1)
        if [ -z "$namespace_to_cleanup" ]; then
            # Fallback: use grep to find demo namespaces
            namespace_to_cleanup=$(kubectl get namespaces -o name | grep "pdb-demo-" | head -1 | sed 's/namespace\///')
            if [ -z "$namespace_to_cleanup" ]; then
                print_warning "No demo namespace found to cleanup"
                return 0
            fi
        fi
    fi
    
    print_info "Cleaning up namespace: $namespace_to_cleanup"
    kubectl delete namespace "$namespace_to_cleanup" --wait=false
    print_success "Demo environment cleaned up"
}

# Main script logic
case "${1:-}" in
    --live-logs)
        show_live_logs
        ;;
    --trace)
        if [ -z "$2" ]; then
            print_error "Usage: $0 --trace <trace-id>"
            exit 1
        fi
        show_trace_analysis "$2"
        ;;
    --audit)
        show_audit_trail
        ;;
    --performance)
        show_performance_metrics
        ;;
    --cleanup)
        cleanup
        ;;
    --help)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (no args)     Run full demo suite"
        echo "  --live-logs   Show live log monitoring"
        echo "  --trace ID    Analyze specific trace"
        echo "  --audit       Show audit trail"
        echo "  --performance Show performance metrics"
        echo "  --cleanup     Clean up demo environment"
        echo "  --help        Show this help"
        ;;
    *)
        run_demo
        ;;
esac 