# Run BDD Feature Tests

## Table of Contents
- [What Do BDD Tests Validate?](#what-do-bdd-tests-validate)
- [Step 1: Auto-Setup Dependencies](#step-1-auto-setup-dependencies)
- [Step 2: Browse and Select Tests](#step-2-browse-and-select-tests)
- [Step 3: Check Environment Variables](#step-3-check-environment-variables)
- [Step 4: Run Tests](#step-4-run-tests)
- [Step 5: Report Results](#step-5-report-results)
- [Important: BDD Tests Deploy Their Own Components](#important-bdd-tests-deploy-their-own-components)
- [Tag Reference](#tag-reference)
- [Contextual Next Steps](#contextual-next-steps)

## What Do BDD Tests Validate?

BDD (Behaviour-Driven Development) features verify that the Canvas operators correctly handle the ODA Custom Resource lifecycle. Each use case maps to specific CRDs and operators:

| Use Case | What it validates | CRDs / Operators tested |
|----------|-------------------|------------------------|
| **UC002** Manage Components | Component creation, update, deletion lifecycle | `Component` → Component Operator |
| **UC003** Configure Exposed APIs | API Gateway route creation, readiness | `ExposedAPI` → API Operator |
| **UC005** Configure Clients and Roles | Identity management, role assignment | `IdentityConfig` → Identity Operator |
| **UC007** Configure Dependent APIs | Cross-component dependency resolution | `DependentAPI` → Dependency Operator |
| **UC010** External Authentication | Authentication flow logging | `IdentityConfig` → Identity Operator |
| **UC012** Configure Observability | Metrics scraping, trace collection | `ExposedAPI` (prometheus/openmetrics) → API Operator + ServiceMonitor |
| **UC013** Seamless Upgrades | Component version upgrades | `Component` → Component Operator (webhook conversion) |
| **UC015** API Gateway Management | Gateway-specific features (Istio/Kong/APISIX) | `ExposedAPI` → API Operator |
| **UC016** Component Registry | Component registration | `Component` → Component Operator |
| **UC017** PDB Management | Pod Disruption Budget policies | `AvailabilityPolicy` → PDB Operator |

The tests themselves deploy a test component (release name `ctk`) from local test data in `feature-definition-and-test-kit/testData/` and then verify that the Canvas processes it correctly. This means:
- The Component CRD schema is validated end-to-end
- Each operator's reconciliation logic is tested against real Kubernetes resources
- The test component YAML in `testData/productcatalog-v1/` serves as a reference implementation of the Component specification

## Step 1: Auto-Setup Dependencies

Check if `node_modules/` exists in each directory and install if needed:

```bash
python <scripts>/check_bdd_deps.py <path-to-feature-definition-and-test-kit>
```

To install manually:

```bash
cd feature-definition-and-test-kit

cd utilities/identity-manager-utils-keycloak && npm install && cd ../..
cd utilities/package-manager-utils-helm && npm install && cd ../..
cd utilities/resource-inventory-utils-kubernetes && npm install && cd ../..
cd utilities/observability-utils-kubernetes && npm install && cd ../..
cd utilities/component-utils && npm install && cd ../..

npm install
```

Only run `npm install` where `node_modules/` is missing. On PowerShell: `Test-Path node_modules`; on bash: `[ -d node_modules ]`.

## Step 2: Browse and Select Tests

Present use cases as a menu:

| Use Case | Title | Features |
|----------|-------|----------|
| UC002 | Manage Components | 6 features |
| UC003 | Configure Exposed APIs | 6 features |
| UC005 | Configure Clients and Roles | 3 features |
| UC007 | Configure Dependent APIs | 2 features |
| UC010 | External Authentication | 1 feature |
| UC012 | Configure Observability | 2 features |
| UC013 | Seamless Upgrades | 2 features |
| UC015 | API Gateway Management | 4 features |
| UC016 | Component Registry Management | 1 feature |
| UC017 | PDB Management | 4 features |

After the user selects a use case, list the specific features and let them pick one or run all.

## Step 3: Check Environment Variables

Some tests require specific environment variables:

| Tests | Required Variables | Purpose |
|-------|--------------------|---------|
| UC005-* | `KEYCLOAK_USER`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM` | Keycloak identity management |
| UC010-* | `KEYCLOAK_USER`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM` | Authentication logging |
| UC012-F001 | OpenTelemetry collector must be port-forwarded to port 8888 | Traces collection |

If required variables are missing, check for `.env` in `feature-definition-and-test-kit/`. If not found, prompt the user.

## Step 4: Run Tests

Execute from the `feature-definition-and-test-kit/` directory:

```bash
# All features for a use case
npm run start:tags -- "@UC003"

# Single feature
npm run start:tags -- "@UC003-F001"

# Specific feature file
npm start -- features/UC003-F001-Expose-APIs-Create-API-Resource.feature
```

## Step 5: Report Results

Stream terminal output. After completion, summarize:

- Total scenarios run
- Passed / Failed / Pending counts
- For failures: failing scenario name and error message
- **Cucumber Report URL**: shareable link valid for 24 hours — highlight to user

JSON results are written to `/tmp/cucumber.json`.

After reporting results, explain what the tests validated in ODA Canvas terms:
- **Passed scenarios** confirm that the corresponding operator(s) correctly processed the CRD lifecycle. For example, if UC003 tests pass, the API Operator successfully created gateway routes for ExposedAPIs and reported them as ready.
- **Failed scenarios** indicate an operator behavior gap. Reference the use case mapping table above to identify which operator and CRD are involved, then suggest checking the operator logs:
  ```bash
  # Example: UC003 failure → check API Operator
  kubectl logs -l app=oda-controller-apioperator -n canvas --tail=50
  
  # UC005 failure → check Identity Operator
  kubectl logs -l app=oda-controller-identityoperator -n canvas --tail=50
  
  # UC007 failure → check Dependency Operator
  kubectl logs -l app=oda-controller-dependentapi -n canvas --tail=50
  ```

## Important: BDD Tests Deploy Their Own Components

- Tests install a test component from local `testData/` using release name `ctk` (default)
- A new component `ctk-productcatalogmanagement` will appear in `components` namespace
- Tests use `helm install` first run, `helm upgrade` for subsequent runs
- After tests complete, the `ctk` release remains — offer cleanup with `helm delete ctk -n components`
- Test charts in `testData/` may differ from remote `oda-components` repo charts

## Tag Reference

| Tag | Scope |
|-----|-------|
| `@UC{NNN}` | All features in a use case |
| `@UC{NNN}-F{NNN}` | Single feature |
| `@ApisixGateway` | Apisix gateway tests only |
| `@KongGateway` | Kong gateway tests only |
| `@OpenTelemetryCollector` | OpenTelemetry tests (requires collector) |
| `@ServiceMonitor` | OpenMetrics tests (requires ServiceMonitor support) |
| `@SkipTest` | Skipped tests |

## Contextual Next Steps

Present these options using `ask_questions`:

| # | Next Step |
|---|-----------|
| 1 | **View components deployed by tests** — Inspect the `ctk` release component and its child resources |
| 2 | **Run another test suite** — Select a different use case to validate |
| 3 | **View ExposedAPIs** — See APIs created by the test component |
| 4 | **Clean up test components** — Remove the `ctk` Helm release |
| 5 | **Return to main menu** |
