# PDB Management Operator - Grafana Dashboards

This directory contains comprehensive Grafana dashboards for monitoring and observing the PDB Management Operator. The dashboards are designed to work with your existing OTEL, Prometheus, and Grafana stack.

## Dashboard Overview

### 1. **Overview Dashboard** (`pdb-operator-overview.json`)

**Purpose**: High-level operational metrics and health status

**Key Metrics**:

- Total managed deployments and PDBs created
- Reconciliation error rate and latency percentiles
- Deployments by availability class
- Cache performance metrics
- Real-time reconciliation rates

**Use Cases**:

- Daily operations monitoring
- SLA compliance tracking
- Performance overview
- Capacity planning

### 2. **Policy Analysis Dashboard** (`pdb-operator-policy-analysis.json`)

**Purpose**: Deep dive into policy behavior, enforcement, and compliance

**Key Metrics**:

- Active policies count
- Policy override attempts and results
- Compliance rate across namespaces
- Enforcement decisions (strict vs flexible vs advisory)
- Policy application patterns

**Use Cases**:

- Policy effectiveness analysis
- Compliance auditing
- Security policy monitoring
- Override pattern analysis

### 3. **Troubleshooting Dashboard** (`pdb-operator-troubleshooting.json`)

**Purpose**: Error diagnosis, performance issues, and debugging

**Key Metrics**:

- Error rates by controller and type
- Circuit breaker states and failures
- Resource usage (CPU, memory)
- Workqueue metrics and backlog
- Recent error and warning logs

**Use Cases**:

- Incident response
- Performance troubleshooting
- Capacity issues diagnosis
- Error pattern analysis

### 4. **Distributed Tracing Dashboard** (`pdb-operator-traces.json`)

**Purpose**: End-to-end request tracing and correlation with logs

**Key Metrics**:

- Trace volume and error rates
- Operation duration percentiles by span
- Request correlation across services
- Error trace analysis
- Logs correlated with trace context

**Use Cases**:

- Root cause analysis
- Performance bottleneck identification
- Request flow visualization
- Cross-service debugging

## Prerequisites

### Required Data Sources

1. **Prometheus**: Metrics collection
   - Scraping PDB operator metrics endpoint (`:8080/metrics`)
   - Standard Kubernetes metrics
2. **Loki**: Log aggregation

   - Collecting operator logs in JSON format
   - Proper log parsing configuration

3. **Tempo**: Distributed tracing

   - OTEL trace collection from operator
   - Trace-log correlation setup

4. **OTEL Collector**: (Optional but recommended)
   - Unified telemetry collection
   - Trace and metrics correlation

## Setup Instructions

### 1. Configure Data Sources in Grafana

First, ensure your Grafana instance has the required data sources configured:

```bash
# Example Prometheus data source
curl -X POST \
  http://your-grafana:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://your-prometheus:9090",
    "access": "proxy"
  }'

# Example Loki data source
curl -X POST \
  http://your-grafana:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Loki",
    "type": "loki",
    "url": "http://your-loki:3100",
    "access": "proxy"
  }'

# Example Tempo data source
curl -X POST \
  http://your-grafana:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Tempo",
    "type": "tempo",
    "url": "http://your-tempo:3200",
    "access": "proxy"
  }'
```

### 2. Import Dashboards

Use the provided import script or import manually:

```bash
# Using the import script (recommended)
./import-dashboards.sh

# Or import individually via Grafana UI
# 1. Go to Grafana UI → + → Import
# 2. Upload each .json file
# 3. Configure data source mappings
```

### 3. Configure Prometheus Scraping

Ensure Prometheus is scraping the operator metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "pdb-management-operator"
    static_configs:
      - targets: ["pdb-management-operator:8080"]
    scrape_interval: 30s
    metrics_path: /metrics
