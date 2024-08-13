const { Given, When, Then, After, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');

const CLEANUP_PACKAGE = true // set to true to uninstall the package after each Scenario

const CV_NAMESPACE = 'canvas-vault'
const CV_PODNAME = 'canvas-vault-hc-0'

function secretStoreName(name, store = '') {
  return `kv-sman-components-${name}/${store}`
}

Given('the secret {string} with value {string} in the secret store for {string} was created', function (key, value, name) {
  const storeName = secretStoreName(name, 'sidecar')
  // resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, `vault kv put ${storeName} ${key}=${value}`)
  resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, `vault write ${storeName} ${key}=${value}`)
});

Then('in the vault a role for {string} does exist', function (name) {
  const roleName = `sman-components-${name}-role`
  try {
    const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault list auth/jwt-k8s-sman/role');
    
    
    let lines = output.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (lines[i] == roleName) {
        return;
      }
    }
  } catch (e) {
    console.log(e.message)
  }
  throw new Error('Role not found: ' + roleName);
});

Then('in the vault a policy for {string} does exist', function (name) {
  const policyName = `sman-components-${name}-policy`
  
  const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault policy list');

  let lines = output.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i] == policyName) {
      return;
    }
  }

  throw new Error('Policy not found: ' + policyName);
});

Then('in the vault a secret store for {string} does exist', function (name) {
  const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault secrets list -format=json');
  const json = JSON.parse(output);

  const property = secretStoreName(name)
  if (json.hasOwnProperty(property) && json[property].type == "kv") {
    return;
  }

  throw new Error(`Secret Store ${property} not found`);
});

/**
 * Code executed After each scenario
 * Optionally Uninstall the package associated with the release name and namespace.
 * Optionally Log the Canvas controller
 */
After('@sman', async function (scenario) {
  
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