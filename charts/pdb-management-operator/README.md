# PDB Management Operator Helm Chart

## Overview
This Helm chart deploys the PDB Management Operator for ODA Canvas.

## Configuration

### Deployment Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|
| `deployment.replicas` | Number of replicas | `2` |
| `deployment.image` | Docker image name | `tmforumodacanvas/pdb-management-operator` |
| `deployment.version` | Image version | `1.0.0` |
| `deployment.imagePullPolicy` | Image pull policy | `IfNotPresent` |
| `deployment.watchNamespace` | Single namespace to watch (empty for all) | `""` |
| `deployment.enableWebhook` | Enable admission webhook | `true` |
| `deployment.enableMetrics` | Enable metrics endpoint | `true` |

### Observability
| Parameter | Description | Default |
|-----------|-------------|---------|
| `observability.logLevel` | Log level (debug, info, error) | `info` |
| `observability.tracing.enabled` | Enable distributed tracing | `false` |
| `observability.tracing.jaegerEndpoint` | Jaeger collector endpoint | `""` |
| `observability.tracing.otlpEndpoint` | OTLP collector endpoint | `""` |
| `observability.tracing.sampleRate` | Trace sampling rate | `1.0` |

### Configuration
| Parameter | Description | Default |
|-----------|-------------|---------|
| `configuration.enablePDB` | Enable PDB creation | `true` |
| `configuration.defaultNamespace` | Default namespace | `default` |
| `configuration.metricsNamespace` | Metrics namespace | `canvas` |
| `configuration.leaderElectionNamespace` | Leader election namespace | `canvas` |

### Custom Configuration
Users can provide additional environment variables using:
```yaml
extraEnvVars:
  - name: CUSTOM_VAR
    value: "custom-value"
```

For tracing backends, configure either Jaeger or OTLP endpoint:
```yaml
observability:
  tracing:
    enabled: true
    # For Jaeger
    jaegerEndpoint: "jaeger-collector.monitoring:14268/api/traces"
    # OR for OTLP (Datadog, Grafana Alloy, etc.)
    otlpEndpoint: "otel-collector.monitoring:4317"
```