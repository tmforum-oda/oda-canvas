// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)

const NAMESPACE = 'components'
const API_DEPLOY_TIMEOUT = 10 * 1000 // 10 seconds
const API_URL_TIMEOUT = 60 * 1000 // 60 seconds
const API_READY_TIMEOUT = 120 * 1000 // 60 seconds
const TIMEOUT_BUFFER = 5 * 1000 // 5 seconds as additional buffer to the timeouts above for the wrapping function

setDefaultTimeout( 20 * 1000);

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
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The API resource should be found within " + API_DEPLOY_TIMEOUT + " seconds")
  }
});

/**
 * Wait for a specified ExposedAPI resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} APINamspece - The name of the ExposedAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is available.
 */
Then('I should see the {string} ExposedAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPI, componentName) {
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getCustomResource('exposedapis', ExposedAPI, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The ExposedAPI resource should be found within " + API_DEPLOY_TIMEOUT + " seconds")
  }
});

/**
 * Wait for a specified ExposedAPI resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} APINamspece - The name of the ExposedAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is available.
 */
Then('I should see the {string} ExposedAPI resource on the {string} component with specification {string}', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPI, componentName, specVersion) {
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getCustomResource('exposedapis', ExposedAPI, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The ExposedAPI resource should be found within " + API_DEPLOY_TIMEOUT + " seconds")
  }

  // test for specification not implemented yet, so return pending
  return 'pending';
});

/**
 * Wait for a specified DependentAPI resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} APINamspece - The name of the DependentAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is available.
 */
Then('I should see the {string} DependentAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (DependentAPI, componentName) {
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the API resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getCustomResource('dependentapis', DependentAPI, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The DependentAPI resource should be found within " + API_DEPLOY_TIMEOUT + " seconds")
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
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was removed within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The API resource should be removed within " + API_DEPLOY_TIMEOUT + " seconds")
  }

});

/**
 * Wait for a specified API resource to be removed and assert that it was removed within a specified timeout.
 *
 * @param {string} APIName - The name of the API resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the API resource is removed.
 */
Then('I should not see the {string} ExposedAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (APIName, componentName) {
  // set the initial value of apiResource to 'not null'
  let apiResource = 'not null'
  var startTime = performance.now()
  var endTime

  // wait until the API resource is removed or the timeout is reached
  while (apiResource != null) {
    apiResource = await resourceInventoryUtils.getCustomResource('exposedapis', ExposedAPI, componentName, global.currentReleaseName, NAMESPACE)
    endTime = performance.now()

    // assert that the API resource was removed within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The ExposedAPI resource should be removed within " + API_DEPLOY_TIMEOUT + " seconds")
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
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, global.currentReleaseName, NAMESPACE)
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
    apiResource = await resourceInventoryUtils.getAPIResource(APIName, componentName, global.currentReleaseName, NAMESPACE)
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

