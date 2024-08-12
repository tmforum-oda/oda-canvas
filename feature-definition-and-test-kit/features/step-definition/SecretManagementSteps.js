const { Given, When, Then, AfterAll, setDefaultTimeout } = require('@cucumber/cucumber');
const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');


const CV_NAMESPACE = 'canvas-vault'
const CV_PODNAME = 'canvas-vault-hc-0'

Then('in the vault a role for {string} does exist', function (name) {
  const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault list auth/jwt-k8s-sman/role');

  const roleName = `sman-components-${name}-role`

  let lines = output.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i] == roleName) {
      return;
    }
  }
  throw new Error('Role not found: ' + roleName);
});

Then('in the vault a policy for {string} does exists', function (name) {
  const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault policy list');

  const policyName = `sman-components-${name}-policy`

  let lines = output.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i] == policyName) {
      return;
    }
  }

  throw new Error('Policy not found: ' + policyName);
});

Then('in the vault a secret store for {string} does exist', function (secretStoreName) {
  const output = resourceInventoryUtils.execCommand(CV_PODNAME, CV_NAMESPACE, 'vault secrets list -format=json');
  const json = JSON.parse(output);

  const property = `kv-sman-components-${secretStoreName}/`
  if (json.hasOwnProperty(property) && json[property].type == "kv") {
    return;
  }

  throw new Error(`Secret Store ${property} not found`);
});