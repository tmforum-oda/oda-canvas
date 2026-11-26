# Demo Examples for PDB Management Operator

This directory contains all the YAML examples extracted from the demo presentation script, organized by category for easier navigation. These files demonstrate the complete functionality of the PDB Management Operator.

## Directory Structure

```
demo/
├── deployments/       # Application deployments with various availability classes
├── services/          # Service-specific configurations
├── policies/          # Availability policies and templates  
├── security/          # Security-related examples and conflict scenarios
├── special-cases/     # Edge cases and invalid configurations
├── scripts/           # Utility scripts for testing
└── README.md          # This file
```

## Prerequisites

Before running the examples, ensure you have:

1. A Kubernetes cluster with the PDB Management Operator installed
2. `kubectl` configured to connect to your cluster
3. The `pdb-demo` namespace created (or modify the examples to use a different namespace)

```bash
# Create the demo namespace
kubectl create namespace pdb-demo
```

## Example Files by Category

### Deployments (`deployments/`)
Application deployments with various availability classes:

- **01-standard-app.yaml** - Basic deployment with standard availability (50%)
- **08-production-app.yaml** - Production deployment with annotation override attempt
- **10-backend-critical.yaml** - Deployment requesting higher availability than policy
- **11-backend-batch.yaml** - Deployment attempting lower availability than minimum
- **13-batch-processor.yaml** - Deployment with valid override reason
- **15-single-replica.yaml** - Single replica deployment (no PDB created)
- **16-temp-deployment.yaml** - Temporary deployment for cleanup testing
- **18-resource-hungry.yaml** - Resource-constrained deployment
- **23-autoscaling-app-with-hpa.yaml** - Deployment with HPA integration
- **24-canary-deployments.yaml** - Canary and stable deployment patterns

### Services (`services/`)
Service-specific configurations with various availability requirements:

- **02-payment-gateway.yaml** - High-availability deployment with comprehensive annotations (75%)
- **03-auth-service.yaml** - Mission-critical deployment (90%)
- **04-oauth2-proxy.yaml** - Security component that auto-upgrades from standard to high-availability
- **06-frontend-service.yaml** - Deployment that matches the frontend policy
- **20-security-service.yaml** - Deployment matching conflicting policies
- **22-payment-processor.yaml** - Financial service deployment with strict requirements

### Policies (`policies/`)
Availability policies and configuration templates:

- **05-frontend-policy.yaml** - Basic AvailabilityPolicy for frontend services
- **07-production-strict-policy.yaml** - Strict enforcement policy for production
- **09-backend-flexible-policy.yaml** - Flexible enforcement with minimum class
- **12-default-advisory-policy.yaml** - Advisory policy requiring override reasons
- **14-weekend-maintenance-policy.yaml** - Policy with weekend maintenance windows
- **21-financial-services-policy.yaml** - Complex enterprise policy with compliance features
- **25-multi-region-policies.yaml** - APAC and EU region policies
- **26-environment-policies.yaml** - Development and production environment policies
- **27-maintenance-demo-template.yaml** - Template for deployment-level maintenance windows

### Security (`security/`)
Security-related examples and conflict scenarios:

- **19-security-policies-conflict.yaml** - Conflicting policies for priority resolution

### Special Cases (`special-cases/`)
Edge cases and invalid configurations for testing:

- **17-invalid-class.yaml** - Deployment with invalid availability class

### Scripts (`scripts/`)
Utility scripts for testing and performance:

- **generate-perf-test.sh** - Script to create multiple deployments for performance testing

## Usage Instructions

### Running Individual Examples

```bash
# Apply a single example from a category
kubectl apply -f deployments/01-standard-app.yaml

# Or apply a policy
kubectl apply -f policies/05-frontend-policy.yaml

# Check the created PDB
kubectl get pdb -n pdb-demo standard-app-pdb -o yaml
```

### Running Demonstration Sequences

1. **Basic Availability Demo:**
```bash
kubectl apply -f deployments/01-standard-app.yaml
kubectl apply -f services/02-payment-gateway.yaml
kubectl apply -f services/03-auth-service.yaml
```

2. **Policy Enforcement Demo:**
```bash
kubectl apply -f policies/05-frontend-policy.yaml
kubectl apply -f services/06-frontend-service.yaml
kubectl apply -f policies/07-production-strict-policy.yaml
kubectl apply -f deployments/08-production-app.yaml
```

