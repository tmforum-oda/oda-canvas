// This TDD uses a utility library to interact with the technical implementation of a specific canvas with Apisix/Kong Gateway deployed.

const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);
const { isKongGatewayDeployed } = require('./ApiGatewayCheck');
const { isApisixGatewayDeployed } = require('./ApiGatewayCheck');

const NAMESPACE = 'components';
const DEFAULT_RELEASE_NAME = 'ctk';
const DEBUG_LOGS = false; // set to true for verbose debugging

setDefaultTimeout(20 * 1000);

//To check kong gateway deployment status
Before({ tags: '@KongGateway' }, async function () {
  console.log('\n=== Kong Gateway Deployment Check ===');
  console.log('Checking if Kong Gateway is deployed...');
  
  try {
    const kongDeployed = await isKongGatewayDeployed();

    if (!kongDeployed) {
      console.log('Kong Gateway is not deployed. Skipping scenario.');
      return 'skipped';
    }

    console.log('✅ Kong Gateway is deployed. Proceeding with scenario.');
    console.log('=== Kong Gateway Deployment Check Complete ===');

  } catch (error) {
    console.error(`❌ Error checking Kong Gateway deployment: ${error.message}`);
    console.error('Possible causes:');
    console.error('- Kong Gateway not installed or configured properly');
    console.error('- Kubernetes cluster access issues');
    console.error('- Required Gateway API CRDs not installed');
    throw error;
  }
});

//To check apisix gateway deployment status
Before({ tags: '@ApisixGateway' }, async function () {
  console.log('\n=== Apisix Gateway Deployment Check ===');
  console.log('Checking if Apisix Gateway is deployed...');
  
  try {
    const apisixDeployed = await isApisixGatewayDeployed();

    if (!apisixDeployed) {
      console.log('Apisix Gateway is not deployed. Skipping scenario.');
      return 'skipped';
    }

    console.log('✅ Apisix Gateway is deployed. Proceeding with scenario.');
    console.log('=== Apisix Gateway Deployment Check Complete ===');

  } catch (error) {
    console.error(`❌ Error checking Apisix Gateway deployment: ${error.message}`);
    console.error('Possible causes:');
    console.error('- Apisix Gateway not installed or configured properly');
    console.error('- Kubernetes cluster access issues');
    console.error('- Apisix service not accessible or ready');
    throw error;
  }
});

//Common for both Apisix and Kong gateway
/**
 * Deploy a component from a package and verify its deployment status.
 *
 * @param {string} componentName - The name of the component to deploy.
 * @param {string} packageName - The name of the package containing the component.
 * @returns {Promise<void>} - A Promise that resolves when the component is deployed.
 */
