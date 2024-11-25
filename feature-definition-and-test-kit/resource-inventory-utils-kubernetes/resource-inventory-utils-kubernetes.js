const k8s = require('@kubernetes/client-node')
const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const testDataFolder = './testData/'

const GROUP = "oda.tmforum.org"
const VERSION = "v1beta4"
const EXPOSED_APIS_PLURAL = "exposedapis"
const DEPENDENT_APIS_PLURAL = "dependentapis"
const COMPONENTS_PLURAL = "components"


const resourceInventoryUtils = {

  /**
  * Function that returns the custom API resource 
  * @param    {String} inCustomCRDPluralName  Plural name of the custom resource type
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inResourceName         Name of the API that is requested
  * @param    {String} inReleaseName          Release name of the component instance
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}         The API resource object, or null if the API is not found
  */
  getCustomResource: async function (inCustomCRDPluralName, inResourceName, inComponentName, inReleaseName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const customResourceName = inReleaseName + '-' + inComponentName + '-' + inResourceName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, inCustomCRDPluralName, undefined, undefined, 'metadata.name=' + customResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },  

  /**
  * Function that returns the custom ExposedAPI resource given ExposedAPI name
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inExposedAPIName       Name of the ExposedAPI that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}        The ExposedAPI resource object, or null if the ExposedAPI is not found
  */
  getExposedAPIResource: async function (inExposedAPIName, inComponentName, inReleaseName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const ExposedAPIResourceName = inReleaseName + '-' + inComponentName + '-' + inExposedAPIName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, EXPOSED_APIS_PLURAL, undefined, undefined, 'metadata.name=' + ExposedAPIResourceName)
    if (namespacedCustomObject.body.items.length === 0) {
      return null // API not found
    } 
      
    return namespacedCustomObject.body.items[0]
  },

  /**
  * Function that returns the custom DependentAPI resource given DependentAPI name
  * @param    {String} inComponentInstance    Name of the component instance
  * @param    {String} inDependentAPIName     Name of the API that is requested
  * @param    {String} inNamespace            Namespace where the component instance is running
  * @return   {Object}          The DependentAPI resource object, or null if the DependentAPI is not found
  */
  getDependentAPIResource: async function (inDependentAPIName, inComponentName, inReleaseName, inNamespace) {
    const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
    const DependentAPIResourceName = inReleaseName + '-' + inComponentName + '-' + inDependentAPIName
    const namespacedCustomObject = await k8sCustomApi.listNamespacedCustomObject(GROUP, VERSION, inNamespace, DEPENDENT_APIS_PLURAL, undefined, undefined, 'metadata.name=' + DependentAPIResourceName)
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

  //For Kong API Gateway CRs
  
  /**
  * Function that returns the HTTPRoute for a given component.
  * @param    {String} componentName       Name of the component
  * @param    {String} resourceName        Name of the resource
  * @param    {String} [inNamespace='components'] - Namespace where the component instance
  * @return   {Object}                     The HTTPRoute object, or null if not found
  */
  getHTTPRouteForComponent: async function (componentName, resourceName, inNamespace = 'components') {
  const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
  const httpRouteResourceName = `kong-api-route-ctk-${componentName}-${componentName}`;
  
  try {
  const response = await k8sCustomApi.listNamespacedCustomObject(
	  'gateway.networking.k8s.io', 
	  'v1', 
	  inNamespace, 
	  'httproutes' 
  );
  
  const items = response.body.items;
  console.log('Found HTTPRoutes:', items.map(item => item.metadata.name));
  const matchingRoutes = items.filter(route => route.metadata.name === httpRouteResourceName);
  console.log('Matching HTTPRoutes:', matchingRoutes.map(route => route.metadata.name));
  
  if (matchingRoutes.length === 0) {
	  console.error(`HTTPRoute ${httpRouteResourceName} not found.`);
	  return null;
  }
  
  return matchingRoutes[0]; // Returning the matching HTTPRoute
  } catch (error) {
  console.error('Error fetching HTTPRoute:', error);
  throw error;
  }
  },
  
  getKongPluginForComponent: async function (componentName, pluginName, inNamespace = 'components') {
  const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
  const kongPluginResourceName = `${pluginName}`;
  
  try {
  const response = await k8sCustomApi.listNamespacedCustomObject(
	  'configuration.konghq.com',
	  'v1',
	  inNamespace,
	  'kongplugins'
  );
  
  const items = response.body.items;
  console.log('Found KongPlugins:', items.map(item => item.metadata.name));
  const matchingPlugins = items.filter(plugin => plugin.metadata.name === kongPluginResourceName);
  console.log('Matching KongPlugins:', matchingPlugins.map(plugin => plugin.metadata.name));
  
  if (matchingPlugins.length === 0) {
	  console.error(`KongPlugin ${kongPluginResourceName} not found.`);
	  return null;
  }
  
  return matchingPlugins[0]; // Returning the matching KongPlugin
  } catch (error) {
  console.error(`Error fetching KongPlugin ${kongPluginResourceName}:`, error);
  throw error;
  }
  },
  
  //For Apisix API Gateway CRs
  
  /**
  * Function that returns the ApisixRoute for a given component.
  * @param    {String} componentName       Name of the component
  * @param    {String} resourceName        Name of the resource
  * @param    {String} [inNamespace='istio-ingress'] - Namespace where the component instance
  * @return   {Object}                     The ApisixRoute object, or null if not found
  */
  getApisixRouteForComponent: async function (componentName, resourceName, inNamespace = 'istio-ingress') {
  const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
  const apisixRouteResourceName = `apisix-api-route-ctk-${componentName}-${componentName}`;
  
  try {
  const response = await k8sCustomApi.listNamespacedCustomObject(
	  'apisix.apache.org',
	  'v2',
	  inNamespace,
	  'apisixroutes'
  );
  
  const items = response.body.items;
  console.log('Found ApisixRoutes:', items.map(item => item.metadata.name));
  const matchingRoutes = items.filter(route => route.metadata.name === apisixRouteResourceName);
  console.log('Matching ApisixRoutes:', matchingRoutes.map(route => route.metadata.name));
  
  if (matchingRoutes.length === 0) {
	  console.error(`ApisixRoute ${apisixRouteResourceName} not found.`);
	  return null;
  }
  
  return matchingRoutes[0]; // Returning the matching ApisixRoute
  } catch (error) {
  console.error('Error fetching ApisixRoute:', error);
  throw error; // Re-throw the error for the test to catch
  }
  },
  
  getApisixPluginForComponent: async function (componentName, pluginName, inNamespace = 'istio-ingress') {
  const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
  const apisixPluginResourceName = `${pluginName}`;
  
  try {
  const response = await k8sCustomApi.listNamespacedCustomObject(
	  'apisix.apache.org',
	  'v2',
	  inNamespace,
	  'apisixpluginconfigs'
  );
  
  const items = response.body.items;
  console.log('Found ApisixPluginConfigs:', items.map(item => item.metadata.name));
  const matchingPlugins = items.filter(plugin => plugin.metadata.name === apisixPluginResourceName);
  
  if (matchingPlugins.length === 0) {
	  console.error(`ApisixPluginConfig ${apisixPluginResourceName} not found.`);
	  return null;
  }
  
  return matchingPlugins[0]; // Returning the matching ApisixPluginConfig
  } catch (error) {
  console.error(`Error fetching ApisixPluginConfig ${apisixPluginResourceName}:`, error);
  throw error;
  }
  },

  /**
   * Function that returns the logs from the ODA Controller pod
   */
  getControllerLogs: async function () {
    // use the kubernetes API to get the logs from the ODA Controller pod
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
    const podList = await k8sCoreApi.listNamespacedPod('canvas', undefined, undefined, undefined, undefined, 'app=oda-controller')
    const controllerPod = podList.body.items[0]
    const controllerPodName = controllerPod.metadata.name
    const controllerPodNamespace = controllerPod.metadata.namespace

    const controllerLogs = await k8sCoreApi.readNamespacedPodLog(controllerPodName, controllerPodNamespace, container='oda-controller')
    console.log(controllerLogs.body)
    return controllerLogs.body
  }
}

module.exports = resourceInventoryUtils
