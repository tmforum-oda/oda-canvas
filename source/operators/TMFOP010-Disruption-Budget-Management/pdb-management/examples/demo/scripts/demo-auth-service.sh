
  #!/bin/bash
  echo "🚀 Starting Auth Service Demo..."
  echo "----------------------------------------"

  # Create namespace if it doesn't exist
  echo "1⃣ Ensuring pdb-demo namespace exists..."
  kubectl create namespace pdb-demo 2>/dev/null || true
  
  # Clean up first
  echo "2⃣ Cleaning up any existing deployment..."
  kubectl delete deployment auth-service -n pdb-demo 2>/dev/null
  sleep 2

  # Start log monitoring in background
  echo "3⃣ Starting log monitor..."
  kubectl logs -n canvas deployment/canvas-pdb-management-operator -f --tail=0 | \
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
  echo "4⃣ Applying auth-service deployment..."
  kubectl apply -f ../services/03-auth-service.yaml

  # Wait and show results
  sleep 3
  kill $LOG_PID 2>/dev/null

  echo "----------------------------------------"
  echo "5⃣ Final Results:"
  kubectl get pdb -n pdb-demo auth-service-pdb -o custom-columns="NAME:.metadata.name,MIN-AVAILABLE:.spec.minAvailable,DISRUPTIONS-ALLOWED:.status.disruptionsAllowed"
