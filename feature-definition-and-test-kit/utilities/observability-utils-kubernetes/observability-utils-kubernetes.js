const k8s = require('@kubernetes/client-node');
const assert = require('assert');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const PROMETHEUS_GROUP = "monitoring.coreos.com";
const PROMETHEUS_VERSION = "v1";
const SERVICEMONITOR_PLURAL = "servicemonitors";

const observabilityUtils = {

  /**
   * Function that returns a ServiceMonitor resource
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should exist
   * @return {Object|null} - The ServiceMonitor resource object, or null if not found
   */
  getServiceMonitor: async function (serviceMonitorName, namespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
      const response = await k8sCustomApi.getNamespacedCustomObject(
        PROMETHEUS_GROUP,
        PROMETHEUS_VERSION,
        namespace,
        SERVICEMONITOR_PLURAL,
        serviceMonitorName
      );
      return response.body;
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        return null; // ServiceMonitor not found
      }
      throw error;
    }
  },

  /**
   * Function that lists all ServiceMonitor resources in a namespace
   * @param {String} namespace - Namespace to search for ServiceMonitors
   * @return {Array} - Array of ServiceMonitor resource objects
   */
  listServiceMonitors: async function (namespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
      const response = await k8sCustomApi.listNamespacedCustomObject(
        PROMETHEUS_GROUP,
        PROMETHEUS_VERSION,
        namespace,
        SERVICEMONITOR_PLURAL
      );
      return response.body.items || [];
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        return [];
      }
      throw error;
    }
  },

  /**
   * Function that checks if a ServiceMonitor exists
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should exist
   * @return {Boolean} - True if ServiceMonitor exists, false otherwise
   */
  serviceMonitorExists: async function (serviceMonitorName, namespace) {
    const serviceMonitor = await this.getServiceMonitor(serviceMonitorName, namespace);
    return serviceMonitor !== null;
  },

  /**
   * Function that validates ServiceMonitor configuration
   * @param {Object} serviceMonitor - The ServiceMonitor resource object
   * @param {Object} expectedConfig - Expected configuration object
   * @return {Boolean} - True if configuration is valid, false otherwise
   */
  validateServiceMonitorConfig: function (serviceMonitor, expectedConfig) {
    try {
      assert(serviceMonitor, 'ServiceMonitor should exist');
      assert(serviceMonitor.spec, 'ServiceMonitor should have spec');
      assert(serviceMonitor.spec.selector, 'ServiceMonitor should have selector');
      assert(serviceMonitor.spec.endpoints, 'ServiceMonitor should have endpoints');
      assert(serviceMonitor.spec.endpoints.length > 0, 'ServiceMonitor should have at least one endpoint');

      const endpoint = serviceMonitor.spec.endpoints[0];

      if (expectedConfig.path) {
        assert(endpoint.path === expectedConfig.path, 
          `ServiceMonitor path should be '${expectedConfig.path}', but found '${endpoint.path}'`);
      }

      if (expectedConfig.port) {
        assert(endpoint.port === expectedConfig.port, 
          `ServiceMonitor port should be '${expectedConfig.port}', but found '${endpoint.port}'`);
      }

      if (expectedConfig.interval) {
        assert(endpoint.interval === expectedConfig.interval, 
          `ServiceMonitor interval should be '${expectedConfig.interval}', but found '${endpoint.interval}'`);
      }

      if (expectedConfig.targetLabels) {
        assert(serviceMonitor.spec.selector.matchLabels, 'ServiceMonitor should have matchLabels');
        for (const [key, value] of Object.entries(expectedConfig.targetLabels)) {
          assert(serviceMonitor.spec.selector.matchLabels[key] === value, 
            `ServiceMonitor should target service with label '${key}=${value}', but found '${key}=${serviceMonitor.spec.selector.matchLabels[key]}'`);
        }
      }

      if (expectedConfig.labels) {
        assert(serviceMonitor.metadata.labels, 'ServiceMonitor should have labels');
        for (const [key, value] of Object.entries(expectedConfig.labels)) {
          assert(serviceMonitor.metadata.labels[key] === value, 
            `ServiceMonitor should have label '${key}=${value}', but found '${key}=${serviceMonitor.metadata.labels[key]}'`);
        }
      }

      return true;
    } catch (error) {
      console.error(`ServiceMonitor validation failed: ${error.message}`);
      return false;
    }
  },

  /**
   * Function that waits for a ServiceMonitor to be created
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should be created
   * @param {Number} timeoutMs - Timeout in milliseconds (default: 30000)
   * @return {Object} - The ServiceMonitor resource object when found
   */
  waitForServiceMonitor: async function (serviceMonitorName, namespace, timeoutMs = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeoutMs) {
      const serviceMonitor = await this.getServiceMonitor(serviceMonitorName, namespace);
      if (serviceMonitor) {
        return serviceMonitor;
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`ServiceMonitor '${serviceMonitorName}' was not created in namespace '${namespace}' within ${timeoutMs}ms`);
  },

  /**
   * Function that waits for a ServiceMonitor to be deleted
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should be deleted
   * @param {Number} timeoutMs - Timeout in milliseconds (default: 30000)
   * @return {Boolean} - True when ServiceMonitor is deleted
   */
  waitForServiceMonitorDeletion: async function (serviceMonitorName, namespace, timeoutMs = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeoutMs) {
      const serviceMonitor = await this.getServiceMonitor(serviceMonitorName, namespace);
      if (!serviceMonitor) {
        return true;
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`ServiceMonitor '${serviceMonitorName}' was not deleted from namespace '${namespace}' within ${timeoutMs}ms`);
  },

  /**
   * Function that gets ServiceMonitor configuration details
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor exists
   * @return {Object} - ServiceMonitor configuration details
   */
  getServiceMonitorConfig: async function (serviceMonitorName, namespace) {
    const serviceMonitor = await this.getServiceMonitor(serviceMonitorName, namespace);
    if (!serviceMonitor) {
      throw new Error(`ServiceMonitor '${serviceMonitorName}' not found in namespace '${namespace}'`);
    }

    const endpoint = serviceMonitor.spec.endpoints[0] || {};
    
    return {
      name: serviceMonitor.metadata.name,
      namespace: serviceMonitor.metadata.namespace,
      labels: serviceMonitor.metadata.labels || {},
      selector: serviceMonitor.spec.selector || {},
      endpoint: {
        path: endpoint.path,
        port: endpoint.port,
        interval: endpoint.interval,
        scheme: endpoint.scheme
      }
    };
  },

  /**
   * Function that creates a ServiceMonitor resource (for testing purposes)
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor should be created
   * @param {Object} config - ServiceMonitor configuration
   * @return {Object} - The created ServiceMonitor resource object
   */
  createServiceMonitor: async function (serviceMonitorName, namespace, config) {
    const serviceMonitorManifest = {
      apiVersion: `${PROMETHEUS_GROUP}/${PROMETHEUS_VERSION}`,
      kind: 'ServiceMonitor',
      metadata: {
        name: serviceMonitorName,
        namespace: namespace,
        labels: config.labels || {}
      },
      spec: {
        selector: config.selector || {},
        endpoints: config.endpoints || [{
          port: 'http',
          path: '/metrics',
          interval: '15s'
        }]
      }
    };

    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
      const response = await k8sCustomApi.createNamespacedCustomObject(
        PROMETHEUS_GROUP,
        PROMETHEUS_VERSION,
        namespace,
        SERVICEMONITOR_PLURAL,
        serviceMonitorManifest
      );
      return response.body;
    } catch (error) {
      throw new Error(`Failed to create ServiceMonitor '${serviceMonitorName}': ${error.message}`);
    }
  },

  /**
   * Function that deletes a ServiceMonitor resource (for testing purposes)
   * @param {String} serviceMonitorName - Name of the ServiceMonitor resource
   * @param {String} namespace - Namespace where the ServiceMonitor exists
   * @return {Boolean} - True if deletion was successful
   */
  deleteServiceMonitor: async function (serviceMonitorName, namespace) {
    try {
      const k8sCustomApi = kc.makeApiClient(k8s.CustomObjectsApi);
      await k8sCustomApi.deleteNamespacedCustomObject(
        PROMETHEUS_GROUP,
        PROMETHEUS_VERSION,
        namespace,
        SERVICEMONITOR_PLURAL,
        serviceMonitorName
      );
      return true;
    } catch (error) {
      if (error.response && error.response.statusCode === 404) {
        return true; // Already deleted
      }
      throw new Error(`Failed to delete ServiceMonitor '${serviceMonitorName}': ${error.message}`);
    }
  }
};

module.exports = observabilityUtils;
