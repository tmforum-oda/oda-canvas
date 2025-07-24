// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');
const identityManagerUtils = require('identity-manager-utils-keycloak');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);

const NAMESPACE = 'components';
const DEFAULT_RELEASE_NAME = 'ctk';
const COMPONENT_DEPLOY_TIMEOUT = 300 * 1000; // 5 minutes
const TIMEOUT_BUFFER = 5 * 1000; // 5 seconds as additional buffer to the timeouts above for the wrapping function
const CLEANUP_PACKAGE = false; // set to true to uninstall the package after each Scenario
const DEBUG_LOGS = false; // set to true to log the controller logs after each failed Scenario
global.currentReleaseName = null;
global.namespace = null;

setDefaultTimeout(20 * 1000);



//Allow skipping tests
Before({ tags: '@SkipTest' }, async function () {
  console.log('Skipping scenario.');
  return 'skipped';
});



/**
 * Verify the given package includes a component that has a specified number of ExposedAPIs in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} numberOfAPIs - The expected number of ExposedAPIs in the component segment.
 * @param {string} componentSegmentName - The name of the component segment.
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete.
 */
Given('an example package {string} with {string} ExposedAPI in its {string} segment', async function (componentPackage, numberOfAPIs, componentSegmentName) {
  console.log('\n=== Starting Package ExposedAPI Verification ===');
  console.log(`Verifying package '${componentPackage}' has ${numberOfAPIs} ExposedAPI(s) in '${componentSegmentName}' segment`);

  try {
    const exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, 'ctk', componentSegmentName);

    // Assert that there are the correct number of ExposedAPIs in the componentSegment
    assert.ok(exposedAPIs.length == numberOfAPIs, `The '${componentSegmentName}' segment should contain ${numberOfAPIs} ExposedAPI(s), but found ${exposedAPIs.length}`);
    
    console.log(`✅ Successfully verified ${exposedAPIs.length} ExposedAPI(s) in '${componentSegmentName}' segment`);
    
    if (DEBUG_LOGS) {
      console.log('Found ExposedAPIs:', JSON.stringify(exposedAPIs, null, 2));
    }
    
    console.log('=== Package ExposedAPI Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during package ExposedAPI verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Package: '${componentPackage}'`);
    console.error(`- Expected ExposedAPIs: ${numberOfAPIs}`);
    console.error(`- Component segment: '${componentSegmentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    console.error('Possible causes:');
    console.error('- Package does not exist or is not accessible');
    console.error('- Component segment not found in package');
    console.error('- ExposedAPI definitions missing or malformed in package');
    console.error('- Package manager utility configuration issue');
    
    console.log('=== Package ExposedAPI Verification Failed ===');
    throw error;
  }
});

/**
 * Verify the given package includes a component that has a specified number of DependentAPIs in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} numberOfAPIs - The expected number of DependentAPIs in the component segment.
 * @param {string} componentSegmentName - The name of the component segment.
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete.
 */
Given('an example package {string} with {string} DependentAPI in its {string} segment', async function (componentPackage, numberOfAPIs, componentSegmentName) {
  console.log('\n=== Starting Package DependentAPI Verification ===');
  console.log(`Verifying package '${componentPackage}' has ${numberOfAPIs} DependentAPI(s) in '${componentSegmentName}' segment`);

  try {
    const dependentAPIs = packageManagerUtils.getDependentAPIsFromPackage(componentPackage, 'ctk', componentSegmentName);
    
    // Assert that there are the correct number of DependentAPI in the componentSegment
    assert.ok(dependentAPIs.length == numberOfAPIs, `The '${componentSegmentName}' segment should contain ${numberOfAPIs} DependentAPI(s), but found ${dependentAPIs.length}`);
    
    console.log(`✅ Successfully verified ${dependentAPIs.length} DependentAPI(s) in '${componentSegmentName}' segment`);
    
    if (DEBUG_LOGS) {
      console.log('Found DependentAPIs:', JSON.stringify(dependentAPIs, null, 2));
    }
    
    console.log('=== Package DependentAPI Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during package DependentAPI verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Package: '${componentPackage}'`);
    console.error(`- Expected DependentAPIs: ${numberOfAPIs}`);
    console.error(`- Component segment: '${componentSegmentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    console.error('Possible causes:');
    console.error('- Package does not exist or is not accessible');
    console.error('- Component segment not found in package');
    console.error('- DependentAPI definitions missing or malformed in package');
    console.error('- Package manager utility configuration issue');
    
    console.log('=== Package DependentAPI Verification Failed ===');
    throw error;
  }
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the default release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 * @returns {Promise<void>} - A Promise that resolves when the package is installed.
 */
When('I install the {string} package', async function (componentPackage) {
  console.log('\n=== Starting Package Installation ===');
  console.log(`Installing package '${componentPackage}' with default release name '${DEFAULT_RELEASE_NAME}'`);
  
  try {
    global.currentReleaseName = DEFAULT_RELEASE_NAME;
    global.namespace = null
    await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE);
    
    console.log(`✅ Successfully installed package '${componentPackage}' as release '${global.currentReleaseName}'`);
    console.log('=== Package Installation Complete ===');

  } catch (error) {
    console.error(`❌ Error during package installation: ${error.message}`);
    console.error('Error details:');
    console.error(`- Package: '${componentPackage}'`);
    console.error(`- Release name: '${DEFAULT_RELEASE_NAME}'`);
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
    console.error('- Helm/package manager not properly configured');
    console.error('- Insufficient permissions to install packages');
    console.error('- Network connectivity issues to package repository');
    console.error('- Kubernetes cluster access issues');
    
    console.log('=== Package Installation Failed ===');
    throw error;
  }
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Same as When('I install the {string} package as release {string}')
 * but with language that reflects installing as a baseline for a test (Given).
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 */
Given('a baseline {string} package installed as release {string}', async function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  global.namespace = null
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the specified release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 */
When('I install the {string} package as release {string}', async function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  global.namespace = null
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the specified release name and namespace.
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 * @param {string} namespace - The name of the namespace.
 */
When('I install the {string} package as release {string} into namespace {string}', async function (componentPackage, releaseName, namespace) {
  global.currentReleaseName = releaseName
  global.namespace = namespace
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, global.namespace)
});

/**
 * Add and update a package repository.
 */
Given('the repository {string} with URL {string} is added and updated', async function (repoName, repoURL) {
  console.log(`Checking if package repo '${repoName}' exists...`);

  // Add package repo if not present
  await packageManagerUtils.addPackageRepoIfNotExists(repoName, repoURL);

  // Update the package repo to ensure latest index
  await packageManagerUtils.updatePackageRepo(repoName);
});


/**
 * Upgrade a specified package using the packageManagerUtils.upgradePackage function. Use the specified release name.
 *
 * @param {string} componentPackage - The name of the package to upgrade.
 * @param {string} releaseName - The name of the release name.
 */
When('I upgrade the {string} package as release {string}', async function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  await packageManagerUtils.upgradePackage(componentPackage, global.currentReleaseName, NAMESPACE)
});


/**
* Validate if a package has been installed (and install it if not) using the packageManagerUtils.installPackage function.
 *
 * @param {string} componentPackage - The name of the example component package to install.
 */
Given('an example package {string} has been installed', async function (componentPackage) {
  global.currentReleaseName = DEFAULT_RELEASE_NAME
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Installing a package from a repository.
 */
When('I install the {string} package as release {string} from the {string} repository', async function (packageName, releaseName, repoName) {
  console.log(`Installing package '${packageName}' as release '${releaseName}' from repo '${repoName}'...`);
  global.currentReleaseName = releaseName;

  // Install (or upgrade) the package from the specified repo
  await packageManagerUtils.installupgradePackageFromRepo(repoName, packageName, releaseName, NAMESPACE);
  console.log(`Successfully installed/upgraded package '${packageName}' as release '${releaseName}'.`);
});

/**
 * Wait for a specified component to have a deployment status of a specified value.
 *
 * @param {string} componentName - The name of the component to check.
 * @param {string} deploymentStatus - The expected deployment status of the component.
 * @returns {Promise<void>} - A Promise that resolves when the component has the expected deployment status.
 */
When('the {string} component has a deployment status of {string}', {timeout : COMPONENT_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (componentName, deploymentStatus) {
  let componentResource = null
  var startTime = performance.now()
  var endTime

  let namespace = global.namespace || NAMESPACE;
  
  console.log(`Waiting for component '${componentName}' in namespace '${namespace}' to have deployment status '${deploymentStatus}'...`);

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource( componentName, namespace)
    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT/1000 + " seconds")

    // check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('status')) || (!componentResource.status.hasOwnProperty('summary/status')) || (!componentResource.status['summary/status'].hasOwnProperty('deployment_status'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
      if (!(componentResource.status['summary/status']['deployment_status'] == deploymentStatus)) {
        componentResource = null // reset the componentResource to null so that we can try again
      }
    }
  }
});

/**
 * Upgrade a specified package using using the packageManagerUtils.upgradePackage function
 *
 * @param {string} componentPackage - The name of the package to upgrade.
 * @returns {void}
 */
When('I upgrade the {string} package', async function (componentPackage) {
  await packageManagerUtils.upgradePackage(componentPackage,   global.currentReleaseName, NAMESPACE)
});

/**
 * Wait for a specified version of a component to be available and assert that it was found within a specified timeout.
 *
 * @param {string} ComponentSpecVersion - The version of the component to check.
 * @param {string} componentName - The name of the component to check.
 * @returns {Promise<void>} - A Promise that resolves when the component is available.
 */
Then('I can query the {string} spec version of the {string} component', {timeout : COMPONENT_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (ComponentSpecVersion, componentName) {
  var startTime = performance.now()
  var endTime
  let componentResource = null
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResourceByVersion(componentName, ComponentSpecVersion, NAMESPACE)
    endTime = performance.now()
    // assert that the Component resource was found within COMPONENT_DEPLOY_TIMEOUT seconds
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The component should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")
  }
  assert.ok(componentResource, "The component resource should be found")
  assert.ok(componentResource.hasOwnProperty('spec'), "The component resource should be found with a spec property")
});

/**
 * Uninstall the specified package.
 *
 * @param {string} releaseName - The release name of the package to be uninstalled.
 */
Given('the release {string} is not installed', async function (releaseName) {
  await packageManagerUtils.uninstallPackage(releaseName, NAMESPACE)
});

/**
 * Uninstall the specified package.
 *
 * @param {string} releaseName - The release name of the package to be uninstalled.
 */
Given('the release {string} is uninstalled', async function (releaseName) {
  await packageManagerUtils.uninstallPackage(releaseName, NAMESPACE)
});

/**
 * Uninstall the specified package for the given release, so it ends up uninstalled.
 *
 * @param {string} releaseName - The release name to uninstall.
 */
Given('I uninstall the release {string}', async function (releaseName) {
  console.log(`Uninstalling release '${releaseName}'...`);
  await packageManagerUtils.uninstallPackage(releaseName, NAMESPACE);
});

/**
 * Uninstall the specified package for the given release and namespace, so it ends up uninstalled.
 *
 * @param {string} releaseName - The release name to uninstall.
 * @param {string} namespace - The name of the namespace.
 */
Given('I uninstall the release {string} from namespace {string}', async function (releaseName, namespace) {
  console.log(`Uninstalling release '${releaseName}' from namespace '${namespace}'...`);
  await packageManagerUtils.uninstallPackage(releaseName, namespace);
});
/**
 * Specified component need to have a deployment status of 'Complete' for the given release.
 *
 * @param {string} componentName - The name of the component to check.
 * @param {string} deploymentStatus - The expected deployment status of the component.
 * @returns {Promise<void>} - A Promise that resolves if the component is 'Complete', or throws if not.
 */
Given('the {string} component has a deployment status of {string} for the {string} release', {timeout : COMPONENT_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (componentName, deploymentStatus, releaseName) {
  let componentResource = null
  var startTime = performance.now()
  var endTime

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(componentName, NAMESPACE)
    // Logs for componentResource for debugging purpose 
    // console.log('Current componentResource:', JSON.stringify(componentResource, null, 2));

    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT/1000 + " seconds")

    // check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('status')) || (!componentResource.status.hasOwnProperty('summary/status')) || (!componentResource.status['summary/status'].hasOwnProperty('deployment_status'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
      if (!(componentResource.status['summary/status']['deployment_status'] == deploymentStatus)) {
        componentResource = null // reset the componentResource to null so that we can try again
      }
    }
  }
});

/**
 * Wait for the operator to process the uninstallation of component.
 */
When('the canvas operator process the uninstallation of components and exposedapis',
  async function () {
    console.log('Delay for the canvas operator to perform clean up...');
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
);

/**
 * Checks that a specified component resource does not exist after a given release has been uninstalled.
 *
 * @param {string} componentName - The name of the component to check.
 * @param {string} releaseName - The release name from which the component was uninstalled.
 */
Then('I should not see the {string} component after {string} release uninstall',
  async function (componentName, releaseName) {
    const compName = `${releaseName}-${componentName}`;

    // Attempt to fetch the component resource
    const componentResource = await resourceInventoryUtils.getComponentResource(compName, NAMESPACE);

    if (componentResource) {
      console.error(`Failure: Component "${compName}" still exists in namespace "${NAMESPACE}".`);
      throw new Error(`Component "${compName}" still exists in namespace "${NAMESPACE}" but should have been removed by canvas`);
    }

    console.log(`Success: No component found with the name "${compName}".`);
});

/**
 * Checks that a specified component resource does not exist after a given release and namespace has been uninstalled.
 *
 * @param {string} componentName - The name of the component to check.
 * @param {string} releaseName - The release name from which the component was uninstalled.
 * @param {string} namespace - The name of the namespace from which the component was uninstalled. 
 */
Then('I should not see the {string} component after {string} release uninstall from namespace {string}',
  async function (componentName, releaseName, namespace) {
    const compName = `${releaseName}-${componentName}`;

    // Attempt to fetch the component resource
    const componentResource = await resourceInventoryUtils.getComponentResource(compName, namespace);

    if (componentResource) {
      console.error(`Failure: Component "${compName}" still exists in namespace "${namespace}".`);
      throw new Error(`Component "${compName}" still exists in namespace "${namespace}" but should have been removed by canvas`);
    }

    console.log(`Success: No component found with the name "${compName}" in namespace "${namespace}".`);
});

/**
 * Code executed before each scenario.
 */
Before(async function (scenario) {
  console.log('\n\n============================================================================')
  console.log(`Feature:    ${scenario.gherkinDocument.feature.name}`);
  console.log(`Tags:       ${scenario.pickle.tags.map(tag => tag.name).join(', ')}`);
  console.log(`Scenario:   ${scenario.pickle.name}`);


  if (DEBUG_LOGS) {
    console.log('\n============================================================================')
    const scenarioName = scenario.pickle.name;
    console.log(`Running scenario: ${scenarioName}`);
    console.log('Scenario started at: ' + new Date().toISOString())
  }
});

/**
 * Code executed After each scenario
 * Optionally Uninstall the package associated with the release name and namespace.
 * Optionally Log the Canvas controller
 */
After(async function (scenario) {
  
  if (CLEANUP_PACKAGE) {
    await packageManagerUtils.uninstallPackage(  global.currentReleaseName, NAMESPACE)   
  }

  if (DEBUG_LOGS) {
    console.log()
    console.log('Scenario status: ' + scenario.result.status)
    if (true) { //(scenario.result.status === 'FAILED') {
      console.log('------------------------------------------------------------------')
      console.log('Controller logs:')
      try {
        console.log()
        console.log('==================================================================')
        console.log('Operator logs for : component-operator')
        console.log(await resourceInventoryUtils.getOperatorLogs('component-operator', null))  
        console.log()
        console.log('==================================================================')
        console.log('Operator logs for : api-operator-istio')
        console.log(await resourceInventoryUtils.getOperatorLogs('api-operator-istio', null))  
        console.log()
        console.log('==================================================================')
        console.log('Operator logs for : identityconfig-operator-keycloak, identityconfig-operator-keycloak')
        console.log(await resourceInventoryUtils.getOperatorLogs('identityconfig-operator-keycloak', 'identityconfig-operator-keycloak'))  
        console.log()
        console.log('==================================================================')
        console.log('Operator logs for : dependent-api-simple-operator', null)
        console.log(await resourceInventoryUtils.getOperatorLogs('canvas-depapi-op'))  
      } catch (error) {
        console.log('Error getting operator logs: ' + error)
      }
      console.log('------------------------------------------------------------------')
    } 
    console.log()
    console.log('Scenario ended at: ' + new Date().toISOString())
  }

});

/**
 * Verify the given package includes a component that has a specific ExposedAPI by name in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} apiName - The name of the ExposedAPI to find.
 * @param {string} componentSegmentName - The name of the component segment.
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete.
 */
Given('An example package {string} with a {string} ExposedAPI in its {string} segment', async function (componentPackage, apiName, componentSegmentName) {
  console.log('\n=== Starting Package ExposedAPI by Name Verification ===');
  console.log(`Verifying package '${componentPackage}' has ExposedAPI '${apiName}' in '${componentSegmentName}' segment`);
  
  try {

    const exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, 'ctk', componentSegmentName);
    console.log(`Found ExposedAPIs in '${componentSegmentName}':`, JSON.stringify(exposedAPIs, null, 2));

    // Find the specific API by name
    foundAPI = null;
    for (const api of exposedAPIs) {
      // get name from api
      const exposedapiName = api['name'];
      console.log(`Checking ExposedAPI: ${exposedapiName}`);
      if (exposedapiName === apiName) {
        foundAPI = api;
        console.log(`✅ Found ExposedAPI '${apiName}' in '${componentSegmentName}' segment`);
      }
    }
      
    assert.ok(foundAPI, `The '${componentSegmentName}' segment should contain ExposedAPI '${apiName}', but it was not found. Found APIs: ${exposedAPIs.map(api => api.name).join(', ')}`);

    console.log(`✅ Successfully verified ExposedAPI '${apiName}' exists in '${componentSegmentName}' segment`);
    
    if (DEBUG_LOGS) {
      console.log('Found ExposedAPI:', JSON.stringify(foundAPI, null, 2));
      console.log('All ExposedAPIs:', JSON.stringify(exposedAPIs, null, 2));
    }
    
    console.log('=== Package ExposedAPI by Name Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during package ExposedAPI by name verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- Package: '${componentPackage}'`);
    console.error(`- Expected ExposedAPI: '${apiName}'`);
    console.error(`- Component segment: '${componentSegmentName}'`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    console.error('Possible causes:');
    console.error('- Package does not exist or is not accessible');
    console.error('- Component segment not found in package');
    console.error(`- ExposedAPI '${apiName}' not defined in '${componentSegmentName}' segment`);
    console.error('- ExposedAPI definitions missing or malformed in package');
    console.error('- Package manager utility configuration issue');
    
    console.log('=== Package ExposedAPI by Name Verification Failed ===');
    throw error;
  }
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the specified release name.
 * This is similar to "I install the {string} package as release {string}" but with different wording.
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 */
When('I install the {string} package with release name {string}', async function (componentPackage, releaseName) {
  console.log(`\n=== Installing Package with Release Name ===`);
  console.log(`Installing package '${componentPackage}' with release name '${releaseName}'`);
  
  global.currentReleaseName = releaseName;
  global.namespace = null;
  
  try {
    await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE);
    console.log(`✅ Successfully installed package '${componentPackage}' with release name '${releaseName}'`);
  } catch (error) {
    console.error(`❌ Failed to install package '${componentPackage}' with release name '${releaseName}': ${error.message}`);
    throw error;
  }
});
