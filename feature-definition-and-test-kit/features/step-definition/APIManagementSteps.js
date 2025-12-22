// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai');
const chaiHttp = require('chai-http');
const assert = require('assert');
chai.use(chaiHttp);

const NAMESPACE = 'components';
const API_DEPLOY_TIMEOUT = 30 * 1000; // 30 seconds
const API_URL_TIMEOUT = 60 * 1000; // 60 seconds
const API_READY_TIMEOUT = 120 * 1000; // 120 seconds
const TIMEOUT_BUFFER = 5 * 1000; // 5 seconds as additional buffer to the timeouts above for the wrapping function
const DEBUG_LOGS = false; // set to true for verbose debugging

setDefaultTimeout(20 * 1000);

/**
 * Wait for a specified ExposedAPI resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} ExposedAPIName - The name of the ExposedAPI resource to check.
 * @param {string} componentName - The name of the component.
 * @returns {Promise<void>} - A Promise that resolves when the ExposedAPI resource is available.
 */
Then('I should see the {string} ExposedAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPIName, componentName) {
  console.log('\n=== Starting ExposedAPI Resource Verification ===');
  console.log(`Verifying ExposedAPI '${ExposedAPIName}' on component '${componentName}'`);
  
  let apiResource = null;
  var startTime = performance.now();
  var endTime;
  let namespace = global.namespace || NAMESPACE;
  try {
    // Wait until the ExposedAPI resource is found or the timeout is reached
    while (apiResource == null) {
      apiResource = await resourceInventoryUtils.getExposedAPIResource(ExposedAPIName, componentName, namespace);
      endTime = performance.now();

      // Assert that the ExposedAPI resource was found within the timeout
      assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, `The ExposedAPI resource '${ExposedAPIName}' should be found within ${API_DEPLOY_TIMEOUT} milliseconds`);
      
      if (!apiResource) {
        // Brief wait before retrying
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    console.log(`✅ Successfully found ExposedAPI '${ExposedAPIName}' on component '${componentName}' after ${Math.round(endTime - startTime)}ms`);
    
    if (DEBUG_LOGS) {
      console.log('ExposedAPI resource details:', JSON.stringify(apiResource, null, 2));
    }
    
    console.log('=== ExposedAPI Resource Verification Complete ===');

  } catch (error) {
    console.error(`❌ Error during ExposedAPI resource verification: ${error.message}`);
    console.error('Error details:');
    console.error(`- ExposedAPI name: '${ExposedAPIName}'`);
    console.error(`- Component name: '${componentName}'`);
    console.error(`- Release name: '${global.currentReleaseName}'`);
    console.error(`- Namespace: '${namespace}'`);
    console.error(`- Timeout duration: ${API_DEPLOY_TIMEOUT}ms`);
    console.error(`- Error type: ${error.constructor.name}`);
    
    console.error('Possible causes:');
    console.error('- Component not fully deployed or ready');
    console.error('- ExposedAPI resource not created by Canvas operators');
    console.error('- Canvas API operator not running or misconfigured');
    console.error('- Component specification missing ExposedAPI definition');
    console.error('- Kubernetes RBAC issues preventing resource access');
    
    console.log('=== ExposedAPI Resource Verification Failed ===');
    throw error;
  }
});

/**
 * Wait for a specified DependentAPI resource to be available and assert that it was found within a specified timeout.
 *
 * @param {string} APIName - The name of the DependentAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the DependentAPI resource is available.
 */
Then('I should see the {string} DependentAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (DependentAPIName, componentName) {
  let apiResource = null
  var startTime = performance.now()
  var endTime
  
  let namespace = global.namespace || NAMESPACE
  // wait until the DependentAPI resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getDependentAPIResource(DependentAPIName, componentName, namespace)
    endTime = performance.now()

    // assert that the DependentAPI resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The DependentAPI resource should be found within " + API_DEPLOY_TIMEOUT + " milliseconds")
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

  // wait until the ExposedAPI resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getExposedAPIResource(ExposedAPI, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was found within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The ExposedAPI resource should be found within " + API_DEPLOY_TIMEOUT + " milliseconds")
  }

  // The apiResource has a spec with a specification that is an array of strings
  // assert that the array contains the specVersion
  var found = false
  for (var i = 0; i < apiResource.spec.specification.length; i++) {
    if (apiResource.spec.specification[i].url == specVersion) {
      found = true
      break
    }
  }

  assert.ok(found, "The ExposedAPI resource should have the specification " + specVersion)

});



