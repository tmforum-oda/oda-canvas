// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const identityManagerUtils = require('identity-manager-utils-keycloak');

const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const chai = require('chai')
const chaiHttp = require('chai-http')
const assert = require('assert');
chai.use(chaiHttp)

const NAMESPACE = 'components'
const COMPONENT_DEPLOY_TIMEOUT = 100 * 1000 // 100 seconds

setDefaultTimeout( 20 * 1000);

/**
 * Check for role to be assigned to the security operator in identity management.
 *
 * @param {string} canvassystemUserName - the username of the operator to check.
 * @param {string} componentName - The name of the component to check.
 * @returns {Promise<void>} - A Promise that resolves when the component is available.
 */
Then('I should see the predefined role assigned to the {string} user for the {string} component in the identity platform', async function (canvassystemUserName, componentName) {
  let componentResource = null
  let canvassystemRole = null
  var startTime = performance.now()
  var endTime

  // wait until the component resource is found or the timeout is reached
  while (componentResource == null) {
    componentResource = await resourceInventoryUtils.getComponentResource(global.currentReleaseName + '-' + componentName, NAMESPACE)
    endTime = performance.now()

    // assert that the component resource was found within the timeout
    assert.ok(endTime - startTime < COMPONENT_DEPLOY_TIMEOUT, "The Component resource should be found within " + COMPONENT_DEPLOY_TIMEOUT + " seconds")

    // check if the component deployment status is deploymentStatus
    if ((!componentResource) || (!componentResource.hasOwnProperty('spec')) || (!componentResource.spec.hasOwnProperty('securityFunction')) || (!componentResource.spec.securityFunction.hasOwnProperty('canvasSystemRole'))) {
      componentResource = null // reset the componentResource to null so that we can try again
    } else {
      canvassystemRole = componentResource.spec.securityFunction.canvasSystemRole;
      allUserRoles = await identityManagerUtils.getRolesForUser(canvassystemUserName, global.currentReleaseName, componentName);
      //return 'pending';
      assert.ok(allUserRoles.includes(canvassystemRole), 'The predefine role for the security operator should be correctly assigned in the identity platform');
    }
  }
});
