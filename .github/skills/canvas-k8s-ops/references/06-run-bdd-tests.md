# Run BDD Feature Tests

## Table of Contents
- [Step 1: Auto-Setup Dependencies](#step-1-auto-setup-dependencies)
- [Step 2: Browse and Select Tests](#step-2-browse-and-select-tests)
- [Step 3: Check Environment Variables](#step-3-check-environment-variables)
- [Step 4: Run Tests](#step-4-run-tests)
- [Step 5: Report Results](#step-5-report-results)
- [Important: BDD Tests Deploy Their Own Components](#important-bdd-tests-deploy-their-own-components)
- [Tag Reference](#tag-reference)

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
