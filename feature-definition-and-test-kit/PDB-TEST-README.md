# PDB Management Operator BDD Tests - Local Testing Guide

This guide explains how to run the PDB Management Operator BDD tests locally before committing changes.

## Prerequisites

1. **Kubernetes Cluster**: Access to a Kubernetes cluster (local or remote)

   ```bash
   kubectl cluster-info
   ```

2. **ODA Canvas Deployed**: The Canvas must be installed with the PDB operator

   ```bash
   kubectl get pods -n canvas
   kubectl get deployment -n canvas canvas-pdb-management-operator
   ```

3. **Node.js and npm**: Required for running Cucumber tests
   ```bash
   node --version  # Should be v14 or higher
   npm --version   # Should be v6 or higher
   ```

## Setup

### 1. Install Dependencies

```bash
cd feature-definition-and-test-kit
npm install
```

### 2. Set Environment Variables

Create a `.env` file or export these variables:

```bash
export KEYCLOAK_USER=admin
export KEYCLOAK_PASSWORD=admin
export KEYCLOAK_BASE_URL=http://localhost:8080
export KEYCLOAK_REALM=master
```

Or source from the test environment file:

```bash
cp .env.test .env
source .env
```

### 3. Verify PDB Operator is Running

```bash
# Check operator deployment
kubectl get deployment -n canvas canvas-pdb-management-operator

# Check operator logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management --tail=20

# Check CRDs are installed
kubectl get crd | grep availability
```

## Running Tests

### Quick Test Commands

```bash
# Dry-run (syntax check only - no actual execution)
npm run test:pdb:dry-run

# Run all PDB tests
npm run test:pdb

# Run specific feature tests
npm run test:pdb:annotation    # Annotation-based PDB management
npm run test:pdb:policy        # Policy-based PDB management
npm run test:pdb:webhook       # Webhook validation
npm run test:pdb:edge          # Edge cases

# Run locally without publishing to Cucumber Reports
npm run test:pdb:local
```

### Using the Test Script

A convenience script is provided for comprehensive testing:

```bash
# Make script executable (first time only)
chmod +x test-pdb-local.sh

# Run all tests with prerequisite checks
./test-pdb-local.sh all

# Run specific test suite
./test-pdb-local.sh annotation
./test-pdb-local.sh policy
./test-pdb-local.sh webhook
./test-pdb-local.sh edge

# Dry-run only
./test-pdb-local.sh dry-run
```

## Test Structure

The PDB BDD tests are organized into four feature files:

1. **UC017-F001-PDB-Management-Annotation-Based.feature**

   - Tests PDB creation from deployment annotations
   - Component function classification
   - Maintenance windows
   - Component name tracking

2. **UC017-F002-PDB-Management-Policy-Based.feature**

   - AvailabilityPolicy enforcement
   - Priority resolution
   - Enforcement modes (strict, flexible, advisory)
   - Custom PDB configurations

3. **UC017-F003-PDB-Management-Webhook-Validation.feature**

   - Webhook validation for policies
   - Default value handling
   - Immutable field validation
   - Configuration constraints

4. **UC017-F004-PDB-Management-Edge-Cases.feature**
   - Scaling scenarios
   - Operator restart recovery
   - Namespace deletion
   - Error handling

## Understanding Test Results

### Successful Test Output

```
44 scenarios (44 passed)
378 steps (378 passed)
2m15.123s (executing steps: 2m14.892s)
```

### Common Issues and Solutions

#### Issue: Operator Not Found

```
PDB Management Operator not deployed
```

**Solution**: Deploy the PDB operator using Helm:

```bash
helm upgrade --install canvas-oda charts/canvas-oda \
  --set pdb-management-operator.enabled=true
```

#### Issue: Components Namespace Missing

```
Error: namespaces "components" not found
```

**Solution**: Create the namespace:

```bash
kubectl create namespace components
```

#### Issue: Timeout Errors

```
Error: PDB was not created within 30000ms
```

**Solution**: The operator may be slow to respond. Increase timeouts in the test configuration or check operator logs:

```bash
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management --tail=50
```

#### Issue: Undefined Steps

```
2 scenarios (2 undefined)
5 steps (5 undefined)
```

**Solution**: Some step definitions may be missing. Check the dry-run output and add missing steps to PDBManagementSteps.js.

## Test Development

### Adding New Scenarios

1. Add scenarios to the appropriate feature file in `features/`
2. Run dry-run to identify missing steps:
   ```bash
   npm run test:pdb:dry-run
   ```
3. Implement missing steps in `features/step-definition/PDBManagementSteps.js`
4. Add utility functions to `resource-inventory-utils-kubernetes/` if needed

### Debugging Tests

Enable debug output by modifying step definitions:

```javascript
// Add console.log statements for debugging
console.log("Creating deployment:", deploymentName);
console.log("PDB response:", pdb);
```

Check operator logs during test execution:

```bash
# In another terminal, watch operator logs
kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management -f
```

## CI/CD Integration

### GitHub Actions

Add to your workflow:

```yaml
- name: Run PDB BDD Tests
  run: |
    cd feature-definition-and-test-kit
    npm install
    npm run test:pdb:dry-run
    # Only run full tests if cluster is available
    if kubectl cluster-info > /dev/null 2>&1; then
      npm run test:pdb:local
    fi
```

### Local Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd feature-definition-and-test-kit
npm run test:pdb:dry-run || {
  echo "PDB BDD tests have syntax errors. Please fix before committing."
  exit 1
}
```

## Troubleshooting

### Check Test Dependencies

```bash
# Verify all required modules are installed
npm ls @cucumber/cucumber
npm ls @kubernetes/client-node

# Check for missing dependencies
npm install
```

### Verify Kubernetes Access

```bash
# Test kubectl access
kubectl auth can-i get pods --all-namespaces

# Check current context
kubectl config current-context

# Test API access from Node.js
node -e "
const k8s = require('@kubernetes/client-node');
const kc = new k8s.KubeConfig();
kc.loadFromDefault();
console.log('Kubernetes config loaded successfully');
"
```

### Clean Test Environment

```bash
# Remove test deployments
kubectl delete deployments -n components -l test=pdb-bdd

# Remove test policies
kubectl delete availabilitypolicies -n components --all

# Clean test results
rm -rf test-results/
```

## Additional Resources

- [Cucumber.js Documentation](https://cucumber.io/docs/cucumber/)
- [ODA Canvas Documentation](https://github.com/tmforum-oda/oda-canvas)
- [PDB Management Operator README](../source/operators/pdb-management/README.md)
- [Kubernetes PDB Documentation](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

## Support

For issues or questions:

1. Check operator logs: `kubectl logs -n canvas -l app.kubernetes.io/name=pdb-management`
2. Review test output carefully for specific error messages
3. Open an issue in the ODA Canvas repository with test logs attached
