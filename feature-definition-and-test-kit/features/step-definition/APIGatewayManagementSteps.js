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