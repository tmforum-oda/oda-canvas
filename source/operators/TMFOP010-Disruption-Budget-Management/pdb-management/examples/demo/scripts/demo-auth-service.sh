
  #!/bin/bash
  echo "🚀 Starting Auth Service Demo..."
  echo "----------------------------------------"

  # Clean up first
  echo "1⃣ Cleaning up any existing deployment..."
  kubectl delete deployment auth-service -n pdb-demo 2>/dev/null
  sleep 2

  # Start log monitoring in background
  echo "2⃣ Starting log monitor..."
  kubectl logs -n canvas deployment/pdb-management-controller-manager -f --tail=0 | \
    grep --line-buffered "auth-service" | \
    while read line; do
      if echo "$line" | grep -q "mission-critical"; then
        echo "✅ Detected mission-critical classification"
      elif echo "$line" | grep -q "PDB created"; then
        echo "✅ PDB successfully created"
      elif echo "$line" | grep -q "Reconciliation completed"; then
        duration=$(echo "$line" | grep -o '"duration":"[^"]*"' | cut -d'"' -f4)
        echo "⚡ Reconciliation completed in $duration"
      fi
    done &
  LOG_PID=$!

  # Apply deployment
  echo "3⃣ Applying auth-service deployment..."
  kubectl apply -f ../services/03-auth-service.yaml

  # Wait and show results
  sleep 3
  kill $LOG_PID 2>/dev/null

  echo "----------------------------------------"
  echo "4⃣ Final Results:"
  kubectl get pdb -n pdb-demo auth-service-pdb -o custom-columns="NAME:.metadata.name,MIN-AVAILABLE:.spec.minAvailable,DISRUPTIONS-ALLOWED:.status.disruptionsAllowed"
