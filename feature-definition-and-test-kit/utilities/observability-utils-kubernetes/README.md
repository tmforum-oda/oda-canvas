# Observability Utils for Kubernetes

This utility library provides functions to interact with Kubernetes observability resources, specifically ServiceMonitor resources used by the Prometheus Operator.

## Purpose

This library is designed to support BDD testing of ODA Canvas observability features. It provides utilities to:

- Check if ServiceMonitor resources exist
- Validate ServiceMonitor configuration
- Wait for ServiceMonitor creation/deletion
- Extract ServiceMonitor configuration details

## Usage

```javascript
const observabilityUtils = require('observability-utils-kubernetes');

// Check if a ServiceMonitor exists
const serviceMonitor = await observabilityUtils.getServiceMonitor('my-servicemonitor', 'components');

// Validate ServiceMonitor configuration
const isValid = observabilityUtils.validateServiceMonitorConfig(serviceMonitor, {
  path: '/metrics',
  port: 'http',
  interval: '15s',
  targetLabels: {
    'name': 'my-service'
  }
});

// Wait for ServiceMonitor to be created
const sm = await observabilityUtils.waitForServiceMonitor('my-servicemonitor', 'components', 30000);
```

## Functions

### `getServiceMonitor(serviceMonitorName, namespace)`
Returns a ServiceMonitor resource object or null if not found.

### `listServiceMonitors(namespace)`
Returns an array of all ServiceMonitor resources in the specified namespace.

### `serviceMonitorExists(serviceMonitorName, namespace)`
Returns true if the ServiceMonitor exists, false otherwise.

### `validateServiceMonitorConfig(serviceMonitor, expectedConfig)`
Validates ServiceMonitor configuration against expected values.

### `waitForServiceMonitor(serviceMonitorName, namespace, timeoutMs)`
Waits for a ServiceMonitor to be created within the specified timeout.

### `waitForServiceMonitorDeletion(serviceMonitorName, namespace, timeoutMs)`
Waits for a ServiceMonitor to be deleted within the specified timeout.

### `getServiceMonitorConfig(serviceMonitorName, namespace)`
Returns ServiceMonitor configuration details in a structured format.

## Dependencies

- `@kubernetes/client-node`: For interacting with the Kubernetes API
- `assert`: For validation functions

## Configuration

The library automatically loads Kubernetes configuration from the default location. Make sure you have:

1. A valid kubeconfig file
2. Access to the cluster where ServiceMonitor resources are deployed
3. Proper RBAC permissions to access ServiceMonitor resources

## Integration with BDD Tests

This library is designed to work with Cucumber.js BDD tests. The functions are used in step definitions to verify observability features of ODA Canvas components.

Example BDD step:
```javascript
Then('a ServiceMonitor resource {string} should exist in the {string} namespace', 
  async function (serviceMonitorName, namespace) {
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, namespace);
    assert(serviceMonitor !== null, `ServiceMonitor should exist`);
  }
);
```

## Error Handling

The library handles common Kubernetes API errors:
- Returns null for 404 (not found) errors
- Throws errors for other API failures
- Provides meaningful error messages for debugging

## Testing

This library is primarily used for testing ODA Canvas observability features. It should be installed in the test environment alongside other Canvas testing utilities.
