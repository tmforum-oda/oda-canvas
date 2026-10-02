#!/bin/bash

# Debug script to monitor PDB events and operator behavior
# Useful for troubleshooting PDB recreation issues

set -e

NAMESPACE=${NAMESPACE:-"default"}
OPERATOR_NAMESPACE=${OPERATOR_NAMESPACE:-"pdb-management-system"}

echo "🔍 PDB Management Operator Debug Information"
echo "============================================="

echo "📊 Operator Status:"
kubectl get pods -n $OPERATOR_NAMESPACE -l app.kubernetes.io/name=pdb-management-operator

echo ""
echo "📋 Current PDBs:"
kubectl get pdb -n $NAMESPACE -o wide

echo ""
echo "📋 Current Deployments with Availability Annotations:"
kubectl get deployments -n $NAMESPACE -o custom-columns=NAME:.metadata.name,REPLICAS:.spec.replicas,AVAILABILITY:.metadata.annotations.'oda\.tmforum\.org/availability-class' | grep -v "<none>"

echo ""
echo "🔍 Recent Operator Logs (last 50 lines):"
echo "----------------------------------------"
kubectl logs -n $OPERATOR_NAMESPACE -l app.kubernetes.io/name=pdb-management-operator --tail=50 | grep -E "(PDB|reconcil|error|warning)" || echo "No relevant logs found"

echo ""
echo "📋 Recent Events in $NAMESPACE:"
echo "------------------------------"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

echo ""
echo "🔍 PDB Controller Configuration:"
echo "-------------------------------"
kubectl get configmap -n $OPERATOR_NAMESPACE -o yaml | grep -A 10 -B 10 -i "enablepdb" || echo "No PDB configuration found"

echo ""
echo "📊 Operator Metrics (if available):"
echo "-----------------------------------"
kubectl get --raw /metrics 2>/dev/null | grep "pdb_management" | head -10 || echo "Metrics not available"

echo ""
echo "🔍 Deployment Finalizers:"
echo "------------------------"
kubectl get deployments -n $NAMESPACE -o custom-columns=NAME:.metadata.name,FINALIZERS:.metadata.finalizers | grep -v "FINALIZERS"

echo ""
echo "💡 Debugging Tips:"
echo "=================="
echo "1. Check if PDB creation is being triggered:"
echo "   kubectl logs -n $OPERATOR_NAMESPACE -l app.kubernetes.io/name=pdb-management-operator -f | grep -i pdb"
echo ""
echo "2. Force deployment reconciliation:"
echo "   kubectl annotate deployment <deployment-name> reconcile=\$(date +%s) --overwrite"
echo ""
echo "3. Check for conflicting PDB controllers:"
echo "   kubectl get deployments -n $OPERATOR_NAMESPACE -o yaml | grep -i pdb"
echo ""
echo "4. Monitor real-time events:"
echo "   kubectl get events -n $NAMESPACE --watch"
echo ""
echo "5. Test specific deployment:"
echo "   ./test-pdb-recreation.sh" 