Given('a component {string} is deployed from package {string}', async function (componentName, packageName) {
  console.log('\n=== Starting Component Deployment ===');
  console.log(`Deploying component '${componentName}' from package '${packageName}'`);
  
  try {
    if (!global.currentReleaseName) {
      global.currentReleaseName = DEFAULT_RELEASE_NAME;
    }
    
    console.log(`Using release name: '${global.currentReleaseName}'`);
    await packageManagerUtils.installPackage(packageName, global.currentReleaseName, NAMESPACE);
    
    console.log(`✅ Package '${packageName}' installed successfully`);
    
    // Verify component resource is created
    const componentResource = await resourceInventoryUtils.getComponentResource(
      `${global.currentReleaseName}-${componentName}`,
      NAMESPACE
    );
    
    assert.ok(componentResource, `Component '${componentName}' should be deployed from package '${packageName}'`);
    
    console.log(`✅ Component '${componentName}' successfully deployed and verified`);
    console.log('=== Component Deployment Complete ===');

  } catch (error) {
    console.error(`❌ Error during component deployment: ${error.message}`);
    console.error('Error details:');
    console.error(`- Component: '${componentName}'`);
    console.error(`- Package: '${packageName}'`);
    console.error(`- Release name: '${global.currentReleaseName}'`);
    console.error(`- Namespace: '${NAMESPACE}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Package not found in configured repositories');
    console.error('- Component definition missing or invalid in package');
    console.error('- Canvas Component operator not running');
    console.error('- Kubernetes cluster resource constraints');
    console.error('- Insufficient permissions to deploy components');
    
    console.log('=== Component Deployment Failed ===');
    throw error;
  }
});

// The gateway operators act asynchronously on ExposedAPI events, so the checks below poll
// until the gateway resource appears (or disappears) instead of sleeping for a fixed time.
const GATEWAY_RESOURCE_TIMEOUT = 60 * 1000; // 60 seconds
const GATEWAY_POLL_INTERVAL = 2 * 1000; // 2 seconds
const TIMEOUT_BUFFER = 5 * 1000; // additional buffer for the wrapping step

/**
 * Poll a lookup until it returns a resource (expectPresent=true) or null (expectPresent=false).
 *
 * @param {Function} lookup - Async function that returns the resource or null.
 * @param {boolean} expectPresent - Whether to wait for the resource to exist or to be removed.
 * @returns {Promise<Object|null>} - The last lookup result.
 */
async function waitForGatewayResource(lookup, expectPresent) {
  const startTime = performance.now();
  let resource = await lookup();
  while (Boolean(resource) !== expectPresent && performance.now() - startTime < GATEWAY_RESOURCE_TIMEOUT) {
    await new Promise(resolve => setTimeout(resolve, GATEWAY_POLL_INTERVAL));
    resource = await lookup();
  }
  return resource;
}

/**
 * Verify that an ExposedAPI created by an earlier scenario still exists.
 *
 * @param {string} resourceName - The name of the ExposedAPI in the component spec.
 * @param {string} componentName - The name of the component.
 * @param {string} packageName - The name of the package the component was installed from.
 */
Given('an existing API resource {string} on component {string} from package {string}', async function (resourceName, componentName, packageName) {
  const exposedAPI = await resourceInventoryUtils.getExposedAPIResource(resourceName, componentName, NAMESPACE);
  assert.ok(exposedAPI, `The ExposedAPI resource ${resourceName} should exist on component ${componentName} (package ${packageName}).`);
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the default release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 */
When('I install the {string} package for testing API resources', async function (componentPackage) {
  global.currentReleaseName = DEFAULT_RELEASE_NAME;
  global.namespace = null;
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE);
});

When('I delete the {string} package', async function (componentPackage) {
  await packageManagerUtils.uninstallPackage(global.currentReleaseName || DEFAULT_RELEASE_NAME, NAMESPACE);
});

/**
 * Verify the given package includes a component that has ExposedAPI in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} componentName - The name of the component.
 * @param {string} componentSegmentName - The name of the component segment.
 */
Given('an example package {string} with a {string} component in its {string} segment', async function (componentPackage, componentName, componentSegmentName) {
  const exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, DEFAULT_RELEASE_NAME, componentSegmentName);
  assert.ok(exposedAPIs && exposedAPIs.length > 0, `The component segment ${componentSegmentName} should contain at least one ExposedAPI.`);
});


//For Kong BDDs
When('the Kong operator processes the deployment', function () {
});

When('the Kong operator processes the deletion', function () {
});

Then('I should see an HTTPRoute resource created for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (apiName, componentName) {
  const httpRoute = await waitForGatewayResource(
    () => resourceInventoryUtils.getHTTPRouteForComponent(componentName, apiName, NAMESPACE), true);
  assert.ok(httpRoute, `HTTPRoute for ExposedAPI ${apiName} on ${componentName} should exist within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

Then('I should not see an HTTPRoute resource for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (apiName, componentName) {
  const httpRoute = await waitForGatewayResource(
    () => resourceInventoryUtils.getHTTPRouteForComponent(componentName, apiName, NAMESPACE), false);
  assert.ok(!httpRoute, `HTTPRoute ${httpRoute?.metadata?.name} for ExposedAPI ${apiName} on ${componentName} should be removed within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

/**
 * Verify that the Kong operator created a KongPlugin for an ExposedAPI.
 *
 * @param {string} pluginPrefix - The KongPlugin name prefix the Kong operator uses (e.g. 'rate-limit', 'apiauthentication').
 */
Then('I should see a {string} KongPlugin resource created for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (pluginPrefix, apiName, componentName) {
  const kongPlugin = await waitForGatewayResource(
    () => resourceInventoryUtils.getKongPluginForComponent(componentName, apiName, pluginPrefix, NAMESPACE), true);
  assert.ok(kongPlugin, `KongPlugin ${pluginPrefix} for ExposedAPI ${apiName} on ${componentName} should exist within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

Then('I should not see a {string} KongPlugin resource for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (pluginPrefix, apiName, componentName) {
  const kongPlugin = await waitForGatewayResource(
    () => resourceInventoryUtils.getKongPluginForComponent(componentName, apiName, pluginPrefix, NAMESPACE), false);
  assert.ok(!kongPlugin, `KongPlugin ${kongPlugin?.metadata?.name} for ExposedAPI ${apiName} on ${componentName} should be removed within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});


//For Apisix BDDs
When('the Apisix operator processes the deployment', function () {
});

When('the Apisix operator processes the deletion', function () {
});

Then('I should see an ApisixRoute resource created for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (apiName, componentName) {
  const apisixRoute = await waitForGatewayResource(
    () => resourceInventoryUtils.getApisixRouteForComponent(componentName, apiName), true);
  assert.ok(apisixRoute, `ApisixRoute for ExposedAPI ${apiName} on ${componentName} should exist within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

Then('I should not see an ApisixRoute resource for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (apiName, componentName) {
  const apisixRoute = await waitForGatewayResource(
    () => resourceInventoryUtils.getApisixRouteForComponent(componentName, apiName), false);
  assert.ok(!apisixRoute, `ApisixRoute ${apisixRoute?.metadata?.name} for ExposedAPI ${apiName} on ${componentName} should be removed within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

/**
 * Verify that the APISIX operator's combined ApisixPluginConfig for an ExposedAPI includes a plugin.
 *
 * @param {string} pluginName - The APISIX plugin name (e.g. 'limit-req', 'key-auth').
 */
Then('I should see an ApisixPluginConfig with the {string} plugin for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (pluginName, apiName, componentName) {
  const hasPlugin = (config) => (config?.spec?.plugins || []).some(plugin => plugin.name === pluginName);
  const apisixPluginConfig = await waitForGatewayResource(async () => {
    const config = await resourceInventoryUtils.getApisixPluginForComponent(componentName, apiName);
    return hasPlugin(config) ? config : null;
  }, true);
  assert.ok(apisixPluginConfig, `ApisixPluginConfig for ExposedAPI ${apiName} on ${componentName} should include the ${pluginName} plugin within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});

Then('I should not see an ApisixPluginConfig for the {string} ExposedAPI on the {string} component', {timeout: GATEWAY_RESOURCE_TIMEOUT + TIMEOUT_BUFFER}, async function (apiName, componentName) {
  const apisixPluginConfig = await waitForGatewayResource(
    () => resourceInventoryUtils.getApisixPluginForComponent(componentName, apiName), false);
  assert.ok(!apisixPluginConfig, `ApisixPluginConfig ${apisixPluginConfig?.metadata?.name} for ExposedAPI ${apiName} on ${componentName} should be removed within ${GATEWAY_RESOURCE_TIMEOUT} milliseconds.`);
});
