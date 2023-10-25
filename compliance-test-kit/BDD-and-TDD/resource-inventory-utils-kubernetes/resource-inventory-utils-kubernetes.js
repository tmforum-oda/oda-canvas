const k8s = require('@kubernetes/client-node')
const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const testDataFolder = './testData/'

const GROUP = "oda.tmforum.org"
const VERSION = "v1beta2"
const APIS_PLURAL = "apis"
const COMPONENTS_PLURAL = "components"


const resourceInventoryUtils = {

  /**
  * Function that returns the custom API resource given API instance
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inAPIName              Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}         The API resource object, or null if the API is not found
  */
  getAPIResource: async function (inAPIName, inComponentName, inReleaseName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const APIResourceName = inReleaseName + '-' + inComponentName + '-' + inAPIName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, APIS_PLURAL, undefined, undefined, 'metadata.name=' + APIResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  /**
  * Function that returns the custom Component resource given Component Name
  * @param    {String} inComponentName        Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
  getComponentResource: async function (inComponentName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)

    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, COMPONENTS_PLURAL, undefined, undefined, 'metadata.name=' + inComponentName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  /**
  * Function that returns the custom Component resource of a specific version, given Component Name
  * @param    {String} inComponentName        Name of the API that is requested
  * @param    {String} inComponentVersion     Version of the component spec that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {String}         String containing the base URL for the API, or null if the API is not found
  */
  getComponentResourceByVersion: async function (inComponentName, inComponentVersion, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, inComponentVersion, inNamespace, COMPONENTS_PLURAL, undefined, undefined, 'metadata.name=' + inComponentName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // Component not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },
}

module.exports = resourceInventoryUtils