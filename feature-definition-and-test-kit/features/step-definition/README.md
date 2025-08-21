# BDD Step Definition Framework and Guidelines

This directory contains step definition JavaScript files that implement Behavior-Driven Development (BDD) test scenarios for the TM Forum ODA Canvas. These step definitions serve as the bridge between human-readable Gherkin feature files and the technical implementation of test automation.

## Frameworks and Dependencies

### Core Testing Framework
- **Cucumber.js** (`@cucumber/cucumber`): BDD framework providing the Gherkin language support and step definition execution
- **Chai** (`chai`): Assertion library for validating test expectations
- **Chai-HTTP** (`chai-http`): HTTP request/response testing plugin for Chai
- **Node.js Assert** (`assert`): Built-in Node.js assertion module for basic validations

### Utility Libraries
The step definitions use modular utility libraries to interact with different Canvas technologies:

- **`utilities/resource-inventory-utils-kubernetes`**: Kubernetes resource management and querying
- **`utilities/package-manager-utils-helm`**: Helm package installation and management
- **`utilities/identity-manager-utils-keycloak`**: Keycloak identity platform integration
- **`utilities/component-utils`**: ODA Component lifecycle and API interactions

### Additional Dependencies
- **`@kubernetes/client-node`**: Kubernetes API client for direct cluster interactions
- **`https`**: Custom HTTPS agents for handling self-signed certificates
- **`axios`**: HTTP client for API requests (used in utility libraries)

## Architecture and Design Patterns

### Modular Architecture
The step definitions follow a modular approach where:
- Each step definition file focuses on a specific Canvas capability domain
- Utility libraries abstract the technical implementation details
- This allows the same step definitions to work with different Canvas implementations by swapping utility libraries

### File Structure and Naming
- **Step Definition Files**: Named with descriptive suffixes indicating their domain
  - `IdentityManagementSteps.js` - Identity and role management
  - `ComponentManagementSteps.js` - Component lifecycle operations  
  - `APIManagementSteps.js` - API resource management
  - `APIGatewayManagementSteps.js` - API Gateway specific operations
  - `ProductCatalogSteps.js` - TMF product catalog interactions
  - `ApiGatewayCheck.js` - Infrastructure validation utilities

### Standard Imports and Setup
Every step definition file follows this standard structure:

```javascript
// Utility library imports - replace with your implementation
const resourceInventoryUtils = require('utilities/resource-inventory-utils-kubernetes');
const packageManagerUtils = require('utilities/package-manager-utils-helm');
const identityManagerUtils = require('utilities/identity-manager-utils-keycloak');
const componentUtils = require('utilities/component-utils');

// Cucumber framework imports
const { Given, When, Then, AfterAll, setDefaultTimeout, Before, After } = require('@cucumber/cucumber');

// Testing library imports
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);

// Configuration constants
const NAMESPACE = 'components';
const COMPONENT_DEPLOY_TIMEOUT = 100 * 1000; // 100 seconds
const API_DEPLOY_TIMEOUT = 10 * 1000; // 10 seconds
const TIMEOUT_BUFFER = 5 * 1000; // 5 seconds

setDefaultTimeout(20 * 1000);
```

## Standard Practices

### Global State Management
- **`global.currentReleaseName`**: Tracks the current Helm release name across scenarios
- **`global.createdResources`**: Array to store created resources for cleanup
- **`global.lastCreated*`**: Stores references to recently created resources for verification

### Error Handling and Validation
- Use `assert.ok()` for boolean validations with descriptive error messages
- Use `assert.equal()` and `assert.notEqual()` for value comparisons
- Include contextual information in assertion messages
- Wrap API calls in try-catch blocks with detailed error logging

### Timeout Management
- Set appropriate timeouts for different operation types
- Use performance timing to track operation duration
- Include timeout buffers to prevent flaky tests
- Configure Cucumber step-level timeouts for long-running operations:
  ```javascript
  Then('step description', {timeout: API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function() {
    // implementation
  });
  ```

### HTTPS and Certificate Handling
For components with self-signed certificates:
```javascript
const https = require('https');
const agent = new https.Agent({
  rejectUnauthorized: false
});

// Use in chai requests
const response = await chai.request(apiURL)
  .get('/endpoint')
  .agent(agent)
  .trustLocalhost(true)
  .disableTLSCerts()
  .send();
```

## Logging Standards and Format

### Structured Logging Approach
Follow the comprehensive logging format established in `IdentityManagementSteps.js`:

