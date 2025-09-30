# ODA Component Kubernetes to Registry Sync Tool

This tool reads ODA Component Custom Resources from Kubernetes clusters and synchronizes them with the Component Registry Service, following TM Forum ODA Canvas specifications.

## Features

- **Kubernetes Integration**: Reads ODA Component CRDs using the Kubernetes API
- **Registry Synchronization**: Creates/updates components in the Component Registry Service
- **Multi-Namespace Support**: Can read components from multiple Kubernetes namespaces
- **Dry-Run Mode**: Test synchronization without making actual changes
- **Flexible Configuration**: Supports both command-line arguments and YAML configuration files
- **Comprehensive Logging**: Detailed logging with verbose mode support
- **Error Handling**: Robust error handling and reporting
- **API Transformation**: Transforms Kubernetes exposedAPIs to Registry Service format

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to a Kubernetes cluster
- Component Registry Service running and accessible
- Proper RBAC permissions to read ODA Component Custom Resources

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Sync components from 'components' namespace to local registry service
python k8s_component_sync.py --registry-url http://localhost:8080 --namespace components

# Sync from multiple namespaces
python k8s_component_sync.py --registry-url http://localhost:8080 --namespace prod --namespace staging

# Dry run to see what would be synced
python k8s_component_sync.py --registry-url http://localhost:8080 --namespace components --dry-run

# Verbose logging
python k8s_component_sync.py --registry-url http://localhost:8080 --namespace components --verbose
```

### Configuration File

Create a `config.yaml` file:

```yaml
registry:
  url: http://localhost:8080
  timeout: 30
  
registry_name: kubernetes-cluster-registry
namespaces:
  - components
  - prod-components
  - staging-components
  
dry_run: false
verbose: true
```

Use with configuration file:

```bash
python k8s_component_sync.py --config config.yaml
```

## How It Works

### 1. Component Discovery
The tool uses the Kubernetes API to discover ODA Components across specified namespaces using the CustomObjectsApi to read components with group "oda.tmforum.org" and version "v1beta3".

### 2. Data Transformation
Kubernetes Component CRDs are transformed to Component Registry Service format:

- **Basic Information**: Extracts name, version, description from spec
- **Exposed APIs**: Transforms coreFunction, managementFunction, and securityFunction APIs
- **Labels**: Combines metadata labels with ODA-specific attributes
- **Metadata**: Adds sync timestamps and source information

### 3. Registry Synchronization
Components are synchronized with the Registry Service:

- **Registry Creation**: Ensures the target registry exists
- **Component Sync**: Creates new components or updates existing ones
- **API Management**: Handles exposed APIs as part of component data
- **Error Handling**: Comprehensive error reporting and recovery

## Integration with ODA Canvas

This tool is designed to integrate with the TM Forum ODA Canvas ecosystem:

- **Component Operators**: Works alongside Canvas Component operators
- **Registry Service**: Feeds the centralized Component Registry Service
- **Discovery**: Enables component discovery across Canvas deployments  
- **Governance**: Supports component lifecycle management

## Troubleshooting

### Common Issues

1. **"ODA Components CRD not found"**
   - Ensure ODA Canvas is installed in the cluster
   - Verify CRD exists: `kubectl get crd components.oda.tmforum.org`

2. **"Registry URL must be specified"**
   - Provide `--registry-url` or set in config file
   - Ensure Registry Service is accessible

3. **"Failed to create/verify registry"**
   - Check Registry Service is running
   - Verify network connectivity and authentication