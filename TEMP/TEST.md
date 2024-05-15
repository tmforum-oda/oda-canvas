# Canvas BDD Tests



## install code-server in cluster

```
TEMP/code-server/install-code-server.sh
```

in Browser open https://code-server.ihc-dt.cluster-3.de

## install helm and node 

Helm and node.js are preinstalled in the image, for details look here: 
[code-server/code-server-with-helm-and-node/Dockerfile](code-server/code-server-with-helm-and-node/Dockerfile)

## clone repo

```
mkdir ~/git
cd ~/git
git clone -b odaa-26 https://github.com/ODA-CANVAS-FORK/oda-canvas-component-vault.git
```

## install npm packages

```
cd ~/git/oda-canvas-component-vault/feature-definition-and-test-kit

cd identity-manager-utils-keycloak
npm install
cd ../package-manager-utils-helm
npm install
cd ../resource-inventory-utils-kubernetes
npm install
cd ..
npm install
```

## run tests

```
export KEYCLOAK_USER=admin 
export KEYCLOAK_PASSWORD=adpass 
export KEYCLOAK_BASE_URL=http://canvas-keycloak.canvas.svc.cluster.local:8083/auth/ 
export KEYCLOAK_REALM=myrealm
  
npm start
```

## Output:

```
> ODA Canvas BDD tests@0.0.1 start
> cucumber-js  --publish

(node:3664) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
.........................................UUUUUUUUUUUUUUU............

Failures:

1) Scenario: Install component and test Observability config # features/UC012-F001-View-Functional-Observability.feature:9
   ? Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
       Undefined. Implement with the following snippet:

         Given('I install a package {string} with a metrics API {string} and release name {string}', function (string, string2, string3) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? When the component 'ctk-productcatalog' has a deployment status of 'Complete'
       Undefined. Implement with the following snippet:

         When('the component {string} has a deployment status of {string}', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? Then the Observability platform monitors the 'metrics' endpoint
       Undefined. Implement with the following snippet:

         Then('the Observability platform monitors the {string} endpoint', function (string) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       

2) Scenario: Uninstall component and test Observability config is cleaned up # features/UC012-F001-View-Functional-Observability.feature:14
   ? Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
       Undefined. Implement with the following snippet:

         Given('I install a package {string} with a metrics API {string} and release name {string}', function (string, string2, string3) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? And the component 'ctk-productcatalog' has a deployment status of 'Complete'
       Undefined. Implement with the following snippet:

         Given('the component {string} has a deployment status of {string}', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? When I uninstall the package with release 'ctk'
       Undefined. Implement with the following snippet:

         When('I uninstall the package with release {string}', function (string) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? Then the Observability platform does not monitor the 'metrics' endpoint
       Undefined. Implement with the following snippet:

         Then('the Observability platform does not monitor the {string} endpoint', function (string) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       

3) Scenario: Install component and view Observability metrics # features/UC012-F001-View-Functional-Observability.feature:28
   ? Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
       Undefined. Implement with the following snippet:

         Given('I install a package {string} with a metrics API {string} and release name {string}', function (string, string2, string3) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? And the component 'ctk-productcatalog' has a deployment status of 'Complete'
       Undefined. Implement with the following snippet:

         Given('the component {string} has a deployment status of {string}', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? When A user creates a 'category' in the 'productcatalog' component
       Undefined. Implement with the following snippet:

         When('A user creates a {string} in the {string} component', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? Then the Observability platform shows the 'createCategory' metrics
       Undefined. Implement with the following snippet:

         Then('the Observability platform shows the {string} metrics', function (string) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       

4) Scenario: Install component and view Observability metrics # features/UC012-F001-View-Functional-Observability.feature:29
   ? Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
       Undefined. Implement with the following snippet:

         Given('I install a package {string} with a metrics API {string} and release name {string}', function (string, string2, string3) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? And the component 'ctk-productcatalog' has a deployment status of 'Complete'
       Undefined. Implement with the following snippet:

         Given('the component {string} has a deployment status of {string}', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? When A user creates a 'catalog' in the 'productcatalog' component
       Undefined. Implement with the following snippet:

         When('A user creates a {string} in the {string} component', function (string, string2) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       
   ? Then the Observability platform shows the 'createCatalog' metrics
       Undefined. Implement with the following snippet:

         Then('the Observability platform shows the {string} metrics', function (string) {
           // Write code here that turns the phrase above into concrete actions
           return 'pending';
         });
       

20 scenarios (4 undefined, 16 passed)
68 steps (15 undefined, 53 passed)
1m50.451s (executing steps: 1m49.075s)
┌──────────────────────────────────────────────────────────────────────────┐
│ View your Cucumber Report at:                                            │
│ https://reports.cucumber.io/reports/52aedd68-6977-43e9-ade4-0d940c1354c9 │
│                                                                          │
│ This report will self-destruct in 24h.                                   │
│ Keep reports forever: https://reports.cucumber.io/profile                │
└──────────────────────────────────────────────────────────────────────────┘
```