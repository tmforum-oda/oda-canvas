# ODA Canvas Open Source Observability Stack

The reference implementation of the ODA Canvas provides an open-source observability stack based on industry standards like OpenMetrics and OpenTelemetry. This reference implementation demonstrates how ODA Components can be monitored using widely-adopted open-source tools.

## Open Source Observability Components

This reference implementation uses the following open-source tools:

### **Prometheus** - Metrics Collection and Storage
- Collects metrics from ODA Components via ServiceMonitor resources
- Stores time-series data for monitoring component health and performance
- Provides alerting capabilities for Canvas operators and components

### **Grafana** - Visualization and Dashboards
- Creates visual dashboards for ODA Component metrics
- Provides alerting and notification capabilities
- Enables Canvas operators to monitor component lifecycle and API usage

### **Jaeger** - Distributed Tracing
- Tracks requests across ODA Components and Canvas operators
- Provides end-to-end visibility into component interactions
- Helps debug performance issues and component dependencies

### **OpenTelemetry Collector** - Telemetry Data Processing
- Receives traces and metrics from ODA Components
- Processes and forwards telemetry data to appropriate backends
- Provides a vendor-neutral way to collect observability data

## Supported Observability Platforms

While this implementation focuses on open-source tools, the Canvas observability architecture has been tested against:

* **Open Source**: Prometheus, Grafana, Jaeger, Kiali
* **Commercial SaaS**: DataDog
* **Cloud-Platforms**: Azure and Google managed observability

## Configuration Files

This implementation includes three simplified configuration files:

- **`prometheus-values.yaml`** - Configures Prometheus to discover ServiceMonitor resources in the components namespace
- **`otel-values.yaml`** - Configures OpenTelemetry Collector to receive traces and forward them to Jaeger
- **`jaeger-values.yaml`** - Configures Jaeger for distributed tracing with in-memory storage (development/testing)

## Installation Guide

### Prerequisites
```bash
kubectl create namespace monitoring
```

### 1. Install Prometheus Stack with Grafana

```bash
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

## Installation Methods

### Method 1: Chart-of-Charts (Recommended)

The simplest way to install the complete observability stack is using the chart-of-charts:

```bash
# Add required Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts  
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

# Install the complete observability stack
helm install observability ../../../charts/observability-stack \
  --create-namespace \
  --namespace monitoring
```

This will install all components (Prometheus, Grafana, Jaeger, OpenTelemetry) in a single command with proper configuration for ODA Canvas.

### Method 2: Individual Component Installation

For more control over each component, you can install them individually:

## ODA Component Integration

### Reference Implementation
For a complete example of how to integrate observability into an ODA Component, see the [Product Catalog Reference Component](https://github.com/tmforum-oda/reference-example-components/tree/master/charts/ProductCatalog) which demonstrates:

- OpenTelemetry tracing instrumentation
- Prometheus metrics exposure
- Canvas-compliant observability patterns

### OpenTelemetry Configuration

Configure ODA Components to send traces to the Canvas observability stack:

```yaml
# Environment variables for ODA Components
OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318"
```


## Post-Installation

### Accessing the Services

After installation, you can access the observability services using port-forwarding:

```bash
# Prometheus
kubectl port-forward svc/observability-kube-prometheus-prometheus 9090:9090 -n monitoring

# Grafana  
kubectl port-forward svc/observability-grafana 3000:80 -n monitoring

# Jaeger
kubectl port-forward svc/observability-jaeger-query 16686:16686 -n monitoring
```

### Getting Grafana Admin Password

```bash
kubectl get secret observability-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
```

### Configuring ODA Components

Configure your ODA Components to send telemetry data to the observability stack:

```yaml
env:
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://opentelemetry-collector.monitoring.svc.cluster.local:4318"
- name: OTEL_RESOURCE_ATTRIBUTES
  value: "service.name=your-component-name"
```

For detailed configuration and troubleshooting, see the [chart documentation](../../../charts/observability-stack/README.md).

## Legacy Installation Instructions

The following instructions are for installing components individually:

