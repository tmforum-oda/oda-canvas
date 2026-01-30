# ODA Canvas Test Utilities

This directory contains a collection of utility libraries that provide abstracted interfaces for interacting with different technical implementations of the ODA Canvas. These utilities support the Behaviour-Driven Development (BDD) test framework by encapsulating implementation-specific details and providing consistent APIs for test scenarios.

## Overview

The utilities follow a modular architecture where each utility module focuses on a specific technology or functional domain. This design allows the BDD tests to remain implementation-agnostic while providing concrete implementations for specific technologies like Kubernetes, Helm, and Keycloak.

## Utility Modules

### 1. component-utils
**Purpose**: Provides utilities for interacting with ODA Components and their APIs, including data management and validation for test scenarios.

**Key Functions**:
- `getAPIURL(componentInstance, apiName, namespace)` - Retrieves the base URL for a specific API
- `loadTestDataFromFile(testDataFile, apiURL)` - Loads test data from JSON files into APIs
- `loadTestDataFromDataTable(resource, dataTable, apiURL)` - Loads test data from Cucumber data tables
- `deleteTestData(resource, apiURL)` - Cleans up test data from APIs
- `validateReturnDataFromFile/Object/DataTable()` - Validates API responses against expected data

**Dependencies**: 
- `@kubernetes/client-node` - Kubernetes API client
- `axios` - HTTP client for API interactions

**Usage**: Used primarily in `ProductCatalogSteps.js` and `IdentityManagementSteps.js` for managing test data and API interactions.

### 2. identity-manager-utils-keycloak
**Purpose**: Provides utilities for interacting with Keycloak identity management system to support authentication and authorization testing.

**Key Functions**:
- `getToken(baseURL, userName, password)` - Obtains authentication token from Keycloak
- `getRolesForClient(clientName)` - Retrieves roles assigned to a specific client
- `clientExists(clientName)` - Checks if a client exists in Keycloak

**Environment Variables Required**:
- `KEYCLOAK_USER` - Admin username for Keycloak
- `KEYCLOAK_PASSWORD` - Admin password
- `KEYCLOAK_BASE_URL` - Base URL of Keycloak instance
- `KEYCLOAK_REALM` - Keycloak realm name

**Dependencies**:
- `axios` - HTTP client
- `dotenv` - Environment variable management
- `qs` - Query string utilities

**Usage**: Used in `ComponentManagementSteps.js` and `IdentityManagementSteps.js` for identity and access management testing.

### 3. package-manager-utils-helm
**Purpose**: Provides utilities for managing Helm chart deployments and extracting component metadata for testing ODA Component lifecycle operations.

**Key Functions**:
- `installPackage(componentPackage, releaseName, namespace)` - Installs or upgrades Helm charts
- `upgradePackage(componentPackage, releaseName, namespace)` - Upgrades existing Helm releases
- `uninstallPackage(releaseName, namespace)` - Uninstalls Helm releases
- `getExposedAPIsFromPackage(componentPackage, releaseName, componentSegmentName)` - Extracts exposed APIs from component specification
- `getDependentAPIsFromPackage(componentPackage, releaseName, componentSegmentName)` - Extracts dependent APIs from component specification
- `addPackageRepoIfNotExists(repoName, repoURL)` - Manages Helm repositories
- `installupgradePackageFromRepo(repoName, packageName, releaseName, namespace)` - Installs packages from repositories

**Dependencies**: None (uses native Node.js child_process for Helm CLI interactions)

**Usage**: Used in `ComponentManagementSteps.js` and `APIGatewayManagementSteps.js` for component deployment and lifecycle management.

### 4. resource-inventory-utils-kubernetes
**Purpose**: Provides utilities for interacting with Kubernetes custom resources specific to the ODA Canvas, including components, APIs, and API Gateway configurations.

**Key Functions**:
- `getCustomResource(crdPluralName, resourceName, componentName, releaseName, namespace)` - Generic custom resource retrieval
- `getExposedAPIResource(apiName, componentName, releaseName, namespace)` - Retrieves ExposedAPI resources
- `getDependentAPIResource(apiName, componentName, releaseName, namespace)` - Retrieves DependentAPI resources
- `getComponentResource(componentName, namespace)` - Retrieves Component resources
- `getComponentResourceByVersion(componentName, version, namespace)` - Retrieves version-specific Component resources
- `getHTTPRouteForComponent(componentName, resourceName, namespace)` - Retrieves Kong HTTPRoute resources
- `getKongPluginForComponent(componentName, pluginName, namespace)` - Retrieves Kong plugin configurations
- `getApisixRouteForComponent(componentName, resourceName, namespace)` - Retrieves APISIX route resources
- `getApisixPluginForComponent(componentName, pluginName, namespace)` - Retrieves APISIX plugin configurations
- `getOperatorLogs(operatorLabel, containerName)` - Retrieves operator pod logs for debugging

