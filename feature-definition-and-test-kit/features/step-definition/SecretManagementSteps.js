const { Given, When, Then, After} = require('@cucumber/cucumber');
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils = require('package-manager-utils-helm');
const secretManagementUtils = require('secret-management-utils-hashicorp');
const assert = require('assert');

const CLEANUP_PACKAGE = true // set to true to uninstall the package after each Scenario

const NAMESPACE = 'components'
const CV_NAMESPACE = 'canvas-vault'
const CV_PODNAME = 'canvas-vault-hc-0'

const DEBUG_LOGS = true // set to true to log the controller logs after each failed Scenario

Given('the secret {string} with value {string} in the secret store for {string} was created', function (secret, value, owner) {
  secretManagementUtils.createSecret(CV_PODNAME, CV_NAMESPACE, owner, secret, value)
});

Then('the {string} package for release {string} is updated', async function(componentPackage, currentReleaseName){
  global.currentReleaseName = currentReleaseName
  await packageManagerUtils.upgradePackage(componentPackage, currentReleaseName, NAMESPACE)
});

Then('in the vault a role for {string} does exist', function (owner) {
  assert.ok(secretManagementUtils.vaultExists(CV_PODNAME, CV_NAMESPACE, owner), `Role '${owner}' not found`)
});

Then('in the vault a role for {string} does not exist', function (owner) {
  assert.ok(!secretManagementUtils.vaultExists(CV_PODNAME, CV_NAMESPACE, owner), `Role '${owner}' not found`)
});

Then('in the vault a policy for {string} does exist', function (owner) {
  assert.ok(secretManagementUtils.policyExists(CV_PODNAME, CV_NAMESPACE, owner), `Policy for '${owner}' not found`)
});

Then('in the vault a policy for {string} does not exist', function (owner) {
  assert.ok(!secretManagementUtils.policyExists(CV_PODNAME, CV_NAMESPACE, owner), `Policy for '${owner}' not found`)
});

Then('in the vault a secret store for {string} does exist', function (owner) {
  assert.ok(secretManagementUtils.secretStoreExists(CV_PODNAME, CV_NAMESPACE, owner),`Secret Store for '${owner}' not found`)
});

Then('the secret {string} in the secret store for {string} does exist', function (secret, owner) {
  assert.ok(secretManagementUtils.secretExists(CV_PODNAME, CV_NAMESPACE, owner, secret), `Secret '${secret}' not exists`)
});

Then('the secret {string} in the secret store for {string} has the value {string}', function (secret, value, owner) {
  const actual = secretManagementUtils.getSecretValue(CV_PODNAME, CV_NAMESPACE, owner, secret)
  assert.equal(actual, value, `Secret '${secret}' has not the value '${value}' but '${actual}'`)
});

Then('the secret {string} in the secret store for {string} does not exist', function (secret, owner) {
  assert.ok(!secretManagementUtils.secretExists(CV_PODNAME, CV_NAMESPACE, owner, secret), `Secret '${secret}' exists`)
});

/**
 * Code executed After each scenario
 * Optionally Uninstall the package associated with the release name and namespace.
 * Optionally Log the Canvas controller
 */
After('@SECRET-MANAGEMENT', async function (scenario) {
  
  if (CLEANUP_PACKAGE) {
    await packageManagerUtils.uninstallPackage('alice', NAMESPACE)
  }

  if (DEBUG_LOGS) {
    console.log()
    console.log('Scenario status: ' + scenario.result.status)
    if (scenario.result.status === 'FAILED') {
      console.log('------------------------------------------------------------------')
      console.log('Controller logs:')
      try {
      console.log(await resourceInventoryUtils.getControllerLogs())  
      } catch (error) {
        console.log('Error getting controller logs: ' + error)
      }
      console.log('------------------------------------------------------------------')
    } 
    console.log()
    console.log('Scenario ended at: ' + new Date().toISOString())
  }

});