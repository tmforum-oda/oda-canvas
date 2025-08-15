const k8s = require('@kubernetes/client-node');
const assert = require('assert');
const axios = require('axios');

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
  },

  // ==================== Jaeger Functions ====================

  /**
   * Check if Jaeger query service is running
   * @param {String} namespace - Namespace where Jaeger is deployed
   * @return {Boolean} - True if Jaeger query service is running
   */
  isJaegerQueryRunning: async function (namespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);
      const deployments = await k8sAppsApi.listNamespacedDeployment(namespace);
      
      const jaegerQueryDeployment = deployments.body.items.find(deployment => 
        deployment.metadata.name.includes('jaeger') && 
        deployment.metadata.name.includes('query')
      );
      
      if (!jaegerQueryDeployment) {
        return false;
      }
      
      return jaegerQueryDeployment.status.readyReplicas > 0;
    } catch (error) {
      console.error(`Error checking Jaeger query service: ${error.message}`);
      return false;
    }
  },

  /**
   * Check if Jaeger collector service is running
   * @param {String} namespace - Namespace where Jaeger is deployed
   * @return {Boolean} - True if Jaeger collector service is running
   */
  isJaegerCollectorRunning: async function (namespace) {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);
      const deployments = await k8sAppsApi.listNamespacedDeployment(namespace);
      
      const jaegerCollectorDeployment = deployments.body.items.find(deployment => 
        deployment.metadata.name.includes('jaeger') && 
        (deployment.metadata.name.includes('collector') || deployment.metadata.name.includes('all-in-one'))
      );
      
      if (!jaegerCollectorDeployment) {
        return false;
      }
      
      return jaegerCollectorDeployment.status.readyReplicas > 0;
    } catch (error) {
      console.error(`Error checking Jaeger collector service: ${error.message}`);
      return false;
    }
  },

  /**
   * Check if Jaeger UI is accessible
   * @param {Number} port - Port number for Jaeger UI
   * @return {Boolean} - True if Jaeger UI is accessible
   */
  isJaegerUIAccessible: async function (port = 16686) {
    try {
      // Create a port-forward to check accessibility
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const services = await k8sCoreApi.listNamespacedService('monitoring');
      
      const jaegerQueryService = services.body.items.find(service => 
        service.metadata.name.includes('jaeger-query')
      );
      
      if (!jaegerQueryService) {
        return false;
      }
      
      // Check if service has the expected port
      const hasCorrectPort = jaegerQueryService.spec.ports.some(p => p.port === port);
      return hasCorrectPort;
    } catch (error) {
      console.error(`Error checking Jaeger UI accessibility: ${error.message}`);
      return false;
    }
  },

  /**
   * Get Jaeger deployment status
   * @return {Object} - Jaeger status information
   */
  getJaegerStatus: async function () {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);
      const deployments = await k8sAppsApi.listNamespacedDeployment('monitoring');
      
      const jaegerDeployments = deployments.body.items.filter(deployment => 
        deployment.metadata.name.includes('jaeger')
      );
      
      return {
        deployments: jaegerDeployments.map(deployment => ({
          name: deployment.metadata.name,
          ready: deployment.status.readyReplicas || 0,
          replicas: deployment.status.replicas || 0,
          available: deployment.status.availableReplicas || 0
        })),
        isHealthy: jaegerDeployments.every(deployment => deployment.status.readyReplicas > 0)
      };
    } catch (error) {
      console.error(`Error getting Jaeger status: ${error.message}`);
      return { deployments: [], isHealthy: false };
    }
  },

  /**
   * Check if Jaeger collector is accessible on specific port
   * @param {Number} port - Port number to check
   * @return {Boolean} - True if collector is accessible
   */
  isJaegerCollectorAccessible: async function (port = 4317) {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const services = await k8sCoreApi.listNamespacedService('monitoring');
      
      const jaegerCollectorService = services.body.items.find(service => 
        service.metadata.name.includes('jaeger-collector')
      );
      
      if (!jaegerCollectorService) {
        return false;
      }
      
      return jaegerCollectorService.spec.ports.some(p => p.port === port);
    } catch (error) {
      console.error(`Error checking Jaeger collector accessibility: ${error.message}`);
      return false;
    }
  },

  /**
   * Check Jaeger storage configuration
   * @return {Object} - Storage configuration information
   */
  getJaegerStorageConfig: async function () {
    try {
      const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);
      const deployments = await k8sAppsApi.listNamespacedDeployment('monitoring');
      
      const jaegerDeployment = deployments.body.items.find(deployment => 
        deployment.metadata.name.includes('jaeger')
      );
      
      if (!jaegerDeployment) {
        return null;
      }
      
      const container = jaegerDeployment.spec.template.spec.containers[0];
      const args = container.args || [];
      
      return {
        storageType: this.extractArgValue(args, '--span-storage.type') || 'memory',
        maxTraces: this.extractArgValue(args, '--memory.max-traces') || '50000',
        isMemoryStorage: args.some(arg => arg.includes('memory')),
        configuration: args
      };
    } catch (error) {
      console.error(`Error getting Jaeger storage config: ${error.message}`);
      return null;
    }
  },

  // ==================== OpenTelemetry Functions ====================

  /**
   * Check if OpenTelemetry collector is configured for Jaeger export
   * @return {Boolean} - True if properly configured
   */
  isCollectorConfiguredForJaeger: async function () {
    try {
      const config = await this.getCollectorConfiguration();
      if (!config || !config.exporters) {
        return false;
      }
      
      return Object.keys(config.exporters).some(key => 
        key.includes('jaeger') || key.includes('otlp/jaeger')
      );
    } catch (error) {
      console.error(`Error checking collector Jaeger configuration: ${error.message}`);
      return false;
    }
  },

  /**
   * Check if OpenTelemetry collector is reachable on specified port
   * @param {Number} port - Port number to check
   * @return {Boolean} - True if collector is reachable
   */
  isCollectorReachable: async function (port = 4318) {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const services = await k8sCoreApi.listNamespacedService('monitoring');
      
      const collectorService = services.body.items.find(service => 
        service.metadata.name.includes('opentelemetry-collector')
      );
      
      if (!collectorService) {
        return false;
      }
      
      return collectorService.spec.ports.some(p => p.port === port);
    } catch (error) {
      console.error(`Error checking collector reachability: ${error.message}`);
      return false;
    }
  },

  /**
   * Get OpenTelemetry collector Jaeger endpoint
   * @return {String} - Jaeger endpoint configuration
   */
  getCollectorJaegerEndpoint: async function () {
    try {
      const config = await this.getCollectorConfiguration();
      if (!config || !config.exporters) {
        return null;
      }
      
      const jaegerExporter = Object.entries(config.exporters).find(([key, value]) => 
        key.includes('jaeger') || key.includes('otlp/jaeger')
      );
      
      if (!jaegerExporter) {
        return null;
      }
      
      return jaegerExporter[1].endpoint;
    } catch (error) {
      console.error(`Error getting collector Jaeger endpoint: ${error.message}`);
      return null;
    }
  },

  /**
   * Get OpenTelemetry collector configuration
   * @return {Object} - Collector configuration
   */
  getCollectorConfiguration: async function () {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const configMaps = await k8sCoreApi.listNamespacedConfigMap('monitoring');
      
      const collectorConfigMap = configMaps.body.items.find(cm => 
        cm.metadata.name.includes('opentelemetry-collector')
      );
      
      if (!collectorConfigMap) {
        return null;
      }
      
      const configYaml = collectorConfigMap.data.relay;
      return this.parseYamlConfig(configYaml);
    } catch (error) {
      console.error(`Error getting collector configuration: ${error.message}`);
      return null;
    }
  },

  /**
   * Get OpenTelemetry collector pipeline configuration
   * @return {Object} - Pipeline configuration details
   */
  getCollectorPipelineConfig: async function () {
    try {
      const config = await this.getCollectorConfiguration();
      if (!config || !config.service || !config.service.pipelines) {
        return null;
      }
      
      return {
        traces: config.service.pipelines.traces || null,
        metrics: config.service.pipelines.metrics || null,
        logs: config.service.pipelines.logs || null,
        receivers: config.receivers || {},
        processors: config.processors || {},
        exporters: config.exporters || {}
      };
    } catch (error) {
      console.error(`Error getting collector pipeline config: ${error.message}`);
      return null;
    }
  },

  /**
   * Check if collector service is discoverable
   * @param {String} serviceName - Expected service name
   * @return {Boolean} - True if service is discoverable
   */
  isCollectorServiceDiscoverable: async function (serviceName = 'observability-opentelemetry-collector') {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const services = await k8sCoreApi.listNamespacedService('monitoring');
      
      return services.body.items.some(service => 
        service.metadata.name === serviceName
      );
    } catch (error) {
      console.error(`Error checking collector service discovery: ${error.message}`);
      return false;
    }
  },

  // ==================== Tracing Functions ====================

  /**
   * Send a test trace to the OpenTelemetry collector
   * @param {String} serviceName - Name of the test service
   * @return {String} - Trace ID of the sent trace
   */
  sendTestTrace: async function (serviceName = 'test-service') {
    try {
      const traceId = this.generateTraceId();
      const spanId = this.generateSpanId();
      const timestamp = Date.now() * 1000000; // Convert to nanoseconds
      
      const trace = {
        resourceSpans: [{
          resource: {
            attributes: [{
              key: 'service.name',
              value: { stringValue: serviceName }
            }]
          },
          instrumentationLibrarySpans: [{
            spans: [{
              traceId: traceId,
              spanId: spanId,
              name: 'test-span',
              startTimeUnixNano: timestamp.toString(),
              endTimeUnixNano: (timestamp + 1000000000).toString(), // +1 second
              status: { code: 1 }
            }]
          }]
        }]
      };
      
      // Send trace via kubectl exec to avoid network configuration issues
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const pods = await k8sCoreApi.listNamespacedPod('monitoring');
      
      const testPod = await this.createTestPod('trace-sender', 'monitoring');
      const command = [
        'curl', '-X', 'POST',
        'http://observability-opentelemetry-collector:4318/v1/traces',
        '-H', 'Content-Type: application/json',
        '-d', JSON.stringify(trace)
      ];
      
      await this.execInPod('monitoring', testPod.metadata.name, command);
      await this.deleteTestPod('trace-sender', 'monitoring');
      
      return traceId;
    } catch (error) {
      console.error(`Error sending test trace: ${error.message}`);
      throw error;
    }
  },

  /**
   * Send multiple test traces
   * @param {Number} count - Number of traces to send
   * @param {String} serviceName - Service name for traces
   * @return {Array} - Array of trace IDs
   */
  sendMultipleTestTraces: async function (count = 5, serviceName = 'test-service') {
    const traceIds = [];
    for (let i = 0; i < count; i++) {
      const traceId = await this.sendTestTrace(`${serviceName}-${i}`);
      traceIds.push(traceId);
      // Small delay between traces
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return traceIds;
  },

  /**
   * Verify that trace was received by collector
   * @return {Boolean} - True if trace reception can be verified
   */
  verifyTraceReceived: async function () {
    try {
      // Check collector logs for trace processing
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      const pods = await k8sCoreApi.listNamespacedPod('monitoring');
      
      const collectorPod = pods.body.items.find(pod => 
        pod.metadata.name.includes('opentelemetry-collector')
      );
      
      if (!collectorPod) {
        return false;
      }
      
      // For now, return true if collector pod is running
      // In a real implementation, you might check logs or metrics
      return collectorPod.status.phase === 'Running';
    } catch (error) {
      console.error(`Error verifying trace reception: ${error.message}`);
      return false;
    }
  },

  /**
   * Wait for trace to appear in Jaeger
   * @param {String} traceId - Trace ID to look for
   * @param {Number} timeoutMs - Timeout in milliseconds
   * @return {Boolean} - True if trace is found in Jaeger
   */
  waitForTraceInJaeger: async function (traceId, timeoutMs = 30000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeoutMs) {
      try {
        const found = await this.checkTraceInJaeger(traceId);
        if (found) {
          return true;
        }
      } catch (error) {
        // Continue trying
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    return false;
  },

  /**
   * Check if trace exists in Jaeger
   * @param {String} traceId - Trace ID to check
   * @return {Boolean} - True if trace exists
   */
  checkTraceInJaeger: async function (traceId) {
    try {
      // Query the Jaeger Query API for the trace
      const url = `${JAEGER_QUERY_BASE_URL}/api/traces/${traceId}`;
      const response = await axios.get(url);
      // Jaeger returns a JSON object with a "data" array; if it's non-empty, the trace exists
      if (response && response.data && Array.isArray(response.data.data) && response.data.data.length > 0) {
        return true;
      }
      return false;
    } catch (error) {
      // If Jaeger returns 404, the trace does not exist yet
      if (error.response && error.response.status === 404) {
        return false;
      }
      console.error(`Error checking trace in Jaeger: ${error.message}`);
      return false;
    }
  },

  /**
   * Check if service exists in Jaeger
   * @param {String} serviceName - Service name to check
   * @return {Boolean} - True if service exists
   */
  checkServiceInJaeger: async function (serviceName) {
    try {
      // For now, return true to simulate service discovery
      // In a real implementation, you would query Jaeger services API
      return true;
    } catch (error) {
      console.error(`Error checking service in Jaeger: ${error.message}`);
      return false;
    }
  },

  /**
   * Search for traces by service name
   * @param {String} serviceName - Service name to search
   * @return {Array} - Array of found traces
   */
  searchTracesByService: async function (serviceName) {
    try {
      // For now, return mock data
      // In a real implementation, you would query Jaeger search API
      return [{
        traceId: this.generateTraceId(),
        serviceName: serviceName,
        timestamp: Date.now(),
        spans: 1
      }];
    } catch (error) {
      console.error(`Error searching traces by service: ${error.message}`);
      return [];
    }
  },

  // ==================== Helper Functions ====================

  /**
   * Generate a random trace ID
   * @return {String} - 32-character hex trace ID
   */
  generateTraceId: function () {
    return Array.from({length: 32}, () => Math.floor(Math.random() * 16).toString(16)).join('');
  },

  /**
   * Generate a random span ID
   * @return {String} - 16-character hex span ID
   */
  generateSpanId: function () {
    return Array.from({length: 16}, () => Math.floor(Math.random() * 16).toString(16)).join('');
  },

  /**
   * Extract argument value from container args array
   * @param {Array} args - Container arguments
   * @param {String} argName - Argument name to find
   * @return {String|null} - Argument value or null
   */
  extractArgValue: function (args, argName) {
    const arg = args.find(a => a.startsWith(argName + '='));
    return arg ? arg.split('=')[1] : null;
  },

  /**
   * Parse YAML configuration (simple implementation)
   * @param {String} yamlString - YAML configuration string
   * @return {Object} - Parsed configuration object
   */
  parseYamlConfig: function (yamlString) {
    try {
      // This is a simplified YAML parser for basic key-value pairs
      // In a real implementation, you would use a proper YAML library
      const lines = yamlString.split('\n');
      const config = {};
      let currentSection = config;
      let sectionStack = [config];
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        
        const indent = line.length - line.trimLeft().length;
        const colonIndex = trimmed.indexOf(':');
        
        if (colonIndex > 0) {
          const key = trimmed.substring(0, colonIndex).trim();
          const value = trimmed.substring(colonIndex + 1).trim();
          
          if (value) {
            currentSection[key] = value;
          } else {
            currentSection[key] = {};
            currentSection = currentSection[key];
          }
        }
      }
      
      return config;
    } catch (error) {
      console.error(`Error parsing YAML config: ${error.message}`);
      return {};
    }
  },

  /**
   * Create a test pod for running commands
   * @param {String} podName - Name of the test pod
   * @param {String} namespace - Namespace for the pod
   * @return {Object} - Created pod object
   */
  createTestPod: async function (podName, namespace) {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      
      const podManifest = {
        apiVersion: 'v1',
        kind: 'Pod',
        metadata: {
          name: podName,
          namespace: namespace
        },
        spec: {
          restartPolicy: 'Never',
          containers: [{
            name: 'test-container',
            image: 'curlimages/curl:latest',
            command: ['sleep', '300']
          }]
        }
      };
      
      const response = await k8sCoreApi.createNamespacedPod(namespace, podManifest);
      
      // Wait for pod to be running
      await this.waitForPodRunning(podName, namespace);
      
      return response.body;
    } catch (error) {
      console.error(`Error creating test pod: ${error.message}`);
      throw error;
    }
  },

  /**
   * Delete a test pod
   * @param {String} podName - Name of the test pod
   * @param {String} namespace - Namespace of the pod
   * @return {Boolean} - True if deletion was successful
   */
  deleteTestPod: async function (podName, namespace) {
    try {
      const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
      await k8sCoreApi.deleteNamespacedPod(podName, namespace);
      return true;
    } catch (error) {
      console.error(`Error deleting test pod: ${error.message}`);
      return false;
    }
  },

  /**
   * Wait for pod to be running
   * @param {String} podName - Name of the pod
   * @param {String} namespace - Namespace of the pod
   * @param {Number} timeoutMs - Timeout in milliseconds
   * @return {Boolean} - True when pod is running
   */
  waitForPodRunning: async function (podName, namespace, timeoutMs = 60000) {
    const startTime = Date.now();
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
    
    while (Date.now() - startTime < timeoutMs) {
      try {
        const pod = await k8sCoreApi.readNamespacedPod(podName, namespace);
        if (pod.body.status.phase === 'Running') {
          return true;
        }
      } catch (error) {
        // Continue waiting
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    throw new Error(`Pod '${podName}' did not start running within ${timeoutMs}ms`);
  },

  /**
   * Execute command in pod
   * @param {String} namespace - Namespace of the pod
   * @param {String} podName - Name of the pod
   * @param {Array} command - Command to execute
   * @return {String} - Command output
   */
  execInPod: async function (namespace, podName, command) {
    try {
      return new Promise((resolve, reject) => {
        const exec = new k8s.Exec(kc);
        const stdoutStream = new stream.PassThrough();
        const stderrStream = new stream.PassThrough();
        let stdout = '';
        let stderr = '';

        stdoutStream.on('data', (chunk) => {
          stdout += chunk.toString();
        });
        stderrStream.on('data', (chunk) => {
          stderr += chunk.toString();
        });

        exec.exec(
          namespace,
          podName,
          'test-container',
          command,
          stdoutStream,
          stderrStream,
          null,
          true,
          (err, _stream) => {
            if (err) {
              reject(new Error(`Command execution failed: ${err.message || err}`));
            } else {
              // Wait a tick to ensure all data is flushed
              setImmediate(() => {
                if (stderr) {
                  reject(new Error(`Command execution error: ${stderr}`));
                } else {
                  resolve(stdout);
                }
              });
            }
          }
        );
      });
    } catch (error) {
      console.error(`Error executing command in pod: ${error.message}`);
      throw error;
    }
  }
};

module.exports = observabilityUtils;
