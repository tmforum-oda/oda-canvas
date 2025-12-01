# {Component Name}

<!-- 
Template for Test Component README files in feature-definition-and-test-kit/testData/ directory
These components are used for BDD testing of the ODA Canvas
Replace all {placeholder} values with actual content
-->

## Overview

{Brief description of this test component and its purpose in the test suite}

**TM Forum Reference**: {TMF API Name} component implementing [TMF{number} {API Name}](https://www.tmforum.org/resources/specification/tmf{number}-{api-name}/)

This component is used to test:
- {Test scenario 1}
- {Test scenario 2}
- {Test scenario 3}

## Component Functions

### Core Function

In its **core function** this component implements:

* The *mandatory* [TMF{number} {API Name}](https://www.tmforum.org/resources/specification/tmf{number}-{api-name}/) Open API
  - {Brief description of what this API provides}
* The *optional* [TMF{number} {Optional API Name}](https://www.tmforum.org/resources/specification/tmf{number}-{optional-api}/) Open API
  - {Brief description if applicable}

<!-- Add more TMF APIs as needed -->

### Management Function

In its **management function** this component implements:

* **Metrics API**: Optional metrics following the [Open Metrics](https://openmetrics.io/) standard
  - Exposes component health metrics
  - Performance indicators
* **Observability Events**: Outbound Open Telemetry events
  - Traces for request flows
  - Metrics for performance monitoring

### Security Function

In its **security function** this component implements:

* The *mandatory* [TMF669 Party Role Management](https://www.tmforum.org/resources/specification/tmf669-party-role-management/) Open API
  - Party role management for authorization
  - Access control based on party roles

## Component Architecture

### Microservices

The implementation consists of **{N}** microservices:

- **{Service 1 Name}**: {Purpose and responsibilities}
  - Port: `{port}`
  - API: `{api-path}`
  
- **{Service 2 Name}**: {Purpose and responsibilities}
  - Port: `{port}`
  - API: `{api-path}`

- **{Service 3 Name}**: {Purpose and responsibilities}
  - Port: `{port}`
  - API: `{api-path}`

<!-- Add more services as needed -->

### Component Structure

```
{component-directory}/
├── charts/                    # Helm chart for deployment
│   └── {component-name}/
├── {service-1}/              # Service 1 implementation
├── {service-2}/              # Service 2 implementation
├── component.yaml            # ODA Component specification
└── README.md                 # This file
```

## ODA Component Specification

This component follows the [ODA Component Specification](https://github.com/tmforum-oda/oda-component-specification) **{version}** (e.g., v1beta3, v1beta4, v1).

### Exposed APIs

The component exposes the following APIs through the Canvas:

| API Name | Specification | Implementation | Port | Path |
| -------- | ------------- | -------------- | ---- | ---- |
| {API 1} | TMF{number} | {Service name} | `{port}` | `{path}` |
| {API 2} | TMF{number} | {Service name} | `{port}` | `{path}` |

### Dependent APIs

The component depends on the following external APIs:

| API Name | Specification | Required | Purpose |
| -------- | ------------- | -------- | ------- |
| {API 1} | TMF{number} | Yes/No | {Why needed} |

### Published Events

<!-- If component publishes events -->

| Event Type | Topic | Description |
| ---------- | ----- | ----------- |
| {Event 1} | `{topic-name}` | {What triggers this event} |

### Subscribed Events

<!-- If component subscribes to events -->

| Event Type | Topic | Description |
| ---------- | ----- | ----------- |
| {Event 1} | `{topic-name}` | {How component responds} |

## Installation

### Prerequisites

- Kubernetes cluster (1.20+)
- Helm 3.x
- ODA Canvas installed with Component Operator

### Install Component

Deploy using Helm:

```bash
helm install {release-name} ./charts/{component-name} -n components
```

Or using the ODA Component envelope:

```bash
kubectl apply -f component.yaml -n components
```

### Verify Installation

Check component status:

```bash
kubectl get component {component-name} -n components
kubectl describe component {component-name} -n components
```

Verify all services are running:

```bash
kubectl get pods -n components -l app={component-name}
kubectl get svc -n components -l app={component-name}
```

Check exposed APIs:

```bash
kubectl get exposedapi -n components -l oda.tmforum.org/componentName={component-name}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
| -------- | ----------- | ------- | -------- |
| `{VAR_NAME}` | {Description} | `{default}` | Yes/No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `{ANOTHER_VAR}` | {Description} | `{default}` | Yes/No |

### Helm Values

Key configuration parameters in `values.yaml`:

```yaml
# Component metadata
component:
  name: {component-name}
  version: {version}
  
# Service configuration
{service1}:
  replicas: {number}
  image:
    repository: {image-repo}
    tag: {tag}
  
# Resource limits
resources:
  limits:
    cpu: {cpu-limit}
    memory: {memory-limit}
```

### Advanced Configuration

#### Identity Management

Configure identity management integration:

```yaml
security:
  identityManagement:
    enabled: true
    realm: {realm-name}
```

#### API Gateway

Configure API Gateway settings:

```yaml
apis:
  gateway:
    type: istio  # or kong, apisix
    domain: {domain}
```

## Testing

### Unit Tests

This component is used in the following BDD test scenarios:

- **{UC-ID}-F{feature-number}**: [{Feature Name}](../features/{UC-ID}-F{feature-number}-{name}.feature)
  - Tests: {What aspect is tested}

### Manual Testing

#### Test Core APIs

```bash
# Get exposed API endpoint
kubectl get exposedapi {api-name} -n components -o jsonpath='{.spec.url}'

# Test API endpoint (example)
curl -X GET http://{endpoint}/{api-path}
```

#### Test Management APIs

```bash
# Check metrics endpoint
kubectl port-forward -n components svc/{service-name} 8080:8080
curl http://localhost:8080/metrics
```

### Test Data

<!-- If component includes test data -->

The component includes sample data for testing:

- {Data type 1}: Located in `{path}`
- {Data type 2}: Located in `{path}`

## Troubleshooting

### Common Issues

#### Issue 1: Component Not Ready

**Symptoms**:
- Component status shows "NotReady"
- Pods in CrashLoopBackOff

**Solution**:
```bash
# Check pod logs
kubectl logs -n components -l app={component-name}

# Check events
kubectl get events -n components --field-selector involvedObject.name={component-name}
```

#### Issue 2: APIs Not Exposed

**Symptoms**:
- ExposedAPI resources not created
- Cannot access APIs through gateway

**Solution**:
```bash
# Verify Component Operator is running
kubectl get pods -n canvas -l app=component-operator

# Check component specification
kubectl get component {component-name} -n components -o yaml
```

### Debug Mode

Enable debug logging:

```yaml
# values.yaml
{serviceName}:
  env:
    LOG_LEVEL: DEBUG
```

Redeploy with debug enabled:

```bash
helm upgrade {release-name} ./charts/{component-name} -n components -f debug-values.yaml
```

## Uninstalling

Remove the component:

```bash
# Using Helm
helm uninstall {release-name} -n components

# Using kubectl
kubectl delete component {component-name} -n components
```

Clean up remaining resources:

```bash
kubectl delete all -n components -l app={component-name}
```

## Related Documentation

- **ODA Component Specification**: [GitHub](https://github.com/tmforum-oda/oda-component-specification)
- **Test Execution Guide**: [Executing-tests.md](../Executing-tests.md)
- **Use Cases**: 
  - [{UC-ID}: {Related Use Case}](../../usecase-library/{UC-ID}-{name}.md)
- **Canvas Design**: [Canvas-design.md](../../Canvas-design.md)

## Contributing

For information about contributing to test components, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

## License

This test component is part of the ODA Canvas project. See [LICENSE](../../LICENSE) for details.
