// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');
const identityManagerUtils = require('identity-manager-utils-keycloak');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)

const NAMESPACE = 'components'
const DEFAULT_RELEASE_NAME = 'ctk'
const COMPONENT_DEPLOY_TIMEOUT = 100 * 1000 // 100 seconds
const API_DEPLOY_TIMEOUT = 10 * 1000 // 10 seconds
const API_URL_TIMEOUT = 60 * 1000 // 60 seconds
const API_READY_TIMEOUT = 120 * 1000 // 60 seconds
const TIMEOUT_BUFFER = 5 * 1000 // 5 seconds as additional buffer to the timeouts above for the wrapping function
const CLEANUP_PACKAGE = false // set to true to uninstall the package after each Scenario
const DEBUG_LOGS = true // set to true to log the controller logs after each failed Scenario
global.currentReleaseName = null;
global.namespace = null;

setDefaultTimeout( 20 * 1000);



//Allow skipping tests
Before({ tags: '@SkipTest' }, async function () {
  console.log('Skipping scenario.');
  return 'skipped';
});



/**
 * Verify the given package includes a component that has a specified number of ExposedAPIs in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} componentName - The name of the component.
 * @param {string} numberOfAPIs - The expected number of ExposedAPIs in the component segment.
 * @param {string} componentSegmentName - The name of the component segment.
 */
Given('an example package {string} with a {string} component with {string} ExposedAPI in its {string} segment', async function (componentPackage, componentName, numberOfAPIs, componentSegmentName) {
  exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, 'ctk', componentSegmentName)
  // assert that there are the correct number of ExposedAPIs in the componentSegment
  assert.ok(exposedAPIs.length == numberOfAPIs, "The componentSegment should contain " + numberOfAPIs + " ExposedAPI")
});

/**
 * Verify the given package includes a component that has a specified number of DependentAPIs in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} componentName - The name of the component.
 * @param {string} numberOfAPIs - The expected number of DependentAPIs in the component segment.
 * @param {string} componentSegmentName - The name of the component segment.
 */
Given('an example package {string} with a {string} component with {string} DependentAPI in its {string} segment', async function (componentPackage, componentName, numberOfAPIs, componentSegmentName) {
  dependentAPIs = packageManagerUtils.getDependentAPIsFromPackage(componentPackage, 'ctk', componentSegmentName)
  // assert that there are the correct number of DependentAPI in the componentSegment
  assert.ok(dependentAPIs.length == numberOfAPIs, "The componentSegment should contain " + numberOfAPIs + " DependentAPI")
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the default release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 */
When('I install the {string} package', async function (componentPackage) {
	global.currentReleaseName = DEFAULT_RELEASE_NAME
	global.namespace = null
  await packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
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
  
  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(  global.currentReleaseName + '-' + componentName, namespace)
    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")

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
    componentResource = await resourceInventoryUtils.getComponentResourceByVersion(  global.currentReleaseName + '-' + componentName, ComponentSpecVersion, NAMESPACE)
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
 * @param {string} packageName - The name of the package to be uninstalled.
 * @param {string} releaseName - The release name to uninstall.
 */
Given('I uninstall the {string} package as release {string}', async function (packageName, releaseName) {
  console.log(`Uninstalling package '${packageName}' with release '${releaseName}'...`);
  await packageManagerUtils.uninstallPackage(releaseName, NAMESPACE);
});

/**
 * Uninstall the specified package for the given release and namespace, so it ends up uninstalled.
 *
 * @param {string} packageName - The name of the package to be uninstalled.
 * @param {string} releaseName - The release name to uninstall.
 * @param {string} namespace - The name of the namespace.
 */
Given('I uninstall the {string} package as release {string} from namespace {string}', async function (packageName, releaseName, namespace) {
  console.log(`Uninstalling package '${packageName}' with release '${releaseName}' from namespace '${namespace}'...`);
  // global.currentReleaseName = releaseName
  // global.namespace = namespace
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
    componentResource = await resourceInventoryUtils.getComponentResource(  releaseName + '-' + componentName, NAMESPACE)
    // Logs for componentResource for debugging purpose 
    // console.log('Current componentResource:', JSON.stringify(componentResource, null, 2));

    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")

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
  if (DEBUG_LOGS) {
    console.log()
    console.log('==================================================================')
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
