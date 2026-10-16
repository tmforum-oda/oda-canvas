
# Installing and executing the BDD tests


To execute the tests, first you install the necessary packages and set the environment variables.

- install necessary packages

  ```bash
  cd utilities/identity-manager-utils-keycloak
  npm install
  cd ../package-manager-utils-helm
  npm install
  cd ../resource-inventory-utils-kubernetes
  npm install
  cd ../observability-utils-kubernetes
  npm install
  cd ../..
  npm install
  ```

- create a `.env` file and set `KEYCLOAK_USER`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_BASE_URL` and `KEYCLOAK_REALM`, - or use another option to define the variables

  ```
  KEYCLOAK_USER=admin 
  KEYCLOAK_PASSWORD=adpass 
  KEYCLOAK_BASE_URL=http://keycloack-ip:8083/auth/
  KEYCLOAK_REALM=odari
  RESOURCE_INVENTORY_BASE_URL=http://localhost:8639/tmf-api/resourceInventoryManagement/v5
  ```



## How to run the tests

Run the test in the command line using the following command:

```bash
npm start
```

All the tests should run and display the results in the command line.

If you only want to run a single test, you can use the following command:

```
npm start -- features/UC003-F001-Expose-APIs-Create-API-Resource.feature
```

The use cases and features are tagged. You can run the tests for a given use case with the following command:

```
npm run start:tags -- "@UC003"
```

Or run the tests for a single feature with the following command:

```
npm run start:tags -- "@UC003-F001"
```

## Selecting the tests for a change

[`test-selection.yaml`](test-selection.yaml) maps the paths a change touches to the features it should run. The selector reads it and prints the features in scope, the tag expression for each run, and the reason for a full run or a skip:

```bash
npm run select-features -- --base origin/main
```

You can also pass the changed paths yourself, one per line (`-` reads them from stdin):

```bash
git diff --name-only origin/main | npm run select-features -- --files -
```

Add `--format json` for machine-readable output.

The Kong and APISIX features need a canvas installed with that gateway instead of Istio, so they get a run of their own. The selector prints the `--set` values to install the canvas for that run.

When you add a feature or a test chart, or rename a path that the map lists, run the check and the unit tests:

```bash
npm run check:selection
npm run test:selection
```

The check fails when a feature has no rule that selects it, when a feature's tags don't match its file name, when a test chart isn't used by any feature, or when a path in the map matches no file.

### In CI

The [`trigger_test`](../.github/workflows/trigger_tests.yml) workflow uses the selector on every pull request to `main`:

- `check_skip_tests_job` lists the files the PR changes and selects the features. The job summary shows the selection.
- `run_tests_job` runs the default selection on a kind cluster with Istio. It's skipped when nothing is selected, for example for a documentation-only PR.
- `run_gateway_tests_job` runs the Kong and APISIX features, when they're selected, each on its own kind cluster with that gateway.
- The BDD badges are updated only after a full run.

`[skip tests]` in the PR title or the last commit message, or a last commit that only removes prerelease suffixes, still skips the tests.

To run the full suite, including both gateway runs, open **Actions > trigger_test > Run workflow**, then pick the branch or enter a tag or commit.

## Updating the master test status


To update the master test status that appears in the top-level [README.md](../README.md), set the following environment variable:

- set or export `CUCUMBER_PUBLISH_TOKEN` 
  
  ```
  CUCUMBER_PUBLISH_TOKEN=9afda79b-9ea0-44ff-8359-7f381ade4bb6
  ```
- run 'npm start' command to execute all the tests