/**
 * Wait for a specified ExposedAPI resource to be removed and assert that it was removed within a specified timeout.
 *
 * @param {string} ExposedAPIName - The name of the ExposedAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the ExposedAPI resource is removed.
 */
Then('I should not see the {string} ExposedAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPIName, componentName) {
  // set the initial value of ExposedAPIResource to 'not null'
  let exposedAPIResource = 'not null'
  var startTime = performance.now()
  var endTime

  // wait until the ExposedAPI resource is removed or the timeout is reached
  while (exposedAPIResource != null) {
    exposedAPIResource = await resourceInventoryUtils.getExposedAPIResource(ExposedAPIName, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was removed within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The ExposedAPI resource should be removed within " + API_DEPLOY_TIMEOUT + " milliseconds")
  }

});


/**
 * Wait for a specified DependentAPI resource to be removed and assert that it was removed within a specified timeout.
 *
 * @param {string} DependentAPIName - The name of the DependentAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the DependentAPI resource is removed.
 */
Then('I should not see the {string} DependentAPI resource on the {string} component', {timeout : API_DEPLOY_TIMEOUT + TIMEOUT_BUFFER}, async function (dependentAPIName, componentName) {
  // set the initial value of DependentAPIResource to 'not null'
  let dependentAPIResource = 'not null'
  var startTime = performance.now()
  var endTime

  // wait until the DependentAPI resource is removed or the timeout is reached
  while (dependentAPIResource != null) {
    dependentAPIResource = await resourceInventoryUtils.getExposedAPIResource(dependentAPIName, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was removed within the timeout
    assert.ok(endTime - startTime < API_DEPLOY_TIMEOUT, "The DependentAPI resource should be removed within " + API_DEPLOY_TIMEOUT + " milliseconds")
  }

});


/**
 * Wait for a specified ExposedAPI resource to have a URL on the Service Mesh or Gateway and assert that it was found within a specified timeout.
 *
 * @param {string} ExposedAPIName - The name of the ExposedAPI resource to check.
 * @returns {Promise<void>} - A Promise that resolves when the ExposedAPI resource has a URL on the Service Mesh or Gateway.
 */
Then('I should see the {string} ExposedAPI resource on the {string} component with a url on the Service Mesh or Gateway', {timeout : API_URL_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPIName, componentName) {
  // get the ExposedAPI resource
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the ExposedAPI resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getExposedAPIResource(ExposedAPIName, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was found within the timeout
    assert.ok(endTime - startTime < API_URL_TIMEOUT, "The url should be found within " + API_URL_TIMEOUT + " milliseconds")

    // check if there is a url on the ExposedAPI resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('apiStatus')) || (!apiResource.status.apiStatus.hasOwnProperty('url'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }

});

Then('I should see the {string} ExposedAPI resource on the {string} component with an implementation ready status on the Service Mesh or Gateway', {timeout : API_READY_TIMEOUT + TIMEOUT_BUFFER}, async function (ExposedAPIName, componentName) {
  // get the ExposedAPI resource
  let apiResource = null
  var startTime = performance.now()
  var endTime

  // wait until the ExposedAPI resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getExposedAPIResource(ExposedAPIName, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was found within the timeout
    assert.ok(endTime - startTime < API_READY_TIMEOUT, "The ready status should be found within " + API_READY_TIMEOUT + " milliseconds")

    // check if there is a url on the ExposedAPI resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('implementation')) || (!apiResource.status.implementation.hasOwnProperty('ready'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    } else if (!(apiResource.status.implementation.ready == true)) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }
});

Then('I should see the {string} DependentAPI resource on the {string} component with a ready status', {timeout : API_READY_TIMEOUT + TIMEOUT_BUFFER},  async function (DependentAPIName, componentName) {
  // get the DependentAPI resource
  let apiResource = null
  var startTime = performance.now()
  var endTime
  // wait until the DependentAPI resource is found or the timeout is reached
  while (apiResource == null) {
    apiResource = await resourceInventoryUtils.getDependentAPIResource(DependentAPIName, componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the ExposedAPI resource was found within the timeout
    assert.ok(endTime - startTime < API_READY_TIMEOUT, "The ready status should be found within " + API_READY_TIMEOUT + " milliseconds")

    // check if there is a url on the ExposedAPI resource status
    if ((!apiResource) || (!apiResource.hasOwnProperty('status')) || (!apiResource.status.hasOwnProperty('implementation')) || (!apiResource.status.implementation.hasOwnProperty('ready'))) {
      apiResource = null // reset the apiResource to null so that we can try again
    } else if (!(apiResource.status.implementation.ready == true)) {
      apiResource = null // reset the apiResource to null so that we can try again
    }
  }


});