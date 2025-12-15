# {Operator Name}

<!-- 
Template for Operator README files in source/operators/ directory
Replace all {placeholder} values with actual content
Include PlantUML sequence diagram showing operator workflow
-->

## Overview

{Provide 2-3 paragraphs explaining:
- The purpose of this operator
- What resources it manages
- How it fits into the ODA Canvas architecture
- Key responsibilities and lifecycle processes
}

This operator follows the [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) and is part of the ODA Canvas modular architecture.

## Sequence Diagram

The following diagram shows how the {Operator Name} interacts with the Kubernetes API and other Canvas components:

![{operator-name}-sequence](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/main/source/operators/{operator-directory}/pumlFiles/{diagram-name}.puml)

[plantUML code](pumlFiles/{diagram-name}.puml)

<!-- If multiple scenarios, include additional diagrams -->

## Key Features

- **{Feature 1}**: {Description}
- **{Feature 2}**: {Description}
- **{Feature 3}**: {Description}

## Managed Resources

This operator manages the following Kubernetes resources:

### Custom Resources

- **{CustomResourceName}**: {Purpose and description}
  - API Group: `{api-group}`
  - Version: `{version}` (e.g., v1beta3)
  - Kind: `{Kind}`

### Created Resources

The operator creates and manages:

- `Deployment` - {Description of deployments created}
- `Service` - {Description of services created}
- `ConfigMap` - {Description of config maps created}
- `Secret` - {Description of secrets created if applicable}
- {Other resources}

## Architecture

### Operator Components

```
{Operator Name}
├── {Component 1} - {Purpose}
├── {Component 2} - {Purpose}
└── {Component 3} - {Purpose}
```

### Integration Points

- **Kubernetes API**: {How it interacts with K8s API}
- **Other Operators**: {Dependencies on or interactions with other operators}
- **External Services**: {Integration with API Gateway, Identity Management, etc.}

## Reference Implementation

The reference implementation is written in **{Language}** using **{Framework}**.

### Technology Stack

- **Language**: {Python/Java/Go/etc.}
- **Framework**: {KOPF/Operator SDK/Kubebuilder/Spring Boot/etc.}
- **Kubernetes Client**: {kubernetes-client library version}
- **Dependencies**: {Key libraries or frameworks}

### Project Structure

```
{operator-directory}/
├── {main-file}.{ext}          # Main operator logic
├── {handler-file}.{ext}       # Event handlers
├── {utility-dir}/             # Utility functions
├── requirements.txt           # Python dependencies (or equivalent)
├── Dockerfile                 # Container image definition
└── README.md                  # This file
```

## Development

### Prerequisites

- {Prerequisite 1, e.g., Python 3.9+}
- {Prerequisite 2, e.g., kubectl configured with cluster access}
- {Prerequisite 3, e.g., Access to Kubernetes cluster (local or remote)}

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/tmforum-oda/oda-canvas.git
cd oda-canvas/source/operators/{operator-directory}
```

2. Install dependencies:
```bash
# For Python/KOPF
pip install -r requirements.txt

# For Java/Maven
mvn clean install

# For Go
go mod download
```

3. Configure environment:
```bash
# Set required environment variables
export LOG_LEVEL=DEBUG
export {OTHER_ENV_VAR}={value}
```

### Interactive Development and Testing

Run the operator locally in standalone mode:

```bash
# For Python/KOPF
kopf run --namespace={namespace} --standalone ./{operator-file}.py

# For Java/Spring Boot
mvn spring-boot:run

# For Go
go run main.go
```

**Note**: Standalone mode allows testing operator logic without deploying to the cluster. The operator will watch the specified namespace and respond to resource events.

### Testing with Sample Resources

Create a test custom resource:

```bash
kubectl apply -f examples/{sample-resource}.yaml -n {namespace}
```

Watch operator logs:

```bash
# If running locally
# Logs appear in terminal

# If deployed to cluster
kubectl logs -n {namespace} deployment/{operator-deployment} -f
```

Verify expected resources are created:

```bash
kubectl get {resource-type} -n {namespace}
kubectl describe {resource-type} {resource-name} -n {namespace}
```

### Debugging

Enable debug logging:

```bash
# For KOPF
export LOG_LEVEL=DEBUG
kopf run --verbose --namespace={namespace} --standalone ./{operator-file}.py

# For others
{framework-specific debug command}
```

Common debugging commands:

```bash
# Check operator status
kubectl get pods -n {namespace} -l app={operator-name}

# View operator logs
kubectl logs -n {namespace} deployment/{operator-deployment}

# Check custom resource status
kubectl get {crd-name} -n {namespace}
kubectl describe {crd-name} {instance-name} -n {namespace}

# Check events
kubectl get events -n {namespace} --sort-by='.lastTimestamp'
```

## Build Automation

### Building Container Image

Build the Docker image:

```bash
docker build -t {image-name}:{tag} .
```

### Continuous Integration

This operator uses GitHub Actions for CI/CD:

- **Build**: Triggered on PR to master/main
- **Test**: Unit and integration tests run automatically
- **Release**: Docker images published to {registry} on version tags

See [.github/workflows/{workflow-file}.yaml](../../../.github/workflows/{workflow-file}.yaml) for details.

### Versioning

This operator follows semantic versioning:

- **Major**: Breaking changes to CRD or behavior
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

## Deployment

### Deploy with Helm

This operator is typically deployed as part of the Canvas installation:

```bash
helm install {release-name} ./charts/{chart-name} -n {namespace}
```

### Standalone Deployment

To deploy just this operator:

```bash
# Install CRDs
kubectl apply -f charts/{chart-name}/crds/

# Deploy operator
helm install {operator-release} ./charts/{chart-name} -n {namespace}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `{VAR_NAME}` | {Description} | `{default}` |

### Operator Parameters

Configured via Helm values or deployment manifest:

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `{param.name}` | {Description} | `{default}` |

## Use Cases

This operator implements the following use cases:

- [{UC-ID}: {Use Case Name}](../../../usecase-library/{UC-ID}-{name}.md)
  - {Brief description of operator's role in this use case}

## Related Documentation

- **Canvas Design**: [Canvas-design.md](../../../Canvas-design.md)
- **Operator Overview**: [source/operators/README.md](../README.md)
- **Helm Chart**: [charts/{chart-name}/](../../../charts/{chart-name}/)
- **Installation Guide**: [installation/README.md](../../../installation/README.md)

## Contributing

For information about contributing to this operator, see [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## License

This operator is part of the ODA Canvas project. See [LICENSE](../../../LICENSE) for details.
