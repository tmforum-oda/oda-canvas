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
const releaseName = 'ctk'
const COMPONENT_DEPLOY_TIMEOUT = 100 * 1000 // 100 seconds
const API_DEPLOY_TIMEOUT = 10 * 1000 // 10 seconds
const API_URL_TIMEOUT = 60 * 1000 // 60 seconds
const API_READY_TIMEOUT = 120 * 1000 // 60 seconds
const TIMEOUT_BUFFER = 5 * 1000 // 5 seconds as additional buffer to the timeouts above for the wrapping function
const CLEANUP_PACKAGE = true // set to true to uninstall the package after each test

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
 * Install a specified package using the packageManagerUtils.installPackage function.
 *
 * @param {string} componentPackage - The name of the package to install.
 */
When('I install the {string} package', function (componentPackage) {
  packageManagerUtils.installPackage(componentPackage, releaseName, NAMESPACE)
});

/**
 * Validate if a package has been installed (and install it if not) using the packageManagerUtils.installPackage function.
 *
 * @param {string} componentPackage - The name of the example component package to install.
 */
Given('An example package {string} has been installed', function (componentPackage) {
  packageManagerUtils.installPackage(componentPackage, releaseName, NAMESPACE)
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
    componentResource = await resourceInventoryUtils.getComponentResource(releaseName + '-' + componentName, NAMESPACE)
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
  packageManagerUtils.upgradePackage(componentPackage, releaseName, NAMESPACE)
});


/**
 * Wait for a specified API resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} APINamspece - The name of the API resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is available.
 */
Then('I should see the {string} API resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (APIName, componentName) {
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, releaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The API resource should be found within " + API_DEPLOY_TIMEOUT + " seconds")
  }
});


/**
 * Wait for a specified API resource to be removed and assert that it was removed within a specified timeout.
 *
 * @param {string} APIName - The name of the API resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is removed.
 */
Then('I should not see the {string} API resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (APIName, componentName) {
  // set the initial value of apiResource to 'not null'
  let apiResource = 'not null'
  var startTime = performance.now()
  var endTime

  // wait until the API resource is removed or the timeout is reached
  while (apiResource != null) {
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, releaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was removed within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The API resource should be removed within " + API_DEPLOY_TIMEOUT + " seconds")
  }

});

/**
 * Wait for a specified API resource to have a URL on the Service Mesh or Gateway and assert that it was found within a specified timeout.
 *
 * @param {string} APIName - The name of the API resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource has a URL on the Service Mesh or Gateway.
 */
Then('I should see the {string} API resource on the {string} component with a url on the Service Mesh or Gateway', {timeout : API_URL_TIMEOUT + TIMEOUT_BUFFER}, async function (APIName, componentName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, releaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_URL_TIMEOUT, "The url should be found within " + API_URL_TIMEOUT + " seconds")

    // check if there is a url on the API resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('apiStatus')) || (!apiResource.status.apiStatus.hasOwnProperty('url'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }

});

Then('I should see the {string} API resource on the {string} component with an implementation ready status on the Service Mesh or Gateway', {timeout : API_READY_TIMEOUT + TIMEOUT_BUFFER}, async function (APIName, componentName) {
  // get the API resource
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, releaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_READY_TIMEOUT, "The ready status should be found within " + API_READY_TIMEOUT + " seconds")

    // check if there is a url on the API resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('implementation')) || (!apiResource.status.implementation.hasOwnProperty('ready'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    } else if (!(apiResource.status.implementation.ready == true)) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
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
    componentResource = await resourceInventoryUtils.getComponentResourceByVersion(releaseName + '-' + componentName, ComponentSpecVersion, NAMESPACE)
    endTime = performance.now()
    // assert that the Component resource was found within COMPONENT_DEPLOY_TIMEOUT seconds
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The component should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")
  }
  assert.ok(componentResource, "The component resource should be found")
  assert.ok(componentResource.hasOwnProperty('spec'), "The component resource should be found with a spec property")
});

/**
 * Check for role to be assigned to the security operator in identity management.
 *
 * @param {string} operatorUserName - the username of the operator to check.
 * @param {string} componentName - The name of the component to check.
 * @returns {Promise<void>} - A Promise that resolves when the component is available.
 */
Then('I should see the predefined role assigned to the {string} user for the {string} component in the identity platform', async function (operatorUserName, componentName) {
  let componentResource = null
  let secconRole = null
  var startTime = performance.now()
  var endTime

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(releaseName + '-' + componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")

    // check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('spec')) || (!componentResource.spec.hasOwnProperty('securityFunction')) || (!componentResource.spec.securityFunction.hasOwnProperty('controllerRole'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
      secconRole = componentResource.spec.securityFunction.controllerRole;
      allUserRoles = await identityManagerUtils.getRolesForUser(operatorUserName, releaseName, componentName);
      //return 'pending';
      assert.ok(allUserRoles.includes(secconRole), 'The predefine role for the security operator should be correctly assigned in the identity platform');
    }
  }
});

/**
 * Uninstall the package associated with the release name and namespace.
 */
AfterAll(function () {
  if (CLEANUP_PACKAGE) {
    packageManagerUtils.uninstallPackage(releaseName, NAMESPACE)   
  }
});
