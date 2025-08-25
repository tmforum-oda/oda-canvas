# PDB Management Operator - Operational Runbook

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Deployment](#installation--deployment)
4. [Monitoring & Observability](#monitoring--observability)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance & Upgrades](#maintenance--upgrades)
7. [Emergency Procedures](#emergency-procedures)
8. [Performance Tuning](#performance-tuning)
9. [Security](#security)
10. [Disaster Recovery](#disaster-recovery)

## Overview

The PDB Management Operator is a Kubernetes operator that automatically manages Pod Disruption Budgets (PDBs) for deployments based on annotations and policies. It provides three enforcement modes: strict, flexible, and advisory.

### Key Features

- **Dual Configuration Model**: Supports both annotation-based and policy-based configuration
- **Policy Enforcement**: Three modes (strict, flexible, advisory) with priority resolution
- **Maintenance Windows**: Automatic PDB suspension during maintenance windows
- **Comprehensive Observability**: Metrics, tracing, and structured logging
- **Performance Optimized**: Caching layer and adaptive circuit breaker

## Architecture

### Components

1. **AvailabilityPolicy Controller**: Manages custom CRDs and policy enforcement
2. **Deployment Controller**: Watches deployments and creates/updates PDBs
3. **PDB Controller**: Manages PDB lifecycle and consistency
4. **Webhook Server**: Validates and defaults AvailabilityPolicy CRDs
5. **Cache Layer**: Optimizes performance with policy caching
6. **Circuit Breaker**: Adaptive client for API call resilience

### Data Flow

```
Deployment Created/Updated
         ↓
   Check Annotations
         ↓
   Apply Policies (if any)
         ↓
   Create/Update PDB
         ↓
   Record Metrics & Events
```

## Installation & Deployment

### Prerequisites

- Kubernetes 1.21+
- cert-manager (for webhook TLS)
- Prometheus (for metrics)
- OpenTelemetry Collector (for tracing)

### Quick Start

```bash
# Deploy to canvas namespace
kubectl apply -k config/default/

# Verify installation
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management
kubectl get crd availabilitypolicies.availability.oda.tmforum.org
```

### Production Deployment

```bash
# 1. Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 2. Deploy with webhooks and TLS
kubectl apply -k config/certmanager/
kubectl apply -k config/webhook/
kubectl apply -k config/default/

# 3. Verify webhook certificates
kubectl get certificate -n canvas
kubectl get validatingwebhookconfiguration
kubectl get mutatingwebhookconfiguration
```

### Configuration Options

| Flag                          | Default | Description                    |
| ----------------------------- | ------- | ------------------------------ |
| `--enable-webhook`            | `true`  | Enable admission webhooks      |
| `--webhook-port`              | `9443`  | Webhook server port            |
| `--max-concurrent-reconciles` | `5`     | Max concurrent reconciliations |
| `--enable-tracing`            | `true`  | Enable OpenTelemetry tracing   |
| `--log-level`                 | `info`  | Log level (debug, info, error) |

## Monitoring & Observability

### Metrics

The operator exposes Prometheus metrics on port 8443:

```bash
# Port forward to access metrics
kubectl port-forward -n canvas svc/controller-manager-metrics-service 8443:8443

# Query metrics
curl -k https://localhost:8443/metrics
```

#### Key Metrics

- `pdb_management_reconciliations_total`: Total reconciliation attempts
- `pdb_management_pdb_created_total`: PDBs created
- `pdb_management_pdb_updated_total`: PDBs updated
- `pdb_management_policy_cache_hits`: Cache hit rate
- `pdb_management_reconciliation_duration_seconds`: Reconciliation latency

### Logging

The operator uses structured JSON logging with trace correlation:

```bash
# View operator logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management -f

# Filter by trace ID
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | jq 'select(.trace_id)'
```

#### Log Levels

- `debug`: Detailed reconciliation steps
- `info`: Normal operations and state changes
- `error`: Errors and failures

### Tracing

OpenTelemetry tracing is enabled by default:

```bash
# View traces in Jaeger/Zipkin
# Configure your tracing backend to collect from otel-collector
```

### Health Checks

```bash
# Check operator health
kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management -o wide

# Check readiness
kubectl get endpoints -n canvas controller-manager-metrics-service
```

## Troubleshooting

### Common Issues

#### 1. PDB Not Created

**Symptoms**: Deployment has annotations but no PDB is created

**Diagnosis**:

```bash
# Check operator logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i "deployment"

# Check deployment annotations
kubectl get deployment <name> -o yaml | grep -A5 -B5 annotations

# Check for errors
kubectl get events -n canvas --sort-by='.lastTimestamp'
```

**Solutions**:

- Verify annotations are correct: `pdb-management.oda.tmforum.org/availability-class`
- Check if policies are blocking creation
- Verify operator has RBAC permissions

#### 2. Webhook Failures

**Symptoms**: CRD operations fail with webhook errors

**Diagnosis**:

```bash
# Check webhook service
kubectl get svc -n canvas webhook-service

# Check webhook certificates
kubectl get certificate -n canvas serving-cert

# Check webhook logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i webhook
```

**Solutions**:

- Verify cert-manager is installed and running
- Check certificate validity: `kubectl describe certificate serving-cert -n canvas`
- Restart operator if certificates are invalid

#### 3. High Memory Usage

**Symptoms**: Operator pods using excessive memory

**Diagnosis**:

```bash
# Check resource usage
kubectl top pods -n canvas -l app.kubernetes.io/name=pdb-management

# Check cache statistics
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i "cache"
```

**Solutions**:

- Increase memory limits in deployment
- Reduce cache size or TTL
- Check for memory leaks in logs

#### 4. Slow Reconciliation

**Symptoms**: PDBs take long time to be created/updated

**Diagnosis**:

```bash
# Check reconciliation metrics
curl -k https://localhost:8443/metrics | grep reconciliation_duration

# Check API server latency
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management | grep -i "circuit"
```

**Solutions**:

- Increase `--max-concurrent-reconciles`
- Check API server performance
- Verify network connectivity

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Patch deployment to enable debug logging
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/2", "value": "--log-level=debug"}]'
```

### Emergency Access

If operator is completely down:

```bash
# Manual PDB creation (emergency only)
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: emergency-pdb
  namespace: <namespace>
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: <app-name>
EOF
```

## Maintenance & Upgrades

### Backup Procedures

Before upgrades, backup critical resources:

```bash
# Backup CRDs
kubectl get crd availabilitypolicies.availability.oda.tmforum.org -o yaml > backup-crd.yaml

# Backup policies
kubectl get availabilitypolicy --all-namespaces -o yaml > backup-policies.yaml

# Backup operator configuration
kubectl get deployment controller-manager -n canvas -o yaml > backup-deployment.yaml
```

### Upgrade Procedures

#### Rolling Update (Recommended)

```bash
# 1. Backup current state
kubectl get availabilitypolicy --all-namespaces -o yaml > pre-upgrade-policies.yaml

# 2. Update operator image
kubectl set image deployment/controller-manager -n canvas manager=<new-image>

# 3. Monitor upgrade
kubectl rollout status deployment/controller-manager -n canvas

# 4. Verify functionality
kubectl get pdb --all-namespaces
```

#### Blue-Green Deployment

```bash
# 1. Deploy new version to different namespace
kubectl apply -k config/default/ -n canvas-new

# 2. Verify new version works
kubectl get pods -n canvas-new

# 3. Switch traffic
kubectl patch svc webhook-service -n canvas -p '{"spec":{"selector":{"app.kubernetes.io/name":"pdb-management-new"}}}'

# 4. Remove old deployment
kubectl delete deployment controller-manager -n canvas
```

### Configuration Changes

#### Update Resource Limits

```bash
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources", "value": {"limits": {"cpu": "1000m", "memory": "1Gi"}, "requests": {"cpu": "200m", "memory": "512Mi"}}}]'
```

#### Update Concurrency Settings

```bash
kubectl patch deployment controller-manager -n canvas --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/3", "value": "--max-concurrent-reconciles=10"}]'
```

## Emergency Procedures

### Operator Down

1. **Immediate Actions**:

   ```bash
   # Check operator status
   kubectl get pods -n canvas -l app.kubernetes.io/name=pdb-management

   # Check for crash loops
   kubectl describe pod -n canvas -l app.kubernetes.io/name=pdb-management
   ```

2. **Restart Operator**:

   ```bash
   kubectl delete pods -n canvas -l app.kubernetes.io/name=pdb-management
   ```

3. **Manual PDB Management** (if needed):
   ```bash
   # Create PDBs manually for critical deployments
   kubectl apply -f emergency-pdbs.yaml
   ```

### Webhook Failures

1. **Disable Webhooks Temporarily**:

   ```bash
   kubectl delete validatingwebhookconfiguration availabilitypolicy-validating-webhook-configuration
   kubectl delete mutatingwebhookconfiguration availabilitypolicy-mutating-webhook-configuration
   ```

2. **Fix Certificate Issues**:

   ```bash
   kubectl delete certificate serving-cert -n canvas
   kubectl apply -f config/certmanager/certificate.yaml
   ```

3. **Re-enable Webhooks**:
   ```bash
   kubectl apply -f config/webhook/
   ```

### Data Corruption

1. **Restore from Backup**:

   ```bash
   kubectl apply -f backup-policies.yaml
   kubectl apply -f backup-crd.yaml
   ```

2. **Reconcile All Resources**:
   ```bash
   # Trigger reconciliation for all deployments
   kubectl annotate deployment --all pdb-management.oda.tmforum.org/reconcile=true
   ```

## Performance Tuning

### Resource Optimization

#### Memory Tuning

```yaml
# Recommended memory settings for different cluster sizes
# Small cluster (< 100 deployments)
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "100m"

# Large cluster (> 500 deployments)
resources:
  limits:
    memory: "2Gi"
    cpu: "1000m"
  requests:
    memory: "1Gi"
    cpu: "500m"
```

#### Cache Tuning

```go
// Cache configuration for different workloads
// High-traffic clusters
cache := NewPolicyCache(500, 10*time.Minute)

// Low-traffic clusters
cache := NewPolicyCache(100, 5*time.Minute)
```

### Concurrency Tuning

```bash
# Adjust based on cluster size and API server capacity
# Small clusters
--max-concurrent-reconciles=3

# Large clusters
--max-concurrent-reconciles=10
```

### Network Tuning

```bash
# Circuit breaker settings for different network conditions
# Stable networks
--circuit-breaker-threshold=5
--circuit-breaker-timeout=30s

# Unstable networks
--circuit-breaker-threshold=3
--circuit-breaker-timeout=60s
```

## Security

### RBAC Best Practices

```yaml
# Minimal RBAC for operator
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pdb-management-operator
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### Network Policies

```yaml
# Restrict operator network access
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pdb-management-network-policy
  namespace: canvas
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: pdb-management
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: TCP
          port: 8443
```

### Pod Security

The operator already implements restricted security context:

```yaml
securityContext:
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - "ALL"
```

## Disaster Recovery

### Backup Strategy

#### Automated Backups

```bash
#!/bin/bash
# backup-operator.sh
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/pdb-management/$DATE"

mkdir -p $BACKUP_DIR

# Backup CRDs
kubectl get crd availabilitypolicies.availability.oda.tmforum.org -o yaml > $BACKUP_DIR/crd.yaml

# Backup all policies
kubectl get availabilitypolicy --all-namespaces -o yaml > $BACKUP_DIR/policies.yaml

# Backup operator configuration
kubectl get deployment controller-manager -n canvas -o yaml > $BACKUP_DIR/deployment.yaml

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
```

#### Recovery Procedures

```bash
# 1. Restore CRDs
kubectl apply -f backup/crd.yaml

# 2. Restore policies
kubectl apply -f backup/policies.yaml

# 3. Restore operator
kubectl apply -f backup/deployment.yaml

# 4. Verify recovery
kubectl get availabilitypolicy --all-namespaces
kubectl get pdb --all-namespaces
```

### Multi-Cluster Recovery

For multi-cluster environments:

```bash
# Export from source cluster
kubectl config use-context source-cluster
kubectl get availabilitypolicy --all-namespaces -o yaml > policies-source.yaml

# Import to target cluster
kubectl config use-context target-cluster
kubectl apply -f policies-source.yaml
```

### Testing Recovery

```bash
# Test backup/restore procedure
kubectl create namespace test-recovery
kubectl apply -f test-policy.yaml -n test-recovery

# Create backup
./backup-operator.sh

# Simulate disaster
kubectl delete namespace test-recovery

# Restore and verify
kubectl apply -f backup/policies.yaml
kubectl get availabilitypolicy -n test-recovery
```

## Support Contacts

- **Primary On-Call**: [Contact Information]
- **Secondary On-Call**: [Contact Information]
- **Escalation**: [Contact Information]

## References

- [Kubernetes Operator Best Practices](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [OpenTelemetry Tracing](https://opentelemetry.io/docs/)
