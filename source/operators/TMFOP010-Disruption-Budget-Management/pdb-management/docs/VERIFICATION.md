# Test Verification and Performance Testing Guide

This guide provides comprehensive verification steps for the PDB Management Operator, including test execution, performance testing, and troubleshooting.

## Quick Verification

### 1. Run Comprehensive Demo

```bash
# Run full demo with verification
./toolsforlocal/comprehensive-demo.sh

# Run quick test
./toolsforlocal/quick-test.sh
```

### 2. Monitor Live Logs

```bash
# Real-time log monitoring
./toolsforlocal/comprehensive-demo.sh --live-logs

# Audit trail
./toolsforlocal/comprehensive-demo.sh --audit

# Performance metrics
./toolsforlocal/comprehensive-demo.sh --performance
```

## Manual Test Execution Steps

### 1. Apply Test Manifests

```bash
# Apply all test cases
kubectl apply -f ./toolsforlocal/demo-test-manifests.yaml

# Wait for operator to process
sleep 10

# Verify PDBs created
kubectl get pdb -n pdb-demo-test
```

### 2. Verification Commands

```bash
# Test Case 1: Basic Standard Availability
kubectl get pdb basic-standard-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 50%

# Test Case 2: High Availability
kubectl get pdb high-availability-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 75%

# Test Case 3: Mission Critical
kubectl get pdb mission-critical-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 90%

# Test Case 4: Non-Critical
kubectl get pdb non-critical-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 25%

# Test Case 5: Security Component (Auto-Upgrade)
kubectl get pdb security-component-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 75% (boosted from standard)

# Test Case 6: Single Replica (should NOT exist)
kubectl get pdb single-replica-pdb -n pdb-demo-test
# Expected: NotFound error

# Test Case 7: Maintenance Window
kubectl get pdb maintenance-window-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 75%

# Test Case 8: Strict Policy (overrides annotation)
kubectl get pdb strict-demo-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 90% (policy overrides annotation)

# Test Case 9: Flexible Policy (higher accepted)
kubectl get pdb flexible-higher-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 90% (higher class accepted)

# Test Case 10: Flexible Policy (lower rejected)
kubectl get pdb flexible-lower-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 75% (lower class rejected, policy applied)

# Test Case 11: Advisory Policy (override accepted)
kubectl get pdb advisory-override-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 25% (override accepted)

# Test Case 12: Custom PDB Configuration
kubectl get pdb custom-demo-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 2 (absolute number)

# Verify policy status
kubectl get availabilitypolicy -n pdb-demo-test -o wide
```

### 3. Update Testing

```bash
# Test annotation update
kubectl annotate deployment basic-standard -n pdb-demo-test \
  oda.tmforum.org/availability-class=high-availability --overwrite

# Wait and verify PDB updated
sleep 5
kubectl get pdb basic-standard-pdb -n pdb-demo-test -o yaml | grep minAvailable
# Expected: 75%

# Test replica scaling
kubectl scale deployment basic-standard -n pdb-demo-test --replicas=1
sleep 5
kubectl get pdb basic-standard-pdb -n pdb-demo-test
# Expected: PDB should be deleted

kubectl scale deployment basic-standard -n pdb-demo-test --replicas=3
sleep 5
kubectl get pdb basic-standard-pdb -n pdb-demo-test
# Expected: PDB recreated
```

### 4. Event Verification

```bash
# Check events for a deployment
kubectl describe deployment basic-standard -n pdb-demo-test | grep Events -A 10

# Check operator events
kubectl get events -n pdb-demo-test --field-selector reason=PDBCreated
kubectl get events -n pdb-demo-test --field-selector reason=PolicyApplied
```

## Advanced Log Analysis

### 1. Trace Analysis

```bash
# Get trace ID from logs
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -r 'select(.trace.trace_id != null) | .trace.trace_id' | head -1

# Analyze specific trace
./toolsforlocal/comprehensive-demo.sh --trace <trace-id>
```

### 2. Audit Trail Analysis

```bash
# Show recent audit events
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg == "Audit log")' | \
  jq -r '"\(.ts) \(.details.action) \(.details.resource) [\(.details.result)]"'
```

### 3. Performance Analysis

```bash
# Show reconciliation durations
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.details.duration != null)' | \
  jq -r '"\(.resource.name // "unknown"): \(.details.duration)"' | \
  sort -k2 -n
```

## Performance Testing

### 1. Unified Performance Testing

