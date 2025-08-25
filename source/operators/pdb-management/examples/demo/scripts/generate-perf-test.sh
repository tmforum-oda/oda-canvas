#!/bin/bash

# Script to generate performance test deployments
# Usage: ./generate-perf-test.sh [COUNT]

COUNT=${1:-30}
NAMESPACE=${2:-pdb-demo}

echo "Creating $COUNT deployments for performance testing in namespace: $NAMESPACE"

for i in $(seq 1 $COUNT); do
  cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perf-test-$i
  namespace: $NAMESPACE
  annotations:
    oda.tmforum.org/availability-class: "standard"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: perf-$i
  template:
    metadata:
      labels:
        app: perf-$i
    spec:
      containers:
      - name: app
        image: nginx:alpine
EOF
done

echo "Performance test deployments created successfully!"