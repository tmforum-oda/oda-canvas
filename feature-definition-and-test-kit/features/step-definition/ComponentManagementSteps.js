// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');
const identityManagerUtils = require('identity-manager-utils-keycloak');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
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
const CLEANUP_PACKAGE = true // set to true to uninstall the package after each test
global.currentReleaseName = null;

setDefaultTimeout( 20 * 1000);

/**
 * Verify the given package includes a component that has a specified number of APIs in a specific segment.
 *
 * @param {string} componentPackage - The name of the example package.
 * @param {string} componentName - The name of the component.
 * @param {string} numberOfAPIs - The expected number of APIs in the component segment.
 * @param {string} componentSegmentName - The name of the component segment.
 */
Given('An example package {string} with a {string} component with {string} API in its {string} segment', async function (componentPackage, componentName, numberOfAPIs, componentSegmentName) {
  exposedAPIs = packageManagerUtils.getExposedAPIsFromPackage(componentPackage, 'ctk', componentSegmentName)
  // assert that there are the correct number of APIs in the componentSegment
  assert.ok(exposedAPIs.length == numberOfAPIs, "The componentSegment should contain " + numberOfAPIs + " API")
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the default release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 */
When('I install the {string} package', function (componentPackage) {
  global.currentReleaseName = DEFAULT_RELEASE_NAME
  packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Same as When('I install the {string} package as release {string}')
 * but with language that reflects installing as a baseline for a test (Given).
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 */
Given('A baseline {string} package installed as release {string}', function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Install a specified package using the packageManagerUtils.installPackage function. Use the specified release name.
 *
 * @param {string} componentPackage - The name of the package to install.
 * @param {string} releaseName - The name of the release name.
 */
When('I install the {string} package as release {string}', function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
});

/**
 * Upgrade a specified package using the packageManagerUtils.upgradePackage function. Use the specified release name.
 *
 * @param {string} componentPackage - The name of the package to upgrade.
 * @param {string} releaseName - The name of the release name.
 */
When('I upgrade the {string} package as release {string}', function (componentPackage, releaseName) {
  global.currentReleaseName = releaseName
  packageManagerUtils.upgradePackage(componentPackage, global.currentReleaseName, NAMESPACE)
});


/**
 * Validate if a package has been installed (and install it if not) using the packageManagerUtils.installPackage function.
 *
 * @param {string} componentPackage - The name of the example component package to install.
 */
Given('An example package {string} has been installed', function (componentPackage) {
  global.currentReleaseName = DEFAULT_RELEASE_NAME
  packageManagerUtils.installPackage(componentPackage, global.currentReleaseName, NAMESPACE)
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

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(  global.currentReleaseName + '-' + componentName, NAMESPACE)
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
When('I upgrade the {string} package', function (componentPackage) {
  packageManagerUtils.upgradePackage(componentPackage,   global.currentReleaseName, NAMESPACE)
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
 * Uninstall the package associated with the release name and namespace.
 */
AfterAll(function () {
  if (CLEANUP_PACKAGE) {
    packageManagerUtils.uninstallPackage(  global.currentReleaseName, NAMESPACE)   
  }
});
