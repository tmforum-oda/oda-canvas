#!/bin/bash

echo "=== ODA Component Metrics Testing ==="
echo ""

SERVICE_NAME="r1-productcatalogmanagement-sm"
NAMESPACE="components"
PORT="4000"
METRICS_PATH="/r1-productcatalogmanagement/metrics"

echo "1. Testing metrics endpoint with port-forward..."
kubectl port-forward svc/$SERVICE_NAME $PORT:$PORT -n $NAMESPACE &
PF_PID=$!

echo "Waiting for port-forward to establish..."
sleep 3

echo ""
echo "2. Current metrics output:"
echo "========================="
curl -s http://localhost:$PORT$METRICS_PATH
echo ""
echo "========================="
echo ""

echo "3. Checking if metrics have actual values..."
METRICS_OUTPUT=$(curl -s http://localhost:$PORT$METRICS_PATH)

if echo "$METRICS_OUTPUT" | grep -q "product_catalog_api_counter [0-9]"; then
    echo "✅ Counter has values!"
    echo "$METRICS_OUTPUT" | grep "product_catalog_api_counter"
else
    echo "❌ Counter has no values - only HELP/TYPE comments"
    echo ""
    echo "To fix this in your ODA Component:"
    echo "- Ensure you're incrementing the counter when API calls happen"
    echo "- Initialize the counter with a default value (0)"
    echo "- Add labels for better context: product_catalog_api_counter{endpoint=\"/products\"} 0"
    echo ""
    echo "4. Testing API endpoints to trigger counter increments..."
    echo "Common TMF 620 Product Catalog endpoints:"
    
    # Test common endpoints
    for endpoint in "/tmf-api/productCatalogManagement/v4/catalog" "/tmf-api/productCatalogManagement/v4/category" "/tmf-api/productCatalogManagement/v4/productOffering" "/products" "/categories" "/offerings"; do
        echo "Testing: http://localhost:$PORT$endpoint"
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT$endpoint)
        echo "  Response: $HTTP_CODE"
    done
    
    echo ""
    echo "5. Check metrics again after API calls:"
    echo "========================================"
    curl -s http://localhost:$PORT$METRICS_PATH
    echo ""
    echo "========================================"
fi

# Cleanup
kill $PF_PID 2>/dev/null

echo ""
echo "=== End of Metrics Test ==="