# PDB Management Operator - Observability Stack

Complete observability setup for the PDB Management Operator including metrics, logs, traces, and dashboards.

## Components Included

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **Loki** - Log aggregation and storage
- **Tempo** - Distributed tracing
- **Promtail** - Log shipping to Loki
- **OTEL Collector** - OpenTelemetry trace collection

## Quick Setup

```bash
# Navigate to this directory
cd toolsforlocal/observability

# Make script executable
chmod +x setup-monitoring.sh

# Run the setup (this will install everything)
./setup-monitoring.sh
```

## What Gets Installed

The script will:

1. Create `monitoring` namespace
2. Add required Helm repositories
3. Install Prometheus + Grafana stack
4. Install Loki (single binary mode)
5. Install Tempo for tracing
6. Install Promtail for log collection
7. Install OTEL Collector for trace ingestion
8. Import PDB Operator dashboards

## Access Services

After installation, access the services:

```bash
# Grafana (admin/admin123)
kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3000:80
# Then visit: http://localhost:3000

# Prometheus
kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090
# Then visit: http://localhost:9090
```

## Pre-imported Dashboards

The following PDB Operator dashboards are automatically imported:

- **PDB Operator Overview** - General metrics and health
- **PDB Operator Policy Analysis** - Policy enforcement metrics
- **PDB Operator Troubleshooting** - Error rates and debugging
- **PDB Operator Traces** - Distributed tracing analysis

## Configuration Files

All configuration is stored as Helm values files:

- `prometheus-values.yaml` - Prometheus + Grafana configuration
- `loki-values.yaml` - Loki log storage configuration
- `tempo-values.yaml` - Tempo tracing configuration
- `promtail-values.yaml` - Log collection configuration
- `otel-collector-values.yaml` - OTEL trace collection

## Verify Installation

```bash
# Check all pods are running
kubectl get pods -n monitoring

# Check PDB operator metrics are being scraped
curl "http://localhost:9090/api/v1/query?query=pdb_management_managed_deployments_total"

# View logs in Grafana
# Go to Explore > Loki > Query: {namespace="canvas"} |= "pdb-management"

# View traces in Grafana
# Go to Explore > Tempo > Search for service containing "pdb-management"
```

## Storage Requirements

- **Prometheus**: 10Gi (configurable in prometheus-values.yaml)
- **Loki**: 10Gi (configurable in loki-values.yaml)
- **Tempo**: 5Gi (configurable in tempo-values.yaml)
- **Grafana**: 1Gi (configurable in prometheus-values.yaml)
- **AlertManager**: 1Gi (configurable in prometheus-values.yaml)

**Total**: ~27Gi of persistent storage

## Customization

Edit the `*-values.yaml` files to customize:

- Storage sizes and classes
- Retention policies
- Resource requests/limits
- Service types (NodePort vs LoadBalancer)
- Data source configurations

Then re-run the setup script to apply changes.

## Troubleshooting

### OTEL Collector Issues

- Ensure image repository is set: `otel/opentelemetry-collector-contrib`
- Check service endpoints are reachable

### Loki Issues

- Use `SingleBinary` mode for local testing
- Ensure sufficient storage space

### Dashboard Import Issues

- Verify JSON files exist in `../../config/grafana/`
- Check Grafana is fully ready before import

### Metrics Not Appearing

- Verify PDB operator is deployed in `canvas` namespace
- Check service name matches: `pdb-management-controller-manager-metrics-service`
- Ensure HTTPS endpoint is accessible

## Cleanup

```bash
# Remove all monitoring components
helm uninstall prometheus-stack -n monitoring
helm uninstall loki -n monitoring
helm uninstall tempo -n monitoring
helm uninstall promtail -n monitoring
helm uninstall otel-collector -n monitoring

# Delete namespace (this will remove PVCs too!)
kubectl delete namespace monitoring
```
