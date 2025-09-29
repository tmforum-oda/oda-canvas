# Custom-Resource Collector

Python application using the Kubernetes API to read Custom-Resources and update entries in the Component-Registry Microservice

## Overview

The Custom-Resource Collector is a Python application that monitors ODA (Open Digital Architecture) Component Custom Resources in Kubernetes and automatically synchronizes them with the Component Registry microservice. It provides real-time synchronization, monitoring, and management of ODA Components across your Kubernetes cluster.

## Features

- **Real-time Monitoring**: Watches Kubernetes ODA Component Custom Resources for changes
- **Automatic Synchronization**: Syncs components, exposed APIs, and labels with Component Registry
- **Batch Processing**: Efficient processing of multiple components
- **Health Monitoring**: Prometheus metrics and health checks
- **Fault Tolerance**: Retry mechanisms and error handling
- **CLI Interface**: Command-line tools for testing and management
- **Kubernetes Native**: Designed to run as a Kubernetes deployment

## Architecture

```
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Kubernetes    │    │  Custom-Resource    │    │   Component         │
│  ODA Components │◄──►│     Collector       │◄──►│    Registry         │
│   (CRDs)        │    │                     │    │   Microservice      │
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
                                │
                                ▼
                       ┌─────────────────────┐
                       │   Prometheus        │
                       │    Metrics          │
                       └─────────────────────┘
```

## Components

### Core Modules

1. **kubernetes_client.py** - Kubernetes API client for monitoring ODA Components
2. **registry_client.py** - Component Registry API client for synchronization
3. **synchronizer.py** - Orchestrates synchronization between Kubernetes and Registry
4. **monitoring.py** - Prometheus metrics and health monitoring
5. **models.py** - Data models for ODA Components and Registry entities
6. **config.py** - Configuration management
7. **main.py** - Main application orchestrator
8. **cli.py** - Command-line interface

### Key Features

- **Event-Driven**: Responds to Kubernetes events (ADDED, MODIFIED, DELETED)
- **Full Synchronization**: Periodic full sync for consistency
- **Label Management**: Automatic creation and mapping of labels
- **API Status Tracking**: Monitors ExposedAPI status changes
- **Orphan Cleanup**: Removes stale entries from registry

## Installation

### Prerequisites

- Python 3.11+
- Kubernetes cluster with ODA Component CRDs
- Component Registry microservice running
- Appropriate RBAC permissions

### Local Development

1. **Clone and setup:**
    ```bash
    cd custom-resource-collector
    pip install -r requirements.txt
    ```

2. **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

3. **Test connections:**
    ```bash
    python -m cli test
    ```

4. **Run locally:**
    ```bash
    python -m cli run
    ```

### Docker Deployment

1. **Build image:**
    ```bash
    docker build -t oda-canvas/custom-resource-collector:latest .
    ```

2. **Run container:**
    ```bash
    docker run -d \
      --name collector \
      -p 8080:8080 \
      -e COMPONENT_REGISTRY_URL=http://registry:8000 \
      -e KUBERNETES_IN_CLUSTER=false \
      -v ~/.kube/config:/home/collector/.kube/config:ro \
      oda-canvas/custom-resource-collector:latest
    ```

### Kubernetes Deployment

1. **Deploy to cluster:**
    ```bash
    kubectl apply -f kubernetes/deployment.yaml
    ```

2. **Check status:**
    ```bash
    kubectl get pods -n oda-canvas -l app=custom-resource-collector
    kubectl logs -n oda-canvas -l app=custom-resource-collector
    ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COMPONENT_REGISTRY_URL` | Component Registry base URL | `http://localhost:8000` |
