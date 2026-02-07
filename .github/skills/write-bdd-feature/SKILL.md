---
name: write-bdd-feature
description: Guide for writing BDD (Behaviour-Driven Development) feature files and step definitions for the ODA Canvas test kit. Covers Gherkin conventions, Cucumber.js patterns, step definition templates, utility library usage, and the complete creation workflow. Use this skill when creating new BDD features, writing Gherkin scenarios, or adding step definitions.
---

# Write BDD Feature — Skill Instructions

## Feature File Conventions

### File Naming Pattern
```
UC{use-case-number}-F{feature-number}-{Descriptive-Title}.feature
```

Examples:
- `UC002-F001-Install-Component.feature`
- `UC003-F004-Expose-APIs-Upgrade-component-with-additional-API.feature`
- `UC007-F002-Dependent-APIs-Configure-Dependent-APIs-Single-Downstream.feature`

### Required Structure

```gherkin
# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC{number}         # tagged as use case {number}
@UC{number}-F{number}    # tagged as feature {number} within use case {number}
Feature: UC{number}-F{number} {Feature Title}

    Background: (optional)
        Given [preconditions that apply to all scenarios]

    Scenario Outline: {Descriptive scenario name}
        Given [initial context or precondition]
        When [action or event occurs]
        Then [expected outcome]

    Examples:
    | Name           | PackageName       | ReleaseName  | ...
    | Descriptive    | example-package   | test-release | ...
```

### Standard Header Comment
**ALWAYS** include this exact comment block at the top of every feature file:
```gherkin
# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
```

### Tagging
Every feature file MUST have two tags on separate lines:
- `@UC{number}` — Use case level tag
- `@UC{number}-F{number}` — Feature level tag
- `@SkipTest` — Optional, to skip a feature

### Parameters
Use single-quoted `'{ParamName}'` convention in Gherkin step text.

## Common Given/When/Then Patterns

### Component Installation and Lifecycle
```gherkin
Given an example package '{PackageName}' with '{Count}' ExposedAPI in its '{SegmentName}' segment
Given a running helm release '{ReleaseName}' from package '{PackageName}'
When I install the '{PackageName}' package as release '{ReleaseName}'
When I upgrade the '{ReleaseName}' release to package '{PackageName}'
When I uninstall the '{ReleaseName}' release
Then the '{ComponentName}' component has a deployment status of 'Complete'
```

### API Resource Management
```gherkin
Then I should see the '{ExposedAPIName}' ExposedAPI resource on the '{ComponentName}' component
Then I should see the '{DependentAPIName}' DependentAPI resource on the '{ComponentName}' component
Then the '{ExposedAPIName}' ExposedAPI should have a url containing '{UrlPattern}'
Then the '{ExposedAPIName}' ExposedAPI should have implementation ready status '{Status}'
```

### Kubernetes Resources
```gherkin
Given a deployment '{DeploymentName}' with '{ReplicaCount}' replicas in namespace '{Namespace}'
Then the PDB named '{PDBName}' should exist in namespace '{Namespace}'
Then the Service '{ServiceName}' should exist in namespace '{Namespace}'
```

### Identity Management (Keycloak)
```gherkin
Given the Keycloak identity management platform is available
Then the Keycloak realm should contain the client '{ClientName}'
Then the client '{ClientName}' should have the role '{RoleName}'
```

### Observability
```gherkin
Then the component '{ComponentName}' should have OpenTelemetry configuration
Then a ServiceMonitor resource should exist for '{ComponentName}'
```

### API Gateway Configuration
```gherkin
Then an Apisix Route should be created for the '{ExposedAPIName}' ExposedAPI
Then a Kong Route should be created for the '{ExposedAPIName}' ExposedAPI
```

## Segment Types

ODA Components are structured into three segments:
- **`coreFunction`**: Core business functionality APIs
- **`managementFunction`**: Administrative and management APIs
- **`securityFunction`**: Security and access control APIs

## Test Data Packages

Available in `feature-definition-and-test-kit/testData/`:
- `productcatalog-v1` — Basic product catalog component
- `productcatalog-v1beta3` — Legacy version for seamless upgrade testing
- `productcatalog-dependendent-API-v1` — Component with dependent API configurations
- `productcatalog-dynamic-roles-v1` — Component with dynamic role definitions
- `productcatalog-enhanced-v1` — Component with enhanced API configurations
- `productinventory-v1` — Product inventory component