#### Section Headers
Use distinctive headers to mark major test sections:
```javascript
console.log('\n=== Starting Test Section Name ===');
console.log('Brief description of what this section does');
// test implementation
console.log('=== Test Section Name Complete ===');
```

#### Success Logging
Mark successful operations with green checkmarks:
```javascript
console.log(`✅ Success message: '${resourceName}' operation completed successfully`);
```

#### Error Logging
Mark failures with red X marks and provide detailed diagnostics:
```javascript
console.error(`❌ Error during operation: ${error.message}`);
console.error('Error details:');
console.error(`- Target resource: '${resourceName}'`);
console.error(`- Error type: ${error.constructor.name}`);

if (error.response) {
  console.error('HTTP Response error details:');
  console.error(`- Status: ${error.response.status}`);
  console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
  console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
}

console.error('Possible causes:');
console.error('- First possible cause');
console.error('- Second possible cause');
console.error('- Additional troubleshooting hints');
```

#### Warning Logging
Use warning emoji for non-critical issues:
```javascript
console.log(`⚠️  Warning: Resource '${resourceName}' not found - this may be expected`);
```

#### Progress Logging
For iterative operations, show progress:
```javascript
console.log(`Processing ${i + 1}/${totalItems}: '${itemName}'`);
```

#### Request/Response Logging
Log key API interactions:
```javascript
console.log(`Making API call to: ${apiURL}/${endpoint}`);
console.log(`Request payload: ${JSON.stringify(payload, null, 2)}`);
```

### Debugging Configuration
Include debug flags for additional logging:
```javascript
const DEBUG_LOGS = false; // set to true for verbose debugging
const CLEANUP_RESOURCES = false; // set to true for automatic cleanup

if (DEBUG_LOGS) {
  console.log('Debug information:', detailedData);
}
```

## Step Definition Patterns

### Given Steps (Preconditions)
Set up test preconditions and verify system state:
```javascript
Given('the {string} component has an existing {string}', async function (componentName, resourceType) {
  // Verify resource exists or create it for test setup
});
```

### When Steps (Actions)
Perform the action being tested:
```javascript
When('I POST a new {string} with the following details:', async function (resourceType, dataTable) {
  // Extract data from dataTable
  // Perform API operation
  // Store results for verification
});
```

### Then Steps (Assertions)
Verify expected outcomes:
```javascript
Then('the {string} should be created in the {string}', async function (resourceName, targetSystem) {
  // Query target system
  // Assert resource exists with expected properties
});
```

### Hooks and Lifecycle Management
```javascript
Before({ tags: '@RequiresSpecificGateway' }, async function () {
  // Check prerequisites and skip if not met
  const gatewayDeployed = await checkGatewayDeployment();
  if (!gatewayDeployed) {
    return 'skipped';
  }
});

After(async function () {
  // Cleanup resources if configured
  if (CLEANUP_RESOURCES && global.createdResources) {
    await cleanupResources(global.createdResources);
  }
});
```

## Data Table Handling
Extract and process data tables from Gherkin steps:
```javascript
When('I create resources with the following details:', async function (dataTable) {
  const resourceData = dataTable.hashes(); // Get all rows as objects
  
  for (let i = 0; i < resourceData.length; i++) {
    const resource = resourceData[i];
    console.log(`Creating resource ${i + 1}/${resourceData.length}: '${resource.name}'`);
    // Process each resource
  }
});
```

## Testing Guidelines

### Resource Lifecycle Management
- Always store created resource references for cleanup
- Implement proper cleanup in After hooks or dedicated cleanup steps
- Use consistent naming patterns for generated resources

### Timing and Synchronization
- Wait for asynchronous operations to complete before assertions
- Use polling loops with timeouts for resource state verification
- Include appropriate delays for Canvas operators to process events

### Canvas Integration
- Use ExposedAPI resources to discover component API endpoints
- Respect Canvas security and authentication mechanisms  
- Follow TMF Open API specifications for API interactions

### Error Recovery
- Design tests to be idempotent where possible
- Clean up partial state on test failures
- Provide clear diagnostics for troubleshooting failures

## Best Practices

1. **Modularity**: Keep step definitions focused on single responsibilities
2. **Reusability**: Write steps that can be reused across multiple scenarios
3. **Maintainability**: Use descriptive variable names and comprehensive comments
4. **Observability**: Implement thorough logging for debugging and monitoring
5. **Resilience**: Handle network timeouts, retries, and partial failures gracefully
6. **Documentation**: Include JSDoc comments for all functions with parameter descriptions

This framework ensures consistent, maintainable, and reliable BDD test implementations across the ODA Canvas test suite.