| `COMPONENT_REGISTRY_API_KEY` | API key for authentication | - |
| `KUBERNETES_NAMESPACE` | Kubernetes namespace to monitor | `default` |
| `KUBERNETES_IN_CLUSTER` | Running inside cluster | `false` |
| `ODA_COMPONENT_GROUP` | ODA Component API group | `oda.tmforum.org` |
| `ODA_COMPONENT_VERSION` | ODA Component API version | `v1beta3` |
| `SYNC_INTERVAL` | Full sync interval (seconds) | `60` |
| `MONITORING_ENABLED` | Enable Prometheus metrics | `true` |
| `MONITORING_PORT` | Metrics server port | `8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

### ODA Component Mapping

The collector maps ODA Components to Registry entities:

- **Component** → Registry Component with labels
- **ExposedAPIs** → Registry ExposedAPIs with status tracking
- **Labels** → Registry Labels (key-value pairs)
- **Metadata** → Additional labels (team, version, domain)

## CLI Usage

### Available Commands

```bash
# Run the collector
python -m cli run

# Test connections
python -m cli test

# List ODA Components
python -m cli list --namespace oda-components

# Manually sync a component
python -m cli sync my-component --namespace default
```

### Examples

```bash
# Test all connections
python -m cli test

# List components in specific namespace
python -m cli list --namespace oda-canvas

# Sync specific component
python -m cli sync prodcat --namespace oda-components

# Run with debug logging
python -m cli run --log-level DEBUG
```

## Monitoring

### Prometheus Metrics

The collector exposes Prometheus metrics on port 8080:

- `oda_collector_components_total` - Total components processed
- `oda_collector_components_current` - Current components monitored
- `oda_collector_apis_total` - Total APIs processed
- `oda_collector_kubernetes_events_total` - Kubernetes events processed
- `oda_collector_registry_api_calls_total` - Registry API calls
- `oda_collector_sync_duration_seconds` - Sync operation duration

### Health Checks

Health status available at `/metrics` endpoint:

```bash
curl http://localhost:8080/metrics
```

## Development

### Project Structure

```
custom-resource-collector/
├── __init__.py              # Package initialization
├── main.py                  # Main application
├── cli.py                   # Command-line interface
├── config.py                # Configuration management
├── models.py                # Data models
├── kubernetes_client.py     # Kubernetes API client
├── registry_client.py       # Registry API client  
├── synchronizer.py          # Synchronization engine
├── monitoring.py            # Metrics and monitoring
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container image
├── .env.example            # Example configuration
└── kubernetes/
    └── deployment.yaml     # Kubernetes manifests
```

### Adding New Features

1. **Extend models** in `models.py` for new data structures
2. **Update synchronizer** in `synchronizer.py` for new sync logic
3. **Add metrics** in `monitoring.py` for observability
4. **Update CLI** in `cli.py` for new commands

## Integration with ODA Canvas

The collector integrates seamlessly with the ODA Canvas ecosystem:

1. **Monitors** ODA Component Custom Resources
2. **Syncs** with Component Registry microservice
3. **Tracks** ExposedAPI lifecycle and status
4. **Manages** component metadata and labels
5. **Provides** observability through metrics

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   ```bash
   python -m cli test  # Test all connections
   ```

2. **RBAC Permissions**:
   ```bash
   kubectl auth can-i get components.oda.tmforum.org --as=system:serviceaccount:oda-canvas:custom-resource-collector
   ```

3. **Component Registry Issues**:
   ```bash
   curl http://registry-url:8000/health
   ```

4. **Missing CRDs**:
   ```bash
   kubectl get crd components.oda.tmforum.org
   ```

### Logs and Debugging

```bash
# View collector logs
kubectl logs -n oda-canvas -l app=custom-resource-collector -f

# Check metrics
curl http://collector-service:8080/metrics

# Verify component sync
python -m cli sync <component-name>
```

## Security

- **RBAC**: Minimal required permissions for ODA Components
- **Non-root**: Runs as non-root user in container
- **Read-only**: Read-only filesystem in container
- **Network**: Only requires access to Kubernetes API and Registry

## License

Part of the TM Forum ODA Canvas project - see main project license.