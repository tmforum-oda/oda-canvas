# View Observability Data

## Table of Contents
- [Auto-Discover Services](#auto-discover-services)
- [Handling Missing Observability Stack](#handling-missing-observability-stack)
- [ServiceMonitor Configuration](#servicemonitor-configuration)
- [Port-Forward and Open UIs](#port-forward-and-open-uis)
- [Proactive Prometheus Guidance](#proactive-prometheus-guidance)
- [Exercising the API for Metrics](#exercising-the-api-for-metrics)
- [Proactive Jaeger Troubleshooting](#proactive-jaeger-troubleshooting)
- [Kubernetes Observability Resources](#kubernetes-observability-resources)
- [Architecture Reference](#architecture-reference)

## Auto-Discover Services

The observability stack is optional and may not be installed. Auto-discover using the helper script:

```bash
kubectl get svc -A -o json | python <scripts>/discover_observability.py
```

This script finds Prometheus, Grafana, Jaeger, and OpenTelemetry services across namespaces, shows service names/namespaces/types/ports, suggests port-forward commands, and prints installation instructions if nothing is found.

## Handling Missing Observability Stack

If no services are found, provide installation instructions. Full docs: https://github.com/tmforum-oda/oda-canvas/tree/main/charts/observability-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add opentelemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

cd charts
helm dependency build observability-stack
helm install observability ./observability-stack --create-namespace --namespace monitoring
```

**Configuring the Canvas to use ServiceMonitors:**

```bash
helm upgrade --install canvas charts/canvas-oda -n canvas \
  --set api-operator-istio.deployment.openMetricsImplementation=ServiceMonitor \
  --create-namespace
```

**Key defaults:**

| Parameter | Default |
|-----------|---------|
| `prometheus.enabled` | `true` |
| `opentelemetry.enabled` | `true` |
| `jaeger.enabled` | `true` |
| `kube-prometheus-stack.grafana.adminPassword` | `prom-operator` |
| Jaeger storage | In-memory, 50,000 traces max |
| Prometheus retention | 15 days |

Check ServiceMonitor CRD availability:

```bash
kubectl get crd servicemonitors.monitoring.coreos.com 2>&1
```

## ServiceMonitor Configuration

Verify the api-operator-istio is configured to create ServiceMonitors:

```bash
kubectl get configmap api-operator-istio-configmap -n canvas -o jsonpath='{.data.OPENMETRICS_IMPLEMENTATION}'
```

- **`ServiceMonitor`** — correct, no action needed.
- **`DataDogAnnotation`** or **`PrometheusAnnotation`** — change to `ServiceMonitor`:

```bash
kubectl patch configmap api-operator-istio-configmap -n canvas --type merge -p '{"data":{"OPENMETRICS_IMPLEMENTATION":"ServiceMonitor"}}'
kubectl rollout restart deployment -n canvas -l app.kubernetes.io/name=api-operator-istio
```

After changing, existing components need redeployment (`helm delete` + `helm install`) for ServiceMonitors. Set permanently:

```bash
helm upgrade canvas charts/canvas-oda -n canvas \
  --set api-operator-istio.deployment.openMetricsImplementation=ServiceMonitor
```

## Port-Forward and Open UIs

Default namespace for observability is `monitoring`. Use the discovered namespace from auto-discovery.

```bash
# Prometheus (default port 9090)
kubectl port-forward svc/observability-prometheus-prometheus 9090:9090 -n monitoring

# Grafana (default port 3000, service port 80)
kubectl port-forward svc/observability-grafana 3000:80 -n monitoring

# Jaeger UI (default port 16686)
kubectl port-forward svc/observability-jaeger-query 16686:16686 -n monitoring
```

Run port-forward as a background process. Open UIs in VS Code Simple Browser:

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` — Default password: `prom-operator`. Retrieve from secret:
  ```bash
  kubectl get secret observability-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
  ```
- **Jaeger**: `http://localhost:16686`

## Proactive Prometheus Guidance

When the user opens Prometheus or asks about it, **proactively offer**:

1. **Generate metrics data** if `product_catalog_api_counter` has low/zero values — suggest `exercise_catalog_api.py`.

2. **Useful PromQL queries:**

   | Query | Description |
   |-------|-------------|
   | `product_catalog_api_counter` | Current totals by notification event type |
   | `rate(product_catalog_api_counter[5m])` | Event rate per second over 5 minutes |
   | `sum by (NotificationEvent) (rate(product_catalog_api_counter[5m]))` | Rate grouped by event type (best for Graph tab) |
   | `sum(rate(product_catalog_api_counter{NotificationEvent=~".*CreationNotification"}[5m]))` | Aggregate creation rate |
   | `sum(rate(product_catalog_api_counter{NotificationEvent=~".*RemoveNotification"}[5m]))` | Aggregate removal rate |
   | `sum(rate(product_catalog_api_counter[5m])) * 60` | Total events per minute |
   | `container_cpu_usage_seconds_total{namespace="components"}` | CPU usage of component pods |
   | `container_memory_working_set_bytes{namespace="components"}` | Memory usage of component pods |

   Tip: Use `rate()` queries in the **Graph** tab with a 15m–1h range. Use instant totals in the **Table** tab.

3. **Workflow suggestion** when no recent data exists:
   - Run `exercise_catalog_api.py --rounds 3`
   - Wait 30 seconds for Prometheus to scrape
   - Enter `sum by (NotificationEvent) (rate(product_catalog_api_counter[5m]))` in Graph tab
   - Set time range to 15 minutes

## Exercising the API for Metrics

Generate notification events for the `product_catalog_api_counter` Prometheus metric:

```bash
python <scripts>/exercise_catalog_api.py <api-base-url> [--rounds N] [--cleanup]
```

The API base URL is the ExposedAPI URL for the `productcatalogmanagement` core function API. For release `r2`:

```bash
# One round: creates 14 resources across 4 types, deletes half
python <scripts>/exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4

# 3 rounds for more data
python <scripts>/exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4 --rounds 3

# Clean up
python <scripts>/exercise_catalog_api.py https://localhost/r2-productcatalogmanagement/tmf-api/productCatalogManagement/v4 --cleanup
```

| Resource Type | Create Notification | Delete Notification | Count |
|--------------|--------------------|--------------------|-------|
| `category` | CategoryCreationNotification | CategoryRemoveNotification | 5 |
| `catalog` | CatalogCreationNotification | CatalogRemoveNotification | 2 |
| `productSpecification` | ProductSpecificationCreationNotification | ProductSpecificationRemoveNotification | 4 |
| `productOffering` | ProductOfferingCreationNotification | ProductOfferingRemoveNotification | 3 |

Each round: ~14 creation events and ~7 deletion events. Resources tagged `[exercise-catalog-api]`, removable with `--cleanup`.

After running, verify:

```bash
kubectl exec -n components deploy/<release>-metricsapi -- wget -qO- http://localhost:4000/<component>/metrics
```

## Proactive Jaeger Troubleshooting

When the user opens Jaeger or asks about traces, **always verify** components are sending traces to the correct OpenTelemetry Collector URL. Reference example components default to a DataDog agent URL that doesn't exist in the reference Canvas.

**Step 1: Check current collector URL:**

```bash
kubectl get deploy <release>-prodcatapi -n components \
  -o jsonpath="{.spec.template.spec.containers[0].env[?(@.name=='OTL_EXPORTER_TRACE_PROTO_COLLECTOR_URL')].value}"
```

**Step 2: Find correct URL:**

```bash
kubectl get svc -A | Select-String 'opentelemetry-collector'
```

Correct format: `http://<collector-service>.<namespace>.svc.cluster.local:4318/v1/traces`
Reference stack default: `http://observability-opentelemetry-collector.monitoring.svc.cluster.local:4318/v1/traces`

**Step 3: Fix if wrong** (points to `datadog-agent` or non-existent service):

```bash
helm upgrade <release> oda-components/productcatalog -n components \
  --set api.otlp.protobuffCollector.url=http://observability-opentelemetry-collector.monitoring.svc.cluster.local:4318/v1/traces \
  --reuse-values
```

> Use `--reuse-values` to preserve other settings (e.g. `component.dependentAPIs.enabled=true`).

**Step 4: Verify traces flowing:**

```bash
python <scripts>/exercise_catalog_api.py https://localhost/<release>-productcatalogmanagement/tmf-api/productCatalogManagement/v4

# PowerShell:
(Invoke-RestMethod http://localhost:16686/api/services).data
# bash:
curl -s http://localhost:16686/api/services | python -m json.tool
```

Component should appear as `<release>-productcatalogmanagement` in Jaeger services.

**Common symptoms of misconfigured collector URL:**
- Jaeger shows no services or only `jaeger-all-in-one`
- Component logs show no errors (traces silently dropped)
- OpenTelemetry Collector logs show only `MetricsExporter` entries, no `TracesExporter`

## Kubernetes Observability Resources

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
kubectl get servicemonitors -A 2>&1
kubectl get pods -n monitoring -l app.kubernetes.io/name=opentelemetry-collector
kubectl logs -n monitoring deployment/observability-opentelemetry-collector
```

If `kubectl get servicemonitors` returns "the server doesn't have a resource type", ServiceMonitor-based metrics discovery is not available.

For UC012 BDD tests, port-forward the collector:

```bash
kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888
```

## Architecture Reference

```
ODA Components → OTLP HTTP (:4318) → OpenTelemetry Collector → Jaeger Collector (:4317) → Jaeger UI
ODA Components → /metrics endpoint → Prometheus (ServiceMonitor discovery) → Grafana dashboards
```
