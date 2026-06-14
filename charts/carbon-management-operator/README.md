# Carbon Management Operator

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: v1](https://img.shields.io/badge/AppVersion-v1-informational?style=flat-square)

The carbon management operator is intended for the ODA Canvas Reference Implementation. Its function is to manage carbon intensity monitoring and carbon-aware scaling for ODA Components using KEDA ScaledObjects and ScaledJobs, integrating with external carbon intensity APIs.

## Features

- Watches `carbonmanagements` CRD for carbon management configurations
- Manages KEDA ScaledObjects and ScaledJobs for carbon-aware autoscaling
- Integrates with external carbon intensity API
- Provides comprehensive RBAC for cluster-wide resource management
- Supports multiple monitored namespaces

## Configuration Parameters

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| deployment.operatorName | string | carbon-management-operator | Name of the operator |
| deployment.carbonImage | string | adarshkrm/carbon-management-operator | Docker image name |
| deployment.carbonVersion | string | 1.0.0 | Image version tag |
| deployment.carbonPrereleaseSuffix | string | | Prerelease suffix (triggers `imagePullPolicy: Always`) |
| deployment.imagePullPolicy | string | IfNotPresent | Image pull policy |
| deployment.replicas | int | 1 | Number of operator replicas |
| deployment.resources.requests.cpu | string | 100m | CPU request |
| deployment.resources.requests.memory | string | 128Mi | Memory request |
| deployment.resources.limits.cpu | string | 500m | CPU limit |
| deployment.resources.limits.memory | string | 512Mi | Memory limit |
| deployment.monitoredNamespaces | string | canvas | Comma-separated list of namespaces to monitor |
| service.metrics.port | int | 8080 | Metrics service port |
| configmap.carbonIntensityApiUrl | string | http://carbon-intensity-service.canvas.svc.cluster.local/tmf-api/performance/v5 | Carbon intensity API endpoint URL |
| serviceAccount.create | bool | true | Create ServiceAccount |
| rbac.create | bool | true | Create RBAC resources |

## Installation

```bash
helm install carbon-management-operator charts/carbon-management-operator \
  --namespace canvas \
  --create-namespace
```

## Configuration Examples

### Custom Image Version

```bash
helm install carbon-management-operator charts/carbon-management-operator \
  --namespace canvas \
  --create-namespace \
  --set deployment.carbonVersion=1.0.1
```

### Multiple Monitored Namespaces

```bash
helm install carbon-management-operator charts/carbon-management-operator \
  --namespace canvas \
  --create-namespace \
  --set deployment.monitoredNamespaces="canvas,components"
```

### Custom Carbon Intensity API

```bash
helm install carbon-management-operator charts/carbon-management-operator \
  --namespace canvas \
  --create-namespace \
  --set configmap.carbonIntensityApiUrl="http://custom-api.example.com/api/v5"
```

## RBAC Permissions

The operator requires the following permissions:
- KOPF Framework peerings and event management
- `carbonmanagements` CRD (get, list, watch, create, update, patch, delete)
- `carbonmanagements/status` and `carbonmanagements/finalizers`
- `keda.sh/scaledobjects` and `keda.sh/scaledjobs`
- Kubernetes core resources (pods, services, configmaps, secrets, deployments, etc.)
- Event creation and patching

## Monitoring

The operator exposes metrics on port `8080`. Configure Prometheus scraping as needed:

```yaml
serviceMonitor:
  enabled: true
  port: 8080
  interval: 30s
```
