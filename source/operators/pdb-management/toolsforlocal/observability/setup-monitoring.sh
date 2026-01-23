#!/bin/bash

# Setup complete observability stack for PDB Management Operator
# Usage: ./setup-monitoring.sh

set -e

echo "🚀 Setting up observability stack..."

# Create namespace
echo "📁 Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Add helm repositories
echo "📦 Adding Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

echo "⚙️  Creating configuration files..."

# Create Prometheus stack values
cat <<EOF > prometheus-values.yaml
# Prometheus configuration
prometheus:
  prometheusSpec:
    # Enable service discovery for your PDB operator
    additionalScrapeConfigs:
      - job_name: 'pdb-management-operator'
        kubernetes_sd_configs:
          - role: endpoints
            namespaces:
              names:
                - canvas
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_name]
            action: keep
            regex: pdb-management-controller-manager-metrics-service
          - source_labels: [__meta_kubernetes_endpoint_port_name]
            action: keep
            regex: https
    # Retain data for 30 days
    retention: 30d
    # Storage for prometheus
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: standard
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi

# Grafana configuration
grafana:
  # Enable persistence
  persistence:
    enabled: true
    storageClassName: standard
    size: 1Gi
  
  # Admin credentials
  adminPassword: admin123
  
  # Configure data sources
  additionalDataSources:
    - name: Loki
      type: loki
      url: http://loki-gateway.monitoring.svc.cluster.local
      access: proxy
    - name: Tempo
      type: tempo
      url: http://tempo.monitoring.svc.cluster.local:3100
      access: proxy
  
  # Enable service for external access
  service:
    type: NodePort
    nodePort: 30080

# AlertManager configuration  
alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: standard
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 1Gi
EOF

# Create Loki values (Single Binary mode)
cat <<EOF > loki-values.yaml
deploymentMode: SingleBinary

loki:
  auth_enabled: false
  commonConfig:
    replication_factor: 1
  storage:
    type: 'filesystem'
  schemaConfig:
    configs:
    - from: "2024-01-01"
      store: tsdb
      index:
        prefix: loki_index_
        period: 24h
      object_store: filesystem
      schema: v13

singleBinary:
  replicas: 1
  persistence:
    enabled: true
    size: 10Gi

backend:
  replicas: 0
read:
  replicas: 0
write:
  replicas: 0

gateway:
  enabled: true
  replicas: 1

monitoring:
  serviceMonitor:
    enabled: true
EOF

# Create Tempo values
cat <<EOF > tempo-values.yaml
tempo:
  storage:
    trace:
      backend: local
      local:
        path: /var/tempo/traces
  
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

persistence:
  enabled: true
  storageClassName: standard
  size: 5Gi

service:
  type: ClusterIP
EOF

# Create Promtail values
cat <<EOF > promtail-values.yaml
config:
  clients:
    - url: http://loki-gateway.monitoring.svc.cluster.local/loki/api/v1/push
  
  scrapeConfigs:
    - job_name: kubernetes-pods
      kubernetes_sd_configs:
        - role: pod
      relabel_configs:
        - source_labels: [__meta_kubernetes_namespace]
          action: keep
          regex: (canvas|monitoring)
        - source_labels: [__meta_kubernetes_pod_name]
          target_label: pod
        - source_labels: [__meta_kubernetes_namespace]
          target_label: namespace
EOF

# Create OTEL Collector values (FIXED)
cat <<EOF > otel-collector-values.yaml
mode: deployment

image:
  repository: otel/opentelemetry-collector-contrib
  tag: "0.91.0"

config:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

  processors:
    batch:

  exporters:
    otlp/tempo:
      endpoint: http://tempo.monitoring.svc.cluster.local:4317
      tls:
        insecure: true

  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [batch]
        exporters: [otlp/tempo]

ports:
  otlp:
    enabled: true
    containerPort: 4317
    servicePort: 4317
    protocol: TCP
  otlp-http:
    enabled: true
    containerPort: 4318 
    servicePort: 4318
    protocol: TCP
EOF

echo "🔧 Installing components..."

# Install Prometheus stack
echo "📊 Installing Prometheus + Grafana..."
helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-values.yaml

# Install Loki
echo "📝 Installing Loki..."
helm upgrade --install loki grafana/loki \
  --namespace monitoring \
  --values loki-values.yaml

# Install Tempo
echo "🔍 Installing Tempo..."
helm upgrade --install tempo grafana/tempo \
  --namespace monitoring \
  --values tempo-values.yaml

# Install Promtail
echo "📤 Installing Promtail..."
helm upgrade --install promtail grafana/promtail \
  --namespace monitoring \
  --values promtail-values.yaml

# Install OTEL Collector
echo "🔄 Installing OTEL Collector..."
helm upgrade --install otel-collector open-telemetry/opentelemetry-collector \
  --namespace monitoring \
  --values otel-collector-values.yaml

# Wait for components to be ready
echo "⏳ Waiting for components to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-stack-grafana -n monitoring
kubectl wait --for=condition=available --timeout=300s deployment/otel-collector -n monitoring

# Import PDB Operator dashboards
echo "📈 Importing PDB Operator dashboards..."
kubectl create configmap pdb-operator-dashboards \
  --from-file=../../config/grafana/pdb-operator-overview.json \
  --from-file=../../config/grafana/pdb-operator-policy-analysis.json \
  --from-file=../../config/grafana/pdb-operator-troubleshooting.json \
  --from-file=../../config/grafana/pdb-operator-traces.json \
  --namespace monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Observability stack installation complete!"
echo ""
echo "🌐 Access URLs (after port-forwarding):"
echo "  Grafana:    http://localhost:3000 (admin/admin123)"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "🔧 To access services:"
echo "  kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3000:80"
echo "  kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090"
echo ""
echo "📊 Check status:"
echo "  kubectl get pods -n monitoring" 