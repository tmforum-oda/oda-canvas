// This TDD uses a utility library to interact with the technical implementation of a specific canvas with Apisix/Kong Gateway deployed.

const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)
const { isKongGatewayDeployed } = require('./ApiGatewayCheck');
const { isApisixGatewayDeployed } = require('./ApiGatewayCheck');
const NAMESPACE = 'components'
const DEFAULT_RELEASE_NAME = 'ctk'
setDefaultTimeout( 20 * 1000);

//To check kong gateway deployment status
Before({ tags: '@KongGateway' }, async function () {
  console.log('Checking if Kong Gateway is deployed...');
  const kongDeployed = await isKongGatewayDeployed();

  if (!kongDeployed) {
    console.log('Kong Gateway is not deployed. Skipping scenario.');
    return 'skipped';
  }

  console.log('Kong Gateway is deployed. Proceeding with scenario.');
});

//To check apisix gateway deployment status
Before({ tags: '@ApisixGateway' }, async function () {
  console.log('Checking if Apisix Gateway is deployed...');
  const apisixDeployed = await isApisixGatewayDeployed();

  if (!apisixDeployed) {
    console.log('Apisix Gateway is not deployed. Skipping scenario.');
    return 'skipped';
  }

  console.log('Apisix Gateway is deployed. Proceeding with scenario.');
});

//Common for both Apisix and Kong gateway
Given('a component {string} is deployed from package {string}', async function (componentName, packageName) {
  if (!global.currentReleaseName) {
    global.currentReleaseName = DEFAULT_RELEASE_NAME;
  }
  await packageManagerUtils.installPackage(packageName, global.currentReleaseName, NAMESPACE);
  const componentResource = await resourceInventoryUtils.getComponentResource(
    `${global.currentReleaseName}-${componentName}`,
    NAMESPACE
  );
  assert.ok(componentResource, `Component ${componentName} should be deployed.`);
});


/**
 * Delete a specified package using the packageManagerUtils.uninstallPackage function.
 *
 * @param {string} componentPackage - The name of the package to delete.
 */
