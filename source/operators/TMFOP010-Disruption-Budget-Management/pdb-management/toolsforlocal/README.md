# PDB Management Operator - Demo Tools

This directory contains comprehensive demo and testing tools for the PDB Management Operator.

## Quick Start

### 1. Run Comprehensive Demo

```bash
./comprehensive-demo.sh
```

This runs a full demo suite showcasing all operator features with live log monitoring.

### 2. Run Quick Test

```bash
./quick-test.sh
```

This applies test manifests and verifies all test cases quickly.

### 3. Monitor Live Logs

```bash
./comprehensive-demo.sh --live-logs
```

Real-time log monitoring with color-coded output.

## Available Scripts

### `comprehensive-demo.sh` - Main Demo Script

**Features:**

- Complete operator functionality demonstration
- All test cases with real-time verification
- Advanced log analysis capabilities
- Interactive trace analysis
- Performance metrics
- Audit trail monitoring

**Usage:**

```bash
# Run full demo
./comprehensive-demo.sh

# Monitor live logs
./comprehensive-demo.sh --live-logs

# Analyze specific trace
./comprehensive-demo.sh --trace <trace-id>

# Show audit trail
./comprehensive-demo.sh --audit

# Show performance metrics
./comprehensive-demo.sh --performance

# Cleanup demo environment
./comprehensive-demo.sh --cleanup

# Show help
./comprehensive-demo.sh --help
```

### `quick-test.sh` - Quick Test Script

**Features:**

- Fast test execution
- All test cases verification
- PDB status checking
- Expected vs actual results

**Usage:**

```bash
# Run quick test
./quick-test.sh

# Cleanup test environment
./quick-test.sh --cleanup

# Show help
./quick-test.sh --help
```

### `demo-test-manifests.yaml` - Test Manifests

**Contains:**

- All test cases in a single file
- Basic annotation tests
- Component function tests
- Policy-based tests
- Edge cases
- Complex scenarios
- Maintenance window tests

## Test Cases Covered

### 1. Basic Annotation Tests

- **Standard Availability** (50% minAvailable)
- **High Availability** (75% minAvailable)
- **Mission Critical** (90% minAvailable)
- **Non-Critical** (20% minAvailable)

### 2. Component Function Tests

- **Security Component** (Auto-upgrade from 50% to 75%)
- **Core Component** (Standard 50%)
- **Management Component** (Standard 50%)

### 3. Edge Cases

- **Single Replica** (No PDB created)
- **Maintenance Window** (With maintenance annotation)

### 4. Policy-Based Tests

- **Strict Enforcement** (Policy overrides annotation)
- **Flexible Enforcement** (Higher class accepted, lower rejected)
- **Advisory Enforcement** (Override with reason)
- **Custom PDB Configuration** (Absolute numbers)

### 5. Complex Scenarios

- **Multi-Criteria Policies** (Labels, namespaces, functions)
- **Maintenance Window Policies** (Time-based rules)

## Log Analysis Features

### Live Log Monitoring

- Real-time log streaming
- Color-coded log levels
- Structured JSON parsing
- Trace context display

### Trace Analysis

- Follow specific trace IDs
- Complete request flow
- Performance timing
- Error tracking

### Audit Trail

- All audit events
- Success/failure tracking
- Duration metrics
- Policy decisions

### Performance Metrics

- Reconciliation timing
- Cache performance
- Resource usage
- Error rates

## Demo Scenarios

### Scenario 1: Basic Usage

```bash
./quick-test.sh
```

Shows basic annotation-based PDB creation.

### Scenario 2: Policy Enforcement

```bash
./comprehensive-demo.sh
```

Demonstrates policy-based configuration with different enforcement levels.

### Scenario 3: Advanced Monitoring

```bash
./comprehensive-demo.sh --live-logs
```

Real-time monitoring of operator behavior.

### Scenario 4: Troubleshooting

```bash
./comprehensive-demo.sh --trace <trace-id>
./comprehensive-demo.sh --audit
```

Advanced debugging and analysis.

## Configuration

### Environment Variables

- `DEMO_NAMESPACE`: Namespace for demo (auto-generated)
- `OPERATOR_NAMESPACE`: Operator namespace (default: canvas)
- `LOG_FILE`: Log output file (auto-generated)

### Prerequisites

- Kubernetes cluster with operator deployed
- `kubectl` configured
- `jq` installed for JSON parsing
- Operator running in `canvas` namespace

## Performance Testing

### Unified Performance Testing

```bash
# Run all performance tests
./unified-performance-test.sh --all

# Run specific tests
./unified-performance-test.sh --basic 100        # Basic performance test
./unified-performance-test.sh --cache            # Cache performance test
./unified-performance-test.sh --advanced 600     # Advanced performance test
./unified-performance-test.sh --circuit-breaker  # Circuit breaker test
./unified-performance-test.sh --rbac             # RBAC debug test

# Show results
./unified-performance-test.sh --results

# Cleanup
./unified-performance-test.sh --cleanup
```

**Available Tests:**

- **Basic Performance**: Tests PDB creation performance with configurable deployment count
- **Cache Performance**: Tests policy cache hit/miss rates
- **Advanced Performance**: Long-running test with dynamic load generation
- **Circuit Breaker**: Tests circuit breaker functionality under API server stress
- **RBAC Debug**: Comprehensive RBAC permission analysis

## Cleanup

### Clean Demo Environment

```bash
./comprehensive-demo.sh --cleanup
```

### Clean Test Environment

```bash
./quick-test.sh --cleanup
```

### Manual Cleanup

```bash
kubectl delete namespace pdb-demo-*
kubectl delete namespace pdb-test
```

## Log Examples

### Structured Log Output

```json
{
  "level": "info",
  "ts": "2025-07-06T09:50:22.454304592Z",
  "msg": "Starting reconciliation",
  "controller": {
    "type": "deployment-pdb",
    "name": "deployment-controller"
  },
  "resource": {
    "namespace": "components",
    "name": "tmf620-productcatalog"
  },
  "trace": {
    "trace_id": "8d23229b-2136-43e4-b000-c79e2d4f35ce",
    "span_id": "a1b2c3d4e5f6"
  },
  "correlationID": "ec083d00-2de8-492e-9697-0808e216df04"
}
```

### Audit Log Output

```json
{
  "level": "info",
  "ts": "2025-07-06T09:50:22.454304592Z",
  "msg": "Audit log",
  "audit": {
    "action": "PDB_CREATED",
    "resource": "tmf620-productcatalog-pdb",
    "result": "success",
    "metadata": {
      "availabilityClass": "high-availability",
      "enforcement": "flexible",
      "policy": "production-policy",
      "durationMs": 245
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Operator not found**

   ```bash
   kubectl get deployment -n canvas pdb-management-controller-manager
   ```

2. **Test namespace exists**

   ```bash
   kubectl delete namespace pdb-demo-test --wait=false
   ```

3. **Log parsing errors**

   ```bash
   # Check if jq is installed
   which jq
   ```

4. **Permission issues**
   ```bash
   # Check RBAC
   kubectl auth can-i create pdb
   ```

### Debug Commands

```bash
# Check operator status
kubectl get pods -n canvas

# Check operator logs
kubectl logs -n canvas deployment/pdb-management-controller-manager

# Check PDBs
kubectl get pdb --all-namespaces

# Check policies
kubectl get availabilitypolicy --all-namespaces
```

## Related Documentation

- [Main README](../../README.md)
- [Technical Documentation](../../docs/TECHNICAL_DOCUMENTATION.md)
- [Verification Guide](../../docs/VERIFICATION.md)