**Dependencies**:
- `@kubernetes/client-node` - Kubernetes API client
- `yaml` - YAML parsing for Kubernetes resources

**Usage**: Used across multiple step definition files (`ComponentManagementSteps.js`, `APIManagementSteps.js`, `IdentityManagementSteps.js`, `APIGatewayManagementSteps.js`) for Kubernetes resource management and validation.

### 5. observability-utils-kubernetes
**Purpose**: Provides utilities for testing ODA Canvas observability features, specifically ServiceMonitor resources used by the Prometheus Operator for metrics collection.

**Key Functions**:
- `getServiceMonitor(serviceMonitorName, namespace)` - Retrieves ServiceMonitor resources
- `listServiceMonitors(namespace)` - Lists all ServiceMonitor resources in a namespace
- `serviceMonitorExists(serviceMonitorName, namespace)` - Checks if a ServiceMonitor exists
- `validateServiceMonitorConfig(serviceMonitor, expectedConfig)` - Validates ServiceMonitor configuration
- `waitForServiceMonitor(serviceMonitorName, namespace, timeoutMs)` - Waits for ServiceMonitor creation
- `waitForServiceMonitorDeletion(serviceMonitorName, namespace, timeoutMs)` - Waits for ServiceMonitor deletion
- `getServiceMonitorConfig(serviceMonitorName, namespace)` - Extracts ServiceMonitor configuration details

**Dependencies**:
- `@kubernetes/client-node` - Kubernetes API client for custom resources

**Usage**: Used in `ObservabilitySteps.js` for testing ServiceMonitor creation, configuration, and cleanup as part of ODA Component observability testing.

## Standards and Structure

### File Naming Convention
- Utility modules follow the pattern: `{functional-domain}-utils-{technology-implementation}`
- Examples: `component-utils`, `identity-manager-utils-keycloak`, `package-manager-utils-helm`

### Directory Structure
Each utility module maintains a consistent structure:
```
{utility-name}/
├── {utility-name}.js          # Main utility module
├── package.json               # Node.js package definition
├── package-lock.json          # Dependency lock file
└── node_modules/              # Installed dependencies
```

### Code Standards

#### Module Structure
- Each utility exports a single object containing all public functions
- Use CommonJS module format (`module.exports`)
- Include comprehensive JSDoc comments for all public functions

#### Function Documentation
All public functions must include JSDoc comments with:
- Function description
- Parameter documentation with types and descriptions
- Return value documentation with type and description
- Example usage where applicable

#### Error Handling
- Use try-catch blocks for async operations
- Return `null` for resource-not-found scenarios
- Throw errors for configuration or system issues
- Log errors to console for debugging

#### Naming Conventions
- Use camelCase for function names
- Use descriptive names that clearly indicate the function's purpose
- Prefix boolean functions with verbs like `is`, `has`, `can`
- Use consistent parameter naming across similar functions

#### Dependencies
- Minimize external dependencies
- Use specific version ranges in package.json
- Document required environment variables
- Include all required dependencies in package.json

### Integration with Step Definitions
- Step definition files import utilities using their package names
- Utilities are imported at the top of step definition files
- Each step definition file includes a comment explaining the utility library usage pattern

### Environment Configuration
- Use `.env` files for environment-specific configuration
- Document all required environment variables in utility documentation
- Provide reasonable defaults where possible
- Validate required environment variables on module initialization

### Testing and Validation
- Each utility should handle edge cases gracefully
- Include timeout configurations for async operations
- Provide debug logging capabilities
- Support different namespaces and deployment configurations

## Adding New Utilities

When creating new utility modules:

1. **Follow the naming convention**: `{domain}-utils-{technology}`
2. **Create the directory structure** with package.json and main module file
3. **Implement consistent error handling** and logging patterns
4. **Document all public functions** with comprehensive JSDoc comments
5. **Add appropriate dependencies** to package.json
6. **Test integration** with step definition files
7. **Update this README** to document the new utility

## Dependencies Overview

The utilities use these primary technologies:
- **Kubernetes**: `@kubernetes/client-node` for cluster interactions
- **HTTP Communications**: `axios` for REST API calls
- **Environment Management**: `dotenv` for configuration
- **Command Line Integration**: Node.js `child_process` for CLI tools
- **Data Parsing**: `yaml` for Kubernetes resource parsing, `qs` for query strings

## Troubleshooting

### Common Issues
- **Environment Variables**: Ensure all required environment variables are set
- **Kubernetes Access**: Verify kubeconfig is properly configured
- **Network Connectivity**: Check access to Keycloak and Kubernetes APIs
- **Helm Installation**: Ensure Helm CLI is installed and accessible
- **Namespace Access**: Verify permissions for target namespaces

### Debug Logging
Most utilities support debug logging through configuration flags. Enable debug output by setting appropriate flags in the step definition files or environment variables.
