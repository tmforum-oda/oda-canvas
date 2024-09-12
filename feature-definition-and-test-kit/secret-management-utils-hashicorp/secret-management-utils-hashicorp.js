const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');

function secretStoreName(name, store = '') {
  return `kv-sman-components-${name}/${store}`
}

function roleName(name) {
  return `sman-components-${name}-role`
}

function policyName(name) {
  return `sman-components-${name}-policy`
}

const secretManagementUtils = {

  createSecret: function(podName, namespace, owner, key, value) {
    const name = secretStoreName(owner, 'sidecar')
    return resourceInventoryUtils.execCommand(podName, namespace, `vault kv put ${name} ${key}=${value}`)
  },

  vaultExists: function(podName, namespace, owner) {
    const name = roleName(owner)
    try {
      const output = resourceInventoryUtils.execCommand(podName, namespace, 'vault list auth/jwt-k8s-sman/role');
      
      
      let lines = output.split('\n');
      for (let i = 0; i < lines.length; i++) {
        if (lines[i] == name) {
          return true;
        }
      }
    } catch (e) {
      console.log(e.message)
    }
    return false
  },

  policyExists: function(podName, namespace, owner) {
    const name = policyName(owner)
    
    const output = resourceInventoryUtils.execCommand(podName, namespace, 'vault policy list');
  
    let lines = output.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (lines[i] == name) {
        return true
      }
    }
  
    return false
  },
  
  secretStoreExists: function(podName, namespace, owner) {
    const output = resourceInventoryUtils.execCommand(podName, namespace, 'vault secrets list -format=json');
    const json = JSON.parse(output);
  
    const name = secretStoreName(owner)
    if (json.hasOwnProperty(name) && json[name].type == "kv") {
      return true
    }
  
    return false
  },

  secretExists: function(podName, namespace, owner, secret) {
    return false
  },

  getSecretValue: function(podName, namespace, owner, secret) {
    return false
  },

}

module.exports = secretManagementUtils