3. **Complete Policy Suite:**
```bash
# Apply all policies first
kubectl apply -f policies/05-frontend-policy.yaml
kubectl apply -f policies/07-production-strict-policy.yaml
kubectl apply -f policies/09-backend-flexible-policy.yaml
kubectl apply -f policies/12-default-advisory-policy.yaml

# Then apply deployments to see policy application
kubectl apply -f services/06-frontend-service.yaml
kubectl apply -f deployments/08-production-app.yaml
kubectl apply -f deployments/10-backend-critical.yaml
kubectl apply -f deployments/11-backend-batch.yaml
kubectl apply -f deployments/13-batch-processor.yaml
```

### Performance Testing

Use the provided script to create multiple deployments for performance testing:

```bash
# Create 30 test deployments
./scripts/generate-perf-test.sh 30

# Create custom number in different namespace
./scripts/generate-perf-test.sh 50 my-test-namespace
```

### Maintenance Window Testing

For maintenance window testing, you'll need to update the template with current timestamps:

```bash
# Get current time + 1 minute for window start
WINDOW_START=$(date -v+1M +%H:%M 2>/dev/null || date -d "+1 minute" +%H:%M)
WINDOW_END=$(date -v+5M +%H:%M 2>/dev/null || date -d "+5 minutes" +%H:%M)

# Update and apply the maintenance demo
sed "s/WINDOW_START/$WINDOW_START/g; s/WINDOW_END/$WINDOW_END/g" policies/27-maintenance-demo-template.yaml | kubectl apply -f -
```

## Monitoring and Verification

### Check Operator Logs
```bash
kubectl logs -n canvas deployment/pdb-management-controller-manager -f
```

### View Created PDBs
```bash
kubectl get pdb -n pdb-demo
kubectl get pdb -n pdb-demo -o yaml
```

### Check Events
```bash
kubectl get events -n pdb-demo --sort-by='.lastTimestamp'
```

### View Policies
```bash
kubectl get availabilitypolicy -n canvas
kubectl describe availabilitypolicy -n canvas
```

## Cleanup

To clean up all demo resources:

```bash
# Delete all deployments
kubectl delete deployment --all -n pdb-demo

# Delete all policies
kubectl delete availabilitypolicy --all -n canvas

# Delete namespace
kubectl delete namespace pdb-demo

# Clean up performance test deployments if created in different namespace
for i in {1..30}; do
  kubectl delete deployment perf-test-$i -n pdb-demo 2>/dev/null
done
```

## Example Workflows

### 1. Basic Demo Flow
```bash
# Create namespace
kubectl create namespace pdb-demo

# Basic availability classes
kubectl apply -f deployments/01-standard-app.yaml
kubectl apply -f services/02-payment-gateway.yaml
kubectl apply -f services/03-auth-service.yaml

# Security component intelligence
kubectl apply -f services/04-oauth2-proxy.yaml

# Verify PDBs created
kubectl get pdb -n pdb-demo
```

### 2. Policy Management Demo
```bash
# Apply policies
kubectl apply -f policies/05-frontend-policy.yaml
kubectl apply -f policies/07-production-strict-policy.yaml
kubectl apply -f policies/09-backend-flexible-policy.yaml

# Apply deployments to test policy application
kubectl apply -f services/06-frontend-service.yaml
kubectl apply -f deployments/08-production-app.yaml
kubectl apply -f deployments/10-backend-critical.yaml
kubectl apply -f deployments/11-backend-batch.yaml

# Check policy enforcement
kubectl get events -n pdb-demo | grep -E "(PolicyEnforced|BelowMinimum)"
```

### 3. Advanced Enterprise Demo
```bash
# Financial services policy
kubectl apply -f policies/21-financial-services-policy.yaml
kubectl apply -f services/22-payment-processor.yaml

# Multi-region policies
kubectl apply -f policies/25-multi-region-policies.yaml

# Environment-specific policies
kubectl apply -f policies/26-environment-policies.yaml
```

## Notes

- All examples use the `pdb-demo` namespace. Modify as needed for your environment.
- Maintenance window examples require timestamp adjustments for current testing.
- Performance test script creates deployments with basic configuration for load testing.
- Financial services examples include compliance-focused annotations and labels.
- Multi-region examples demonstrate timezone-aware maintenance windows.

These examples provide comprehensive coverage of all operator features demonstrated in the presentation script.