**Default release name**: `ctk` (Canvas Test Kit)
**Default namespace**: `components`

## Step Definition Conventions

### Existing Files (DO NOT create duplicates)
- `ComponentManagementSteps.js` — Component installation, upgrade, uninstall, status
- `APIManagementSteps.js` — ExposedAPI and DependentAPI resources
- `APIGatewayManagementSteps.js` — Apisix, Kong route/plugin configuration
- `IdentityManagementSteps.js` — Keycloak client, role, permission management
- `ObservabilitySteps.js` — ServiceMonitor and OpenTelemetry
- `PDBManagementSteps.js` — PodDisruptionBudget management
- `ResourceInventorySteps.js` — Generic Kubernetes resource operations
- `ProductCatalogSteps.js` — TMF-specific product catalog API interactions

### Before Creating New Steps
1. Search existing step definition files for similar patterns
2. Check if existing steps can be reused or extended
3. Only create new steps when no existing pattern matches

### Step Definition Template

```javascript
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');
const { Given, When, Then, setDefaultTimeout } = require('@cucumber/cucumber');
const assert = require('assert');

const NAMESPACE = 'components';
const DEFAULT_TIMEOUT = 20 * 1000;
const DEBUG_LOGS = false;

setDefaultTimeout(DEFAULT_TIMEOUT);

/**
 * [JSDoc comment describing the step's purpose]
 *
 * @param {string} parameterName - Description of parameter
 * @returns {Promise<void>}
 */
Given('step definition pattern {string}', async function (parameterName) {
  console.log('\n=== Starting [Step Name] ===');
  try {
    const result = await resourceInventoryUtils.someOperation(parameterName);
    assert.ok(result, 'Expected result to be truthy');
    console.log('✅ Successfully completed [step name]');
  } catch (error) {
    console.error(`❌ Error during [step name]: ${error.message}`);
    throw error;
  }
});
```

### Utility Libraries

Located in `feature-definition-and-test-kit/utilities/` (local npm packages linked via `file:`):

| Package | Purpose |
|---------|---------|
| `resource-inventory-utils-kubernetes` | K8s resource CRUD, wait for conditions, query status |
| `package-manager-utils-helm` | Helm install/upgrade/uninstall, chart metadata |
| `identity-manager-utils-keycloak` | Keycloak authentication, client/role management |
| `component-utils` | ODA Component API interactions, test data loading |
| `observability-utils-kubernetes` | ServiceMonitor, Prometheus configuration |
| `resource-inventory-utils-TMF639` | TMF639 Resource Inventory API operations |

## Creation Workflow

### Step 1: Understand Requirements
1. Read the use case document in `usecase-library/UC{number}-*.md`
2. Identify the specific behaviour being tested
3. Check for similar existing features

### Step 2: Create Feature File
1. Determine correct UC and F numbers (check existing features for next available)
2. Create file at `feature-definition-and-test-kit/features/UC{number}-F{number}-{Title}.feature`
3. Include standard header comment, two-level tags, Feature declaration
4. Write Scenario Outline with Examples table (preferred) or individual Scenarios
5. Reuse existing Given/When/Then patterns

### Step 3: Create Step Definitions (only if needed)
1. Add new steps to the appropriate existing file
2. Include JSDoc comments
3. Use utility libraries — never make direct K8s API calls
4. Add error handling and debug logging

### Step 4: Update README.md
Add entry to `feature-definition-and-test-kit/README.md` in the "List of BDD Features" section:
```markdown
### UC{number} - {Use Case Title}
* ⏳ [F{number} - {Feature Title}](features/UC{number}-F{number}-{Title}.feature)
```
Status indicators: `⏳` test defined but not validated, `✅` implemented and passing.

## Key Principles

1. **Reuse over recreation** — always search for existing patterns first
2. **Implementation-agnostic** — test Canvas behaviour, not operator internals
3. **Consistency** — follow naming conventions and structure exactly
4. **Readability** — scenarios should be understandable by business stakeholders
5. **Always update README.md** — maintain the feature catalog
