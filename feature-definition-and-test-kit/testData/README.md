# BDD test charts

The BDD features install these Helm charts as the ODA Components they test. Each one is a component from [reference-example-components](https://github.com/tmforum-oda/reference-example-components), using its published `tmforumodacanvas` images, with only the changes its scenarios need. For example, it might remove an optional API, add a dependent API, use an older CRD version for the N-1 and N-2 tests, or add an upgrade.

The charts are kept here rather than installed from the reference repository, so the tests are reproducible and don't change when a reference component is released. Only UC002-F003 and UC002-F004 install the published reference charts, because that is what they test.

## Test charts

The table is generated from each chart's `Chart.yaml` and the feature files: run `npm run chart-inventory` in `feature-definition-and-test-kit`. `npm run check:selection`, which runs on every pull request, fails when the table is out of date.

<!-- chart-inventory:start -->

| Test chart | Chart name | Description | Used by |
| --- | --- | --- | --- |
| [`productcatalog-depapitest-v1`](productcatalog-depapitest-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as the downstream catalog for UC007-F002 | UC007-F002 |
| [`productcatalog-dependent-API-v1beta3`](productcatalog-dependent-API-v1beta3/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as an oda.tmforum.org/v1beta3 Component, with its dependent API enabled | UC013-F001 |
| [`productcatalog-dependent-API-v1beta4`](productcatalog-dependent-API-v1beta4/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as an oda.tmforum.org/v1beta4 Component, with its dependent API enabled | UC013-F001 |
| [`productcatalog-dynamic-roles-v1`](productcatalog-dynamic-roles-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component, unchanged | UC005-F002 |
| [`productcatalog-enhanced-v1`](productcatalog-enhanced-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component, unchanged | UC002-F002, UC003-F004, UC003-F005 |
| [`productcatalog-static-roles-v1`](productcatalog-static-roles-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component with static componentRoles | UC005-F003 |
| [`productcatalog-updated-v1`](productcatalog-updated-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component with an updated TMF620 specification URL | UC002-F002 |
| [`productcatalog-v1`](productcatalog-v1/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component without the optional TMF671 Promotion Management API | UC002-F001, UC002-F002, UC002-F005, UC002-F006, UC003-F001, UC003-F002, UC003-F003, UC003-F004, UC003-F005, UC005-F001, UC012-F001, UC012-F002, UC013-F002, UC016-F001 |
| [`productcatalog-v1beta3`](productcatalog-v1beta3/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as an oda.tmforum.org/v1beta3 Component | UC013-F001, UC015-F001, UC015-F002 |
| [`productcatalog-v1beta3-plugin`](productcatalog-v1beta3-plugin/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as an oda.tmforum.org/v1beta3 Component, with API key verification and rate limiting enabled | UC015-F003, UC015-F004 |
| [`productcatalog-v1beta4`](productcatalog-v1beta4/Chart.yaml) | `productcatalog` | BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component as an oda.tmforum.org/v1beta4 Component | UC013-F001 |
| [`productinventory-v1`](productinventory-v1/Chart.yaml) | `productinventory` | BDD test chart - the reference TMFC005-ProductInventoryManagement ODA Component | UC007-F002 |
| [`productordercaptureandvalidation-mgmt-dependent-API-v1`](productordercaptureandvalidation-mgmt-dependent-API-v1/Chart.yaml) | `productordercaptureandvalidation` | BDD test chart - the reference TMFC002-ProductOrderCaptureAndValidation ODA Component with a DependentAPI in its managementFunction segment | UC002-F001, UC007-F001 |
| [`productordercaptureandvalidation-sec-dependent-API-v1`](productordercaptureandvalidation-sec-dependent-API-v1/Chart.yaml) | `productordercaptureandvalidation` | BDD test chart - the reference TMFC002-ProductOrderCaptureAndValidation ODA Component with a DependentAPI in its securityFunction segment | UC002-F001, UC007-F001 |
| [`productordercaptureandvalidation-v1`](productordercaptureandvalidation-v1/Chart.yaml) | `productordercaptureandvalidation` | BDD test chart - the reference TMFC002-ProductOrderCaptureAndValidation ODA Component, with DependentAPIs on a product catalog and a product inventory | UC002-F001, UC007-F001, UC007-F002 |

<!-- chart-inventory:end -->

## Adding or changing a test chart

1. **Start from a reference component.** Copy its chart from [reference-example-components](https://github.com/tmforum-oda/reference-example-components/tree/main/charts), and make only the changes your scenarios need.
2. **Record where the chart comes from.** In `Chart.yaml`, set `description` to say what the chart is, for example `BDD test chart - the reference TMFC001-ProductCatalogManagement ODA Component without the optional TMF671 Promotion Management API`. Add a comment naming the reference chart, its version and your changes.
3. **Use the reference components' images.** Use `tmforumodacanvas/*` images, never images from a personal Docker Hub account. `npm run check:selection` fails on any `lesterthomas/` image (#369).
4. **Keep Job templates identical across charts that share a release name.** Most features install their chart as release `ctk`, and move between charts with `helm upgrade`. Kubernetes can't change a Job's pod template, so two charts installed as `ctk` must render identical Jobs, for example `ctk-productcataloginitialization` and `ctk-roleinitialization`. A chart that needs different Jobs, such as one for another component, should use its own release name.
5. **Use the chart in a feature.** `npm run check:selection` fails on a chart that no feature uses. A change to a chart runs the BDD features that use it (see [Executing-tests.md](../Executing-tests.md)).
6. **Update the table.** Run `npm run chart-inventory`, and commit the updated README.
