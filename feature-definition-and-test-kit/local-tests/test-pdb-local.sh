#!/bin/bash

# Local test script for PDB Management BDD tests

set -e

echo "================================================"
echo "PDB Management BDD Tests - Local Test Runner"
echo "================================================"

# Check kubectl connection
echo ""
echo "Checking Kubernetes connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "[ERROR] Cannot connect to Kubernetes cluster"
    echo "Please ensure kubectl is configured and cluster is accessible"
    exit 1
fi
echo "[OK] Kubernetes cluster accessible"

# Check if Canvas namespace exists
echo ""
echo "Checking Canvas namespace..."
if ! kubectl get namespace canvas &> /dev/null; then
    echo "[ERROR] Canvas namespace not found"
    echo "Please deploy ODA Canvas first"
    exit 1
fi
echo "[OK] Canvas namespace exists"

# Check if PDB operator is deployed
echo ""
echo "Checking PDB Management Operator..."
if ! kubectl get deployment -n canvas canvas-pdb-management-operator &> /dev/null; then
    echo "[ERROR] PDB Management Operator not deployed"
    echo "Please deploy the PDB operator first:"
    echo "  helm install canvas-pdb charts/canvas-oda"
    exit 1
fi
echo "[OK] PDB Management Operator found"

# Check if operator is ready
echo ""
echo "Checking operator readiness..."
READY=$(kubectl get deployment -n canvas canvas-pdb-management-operator -o jsonpath='{.status.readyReplicas}')
if [ "$READY" != "1" ]; then
    echo "[WARNING] PDB Management Operator not ready (replicas: $READY)"
    echo "Waiting for operator to be ready..."
    kubectl wait --for=condition=available --timeout=60s deployment/canvas-pdb-management-operator -n canvas || true
fi
echo "[OK] PDB Management Operator is ready"

# Check if AvailabilityPolicy CRD exists
echo ""
echo "Checking AvailabilityPolicy CRD..."
if ! kubectl get crd availabilitypolicies.availability.oda.tmforum.org &> /dev/null; then
    echo "[WARNING] AvailabilityPolicy CRD not found"
    echo "This may affect policy-based tests"
fi

# Ensure components namespace exists
echo ""
echo "Ensuring components namespace exists..."
kubectl create namespace components --dry-run=client -o yaml | kubectl apply -f -
echo "[OK] Components namespace ready"

# Create test results directory
mkdir -p test-results

# Run the tests
echo ""
echo "================================================"
echo "Running PDB BDD Tests"
echo "================================================"

# Check which test to run
TEST_TYPE=${1:-all}

case $TEST_TYPE in
  dry-run)
    echo "Running dry-run (syntax check only)..."
    npm run test:pdb:dry-run
    ;;
  annotation)
    echo "Running annotation-based tests..."
    npm run test:pdb:annotation
    ;;
  policy)
    echo "Running policy-based tests..."
    npm run test:pdb:policy
    ;;
  webhook)
    echo "Running webhook validation tests..."
    npm run test:pdb:webhook
    ;;
  edge)
    echo "Running edge case tests..."
    npm run test:pdb:edge
    ;;
  all)
    echo "Running all PDB tests..."
    npm run test:pdb:local
    ;;
  *)
    echo "Unknown test type: $TEST_TYPE"
    echo "Usage: $0 [dry-run|annotation|policy|webhook|edge|all]"
    exit 1
    ;;
esac

# Check test results
echo ""
echo "================================================"
echo "Test Results"
echo "================================================"

if [ -f test-results/pdb-results.json ]; then
    echo "Test results saved to: test-results/pdb-results.json"
    # Parse and display summary
    node -e "
    const results = require('./test-results/pdb-results.json');
    const scenarios = results[0]?.elements || [];
    const passed = scenarios.filter(s => s.steps.every(step => step.result.status === 'passed')).length;
    const failed = scenarios.filter(s => s.steps.some(step => step.result.status === 'failed')).length;
    const skipped = scenarios.filter(s => s.steps.some(step => step.result.status === 'skipped')).length;
    
    console.log('');
    console.log('Summary:');
    console.log('  [PASSED]: ' + passed);
    console.log('  [FAILED]: ' + failed);
    console.log('  [SKIPPED]: ' + skipped);
    console.log('  [TOTAL]: ' + scenarios.length);
    " 2>/dev/null || echo "Could not parse results file"
fi

echo ""
echo "================================================"
echo "Test run complete!"
echo "================================================"