Given('an existing API resource {string} on component {string} from package {string}', async function (resourceName, componentName, packageName) {
  const exposedAPI = await resourceInventoryUtils.getExposedAPIResource(resourceName, componentName, global.currentReleaseName, NAMESPACE);
  assert.ok(exposedAPI, `The ExposedAPI resource ${resourceName} should exist on component ${componentName}.`);
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the default release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 */
When('I install the {string} package for testing API resources', async function (componentPackage) {
  global.currentReleaseName = DEFAULT_RELEASE_NAME
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
  const delayAfterInstall = 5000; // Introduced a delay to allow for complete creation of resources. 5 seconds as faced issue in less than 5 sec
  console.log(`Waiting ${delayAfterInstall}ms after installing ${global.currentReleaseName}`);
  await new Promise(resolve => setTimeout(resolve, delayAfterInstall));
});

When('I delete the {string} package', async function (componentPackage) {
  await packageManagerUtils.uninstallPackage(global.currentReleaseName, NAMESPACE);
  const delayAfterUninstall = 5000; //Introduce a delay to allow for complete cleanup of resources. 5 seconds as faced issue in less than 5 sec
  console.log(`Waiting ${delayAfterUninstall}ms after uninstalling ${global.currentReleaseName}`);
  await new Promise(resolve => setTimeout(resolve, delayAfterUninstall));
});

/**
 * Verify that the specified ExposedAPI resource no longer exists.
 *
 * @param {string} resourceName - The name of the ExposedAPI resource to check.
 * @param {string} componentName - The name of the component to check.
 */
Then('I should not see the {string} ExposedAPI resources on the {string} component', async function (resourceName, componentName) {
  const exposedAPI = await resourceInventoryUtils.getExposedAPIResource(resourceName, componentName, global.currentReleaseName, NAMESPACE);
  if (!exposedAPI) {
    console.log(`ExposedAPI resource ${resourceName} successfully deleted.`);
  }
  assert.ok(!exposedAPI, `The ExposedAPI resources ${resourceName} should not exist.`);
});

/**
 * Verify the given package includes a component that has ExposedAPI in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} componentName - The name of the component.
 * @param {string} componentSegmentName - The name of the component segment.
 */
Given('an example package {string} with a {string} component in its {string} segment', async function (componentPackage, componentName, componentSegmentName) {
  const exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, 'ctk', componentSegmentName);
  assert.ok(exposedAPIs && exposedAPIs.length > 0, `The component segment ${componentSegmentName} should contain at least one ExposedAPI.`);
});


//For Kong BDDs
When('the Kong operator processes the deployment', function () {
});

Then('I should see an HTTPRoute resource created for {string}', async function (componentName) {
  const httpRoute = await resourceInventoryUtils.getHTTPRouteForComponent(componentName, NAMESPACE);
  assert.ok(httpRoute, `HTTPRoute for ${componentName} should exist.`);
});

/**
 * Wait for the Kong operator to process the deletion.
 * This step simulates waiting for the Kong operator to complete its task.
 */
When('the Kong operator processes the deletion', async function () {
  console.log('Waiting for Kong operator to process deletion...');
  await new Promise(resolve => setTimeout(resolve, 5000)); // Waiting for 5 seconds
});

/**
 * Verify that the HTTPRoute for a specified component no longer exists.
 *
 * @param {string} componentName - The name of the component to check.
 */
Then('I should not see an HTTPRoute resource for {string}', async function (componentName) {
  const httpRoute = await resourceInventoryUtils.getHTTPRouteForComponent(componentName, global.currentReleaseName, NAMESPACE);
  assert.ok(!httpRoute, `The HTTPRoute for ${componentName} should not exist.`);
});

Then('I should see an KongPlugin Rate Limit resource created for {string} with the name {string}', async function (componentName, RateLimitPluginName) {
  const kongPluginName = `${RateLimitPluginName}-ctk-${componentName}-${componentName}`;
  const kongplugin = await resourceInventoryUtils.getKongPluginForComponent(componentName, kongPluginName, NAMESPACE);
  assert.ok(kongplugin, `KongPlugin ${kongPluginName} for ${componentName} should exist.`);
});

Then('I should see an KongPlugin API Authentication resource created for {string} with the name {string}', async function (componentName, ApiAuthPluginName) {
  const kongPluginName = `${ApiAuthPluginName}-ctk-${componentName}-${componentName}`;
  const kongplugin = await resourceInventoryUtils.getKongPluginForComponent(componentName, kongPluginName, NAMESPACE);
  assert.ok(kongplugin, `KongPlugin ${kongPluginName} for ${componentName} should exist.`);
});

/**
 * Verify that the specific KongPlugin resources for a component no longer exist.
 *
 * @param {string} componentName - The name of the component to check.
 */
Then('I should not see an KongPlugin resource for {string}', async function (componentName) {
  const namespace = NAMESPACE;
  const apiAuthPluginName = `key-auth-ctk-${componentName}-${componentName}`;  
  const rateLimitPluginName = `rate-limit-ctk-${componentName}-${componentName}`; 
  console.log(`Checking that HTTPRoute or KongPlugin resources for ${componentName} do not exist in namespace ${namespace}`);
  const apiAuthPlugin = await resourceInventoryUtils.getKongPluginForComponent(componentName, apiAuthPluginName, namespace); 
  assert.ok(!apiAuthPlugin, `The KongPlugin ${apiAuthPluginName} for ${componentName} should not exist.`);
  const rateLimitPlugin = await resourceInventoryUtils.getKongPluginForComponent(componentName, rateLimitPluginName, namespace);
  assert.ok(!rateLimitPlugin, `The KongPlugin ${rateLimitPluginName} for ${componentName} should not exist.`);
});


//For Apisix BDDs
When('the Apisix operator processes the deployment', function () {
});
Then('I should see an ApisixRoute resource created for {string}', async function (componentName) {
  const ApisixRoute = await resourceInventoryUtils.getApisixRouteForComponent(componentName, NAMESPACE);
  assert.ok(ApisixRoute, `ApisixRoute for ${componentName} should exist.`);
});

/**
 * Wait for the Apisix operator to process the deletion.
 * This step simulates waiting for the Apisix operator to complete its task.
 */
When('the Apisix operator processes the deletion', async function () {
  console.log('Waiting for Apisix operator to process deletion...');
  await new Promise(resolve => setTimeout(resolve, 5000)); // Waiting for 5 seconds
});

/**
 * Verify that the ApisixRoute for a specified component no longer exists.
 *
 * @param {string} componentName - The name of the component to check.
 */
Then('I should not see an ApisixRoute resource for {string}', async function (componentName) {
  const apisixRoute = await resourceInventoryUtils.getApisixRouteForComponent(componentName, global.currentReleaseName, NAMESPACE);
  assert.ok(!apisixRoute, `The ApisixRoute for ${componentName} should not exist.`);
});

Then('I should see an ApisixPluginConfig Rate Limit resource created for {string} with the name {string}', async function (componentName, RateLimitPluginName) {
  const apisixPluginName = `combined-apisixpluginconfig-ctk-${componentName}-${componentName}`;
  const namespace = 'istio-ingress'; 
  console.log(`Checking ApisixPluginConfig: ${apisixPluginName} in namespace ${namespace} for ${RateLimitPluginName}`);
  const apisixplugin = await resourceInventoryUtils.getApisixPluginForComponent(componentName, apisixPluginName, namespace);
  assert.ok(apisixplugin, `ApisixPluginConfig ${apisixPluginName} for ${componentName} should exist.`);
});

Then('I should see an ApisixPluginConfig API Authentication resource created for {string} with the name {string}', async function (componentName, ApiAuthPluginName) {
  const apisixPluginName = `combined-apisixpluginconfig-ctk-${componentName}-${componentName}`;
  const namespace = 'istio-ingress'; 
  console.log(`Checking ApisixPluginConfig: ${apisixPluginName} in namespace ${namespace} for ${ApiAuthPluginName}`);
  const apisixplugin = await resourceInventoryUtils.getApisixPluginForComponent(componentName, apisixPluginName, namespace);
  assert.ok(apisixplugin, `ApisixPluginConfig ${apisixPluginName} for ${componentName} should exist.`);
});

/**
 * Verify that the ApisixPluginConfig for a specified component no longer exists.
 *
 * @param {string} componentName - The name of the component to check.
 */
Then('I should not see an ApisixPlugin resource for {string}', async function (componentName) {
  const namespace = 'istio-ingress'; // Namespace where the resource is expected to exist
  const apisixPluginName = `combined-apisixpluginconfig-ctk-${componentName}-${componentName}`; // Construct the resource name
  console.log(`Checking that ApisixPluginConfig ${apisixPluginName} does not exist in namespace ${namespace}`);
  const apisixplugin = await resourceInventoryUtils.getApisixPluginForComponent(componentName, apisixPluginName, namespace);
  assert.ok(!apisixplugin, `The ApisixPluginConfig ${apisixPluginName} for ${componentName} should not exist.`);
});



