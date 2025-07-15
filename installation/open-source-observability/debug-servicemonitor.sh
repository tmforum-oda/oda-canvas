#!/bin/bash

echo "=== ODA Canvas ServiceMonitor Debugging ==="
echo ""

echo "1. Checking if ServiceMonitor exists in components namespace:"
kubectl get servicemonitors -n components
echo ""

echo "2. Checking ServiceMonitor details:"
kubectl describe servicemonitor r1-productcatalogmanagement-metrics -n components 2>/dev/null || echo "ServiceMonitor not found"
echo ""

echo "3. Checking if target service exists:"
kubectl get svc -n components -l name=r1-productcatalogmanagement-sm
echo ""

echo "4. Checking all services in components namespace:"
kubectl get svc -n components --show-labels
echo ""


echo "5. Checking namespace labels:"
kubectl get namespace components --show-labels
echo ""

echo "6. Checking Prometheus instance configuration:"
kubectl get prometheus -n monitoring -o yaml | grep -A 10 -B 10 serviceMonitor
echo ""

echo "7. Checking if Prometheus can access components namespace:"
kubectl auth can-i get servicemonitors --namespace=components --as=system:serviceaccount:monitoring:monitoring-kube-prometheus-prometheus
if [ $? -ne 0 ]; then
  echo "❌ Prometheus cannot access components namespace - RBAC issue detected!"
  echo "To fix this, ensure your prometheus-values.yaml has:"
  echo "  rbac: create: true"
  echo "  prometheus.rbac.create: true"
  echo "  prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues: false"
  echo ""
  echo "Then run: helm upgrade monitoring prometheus-community/kube-prometheus-stack -n monitoring -f ./prometheus-values-fixed.yaml"
else
  echo "✅ Prometheus can access components namespace"
fi
echo ""

echo "8. Checking Prometheus operator logs (last 50 lines):"
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus-operator --tail=50
echo ""

echo "9. Checking Prometheus server logs (last 20 lines):"
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus --tail=20
echo ""

echo "10. Checking current Prometheus targets:"
echo "Run: kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring"
echo "Then visit: http://localhost:9090/targets"
echo ""

echo "11. Manual ServiceMonitor validation:"
echo "Expected ServiceMonitor selector: name=r1-productcatalogmanagement-sm"
echo "Checking if service has this label:"
kubectl get svc -n components -o jsonpath='{.items[*].metadata.labels.name}' | grep r1-productcatalogmanagement-sm || echo "No service found with required label"
echo ""

echo "12. Force Prometheus reload:"
echo "If needed, run: kubectl delete pod -n monitoring -l app.kubernetes.io/name=prometheus"
echo ""

echo "13. Testing metrics endpoint for Content-Type issues:"
echo "Checking if metrics endpoint returns proper Prometheus format..."
SERVICE_NAME="r1-productcatalogmanagement-sm"
METRICS_PATH="/r1-productcatalogmanagement/metrics"
PORT="4000"

# Test if service exists
kubectl get svc $SERVICE_NAME -n components >/dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Service $SERVICE_NAME exists"
  
  # Test metrics endpoint
  echo "Testing metrics endpoint (this may take a few seconds)..."
  kubectl port-forward svc/$SERVICE_NAME $PORT:$PORT -n components &
  PF_PID=$!
  sleep 3
  
  # Test the endpoint
  RESPONSE=$(curl -s -H "Accept: text/plain" http://localhost:$PORT$METRICS_PATH 2>/dev/null)
  CONTENT_TYPE=$(curl -s -I -H "Accept: text/plain" http://localhost:$PORT$METRICS_PATH 2>/dev/null | grep -i content-type)
  
  if echo "$RESPONSE" | grep -q "# HELP\|# TYPE"; then
    echo "✅ Metrics endpoint returns valid Prometheus format"
  else
    echo "❌ Metrics endpoint does not return valid Prometheus format"
    echo "Content-Type: $CONTENT_TYPE"
    echo "Response preview:"
    echo "$RESPONSE" | head -5
    echo ""
    echo "Try these alternative paths:"
    echo "  /metrics"
    echo "  /actuator/prometheus"
    echo "  /api/metrics"
  fi
  
  # Clean up port-forward
  kill $PF_PID 2>/dev/null
else
  echo "❌ Service $SERVICE_NAME not found"
fi
echo ""

echo "=== End of Debug Output ==="