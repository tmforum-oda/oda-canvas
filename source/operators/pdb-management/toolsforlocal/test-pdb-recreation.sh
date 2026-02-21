#!/bin/bash

# Test script to verify PDB recreation after manual deletion
# This script tests the fix for the bug where deleted PDBs weren't being recreated

set -e

NAMESPACE=${NAMESPACE:-"default"}
DEPLOYMENT_NAME="test-pdb-recreation"
PDB_NAME="${DEPLOYMENT_NAME}-pdb"

echo "🧪 Testing PDB Recreation After Deletion"
echo "========================================="

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up test resources..."
    kubectl delete deployment $DEPLOYMENT_NAME -n $NAMESPACE --ignore-not-found=true
    kubectl delete pdb $PDB_NAME -n $NAMESPACE --ignore-not-found=true
    echo "✅ Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Create test deployment with availability class
echo "📦 Creating test deployment with availability annotations..."
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $DEPLOYMENT_NAME
  namespace: $NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "high-availability"
    oda.tmforum.org/component-function: "core"
    oda.tmforum.org/componentName: "test-component"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: $DEPLOYMENT_NAME
  template:
    metadata:
      labels:
        app: $DEPLOYMENT_NAME
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
EOF

echo "⏳ Waiting for initial PDB creation..."
sleep 5

# Check if PDB was created
echo "🔍 Checking if PDB was created..."
if kubectl get pdb $PDB_NAME -n $NAMESPACE > /dev/null 2>&1; then
    echo "✅ Initial PDB created successfully"
    kubectl get pdb $PDB_NAME -n $NAMESPACE -o yaml | grep -E "(minAvailable|maxUnavailable):"
else
    echo "❌ Initial PDB creation failed"
    echo "🔍 Checking operator logs..."
    kubectl logs -l app.kubernetes.io/name=pdb-management-operator -n pdb-management-system --tail=20
    exit 1
fi

# Wait for operator to be ready
echo "⏳ Waiting for operator to stabilize..."
sleep 3

# Delete the PDB manually to trigger the bug scenario
echo "🗑️  Manually deleting PDB to test recreation..."
kubectl delete pdb $PDB_NAME -n $NAMESPACE

echo "⏳ Waiting for PDB recreation (should happen within 30 seconds)..."

# Monitor PDB recreation with timeout
TIMEOUT=60
ELAPSED=0
RECREATED=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    if kubectl get pdb $PDB_NAME -n $NAMESPACE > /dev/null 2>&1; then
        echo "✅ PDB recreated successfully after ${ELAPSED} seconds!"
        kubectl get pdb $PDB_NAME -n $NAMESPACE -o yaml | grep -E "(minAvailable|maxUnavailable):"
        RECREATED=true
        break
    fi
    
    echo "⏳ Still waiting... (${ELAPSED}s elapsed)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ "$RECREATED" = false ]; then
    echo "❌ PDB was NOT recreated within ${TIMEOUT} seconds!"
    echo "🔍 This indicates the bug is still present"
    
    echo "🔍 Checking operator logs for errors..."
    kubectl logs -l app.kubernetes.io/name=pdb-management-operator -n pdb-management-system --tail=30
    
    echo "🔍 Checking deployment events..."
    kubectl describe deployment $DEPLOYMENT_NAME -n $NAMESPACE | tail -20
    
    exit 1
fi

# Test multiple deletions to ensure consistency
echo "🔄 Testing multiple PDB deletions..."
for i in {1..3}; do
    echo "   🗑️  Deletion test $i/3..."
    kubectl delete pdb $PDB_NAME -n $NAMESPACE
    
    # Wait for recreation
    sleep 15
    
    if kubectl get pdb $PDB_NAME -n $NAMESPACE > /dev/null 2>&1; then
        echo "   ✅ Recreation test $i/3 passed"
    else
        echo "   ❌ Recreation test $i/3 failed"
        exit 1
    fi
done

echo ""
echo "🎉 All tests passed! PDB recreation is working correctly."
echo "✅ Bug fix verified successfully"

# Show final state
echo ""
echo "📊 Final state:"
echo "   Deployment: $(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.status.readyReplicas}/{.spec.replicas}')"
echo "   PDB: $(kubectl get pdb $PDB_NAME -n $NAMESPACE -o jsonpath='{.spec.minAvailable}')"
echo "   PDB Labels: $(kubectl get pdb $PDB_NAME -n $NAMESPACE -o jsonpath='{.metadata.labels}')" 