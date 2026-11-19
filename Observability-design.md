# Observability design

This document describes the design artefacts for the Observability part of the [overall ODA Canvas design](Canvas-design.md).

There is an introductory video, part 5 of the [ODA Canvas training videos](https://tmforum-oda.github.io/oda-ca-docs/docs/training-videos/index.html), showing the reference observability stack (Prometheus, Grafana and Jaeger) live:

[![Observability in the ODA Canvas](https://img.youtube.com/vi/3Mcv0oc-0rs/0.jpg)](https://youtu.be/3Mcv0oc-0rs)

## Overview

Traditionally, every application arrives with its own monitoring agents and its own dashboards, and operations teams spend weeks wiring each one into their tools. A service provider may run dozens of components from many vendors, and needs one consistent view across all of them.

An ODA Component is different. It declares its metrics API in its specification, and the Canvas configures the observability platform for it automatically. The Canvas builds on open standards, so any compliant platform can be used:

* **OpenMetrics** for metrics: the component exposes a metrics endpoint, which the platform scrapes.
* **OpenTelemetry** for traces: the component pushes its traces over OTLP to a collector.

The Canvas mandates no product. The reference implementation uses Prometheus, Grafana and Jaeger, but a managed cloud service or another observability platform can be used instead.

## Three kinds of observability

| Kind | What it shows | Where it comes from | Use case |
|---|---|---|---|
| Technical metrics | How a component is running: CPU, memory, request rates and latencies | The platform (the container metrics of every pod) and the service mesh. Nothing is needed from the component. | [UC011](usecase-library/UC011-View-Technical-Observability.md) |
| Business metrics | Metrics specific to each component, for example the number of orders captured, or catalog items created | The component's own metrics API, declared in its specification | [UC012](usecase-library/UC012-View-Business-Observability.md) |
| Traces | One request, step by step, across components and the Canvas services they use | The component, sending OpenTelemetry traces to a collector | [UC012](usecase-library/UC012-View-Business-Observability.md) |

Together, they show whether a component is healthy, give insight into its business performance, and help troubleshoot issues, for example by showing where the time is spent in a request.

## A component declares its metrics API

A component lists its metrics API in the `managementFunction` of its specification, alongside its other exposed APIs. The `apiType` is `openmetrics` (preferred) or `prometheus`, with the path and port where the metrics can be read:

```yaml
managementFunction:
  exposedAPIs:
  - name: metrics
    apiType: openmetrics
    implementation: {{.Release.Name}}-{{.Values.component.name}}-sm
    path: /{{.Release.Name}}-{{.Values.component.name}}/metrics
    port: 4000
```

The component does not say which observability platform will read its metrics. That is the Canvas's job.

## How the Canvas configures metrics collection

When the component is deployed, the component operator creates an `ExposedAPI` resource for each API. The API operator handles each one, and for an API of type `openmetrics` or `prometheus` it also configures the observability platform:

1. In the reference Canvas, the API operator creates a `ServiceMonitor` resource for the metrics API, with a scrape interval of 15 seconds.
2. Prometheus (through the Prometheus operator) finds the `ServiceMonitor` and starts scraping the component's metrics endpoint.
3. The `ServiceMonitor` is owned by the `ExposedAPI`, so when the component is uninstalled, it is removed with it.

Not every platform uses `ServiceMonitor` resources, so the API operator has a setting, `openMetricsImplementation` (the `OPENMETRICS_IMPLEMENTATION` environment variable), with three options:

| Option | What the API operator does | Use it for |
|---|---|---|
| `ServiceMonitor` | Creates a `ServiceMonitor` custom resource | Platforms that use the Prometheus operator, such as the reference stack |
| `PrometheusAnnotation` | Adds Prometheus scrape annotations to the component's pods | Prometheus without the Prometheus operator, and some managed Prometheus services, such as [Azure Monitor managed service for Prometheus](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-metrics-overview) |
| `DataDogAnnotation` | Adds pod annotations in Datadog's format | Datadog |

The setting is supported by the Istio, Kong and Apache APISIX API operators. In the `canvas-oda` chart, the Istio API operator defaults to `ServiceMonitor`, and the Kong and APISIX API operators default to `PrometheusAnnotation`. With the reference observability stack, set it to `ServiceMonitor`, for example:

```bash
helm upgrade --install canvas charts/canvas-oda -n canvas --create-namespace \
  --set api-operator-istio.deployment.openMetricsImplementation=ServiceMonitor
```

The component specification stays the same in every case.

## Traces

Traces work the other way round: instead of being scraped, the component pushes its traces as they happen. It sends them with the OpenTelemetry protocol (OTLP over HTTP, port 4318) to the OpenTelemetry Collector, which batches them and forwards them to Jaeger. Because the protocol is standard, the collector can forward them to another tracing platform instead.

The collector address is part of the environment, not of the component specification, so it is set when the component is installed, in its Helm values. For example, the product catalog test component in the [test kit](feature-definition-and-test-kit/README.md) uses:

```yaml
api:
  otlp:
    protobuffCollector:
      enabled: true
      url: http://observability-opentelemetry-collector.monitoring.svc.cluster.local:4318/v1/traces
```

A trace in Jaeger shows one request from end to end: the incoming HTTP call, the middleware steps that validate the request against the TMF API definition, and the calls to the database, each with how long it took.

## The reference observability stack

The [observability stack chart](charts/observability-stack/README.md) (`charts/observability-stack`) installs a complete open-source stack into its own `monitoring` namespace:

* **Prometheus** (from `kube-prometheus-stack`, with the Prometheus operator, kube-state-metrics and Alertmanager) collects and stores metrics.
* **Grafana** turns them into dashboards, with Prometheus as its data source. It includes the standard Kubernetes dashboards, so choosing the `components` namespace shows the CPU and memory of every deployed component.
* **Jaeger** stores and displays traces.
* **The OpenTelemetry Collector** receives telemetry from components and forwards traces to Jaeger.

See the chart's README for how to install it and how to reach each user interface.

## Observability in the Canvas Portal

The [Canvas Portal](canvas-portal-v2/README.md) has an **Observability** page that finds the observability tools in the cluster by their service names, and shows the address of each one inside the cluster. It looks for Langfuse (for LLM observability), Grafana and Prometheus. The Canvas is still under development, and LLM observability is in the backlog.

## Use cases

The observability use cases are documented in the [use case library](usecase-library/README.md) as follows:

* [UC006-Configure-Observability](usecase-library/UC006-Configure-Observability.md)
* [UC011-View-Technical-Observability](usecase-library/UC011-View-Technical-Observability.md)
* [UC012-View-Business-Observability](usecase-library/UC012-View-Business-Observability.md)

## BDD Features

For each use case, a set of BDD features describes the behaviour required of the Canvas, using scenarios. The goal is for a set of business-friendly pseudo-code that describes the behaviour of the Canvas, and that directly maps to steps that will test that feature. Some features are optional - the test report will indicate which features have passed, but will not fail the test for a canvas if an optional feature is not implemented.

| Feature | What it tests | Tag |
|---|---|---|
| [UC012-F001 OpenTelemetry Collector configuration](https://github.com/tmforum-oda/oda-canvas/blob/main/feature-definition-and-test-kit/features/UC012-F001-Observability-OpenTelemetry-configuration.feature) | Adding catalog data sends new events to the OpenTelemetry Collector | `@OpenTelemetryCollector` |
| [UC012-F002 Open-Metrics configuration](https://github.com/tmforum-oda/oda-canvas/blob/main/feature-definition-and-test-kit/features/UC012-F002-Observability-OpenMetrics-configuration.feature) | Installing a component creates a `ServiceMonitor` for its metrics API, and uninstalling it removes it | `@ServiceMonitor` |

Both are tagged, so a Canvas without these tools can skip them.
