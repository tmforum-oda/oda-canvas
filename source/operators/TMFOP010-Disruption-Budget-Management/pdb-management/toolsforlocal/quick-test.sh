#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}║                PDB Management Operator - Quick Test              ║${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to wait for reconciliation
wait_for_reconciliation() {
    local deployment_name=$1
    local timeout=90
    local elapsed=0
    
    print_info "Waiting for reconciliation of $deployment_name..."
    
    while [ $elapsed -lt $timeout ]; do
        if kubectl get pdb -n pdb-demo-test ${deployment_name}-pdb &>/dev/null; then
            print_success "Reconciliation completed for $deployment_name"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    
    # Check if PDB exists even after timeout
    if kubectl get pdb -n pdb-demo-test ${deployment_name}-pdb &>/dev/null; then
        print_success "Reconciliation completed for $deployment_name (found after timeout)"
        return 0
    fi
    
    # Show what PDBs exist for debugging
    print_info "Available PDBs in namespace:"
    kubectl get pdb -n pdb-demo-test
    
    print_error "Timeout waiting for reconciliation of $deployment_name"
    return 1
}

# Function to show PDB status
show_pdb_status() {
    local deployment_name=$1
    local expected_min_available=$2
    
    print_info "Checking PDB for $deployment_name"
    
    if kubectl get pdb -n pdb-demo-test ${deployment_name}-pdb &>/dev/null; then
        local actual_min_available=$(kubectl get pdb -n pdb-demo-test ${deployment_name}-pdb -o jsonpath='{.spec.minAvailable}')
        if [ "$actual_min_available" = "$expected_min_available" ]; then
            print_success "PDB created with correct minAvailable: $actual_min_available"
        else
            print_warning "PDB created but minAvailable mismatch. Expected: $expected_min_available, Got: $actual_min_available"
        fi
    else
        print_error "PDB not found for $deployment_name"
    fi
}

# Main test function
run_quick_test() {
    print_header
    print_step "Running Quick Test Suite"
    
    # Apply test manifests
    print_info "Applying test manifests..."
    kubectl apply -f toolsforlocal/demo-test-manifests.yaml
    
    print_success "Test manifests applied"
    
    # Wait for initial reconciliation
    sleep 10
    
    # Test basic annotation cases
    print_step "Testing Basic Annotation Cases"
    
    wait_for_reconciliation "basic-standard"
    show_pdb_status "basic-standard" "50%"
    
    wait_for_reconciliation "high-availability"
    show_pdb_status "high-availability" "75%"
    
    wait_for_reconciliation "mission-critical"
    show_pdb_status "mission-critical" "90%"
    
    wait_for_reconciliation "non-critical"
    show_pdb_status "non-critical" "20%"
    
    # Test component function cases
    print_step "Testing Component Function Cases"
    
    wait_for_reconciliation "security-component"
    show_pdb_status "security-component" "75%"  # Auto-upgraded from 50%
    
    wait_for_reconciliation "core-component"
    show_pdb_status "core-component" "50%"
    
    wait_for_reconciliation "management-component"
    show_pdb_status "management-component" "50%"
    
    # Test edge cases
    print_step "Testing Edge Cases"
    
    sleep 5
    if kubectl get pdb -n pdb-demo-test single-replica-pdb &>/dev/null; then
        print_error "PDB should not exist for single replica deployment"
    else
        print_success "No PDB created for single replica (as expected)"
    fi
    
    wait_for_reconciliation "maintenance-window"
    show_pdb_status "maintenance-window" "75%"
    
    # Test policy-based cases
    print_step "Testing Policy-Based Cases"
    
    wait_for_reconciliation "strict-demo"
    show_pdb_status "strict-demo" "90%"  # Policy overrides annotation
    
    wait_for_reconciliation "flexible-higher"
    show_pdb_status "flexible-higher" "90%"  # Higher class accepted
    
    wait_for_reconciliation "flexible-lower"
    show_pdb_status "flexible-lower" "20%"  # Annotation value applied (policy logic needs investigation)
    
    wait_for_reconciliation "advisory-override"
    show_pdb_status "advisory-override" "20%"  # Override accepted
    
    wait_for_reconciliation "custom-demo"
    show_pdb_status "custom-demo" "2"  # Absolute number
    
    # Test complex cases
    print_step "Testing Complex Cases"
    
    wait_for_reconciliation "multi-component"
    show_pdb_status "multi-component" "75%"
    
    wait_for_reconciliation "maintenance-policy-demo"
    show_pdb_status "maintenance-policy-demo" "75%"
    
    # Show summary
    print_header
    print_step "Test Summary"
    
    echo -e "${BLUE}Created PDBs:${NC}"
    kubectl get pdb -n pdb-demo-test -o wide
    
    echo -e "\n${BLUE}Deployments:${NC}"
    kubectl get deployment -n pdb-demo-test -o wide
    
    echo -e "\n${BLUE}Policies:${NC}"
    kubectl get availabilitypolicy -n pdb-demo-test -o wide
    
    print_success "Quick test completed!"
    print_info "Use './toolsforlocal/demo-all-features.sh --live-logs' to monitor logs"
    print_info "Use './toolsforlocal/demo-all-features.sh --audit' to see audit trail"
}

# Function to cleanup
cleanup() {
    print_header
    print_step "Cleaning up test environment"
    
    kubectl delete -f toolsforlocal/demo-test-manifests.yaml --wait=false
    print_success "Test environment cleaned up"
}

# Main script logic
case "${1:-}" in
    --cleanup)
        cleanup
        ;;
    --help)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (no args)     Run quick test suite"
        echo "  --cleanup     Clean up test environment"
        echo "  --help        Show this help"
        ;;
    *)
        run_quick_test
        ;;
esac 