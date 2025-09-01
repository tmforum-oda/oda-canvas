const k8s = require('@kubernetes/client-node')
const execSync = require('child_process').execSync;
const YAML = require('yaml')
const assert = require('assert');

const kc = new k8s.KubeConfig()
kc.loadFromDefault()

const testDataFolder = './testData/'

const GROUP = "oda.tmforum.org"
const VERSION = "v1"
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
    
    return matchingRoutes[0]; 
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
    
    return matchingPlugins[0]; 
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
    
    return matchingRoutes[0]; 
    } catch (error) {
    console.error('Error fetching ApisixRoute:', error);
    throw error; 
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
    
    return matchingPlugins[0]; 
    } catch (error) {
    console.error(`Error fetching ApisixPluginConfig ${apisixPluginResourceName}:`, error);
    throw error;
    }
    },

  /**
   * Function that returns the logs from the ODA operator pod
   */
  getOperatorLogs: async function (inOperatorLabel, inContainerName) {
    // use the kubernetes API to get the logs from the ODA operator pod
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api)
    const podList = await k8sCoreApi.listNamespacedPod('canvas', undefined, undefined, undefined, undefined, 'app=' + inOperatorLabel)
    const operatorPod = podList.body.items[0]
    const operatorPodName = operatorPod.metadata.name
    const operatorPodNamespace = operatorPod.metadata.namespace
    var operatorLogs
    if (inContainerName) {
      operatorLogs = await k8sCoreApi.readNamespacedPodLog(operatorPodName, operatorPodNamespace, container=inContainerName)
    } else {
      operatorLogs = await k8sCoreApi.readNamespacedPodLog(operatorPodName, operatorPodNamespace)
    }
    return operatorLogs.body
  },

  /**
   * Function that checks if the PDB Management Operator is ready
   * @return   {Boolean}                  True if operator is ready, false otherwise
   */
  isPDBOperatorReady: async function () {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const response = await k8sAppsApi.readNamespacedDeployment(
        'canvas-pdb-management-operator',
        'canvas'
      )
      return response.body.status && response.body.status.readyReplicas > 0
    } catch (error) {
      return false
    }
  },

  /**
   * Function that gets a PDB resource
   * @param    {String} pdbName           Name of the PDB
   * @param    {String} inNamespace       Namespace of the PDB
   * @return   {Object}                 The PDB resource object, or null if not found
   */
  getPDBResource: async function (pdbName, inNamespace) {
    try {
      // Use execSync to get PDB via kubectl as a workaround
      const result = execSync(
        `kubectl get pdb ${pdbName} -n ${inNamespace} -o json 2>/dev/null`,
        { encoding: 'utf-8' }
      );
      return JSON.parse(result);
    } catch (error) {
      // If kubectl returns error (PDB not found), return null
      if (error.status === 1 || error.message.includes('NotFound')) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Function that ensures a namespace exists
   * @param    {String} namespaceName     Name of the namespace
   */
  ensureNamespaceExists: async function (namespaceName) {
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
    try {
      await k8sCoreApi.readNamespace(namespaceName);
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        // Namespace doesn't exist, create it
        const namespace = {
          apiVersion: 'v1',
          kind: 'Namespace',
          metadata: {
            name: namespaceName
          }
        };
        try {
          await k8sCoreApi.createNamespace(namespace);
          console.log(`Created namespace: ${namespaceName}`);
        } catch (createError) {
          console.warn(`Failed to create namespace ${namespaceName}:`, createError.message);
        }
      }
    }
  },

  /**
   * Function that creates a deployment for testing purposes
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where to create the deployment
   * @param    {Number} replicas          Number of replicas
   * @param    {Object} annotations       Annotations to add to the deployment
   * @param    {Object} labels           Labels to add to the deployment
   * @return   {Object}                   The created deployment object
   */
  createTestDeployment: async function (deploymentName, inNamespace, replicas, annotations = {}, labels = {}) {
    try {
      // Ensure namespace exists first
      await this.ensureNamespaceExists(inNamespace);
      
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const deployment = {
        apiVersion: 'apps/v1',
        kind: 'Deployment',
        metadata: {
          name: deploymentName,
          namespace: inNamespace,
          annotations: annotations,
          labels: {
            app: deploymentName,
            ...labels
          }
        },
        spec: {
          replicas: replicas,
          selector: {
            matchLabels: {
              app: deploymentName
            }
          },
          template: {
            metadata: {
              labels: {
                app: deploymentName,
                ...labels
              }
            },
            spec: {
              containers: [{
                name: 'test-container',
                image: 'nginx:latest',
                resources: {
                  requests: {
                    memory: '64Mi',
                    cpu: '50m'
                  },
                  limits: {
                    memory: '128Mi',
                    cpu: '100m'
                  }
                }
              }]
            }
          }
        }
      }

      const response = await k8sAppsApi.createNamespacedDeployment(inNamespace, deployment)
      return response.body
    } catch (error) {
      console.error(`Failed to create deployment ${deploymentName} in namespace ${inNamespace}:`, error.message);
      throw error;
    }
  },

  /**
   * Function that scales a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace of the deployment
   * @param    {Number} replicas          New number of replicas
   */
  scaleTestDeployment: async function (deploymentName, inNamespace, replicas) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const patch = [{
        op: 'replace',
        path: '/spec/replicas',
        value: replicas
      }]
      
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      console.error(`Failed to scale deployment ${deploymentName} in namespace ${inNamespace}:`, error.message);
      throw error;
    }
  },

  /**
   * Function that updates deployment annotations
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace of the deployment
   * @param    {Object} annotations       New annotations
   */
  updateDeploymentAnnotations: async function (deploymentName, inNamespace, annotations) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const patch = [{
        op: 'replace',
        path: '/metadata/annotations',
        value: annotations
      }]
      
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      console.error(`Failed to update annotations for deployment ${deploymentName} in namespace ${inNamespace}:`, error.message);
      throw error;
    }
  },

  /**
   * Function that creates an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy
   * @param    {String} inNamespace       Namespace where to create the policy
   * @param    {Object} spec              Policy specification
   * @return   {Object}                   The created policy object
   */
  createAvailabilityPolicy: async function (policyName, inNamespace, spec) {
    try {
      // Ensure namespace exists first
      await this.ensureNamespaceExists(inNamespace);
      
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      const policy = {
        apiVersion: 'availability.oda.tmforum.org/v1alpha1',
        kind: 'AvailabilityPolicy',
        metadata: {
          name: policyName,
          namespace: inNamespace
        },
        spec: spec
      }

      const response = await k8sCustomApi.createNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policy
      )
      return response.body
    } catch (error) {
      console.error(`Failed to create AvailabilityPolicy ${policyName} in namespace ${inNamespace}:`, error.message);
      // Don't throw the error here - let tests handle the validation
      return null;
    }
  },

  /**
   * Function that deletes an AvailabilityPolicy custom resource
   * @param    {String} policyName        Name of the policy to delete
   * @param    {String} inNamespace       Namespace where the policy is located
   */
  deleteAvailabilityPolicy: async function (policyName, inNamespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      await k8sCustomApi.deleteNamespacedCustomObject(
        'availability.oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      )
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (policy already deleted)
    }
  },

  /**
   * Function that deletes a test deployment
   * @param    {String} deploymentName    Name of the deployment to delete
   * @param    {String} inNamespace       Namespace where the deployment is located
   */
  deleteTestDeployment: async function (deploymentName, inNamespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      await k8sAppsApi.deleteNamespacedDeployment(deploymentName, inNamespace)
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (deployment already deleted)
    }
  },

  /**
   * Function that deletes a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where the deployment should be deleted
   */
  deleteTestDeployment: async function (deploymentName, inNamespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      await k8sAppsApi.deleteNamespacedDeployment(deploymentName, inNamespace)
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (deployment already deleted)
    }
  },

  /**
   * Function that scales a test deployment
   * @param    {String} deploymentName    Name of the deployment
   * @param    {String} inNamespace       Namespace where the deployment exists
   * @param    {Number} replicas          Number of replicas to scale to
   */
  scaleTestDeployment: async function (deploymentName, inNamespace, replicas) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api)
      const patch = [
        {
          op: 'replace',
          path: '/spec/replicas',
          value: replicas
        }
      ]
      await k8sAppsApi.patchNamespacedDeployment(
        deploymentName,
        inNamespace,
        patch,
        undefined,
        undefined,
        undefined,
        undefined,
        { headers: { 'Content-Type': 'application/json-patch+json' } }
      )
    } catch (error) {
      throw new Error(`Failed to scale deployment ${deploymentName}: ${error.message}`)
    }
  },

  /**
   * Function that deletes an availability policy
   * @param    {String} policyName        Name of the policy
   * @param    {String} inNamespace       Namespace where the policy should be deleted
   */
  deleteAvailabilityPolicy: async function (policyName, inNamespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi)
      await k8sCustomApi.deleteNamespacedCustomObject(
        'oda.tmforum.org',
        'v1alpha1',
        inNamespace,
        'availabilitypolicies',
        policyName
      )
    } catch (error) {
      if (error.response && error.response.statusCode !== 404) {
        throw error
      }
      // Ignore 404 errors (policy already deleted)
    }
  }
}

module.exports = resourceInventoryUtils