```

### 4. Configure Log Collection

For Loki integration, ensure logs are collected in JSON format:

```yaml
# If using Promtail
- job_name: pdb-operator
  static_configs:
    - targets:
        - localhost
      labels:
        job: pdb-management-operator
        __path__: /var/log/pods/canvas_pdb-management-*/*.log
  pipeline_stages:
    - json:
        expressions:
          level: level
          msg: msg
          ts: ts
          trace_id: trace_id
          span_id: span_id
          correlationID: correlationID
```

## Dashboard Customization

### Variables and Templating

All dashboards include these template variables:

- **Data Source**: Select your specific Prometheus/Loki/Tempo instances
- **Namespace**: Filter by Kubernetes namespace
- **Time Range**: Adjustable time windows

### Alerting Integration

Key metrics suitable for alerting:

```promql
# High error rate
rate(pdb_operator_reconciliation_errors_total[5m]) > 0.1

# High latency
histogram_quantile(0.95, pdb_operator_reconciliation_duration_seconds_bucket) > 1.0

# Low compliance
(pdb_operator_compliance_status{status="compliant"} / pdb_operator_compliance_status) < 0.95

# Circuit breaker tripped
pdb_operator_circuit_breaker_state{state="open"} > 0
```

### Panel Customization

Each dashboard can be customized for your environment:

1. **Thresholds**: Adjust warning/critical thresholds based on your SLAs
2. **Time Windows**: Modify default time ranges (currently 1 hour)
3. **Refresh Rates**: Change auto-refresh intervals (currently 30s)
4. **Filtering**: Add additional label filters for multi-tenant setups

## Metrics Reference

### Core Operator Metrics

| Metric                                         | Type      | Description                            | Labels                            |
| ---------------------------------------------- | --------- | -------------------------------------- | --------------------------------- |
| `pdb_operator_managed_deployments`             | Gauge     | Number of deployments under management | `namespace`, `availability_class` |
| `pdb_operator_pdbs_created_total`              | Counter   | Total PDBs created                     | `namespace`, `result`             |
| `pdb_operator_reconciliation_duration_seconds` | Histogram | Reconciliation latency                 | `controller`                      |
| `pdb_operator_reconciliation_errors_total`     | Counter   | Reconciliation errors                  | `controller`, `error_type`        |
| `pdb_operator_cache_hit_ratio`                 | Gauge     | Cache hit percentage                   | `cache_type`                      |

### Policy Metrics

| Metric                                      | Type    | Description                  | Labels                     |
| ------------------------------------------- | ------- | ---------------------------- | -------------------------- |
| `pdb_operator_availability_policies_active` | Gauge   | Active policies              | `namespace`, `policy_name` |
| `pdb_operator_enforcement_decisions_total`  | Counter | Policy enforcement decisions | `enforcement`, `decision`  |
| `pdb_operator_override_attempts_total`      | Counter | Annotation override attempts | `result`, `reason`         |
| `pdb_operator_compliance_status`            | Gauge   | Compliance status            | `namespace`, `status`      |

### System Metrics

| Metric                               | Type    | Description                | Labels             |
| ------------------------------------ | ------- | -------------------------- | ------------------ |
| `pdb_operator_circuit_breaker_state` | Gauge   | Circuit breaker states     | `service`, `state` |
| `pdb_operator_workqueue_depth`       | Gauge   | Controller workqueue depth | `controller`       |
| `pdb_operator_workqueue_adds_total`  | Counter | Items added to workqueue   | `controller`       |

## Troubleshooting

### Common Issues

1. **No Data in Dashboards**:

   - Verify data source connectivity
   - Check Prometheus scraping configuration
   - Ensure operator is exposing metrics on `:8080/metrics`

2. **Missing Traces**:

   - Verify OTEL collector configuration
   - Check Tempo data source setup
   - Ensure operator has tracing enabled

3. **Log Correlation Issues**:

   - Verify Loki is parsing JSON logs correctly
   - Check trace context injection in logs
   - Ensure correlation ID generation is working

4. **Performance Issues**:
   - Reduce dashboard refresh rates
   - Optimize time ranges for large datasets
   - Use recording rules for complex queries

### Verification Commands

```bash
# Check operator metrics endpoint
kubectl port-forward -n canvas svc/pdb-management-operator 8080:8080
curl http://localhost:8080/metrics | grep pdb_operator

# Check log format
kubectl logs -n canvas deployment/pdb-management-operator | head -5

# Verify trace export
kubectl logs -n canvas deployment/pdb-management-operator | grep -i trace
```

## Advanced Configuration

### Multi-Cluster Setup

For multi-cluster deployments:

1. Add cluster label to all metrics:

```yaml
external_labels:
  cluster: "production"
```

2. Update dashboard variables to include cluster filtering

3. Configure federated Prometheus setup

### High Availability

For HA Grafana setups:

1. Store dashboards in git for version control
2. Use provisioning for automated deployment
3. Configure dashboard folders and permissions
4. Set up dashboard backup procedures

## Support

For issues or questions:

1. Check the operator logs for errors
2. Verify data source connectivity
3. Review Prometheus/Loki/Tempo configuration
4. Refer to the operator documentation
5. Open an issue with dashboard logs and configuration details
