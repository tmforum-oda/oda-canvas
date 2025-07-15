# ODA Canvas Observability Installation

The ODA Canvas observability stack is based on open standards like OpenMetrics and OpenTelemetry. It provides comprehensive monitoring capabilities for ODA Components and Canvas operators.

## Supported Observability Platforms

The Canvas observability implementation has been tested against:

* Prometheus, Grafana, Kiali (open source)
* DataDog SaaS observability
* Azure managed observability

## Installation Guide

### 1. Install Kube-Prometheus-Stack

```bash
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring -f prometheus-values.yaml
```

### 2. Install OpenTelemetry Collector

```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm install otel-collector open-telemetry/opentelemetry-collector -n monitoring -f otel-values.yaml
```

### 3. Install Jaeger for Distributed Tracing

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update
helm install jaeger jaegertracing/jaeger -n monitoring -f jaeger-values.yaml
```

## ODA Component Integration

### OpenTelemetry Configuration

Configure ODA Components to send traces and metrics to the Canvas observability stack:

```yaml
# Environment variables for ODA Components
OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318"
OTEL_SERVICE_NAME: "your-oda-component-name"
OTEL_RESOURCE_ATTRIBUTES: "oda.component.name=your-component,oda.component.version=1.0.0"
```

### Prometheus Metrics

Add these annotations to ODA Component pods for automatic metrics discovery:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
```

### ServiceMonitor for ODA Components

ODA Components can use ServiceMonitor resources for automatic metrics discovery by the Canvas observability stack:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-oda-component-metrics
  namespace: components
  labels:
    oda.tmforum.org/componentName: my-oda-component
spec:
  selector:
    matchLabels:
      name: my-oda-component-service
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

## Testing the Canvas Observability Stack

### Send Test Traces

```bash
kubectl run trace-test --image=curlimages/curl --rm -i --tty -- curl -X POST \
  http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "oda-component-test"}},
          {"key": "oda.component.name", "value": {"stringValue": "test-component"}},
          {"key": "oda.component.version", "value": {"stringValue": "1.0.0"}}
        ]
      },
      "instrumentationLibrarySpans": [{
        "spans": [{
          "traceId": "1234567890abcdef1234567890abcdef",
          "spanId": "fedcba0987654321",
          "name": "test-canvas-trace",
          "startTimeUnixNano": "1609459200000000000",
          "endTimeUnixNano": "1609459201000000000"
        }]
      }]
    }]
  }'
```

## Access Monitoring UIs

### Prometheus
```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
```
Visit: http://localhost:9090

### Grafana
```bash
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```
Visit: http://localhost:3000

Get admin password:
```bash
kubectl get secrets monitoring-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
```

### Jaeger
```bash
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
```
Visit: http://localhost:16686

## Canvas Observability Features

The ODA Canvas observability stack provides:

- **Component Lifecycle Monitoring**: Track ODA Component deployment, updates, and health
- **API Gateway Metrics**: Monitor API usage and performance through Canvas API management
- **Service Mesh Observability**: Service-to-service communication metrics between Components
- **Distributed Tracing**: End-to-end trace tracking across Canvas operators and Components
- **Canvas Operator Metrics**: Monitor Canvas operator performance and Component management lifecycle
- **Security Metrics**: Track authentication, authorization, and security events

This observability implementation supports the Canvas's modular architecture, providing insights into Component interactions, API patterns, and system health across the entire ODA ecosystem.