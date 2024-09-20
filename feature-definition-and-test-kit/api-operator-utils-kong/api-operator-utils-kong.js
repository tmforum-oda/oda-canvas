const k8s = require('@kubernetes/client-node');
const assert = require('assert');
 
// Initialize Kubernetes client
const k8sApi = new k8s.KubeConfig();
k8sApi.loadFromDefault();
const customObjectsApi = k8sApi.makeApiClient(k8s.KubernetesObjectApi);
 
// Define constants
const GROUP = 'gateway.networking.k8s.io';
const VERSION = 'v1';
const HTTPROUTE_PLURAL = 'httproutes';
const KONGPLUGIN_GROUP = 'configuration.konghq.com';
const KONGPLUGIN_VERSION = 'v1';
const KONGPLUGIN_PLURAL = 'kongplugins';
 
/**
* Create or update an API resource (HTTPRoute) in the Kubernetes cluster.
* @param {Object} apiResource - The API resource configuration.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<Object>} The response from the Kubernetes API.
*/
async function createOrUpdateAPIResource(apiResource, namespace) {
  const ingressName = `kong-api-route-${apiResource.path.replace(/[^a-zA-Z0-9]/g, '-')}`;
  const manifest = {
    apiVersion: `${GROUP}/${VERSION}`,
    kind: 'HTTPRoute',
    metadata: {
      name: ingressName,
      namespace: namespace,
    },
    spec: {
      parentRefs: [
        {
          name: 'kong',
          namespace: 'components',
        },
      ],
      rules: [
        {
          matches: [
            {
              path: {
                type: 'PathPrefix',
                value: apiResource.path,
              },
            },
          ],
          backendRefs: [
            {
              name: 'istio-ingress',
              kind: 'Service',
              port: 80,
              namespace: 'istio-ingress',
            },
          ],
        },
      ],
    },
  };
 
  try {
    await customObjectsApi.getNamespacedCustomObject(GROUP, VERSION, namespace, HTTPROUTE_PLURAL, ingressName);
    return await customObjectsApi.replaceNamespacedCustomObject(GROUP, VERSION, namespace, HTTPROUTE_PLURAL, ingressName, manifest);
  } catch (error) {
    if (error.response && error.response.statusCode === 404) {
      return await customObjectsApi.createNamespacedCustomObject(GROUP, VERSION, namespace, HTTPROUTE_PLURAL, manifest);
    } else {
      throw error;
    }
  }
}
 
/**
* Get an HTTPRoute resource from the Kubernetes cluster.
* @param {String} path - The API path.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<Object>} The HTTPRoute resource.
*/
async function getHTTPRoute(path, namespace) {
  const ingressName = `kong-api-route-${path.replace(/[^a-zA-Z0-9]/g, '-')}`;
  try {
    return await customObjectsApi.getNamespacedCustomObject(GROUP, VERSION, namespace, HTTPROUTE_PLURAL, ingressName);
  } catch (error) {
    if (error.response && error.response.statusCode === 404) {
      return null;
    } else {
      throw error;
    }
  }
}
 
/**
* Get a KongPlugin from the Kubernetes cluster.
* @param {String} pluginType - The type of the plugin (e.g., 'rate-limit').
* @param {String} path - The API path.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<Object>} The KongPlugin resource.
*/
async function getPlugin(pluginType, path, namespace) {
  const pluginName = `${pluginType}-${path.replace(/[^a-zA-Z0-9]/g, '-')}`;
  try {
    return await customObjectsApi.getNamespacedCustomObject(KONGPLUGIN_GROUP, KONGPLUGIN_VERSION, namespace, KONGPLUGIN_PLURAL, pluginName);
  } catch (error) {
    if (error.response && error.response.statusCode === 404) {
      return null;
    } else {
      throw error;
    }
  }
}
 
/**
* Apply plugins from a URL.
* @param {String} url - The URL of the plugin template.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<Array>} The list of applied plugins.
*/
async function applyPluginsFromURL(url, namespace) {
  // Fetch the YAML template from the URL
  const response = await fetch(url);
  const yamlText = await response.text();
 
  // Parse YAML and create/update plugins
  const documents = yaml.safeLoadAll(yamlText);
  const appliedPlugins = [];
 
  for (const doc of documents) {
    const pluginName = doc.metadata.name;
    try {
      await customObjectsApi.getNamespacedCustomObject(KONGPLUGIN_GROUP, KONGPLUGIN_VERSION, namespace, KONGPLUGIN_PLURAL, pluginName);
      await customObjectsApi.replaceNamespacedCustomObject(KONGPLUGIN_GROUP, KONGPLUGIN_VERSION, namespace, KONGPLUGIN_PLURAL, pluginName, doc);
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        await customObjectsApi.createNamespacedCustomObject(KONGPLUGIN_GROUP, KONGPLUGIN_VERSION, namespace, KONGPLUGIN_PLURAL, doc);
      } else {
        throw error;
      }
    }
    appliedPlugins.push(pluginName);
  }
  return appliedPlugins;
}
 
/**
* Get applied plugins for an API resource.
* @param {String} path - The API path.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<Array>} The list of applied plugins.
*/
async function getAppliedPlugins(path, namespace) {
  const plugins = [];
  const pluginTypes = ['rate-limit', 'api-key-auth']; // Add more plugin types as needed
  for (const type of pluginTypes) {
    try {
      const plugin = await getPlugin(type, path, namespace);
      if (plugin) {
        plugins.push(plugin);
      }
    } catch (error) {
      throw error;
    }
  }
  return plugins;
}
 
/**
* Delete an API resource (HTTPRoute) from the Kubernetes cluster.
* @param {String} path - The API path.
* @param {String} namespace - The Kubernetes namespace.
* @returns {Promise<void>}
*/
async function deleteAPIResource(path, namespace) {
  const ingressName = `kong-api-route-${path.replace(/[^a-zA-Z0-9]/g, '-')}`;
  try {
    await customObjectsApi.deleteNamespacedCustomObject(GROUP, VERSION, namespace, HTTPROUTE_PLURAL, ingressName);
  } catch (error) {
    if (error.response && error.response.statusCode !== 404) {
      throw error;
    }
  }
}
 
module.exports = {
  createOrUpdateAPIResource,
  getHTTPRoute,
  getPlugin,
  applyPluginsFromURL,
  getAppliedPlugins,
  deleteAPIResource,
};