```bash
# Run all performance tests
./toolsforlocal/unified-performance-test.sh --all

# Run specific tests
./toolsforlocal/unified-performance-test.sh --basic 100        # Basic performance test
./toolsforlocal/unified-performance-test.sh --cache            # Cache performance test
./toolsforlocal/unified-performance-test.sh --advanced 600     # Advanced performance test
./toolsforlocal/unified-performance-test.sh --circuit-breaker  # Circuit breaker test
./toolsforlocal/unified-performance-test.sh --rbac             # RBAC debug test

# Show results
./toolsforlocal/unified-performance-test.sh --results

# Cleanup
./toolsforlocal/unified-performance-test.sh --cleanup
```

### 2. Comprehensive Test Suite

```bash
./toolsforlocal/test-suite.sh
```

## Monitoring During Tests

### Prometheus Queries

If you have Prometheus installed:

```promql
# Reconciliation performance
histogram_quantile(0.95, rate(pdb_management_reconciliation_duration_seconds_bucket[5m]))

# PDB creation rate
rate(pdb_management_pdbs_created_total[1m])

# Error rate
rate(pdb_management_reconciliation_errors_total[1m])

# Cache hit rate
rate(pdb_management_cache_hits_total[5m]) /
(rate(pdb_management_cache_hits_total[5m]) + rate(pdb_management_cache_misses_total[5m]))

# Managed deployments by availability class
pdb_management_managed_deployments{availability_class="high-availability"}
pdb_management_managed_deployments{availability_class="mission-critical"}
pdb_management_managed_deployments{availability_class="standard"}
```

### Grafana Dashboard

Create a dashboard with these panels:

1. **Reconciliation Duration** (p50, p95, p99)
2. **PDB Operations Rate** (created, updated, deleted)
3. **Cache Hit Rate**
4. **Error Rate by Type**
5. **Operator Resource Usage** (CPU, Memory)
6. **Active Deployments by Availability Class**
7. **Policy Evaluation Performance**
8. **Circuit Breaker Status**

## Expected Performance Baselines

Based on the operator design:

| Metric             | Expected Value | Notes                |
| ------------------ | -------------- | -------------------- |
| Reconciliation p95 | <200ms         | For <200 deployments |
| Cache Hit Rate     | >80%           | After warm-up period |
| Memory Usage       | <150Mi         | For 200 deployments  |
| CPU Usage          | <100m          | Steady state         |
| PDB Creation Time  | <5s            | Per deployment       |
| Policy Evaluation  | <50ms          | With cache hit       |
| Log Processing     | <10ms          | Per log entry        |
| Trace Propagation  | <5ms           | Per span             |

## Unified Logging Verification

### 1. Log Structure Verification

```bash
# Verify structured JSON logs
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=10 | \
  jq -c 'select(.level != null)' | head -5
```

### 2. Trace Context Verification

```bash
# Verify trace propagation
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=50 | \
  jq -c 'select(.trace.trace_id != null)' | \
  jq -r '"\(.ts) Trace: \(.trace.trace_id) Span: \(.trace.span_id)"' | \
  head -10
```

### 3. Audit Log Verification

```bash
# Verify audit logs have trace context
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg == "Audit log")' | \
  jq -r '"\(.ts) \(.details.action) Trace: \(.trace.trace_id // "none")"'
```

## Troubleshooting Performance Issues

### 1. High Reconciliation Time

```bash
# Check cache hit rate
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg | contains("cache"))' | \
  jq -r '"\(.ts) \(.msg)"'

# Look for circuit breaker events
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg | contains("circuit"))' | \
  jq -r '"\(.ts) \(.msg)"'
```

### 2. High Memory Usage

```bash
# Check cache size
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg | contains("cache"))' | \
  jq -r '"\(.ts) \(.msg)"'

# Check for memory leaks
kubectl top pod -n canvas deployment/pdb-management-controller-manager
```

### 3. Slow PDB Creation

```bash
# Check operator logs for errors
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.level == "error")' | \
  jq -r '"\(.ts) \(.msg)"'

# Check webhook latency
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c 'select(.msg | contains("webhook"))' | \
  jq -r '"\(.ts) \(.msg)"'
```

### 4. Log Analysis Issues

```bash
# Check if jq is installed
which jq

# Verify log format
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=1 | jq .

# Check for malformed JSON
kubectl logs -n canvas deployment/pdb-management-controller-manager --tail=100 | \
  jq -c '.' 2>/dev/null | wc -l
```

## 🧹 Cleanup

### Clean Test Environment

```bash
# Clean demo environment
./toolsforlocal/comprehensive-demo.sh --cleanup

# Clean test environment
./toolsforlocal/quick-test.sh --cleanup

# Manual cleanup
kubectl delete namespace pdb-demo-test --wait=false
kubectl delete namespace pdb-demo-* --wait=false
```

## Related Documentation

- [Main README](../README.md)
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
- [Demo Tools README](../toolsforlocal/README.md)
