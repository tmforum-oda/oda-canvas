# MCP Server Configuration

This directory contains Kubernetes manifests for deploying the Model Context Protocol (MCP) server functionality alongside the PDB Management Operator.

## Overview

The MCP server provides intelligent cluster analysis and policy recommendation capabilities through a standardized protocol that can be used by AI assistants like Claude.

## Components

### Core Manifests

- `service.yaml`: Kubernetes Service exposing the MCP server
- `configmap.yaml`: Configuration for MCP server settings and tool definitions  
- `network-policy.yaml`: Network security policies for MCP server access
- `kustomization.yaml`: Kustomize configuration to apply all resources

### Examples and Documentation

- `client-example.yaml`: ConfigMap with example client configurations and usage instructions
- `README.md`: This documentation file

## Deployment

### Option 1: Using Kustomize (Recommended)

Deploy the MCP server configuration alongside the operator:

```bash
# Deploy the full operator with MCP enabled
kubectl apply -k config/default/
kubectl apply -k config/mcp/
```

### Option 2: Direct Application

Apply the manifests directly:

```bash
kubectl apply -f config/mcp/
```

### Option 3: Integrate with Main Deployment

Add the MCP configuration to your main kustomization.yaml:

```yaml
resources:
- ../default
- ../mcp
```

## Configuration

### Enable/Disable MCP Server

The MCP server is controlled by command line flags:

```bash
# Enable MCP (default)
--enable-mcp=true
--mcp-bind-address=:8090

# Disable MCP
--enable-mcp=false
```

### Environment Variables

You can also use environment variables:

```bash
export ENABLE_MCP=true
export MCP_BIND_ADDRESS=:8090
```

## Security Considerations

### Network Policies

The included NetworkPolicy restricts access to:
- Pods in the `canvas` namespace
- Pods in the `monitoring` namespace  
- Pods with label `app.kubernetes.io/name: claude-mcp-client`

### Authentication

Currently, the MCP server runs without authentication for simplicity. For production deployments, consider:

1. **Network-level security**: Use NetworkPolicies and firewall rules
2. **Service mesh**: Implement mTLS with Istio/Linkerd
3. **API Gateway**: Add authentication via an API gateway
4. **Custom auth**: Modify the MCP server to include authentication

## Client Setup

### Claude Desktop

1. Port forward to the MCP service:
   ```bash
   kubectl port-forward -n canvas service/pdb-management-mcp-service 8090:8090
   ```

2. Configure Claude Desktop (see `client-example.yaml` for details):
   ```json
   {
     "mcpServers": {
       "pdb-management": {
         "command": "curl",
         "args": ["-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-", "http://localhost:8090/mcp"]
       }
     }
   }
   ```

### Other MCP Clients

The server exposes a standard HTTP endpoint at `/mcp` that accepts JSON-RPC 2.0 requests following the MCP specification.

## Available Tools

### Analysis Tools

- **analyze_cluster_availability**: Provides comprehensive analysis of PDB coverage across the cluster
- **analyze_workload_patterns**: Identifies deployment patterns and workload characteristics

### Recommendation Tools

- **recommend_availability_classes**: Suggests optimal availability classes based on workload analysis
- **recommend_policies**: Recommends AvailabilityPolicy configurations for better management

### Management Tools

- **create_availability_policy**: Creates new AvailabilityPolicy resources
- **update_deployment_annotations**: Modifies deployment annotations for availability management
- **simulate_policy_impact**: Previews the impact of policy changes before applying them

## Troubleshooting

### Check MCP Server Status

```bash
# Check if the service is running
kubectl get service -n canvas pdb-management-mcp-service

# Check operator logs for MCP messages
kubectl logs -n canvas deployment/pdb-management-controller-manager | grep mcp

# Test health endpoint
kubectl port-forward -n canvas service/pdb-management-mcp-service 8090:8090
curl http://localhost:8090/health
```

### Common Issues

1. **Connection Refused**: Ensure MCP is enabled and the operator is running
2. **Network Policy Blocks**: Check that your client pods have the correct labels
3. **Port Forward Fails**: Verify the service exists and has the correct port configuration

### Debug Mode

Enable debug logging to see detailed MCP operation:

```bash
kubectl patch deployment pdb-management-controller-manager -n canvas \
  --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": ["--leader-elect", "--log-level=debug", "--enable-mcp=true"]}]'
```

## Monitoring

### Metrics

The MCP server exposes Prometheus metrics on the main metrics port:

- `mcp_server_requests_total`: Total number of MCP requests
- `mcp_server_request_duration_seconds`: Request duration histogram
- `mcp_server_active_connections`: Number of active connections
- `mcp_tools_invocation_total`: Tool invocation counters

### Health Checks

Health endpoint: `GET /health`

```json
{
  "status": "healthy",
  "initialized": true,
  "timestamp": 1703123456
}
```

## Examples

See `client-example.yaml` for detailed examples of:
- Client configuration
- Example MCP requests
- Claude Desktop setup instructions