# AGENTS.md — feature-definition-and-test-kit/

BDD (Behaviour-Driven Development) test suite that validates ODA Canvas compliance. Features are written in Gherkin and executed with Cucumber.js against a live Kubernetes cluster.

## Technology

- **Test runner**: Cucumber.js v7 (`@cucumber/cucumber`)
- **Assertions**: Chai
- **Language**: JavaScript (CommonJS — uses `require()`, not ES modules)
- **Runtime**: Node.js

## Directory Structure

```
feature-definition-and-test-kit/
  features/
    UC###-F###-<Description>.feature    # Gherkin feature files
    step-definition/                    # Step implementations
      ComponentManagementSteps.js
      APIManagementSteps.js
      IdentityManagementSteps.js
      ObservabilitySteps.js
      ...
  testData/                             # Test component YAMLs and fixtures
  utilities/                            # Shared utility npm packages (local)
    component-utils/
    identity-manager-utils-keycloak/
    package-manager-utils-helm/
    resource-inventory-utils-kubernetes/
    observability-utils-kubernetes/
  local-tests/                          # Local test configurations
```

## Feature File Conventions

### Naming

Files follow: `UC<NNN>-F<NNN>-<Descriptive-Name>.feature`
- Example: `UC003-F001-Expose-APIs-Create-API-Resource.feature`
- Words in descriptive name are hyphenated

### Structure

```gherkin
# This feature corresponds to use case UC003 - Configure Exposed APIs
# and covers the scenario where...

@UC003 @UC003-F001
Feature: UC003-F001 Expose APIs: Create API Resource

  Scenario Outline: ...
    Given ...
    When ...
    Then ...

    Examples:
      | param1 | param2 |
      | value1 | value2 |
```

### Tags

- `@UC###` — Use case tag (e.g., `@UC003`)
- `@UC###-F###` — Feature tag (e.g., `@UC003-F001`)
- `@SkipTest` — Mark features to be skipped
- Tags go on separate lines above the `Feature:` line

### Parameters

Use single-quoted `'<ParamName>'` convention in Gherkin step text.

## Step Definition Conventions

- One file per domain: `ComponentManagementSteps.js`, `APIManagementSteps.js`, etc.
- Import utilities via local packages: `require('resource-inventory-utils-kubernetes')`
- Use `global.currentReleaseName` and `global.namespace` for shared state
- Define timeout constants: `COMPONENT_DEPLOY_TIMEOUT = 600 * 1000`
- Use `DEBUG_LOGS` flag for verbose output

## Do

- Write feature files that are **implementation-agnostic** — test Canvas behaviour, not specific operator internals
- Use the utility layer for Kubernetes and Helm interactions, not direct API calls in step definitions
- Follow the `UC###-F###` naming convention strictly
- Add both `@UC###` and `@UC###-F###` tags to every feature
- Start feature files with a comment block explaining the business context
- Use `Scenario Outline` with `Examples` tables for parameterised tests
- Update the use case library README when adding new features

## Don't

- Do not reference specific operator implementations in step definitions
- Do not make direct Kubernetes API calls in step definitions — use the utility packages
- Do not skip the header comment explaining the feature's business context
- Do not run tests without a live Kubernetes cluster with Canvas deployed

## Commands

```bash
# Install dependencies
npm install

# Run all BDD tests
npm start

# Run tests with specific tags
npm run start:tags

# Run a single feature
npx cucumber-js features/UC003-F001-Expose-APIs-Create-API-Resource.feature
```

## Utilities

Utilities are **local npm packages** linked via `file:` in `package.json`. They are NOT published to npm.

| Package | Purpose |
|---------|---------|
| `component-utils` | API URL retrieval, test data loading/validation |
| `identity-manager-utils-keycloak` | Keycloak token/role management |
| `package-manager-utils-helm` | Helm chart install/upgrade/uninstall |
| `resource-inventory-utils-kubernetes` | Kubernetes resource queries |
| `observability-utils-kubernetes` | Observability checks |

## Environment

Tests require a `.env` file at the root for configuration. Key variables include Keycloak credentials (`KEYCLOAK_USER`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM`).
