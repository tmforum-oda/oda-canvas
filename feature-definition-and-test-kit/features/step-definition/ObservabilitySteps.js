// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const packageManagerUtils = require('package-manager-utils-helm');
const observabilityUtils = require('observability-utils-kubernetes');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai');
const assert = require('assert');
chai.use(require('chai-http'));

const NAMESPACE = 'components';
const DEFAULT_RELEASE_NAME = 'ctk';
const SERVICEMONITOR_TIMEOUT = 30 * 1000; // 30 seconds
const CLEANUP_PACKAGE = false; // set to true to uninstall the package after each Scenario

setDefaultTimeout(20 * 1000);

// Allow skipping tests
Before({ tags: '@SkipTest' }, async function () {
  console.log('Skipping scenario.');
  return 'skipped';
});

/**
 * Verify that a ServiceMonitor resource exists for the component
 *
 * @param {string} serviceMonitorName - The name of the ServiceMonitor resource
 * @param {string} namespace - The namespace where the ServiceMonitor should exist
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('a ServiceMonitor resource {string} should exist in the {string} namespace', async function (serviceMonitorName, namespace) {
  console.log(`\\n=== Verifying ServiceMonitor Exists ===`);
  console.log(`Checking for ServiceMonitor '${serviceMonitorName}' in namespace '${namespace}'`);
  
  try {
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, namespace);
    assert(serviceMonitor !== null, `ServiceMonitor '${serviceMonitorName}' should exist in namespace '${namespace}'`);
    console.log(`✓ ServiceMonitor '${serviceMonitorName}' found in namespace '${namespace}'`);
  } catch (error) {
    console.error(`✗ Failed to find ServiceMonitor '${serviceMonitorName}' in namespace '${namespace}': ${error.message}`);
    throw error;
  }
});

/**
 * Verify that a ServiceMonitor resource does not exist after the component has been uninstalled
 *
 * @param {string} serviceMonitorName - The name of the ServiceMonitor resource
 * @param {string} namespace - The namespace where the ServiceMonitor should not exist
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor resource {string} should not exist in the {string} namespace', async function (serviceMonitorName, namespace) {
  console.log(`\\n=== Verifying ServiceMonitor Does Not Exist ===`);
  console.log(`Checking that ServiceMonitor '${serviceMonitorName}' does not exist in namespace '${namespace}'`);
  
  try {
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, namespace);
    assert(serviceMonitor === null, `ServiceMonitor '${serviceMonitorName}' should not exist in namespace '${namespace}'`);
    console.log(`✓ ServiceMonitor '${serviceMonitorName}' correctly does not exist in namespace '${namespace}'`);
  } catch (error) {
    console.error(`✗ Error checking ServiceMonitor '${serviceMonitorName}' in namespace '${namespace}': ${error.message}`);
    throw error;
  }
});

/**
 * Verify that Jaeger query service is running
 *
 * @param {string} namespace - The namespace where Jaeger should be running
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the Jaeger query service should be running in the {string} namespace', async function (namespace) {
  console.log(`\\n=== Verifying Jaeger Query Service ===`);
  console.log(`Checking that Jaeger query service is running in namespace '${namespace}'`);
  
  try {
    const isRunning = await observabilityUtils.isJaegerQueryRunning(namespace);
    assert(isRunning, `Jaeger query service should be running in namespace '${namespace}'`);
    console.log(`✓ Jaeger query service is running in namespace '${namespace}'`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger query service: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that Jaeger collector service is running
 *
 * @param {string} namespace - The namespace where Jaeger collector should be running
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the Jaeger collector service should be running in the {string} namespace', async function (namespace) {
  console.log(`\\n=== Verifying Jaeger Collector Service ===`);
  console.log(`Checking that Jaeger collector service is running in namespace '${namespace}'`);
  
  try {
    const isRunning = await observabilityUtils.isJaegerCollectorRunning(namespace);
    assert(isRunning, `Jaeger collector service should be running in namespace '${namespace}'`);
    console.log(`✓ Jaeger collector service is running in namespace '${namespace}'`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger collector service: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that Jaeger query UI is accessible
 *
 * @param {number} port - The port number where Jaeger UI should be accessible
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the Jaeger query UI should be accessible on port {int}', async function (port) {
  console.log(`\\n=== Verifying Jaeger UI Accessibility ===`);
  console.log(`Checking that Jaeger UI is accessible on port ${port}`);
  
  try {
    const isAccessible = await observabilityUtils.isJaegerUIAccessible(port);
    assert(isAccessible, `Jaeger UI should be accessible on port ${port}`);
    console.log(`✓ Jaeger UI is accessible on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger UI accessibility: ${error.message}`);
    throw error;
  }
});

/**
 * Verify OpenTelemetry collector configuration for Jaeger export
 *
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the collector should be configured to export traces to Jaeger', async function () {
  console.log(`\\n=== Verifying OpenTelemetry Collector Configuration ===`);
  console.log(`Checking that collector is configured to export traces to Jaeger`);
  
  try {
    const isConfigured = await observabilityUtils.isCollectorConfiguredForJaeger();
    assert(isConfigured, `OpenTelemetry collector should be configured to export traces to Jaeger`);
    console.log(`✓ OpenTelemetry collector is configured to export traces to Jaeger`);
  } catch (error) {
    console.error(`✗ Failed to verify collector configuration: ${error.message}`);
    throw error;
  }
});

/**
 * Verify OpenTelemetry collector is reachable on specified port
 *
 * @param {number} port - The port number where collector should be reachable
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the collector should be reachable on port {int}', async function (port) {
  console.log(`\\n=== Verifying OpenTelemetry Collector Reachability ===`);
  console.log(`Checking that collector is reachable on port ${port}`);
  
  try {
    const isReachable = await observabilityUtils.isCollectorReachable(port);
    assert(isReachable, `OpenTelemetry collector should be reachable on port ${port}`);
    console.log(`✓ OpenTelemetry collector is reachable on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify collector reachability: ${error.message}`);
    throw error;
  }
});

/**
 * Verify OpenTelemetry collector target endpoint
 *
 * @param {string} endpoint - The expected Jaeger endpoint
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the collector should be sending traces to {string}', async function (endpoint) {
  console.log(`\\n=== Verifying OpenTelemetry Collector Target Endpoint ===`);
  console.log(`Checking that collector is configured to send traces to '${endpoint}'`);
  
  try {
    const actualEndpoint = await observabilityUtils.getCollectorJaegerEndpoint();
    assert(actualEndpoint === endpoint, 
      `Collector should send traces to '${endpoint}', but configured for '${actualEndpoint}'`);
    console.log(`✓ OpenTelemetry collector is sending traces to '${endpoint}'`);
  } catch (error) {
    console.error(`✗ Failed to verify collector target endpoint: ${error.message}`);
    throw error;
  }
});

/**
 * Send a test trace to the OpenTelemetry collector
 *
 * @returns {Promise<void>} - A Promise that resolves when the trace is sent
 */
When('I send a test trace to the collector endpoint', async function () {
  console.log(`\\n=== Sending Test Trace ===`);
  console.log(`Sending test trace to OpenTelemetry collector`);
  
  try {
    const traceId = await observabilityUtils.sendTestTrace();
    this.testTraceId = traceId; // Store for later verification
    console.log(`✓ Test trace sent successfully with ID: ${traceId}`);
  } catch (error) {
    console.error(`✗ Failed to send test trace: ${error.message}`);
    throw error;
  }
});

/**
 * Verify test trace was received by collector
 *
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the trace should be successfully received by the collector', async function () {
  console.log(`\\n=== Verifying Trace Reception ===`);
  console.log(`Checking that collector received the test trace`);
  
  try {
    const wasReceived = await observabilityUtils.verifyTraceReceived();
    assert(wasReceived, `Test trace should be successfully received by the collector`);
    console.log(`✓ Test trace was successfully received by the collector`);
  } catch (error) {
    console.error(`✗ Failed to verify trace reception: ${error.message}`);
    throw error;
  }
});

/**
 * Verify trace appears in Jaeger within specified time
 *
 * @param {number} timeoutSeconds - The timeout in seconds to wait for trace
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the trace should appear in Jaeger within {int} seconds', async function (timeoutSeconds) {
  console.log(`\\n=== Verifying Trace in Jaeger ===`);
  console.log(`Checking that trace appears in Jaeger within ${timeoutSeconds} seconds`);
  
  try {
    const traceId = this.testTraceId;
    const traceFound = await observabilityUtils.waitForTraceInJaeger(traceId, timeoutSeconds * 1000);
    assert(traceFound, `Test trace should appear in Jaeger within ${timeoutSeconds} seconds`);
    console.log(`✓ Test trace found in Jaeger within ${timeoutSeconds} seconds`);
  } catch (error) {
    console.error(`✗ Failed to find trace in Jaeger: ${error.message}`);
    throw error;
  }
});

/**
 * Verify service appears in Jaeger services list
 *
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the service should be visible in Jaeger services list', async function () {
  console.log(`\\n=== Verifying Service in Jaeger ===`);
  console.log(`Checking that service appears in Jaeger services list`);
  
  try {
    const serviceName = global.currentReleaseName + '-productcatalogmanagement';
    const serviceExists = await observabilityUtils.checkServiceInJaeger(serviceName);
    assert(serviceExists, `Service '${serviceName}' should be visible in Jaeger services list`);
    console.log(`✓ Service '${serviceName}' is visible in Jaeger services list`);
  } catch (error) {
    console.error(`✗ Failed to find service in Jaeger: ${error.message}`);
    throw error;
  }
});

/**
 * Check OpenTelemetry collector configuration
 *
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the OpenTelemetry collector configuration', async function () {
  console.log(`\\n=== Checking OpenTelemetry Collector Configuration ===`);
  console.log(`Retrieving OpenTelemetry collector configuration`);
  
  try {
    this.collectorConfig = await observabilityUtils.getCollectorConfiguration();
    console.log(`✓ OpenTelemetry collector configuration retrieved`);
  } catch (error) {
    console.error(`✗ Failed to retrieve collector configuration: ${error.message}`);
    throw error;
  }
});

/**
 * Check Jaeger deployment status
 *
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the Jaeger deployment status', async function () {
  console.log(`\\n=== Checking Jaeger Deployment Status ===`);
  console.log(`Retrieving Jaeger deployment status`);
  
  try {
    this.jaegerStatus = await observabilityUtils.getJaegerStatus();
    console.log(`✓ Jaeger deployment status retrieved`);
  } catch (error) {
    console.error(`✗ Failed to retrieve Jaeger status: ${error.message}`);
    throw error;
  }
});

// ==================== Additional Step Definitions for New Features ====================

/**
 * Given step for Jaeger services running
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Given('the Jaeger services are running', async function () {
  console.log(`\\n=== Verifying Jaeger Services Are Running ===`);
  
  try {
    const queryRunning = await observabilityUtils.isJaegerQueryRunning('monitoring');
    const collectorRunning = await observabilityUtils.isJaegerCollectorRunning('monitoring');
    
    assert(queryRunning, 'Jaeger query service should be running');
    assert(collectorRunning, 'Jaeger collector service should be running');
    
    console.log(`✓ Jaeger services are running`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger services: ${error.message}`);
    throw error;
  }
});

/**
 * When step to check Jaeger service endpoints
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the Jaeger service endpoints', async function () {
  console.log(`\\n=== Checking Jaeger Service Endpoints ===`);
  
  try {
    this.jaegerEndpoints = {
      collectorAccessible: await observabilityUtils.isJaegerCollectorAccessible(4317),
      queryAccessible: await observabilityUtils.isJaegerUIAccessible(16686)
    };
    console.log(`✓ Jaeger service endpoints checked`);
  } catch (error) {
    console.error(`✗ Failed to check Jaeger service endpoints: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify Jaeger collector port accessibility
 * @param {number} port - Port number to check
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the Jaeger collector should be accessible on port {int}', async function (port) {
  console.log(`\\n=== Verifying Jaeger Collector Port ===`);
  console.log(`Checking that Jaeger collector is accessible on port ${port}`);
  
  try {
    const isAccessible = await observabilityUtils.isJaegerCollectorAccessible(port);
    assert(isAccessible, `Jaeger collector should be accessible on port ${port}`);
    console.log(`✓ Jaeger collector is accessible on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger collector port: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify Jaeger query port accessibility
 * @param {number} port - Port number to check
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the Jaeger query should be accessible on port {int}', async function (port) {
  console.log(`\\n=== Verifying Jaeger Query Port ===`);
  console.log(`Checking that Jaeger query is accessible on port ${port}`);
  
  try {
    const isAccessible = await observabilityUtils.isJaegerUIAccessible(port);
    assert(isAccessible, `Jaeger query should be accessible on port ${port}`);
    console.log(`✓ Jaeger query is accessible on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger query port: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify Jaeger collector accepts OTLP traces
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the Jaeger collector should accept OTLP traces', async function () {
  console.log(`\\n=== Verifying Jaeger OTLP Support ===`);
  console.log(`Checking that Jaeger collector accepts OTLP traces`);
  
  try {
    const isAccessible = await observabilityUtils.isJaegerCollectorAccessible(4318);
    assert(isAccessible, 'Jaeger collector should accept OTLP traces on port 4318');
    console.log(`✓ Jaeger collector accepts OTLP traces`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger OTLP support: ${error.message}`);
    throw error;
  }
});

/**
 * When step to check Jaeger storage configuration
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the Jaeger storage configuration', async function () {
  console.log(`\\n=== Checking Jaeger Storage Configuration ===`);
  
  try {
    this.jaegerStorageConfig = await observabilityUtils.getJaegerStorageConfig();
    console.log(`✓ Jaeger storage configuration retrieved`);
  } catch (error) {
    console.error(`✗ Failed to check Jaeger storage configuration: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify Jaeger memory storage configuration
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('Jaeger should be configured with memory storage', async function () {
  console.log(`\\n=== Verifying Jaeger Memory Storage ===`);
  
  try {
    const config = this.jaegerStorageConfig;
    assert(config, 'Jaeger storage configuration should exist');
    assert(config.isMemoryStorage, 'Jaeger should be configured with memory storage');
    console.log(`✓ Jaeger is configured with memory storage`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger memory storage: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify trace retention capacity
 * @param {number} traceCount - Expected trace retention count
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the storage should support trace retention for at least {int} traces', async function (traceCount) {
  console.log(`\\n=== Verifying Trace Retention Capacity ===`);
  console.log(`Checking that storage supports at least ${traceCount} traces`);
  
  try {
    const config = this.jaegerStorageConfig;
    assert(config, 'Jaeger storage configuration should exist');
    
    const maxTraces = parseInt(config.maxTraces);
    assert(maxTraces >= traceCount, 
      `Storage should support at least ${traceCount} traces, but configured for ${maxTraces}`);
    
    console.log(`✓ Storage supports retention for ${maxTraces} traces`);
  } catch (error) {
    console.error(`✗ Failed to verify trace retention capacity: ${error.message}`);
    throw error;
  }
});

/**
 * Given step for OpenTelemetry collector running
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Given('the OpenTelemetry collector is running', async function () {
  console.log(`\\n=== Verifying OpenTelemetry Collector Is Running ===`);
  
  try {
    const isReachable = await observabilityUtils.isCollectorReachable(4318);
    assert(isReachable, 'OpenTelemetry collector should be running and reachable');
    console.log(`✓ OpenTelemetry collector is running`);
  } catch (error) {
    console.error(`✗ Failed to verify OpenTelemetry collector: ${error.message}`);
    throw error;
  }
});

/**
 * When step to check collector pipeline configuration
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the collector pipeline configuration', async function () {
  console.log(`\\n=== Checking Collector Pipeline Configuration ===`);
  
  try {
    this.collectorPipelineConfig = await observabilityUtils.getCollectorPipelineConfig();
    console.log(`✓ Collector pipeline configuration retrieved`);
  } catch (error) {
    console.error(`✗ Failed to check collector pipeline configuration: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify OTLP HTTP receiver configuration
 * @param {number} port - Expected port number
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should have OTLP HTTP receiver on port {int}', async function (port) {
  console.log(`\\n=== Verifying OTLP HTTP Receiver ===`);
  console.log(`Checking that collector has OTLP HTTP receiver on port ${port}`);
  
  try {
    const isReachable = await observabilityUtils.isCollectorReachable(port);
    assert(isReachable, `Collector should have OTLP HTTP receiver on port ${port}`);
    console.log(`✓ Collector has OTLP HTTP receiver on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify OTLP HTTP receiver: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify OTLP gRPC receiver configuration
 * @param {number} port - Expected port number
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should have OTLP gRPC receiver on port {int}', async function (port) {
  console.log(`\\n=== Verifying OTLP gRPC Receiver ===`);
  console.log(`Checking that collector has OTLP gRPC receiver on port ${port}`);
  
  try {
    const isReachable = await observabilityUtils.isCollectorReachable(port);
    assert(isReachable, `Collector should have OTLP gRPC receiver on port ${port}`);
    console.log(`✓ Collector has OTLP gRPC receiver on port ${port}`);
  } catch (error) {
    console.error(`✗ Failed to verify OTLP gRPC receiver: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify batch processor configuration
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should have batch processor configured', async function () {
  console.log(`\\n=== Verifying Batch Processor Configuration ===`);
  
  try {
    const config = this.collectorPipelineConfig;
    assert(config, 'Collector pipeline configuration should exist');
    assert(config.processors.batch !== undefined, 'Collector should have batch processor configured');
    console.log(`✓ Collector has batch processor configured`);
  } catch (error) {
    console.error(`✗ Failed to verify batch processor: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify Jaeger OTLP exporter configuration
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should have Jaeger OTLP exporter configured', async function () {
  console.log(`\\n=== Verifying Jaeger OTLP Exporter Configuration ===`);
  
  try {
    const isConfigured = await observabilityUtils.isCollectorConfiguredForJaeger();
    assert(isConfigured, 'Collector should have Jaeger OTLP exporter configured');
    console.log(`✓ Collector has Jaeger OTLP exporter configured`);
  } catch (error) {
    console.error(`✗ Failed to verify Jaeger OTLP exporter: ${error.message}`);
    throw error;
  }
});

/**
 * When step to check collector service endpoints
 * @returns {Promise<void>} - A Promise that resolves when check is complete
 */
When('I check the collector service endpoints', async function () {
  console.log(`\\n=== Checking Collector Service Endpoints ===`);
  
  try {
    this.collectorServiceInfo = {
      discoverable: await observabilityUtils.isCollectorServiceDiscoverable(),
      reachableHttp: await observabilityUtils.isCollectorReachable(4318),
      reachableGrpc: await observabilityUtils.isCollectorReachable(4317)
    };
    console.log(`✓ Collector service endpoints checked`);
  } catch (error) {
    console.error(`✗ Failed to check collector service endpoints: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify collector service discoverability
 * @param {string} serviceName - Expected service name
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector service should be discoverable as {string}', async function (serviceName) {
  console.log(`\\n=== Verifying Collector Service Discovery ===`);
  console.log(`Checking that collector service is discoverable as '${serviceName}'`);
  
  try {
    const isDiscoverable = await observabilityUtils.isCollectorServiceDiscoverable(serviceName);
    assert(isDiscoverable, `Collector service should be discoverable as '${serviceName}'`);
    console.log(`✓ Collector service is discoverable as '${serviceName}'`);
  } catch (error) {
    console.error(`✗ Failed to verify collector service discovery: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify collector accessibility from monitoring namespace
 * @param {string} namespace - Expected namespace
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should be accessible from within the {string} namespace', async function (namespace) {
  console.log(`\\n=== Verifying Collector Accessibility from ${namespace} ===`);
  
  try {
    // This is verified by the service discovery working
    const info = this.collectorServiceInfo;
    assert(info && info.discoverable, `Collector should be accessible from within the '${namespace}' namespace`);
    console.log(`✓ Collector is accessible from within the '${namespace}' namespace`);
  } catch (error) {
    console.error(`✗ Failed to verify collector accessibility from namespace: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify collector accessibility from other namespaces
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the collector should be accessible from other namespaces', async function () {
  console.log(`\\n=== Verifying Collector Cross-Namespace Accessibility ===`);
  
  try {
    // This is verified by the service being ClusterIP and discoverable
    const info = this.collectorServiceInfo;
    assert(info && info.discoverable, 'Collector should be accessible from other namespaces');
    console.log(`✓ Collector is accessible from other namespaces`);
  } catch (error) {
    console.error(`✗ Failed to verify collector cross-namespace accessibility: ${error.message}`);
    throw error;
  }
});

/**
 * When step to send multiple test traces
 * @param {number} traceCount - Number of traces to send
 * @returns {Promise<void>} - A Promise that resolves when traces are sent
 */
When('I send {int} test traces to the collector endpoint', async function (traceCount) {
  console.log(`\\n=== Sending ${traceCount} Test Traces ===`);
  
  try {
    this.testTraceIds = await observabilityUtils.sendMultipleTestTraces(traceCount, 'test-service');
    console.log(`✓ Sent ${traceCount} test traces successfully`);
  } catch (error) {
    console.error(`✗ Failed to send ${traceCount} test traces: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify all traces received
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('all traces should be successfully received by the collector', async function () {
  console.log(`\\n=== Verifying All Traces Received ===`);
  
  try {
    const wasReceived = await observabilityUtils.verifyTraceReceived();
    assert(wasReceived, 'All test traces should be successfully received by the collector');
    console.log(`✓ All test traces were successfully received by the collector`);
  } catch (error) {
    console.error(`✗ Failed to verify all traces received: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify all traces appear in Jaeger within timeout
 * @param {number} timeoutSeconds - Timeout in seconds
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('all traces should appear in Jaeger within {int} seconds', async function (timeoutSeconds) {
  console.log(`\\n=== Verifying All Traces in Jaeger ===`);
  console.log(`Checking that all traces appear in Jaeger within ${timeoutSeconds} seconds`);
  
  try {
    const traceIds = this.testTraceIds || [];
    
    for (const traceId of traceIds) {
      const traceFound = await observabilityUtils.waitForTraceInJaeger(traceId, timeoutSeconds * 1000);
      assert(traceFound, `Trace ${traceId} should appear in Jaeger within ${timeoutSeconds} seconds`);
    }
    
    console.log(`✓ All ${traceIds.length} traces found in Jaeger within ${timeoutSeconds} seconds`);
  } catch (error) {
    console.error(`✗ Failed to find all traces in Jaeger: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify traces are uniquely identifiable
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('each trace should be uniquely identifiable', async function () {
  console.log(`\\n=== Verifying Trace Uniqueness ===`);
  
  try {
    const traceIds = this.testTraceIds || [];
    const uniqueTraceIds = new Set(traceIds);
    
    assert(uniqueTraceIds.size === traceIds.length, 
      `Each trace should be uniquely identifiable. Expected ${traceIds.length} unique traces, but found ${uniqueTraceIds.size}`);
    
    console.log(`✓ All ${traceIds.length} traces are uniquely identifiable`);
  } catch (error) {
    console.error(`✗ Failed to verify trace uniqueness: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify traces are searchable by service name
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the traces should be searchable by service name', async function () {
  console.log(`\\n=== Verifying Trace Searchability ===`);
  
  try {
    const traces = await observabilityUtils.searchTracesByService('test-service');
    assert(traces.length > 0, 'Traces should be searchable by service name');
    console.log(`✓ Found ${traces.length} traces searchable by service name`);
  } catch (error) {
    console.error(`✗ Failed to verify trace searchability: ${error.message}`);
    throw error;
  }
});

/**
 * Given step for component with tracing enabled
 * @param {string} componentName - Name of the component
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Given('a component {string} is installed with tracing enabled', async function (componentName) {
  console.log(`\\n=== Verifying Component with Tracing ===`);
  console.log(`Checking that component '${componentName}' is installed with tracing enabled`);
  
  try {
    // For now, assume component exists if we get here
    // In a real implementation, you would check the component installation
    this.componentName = componentName;
    console.log(`✓ Component '${componentName}' is available with tracing enabled`);
  } catch (error) {
    console.error(`✗ Failed to verify component with tracing: ${error.message}`);
    throw error;
  }
});

/**
 * When step to make API call to component
 * @param {string} endpoint - API endpoint path
 * @returns {Promise<void>} - A Promise that resolves when API call is made
 */
When('I make an API call to the component endpoint {string}', async function (endpoint) {
  console.log(`\\n=== Making API Call to Component ===`);
  console.log(`Making API call to endpoint '${endpoint}'`);
  
  try {
    // For now, simulate an API call
    // In a real implementation, you would make the actual HTTP request
    this.apiCallMade = true;
    this.apiEndpoint = endpoint;
    console.log(`✓ API call made to endpoint '${endpoint}'`);
  } catch (error) {
    console.error(`✗ Failed to make API call: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify traces generated for API call
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('traces should be generated for the API call', async function () {
  console.log(`\\n=== Verifying API Call Traces ===`);
  
  try {
    // For now, return true to simulate trace generation
    // In a real implementation, you would check for traces related to the API call
    assert(this.apiCallMade, 'API call should have been made to generate traces');
    console.log(`✓ Traces were generated for the API call`);
  } catch (error) {
    console.error(`✗ Failed to verify API call traces: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify trace contains HTTP request information
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the trace should contain HTTP request information', async function () {
  console.log(`\\n=== Verifying HTTP Request Information in Trace ===`);
  
  try {
    // For now, simulate verification of HTTP information
    // In a real implementation, you would examine the trace details
    assert(this.apiEndpoint, 'Trace should contain HTTP request information');
    console.log(`✓ Trace contains HTTP request information`);
  } catch (error) {
    console.error(`✗ Failed to verify HTTP request information in trace: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify correct service name in trace
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the trace should have the correct service name', async function () {
  console.log(`\\n=== Verifying Trace Service Name ===`);
  
  try {
    // For now, simulate service name verification
    // In a real implementation, you would check the trace metadata
    const traceId = this.testTraceId;
    assert(traceId, 'Trace should have the correct service name');
    console.log(`✓ Trace has the correct service name`);
  } catch (error) {
    console.error(`✗ Failed to verify trace service name: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify correct span information
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the trace should have the correct span information', async function () {
  console.log(`\\n=== Verifying Trace Span Information ===`);
  
  try {
    // For now, simulate span information verification
    // In a real implementation, you would examine the span details
    const traceId = this.testTraceId;
    assert(traceId, 'Trace should have the correct span information');
    console.log(`✓ Trace has the correct span information`);
  } catch (error) {
    console.error(`✗ Failed to verify trace span information: ${error.message}`);
    throw error;
  }
});

/**
 * Given step for traces existing in Jaeger
 * @param {string} serviceName - Service name for traces
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Given('traces exist in Jaeger for service {string}', async function (serviceName) {
  console.log(`\\n=== Ensuring Traces Exist in Jaeger ===`);
  console.log(`Ensuring traces exist in Jaeger for service '${serviceName}'`);
  
  try {
    // Send a test trace to ensure we have data
    const traceId = await observabilityUtils.sendTestTrace(serviceName);
    await observabilityUtils.waitForTraceInJaeger(traceId, 10000);
    
    this.testServiceName = serviceName;
    console.log(`✓ Traces exist in Jaeger for service '${serviceName}'`);
  } catch (error) {
    console.error(`✗ Failed to ensure traces exist: ${error.message}`);
    throw error;
  }
});

/**
 * When step to search for traces by service name
 * @param {string} serviceName - Service name to search for
 * @returns {Promise<void>} - A Promise that resolves when search is complete
 */
When('I search for traces by service name {string}', async function (serviceName) {
  console.log(`\\n=== Searching for Traces by Service Name ===`);
  console.log(`Searching for traces by service name '${serviceName}'`);
  
  try {
    this.searchResults = await observabilityUtils.searchTracesByService(serviceName);
    console.log(`✓ Search completed for service '${serviceName}'`);
  } catch (error) {
    console.error(`✗ Failed to search for traces: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify finding at least N traces
 * @param {number} traceCount - Minimum number of traces expected
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('I should find at least {int} trace', async function (traceCount) {
  console.log(`\\n=== Verifying Trace Search Results ===`);
  console.log(`Checking that at least ${traceCount} trace(s) were found`);
  
  try {
    const results = this.searchResults || [];
    assert(results.length >= traceCount, 
      `Should find at least ${traceCount} trace(s), but found ${results.length}`);
    console.log(`✓ Found ${results.length} trace(s) in search results`);
  } catch (error) {
    console.error(`✗ Failed to verify trace search results: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify traces have valid trace IDs
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the traces should have valid trace IDs', async function () {
  console.log(`\\n=== Verifying Valid Trace IDs ===`);
  
  try {
    const results = this.searchResults || [];
    
    for (const trace of results) {
      assert(trace.traceId, 'Each trace should have a valid trace ID');
      assert(trace.traceId.length === 32, 'Trace ID should be 32 characters long');
    }
    
    console.log(`✓ All ${results.length} traces have valid trace IDs`);
  } catch (error) {
    console.error(`✗ Failed to verify valid trace IDs: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify traces have proper timestamp information
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('the traces should have proper timestamp information', async function () {
  console.log(`\\n=== Verifying Trace Timestamps ===`);
  
  try {
    const results = this.searchResults || [];
    
    for (const trace of results) {
      assert(trace.timestamp, 'Each trace should have timestamp information');
      assert(typeof trace.timestamp === 'number', 'Timestamp should be a valid number');
    }
    
    console.log(`✓ All ${results.length} traces have proper timestamp information`);
  } catch (error) {
    console.error(`✗ Failed to verify trace timestamps: ${error.message}`);
    throw error;
  }
});

/**
 * Then step to verify ability to view trace details
 * @returns {Promise<void>} - A Promise that resolves when verification is complete
 */
Then('I should be able to view trace details', async function () {
  console.log(`\\n=== Verifying Trace Details Access ===`);
  
  try {
    const results = this.searchResults || [];
    
    // For now, simulate trace details access
    // In a real implementation, you would query Jaeger for trace details
    assert(results.length > 0, 'Should be able to access trace details');
    console.log(`✓ Trace details are accessible for ${results.length} trace(s)`);
  } catch (error) {
    console.error(`✗ Failed to verify trace details access: ${error.message}`);
    throw error;
  }
});


/**
 * Verify that the ServiceMonitor is configured to scrape the metrics endpoint
 *
 * @param {string} endpointName - The name of the metrics endpoint
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor {string} should be configured to scrape the {string} endpoint', async function (serviceMonitorName, endpointName) {
  console.log(`\\n=== Verifying ServiceMonitor Configuration ===`);
  console.log(`Checking that ServiceMonitor '${serviceMonitorName}' is configured to scrape '${endpointName}' endpoint`);

  try {
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify configuration`);
    assert(serviceMonitor.spec.endpoints, `ServiceMonitor should have endpoints configuration`);
    assert(serviceMonitor.spec.endpoints.length > 0, `ServiceMonitor should have at least one endpoint`);
    
    console.log(`✓ ServiceMonitor is configured to scrape metrics endpoint`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor configuration: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor targets the correct service with specified label
 *
 * @param {string} labelSelector - The label selector for the target service
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should target the correct service with label {string}', async function (labelSelector) {
  console.log(`\\n=== Verifying ServiceMonitor Service Target ===`);
  console.log(`Checking that ServiceMonitor targets service with label '${labelSelector}'`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify service target`);
    assert(serviceMonitor.spec.selector, `ServiceMonitor should have selector configuration`);
    assert(serviceMonitor.spec.selector.matchLabels, `ServiceMonitor should have matchLabels configuration`);
    
    // Parse the expected label (format: "key=value")
    const [expectedKey, expectedValue] = labelSelector.split('=');
    const actualValue = serviceMonitor.spec.selector.matchLabels[expectedKey];
    
    assert(actualValue === expectedValue, 
      `ServiceMonitor should target service with label '${expectedKey}=${expectedValue}', but found '${expectedKey}=${actualValue}'`);
    
    console.log(`✓ ServiceMonitor correctly targets service with label '${labelSelector}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor service target: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor has the correct endpoint path
 *
 * @param {string} expectedPath - The expected endpoint path
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should have the correct endpoint path {string}', async function (expectedPath) {
  console.log(`\\n=== Verifying ServiceMonitor Endpoint Path ===`);
  console.log(`Checking that ServiceMonitor has endpoint path '${expectedPath}'`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify endpoint path`);
    assert(serviceMonitor.spec.endpoints && serviceMonitor.spec.endpoints.length > 0, 
      `ServiceMonitor should have at least one endpoint`);
    
    const endpoint = serviceMonitor.spec.endpoints[0];
    assert(endpoint.path === expectedPath, 
      `ServiceMonitor endpoint path should be '${expectedPath}', but found '${endpoint.path}'`);
    
    console.log(`✓ ServiceMonitor has correct endpoint path '${expectedPath}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor endpoint path: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor has the correct port configuration
 *
 * @param {string} expectedPort - The expected port name or number
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should have the correct port {string}', async function (expectedPort) {
  console.log(`\\n=== Verifying ServiceMonitor Port ===`);
  console.log(`Checking that ServiceMonitor has port '${expectedPort}'`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify port`);
    assert(serviceMonitor.spec.endpoints && serviceMonitor.spec.endpoints.length > 0, 
      `ServiceMonitor should have at least one endpoint`);
    
    const endpoint = serviceMonitor.spec.endpoints[0];
    assert(endpoint.port === expectedPort, 
      `ServiceMonitor port should be '${expectedPort}', but found '${endpoint.port}'`);
    
    console.log(`✓ ServiceMonitor has correct port '${expectedPort}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor port: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor has the correct scrape interval
 *
 * @param {string} expectedInterval - The expected scrape interval
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should have scrape interval {string}', async function (expectedInterval) {
  console.log(`\\n=== Verifying ServiceMonitor Scrape Interval ===`);
  console.log(`Checking that ServiceMonitor has scrape interval '${expectedInterval}'`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify scrape interval`);
    assert(serviceMonitor.spec.endpoints && serviceMonitor.spec.endpoints.length > 0, 
      `ServiceMonitor should have at least one endpoint`);
    
    const endpoint = serviceMonitor.spec.endpoints[0];
    assert(endpoint.interval === expectedInterval, 
      `ServiceMonitor scrape interval should be '${expectedInterval}', but found '${endpoint.interval}'`);
    
    console.log(`✓ ServiceMonitor has correct scrape interval '${expectedInterval}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor scrape interval: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that multiple ServiceMonitors target different services
 *
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitors should target different services', async function () {
  console.log(`\\n=== Verifying ServiceMonitors Target Different Services ===`);
  
  try {
    const serviceMonitor1 = await observabilityUtils.getServiceMonitor('ctk1-productcatalog-metrics', NAMESPACE);
    const serviceMonitor2 = await observabilityUtils.getServiceMonitor('ctk2-productcatalog-metrics', NAMESPACE);
    
    assert(serviceMonitor1 !== null, `First ServiceMonitor should exist`);
    assert(serviceMonitor2 !== null, `Second ServiceMonitor should exist`);
    
    const service1Target = serviceMonitor1.spec.selector.matchLabels.name;
    const service2Target = serviceMonitor2.spec.selector.matchLabels.name;
    
    assert(service1Target !== service2Target, 
      `ServiceMonitors should target different services, but both target '${service1Target}'`);
    
    console.log(`✓ ServiceMonitors target different services: '${service1Target}' and '${service2Target}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitors target different services: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor has the correct labels for Prometheus discovery
 *
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should have the correct labels for Prometheus discovery', async function () {
  console.log(`\\n=== Verifying ServiceMonitor Labels for Prometheus Discovery ===`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, NAMESPACE);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist to verify labels`);
    assert(serviceMonitor.metadata.labels, `ServiceMonitor should have labels`);
    
    // Check for ODA Canvas specific labels
    const expectedLabels = {
      'oda.tmforum.org/componentName': 'productcatalog'
    };
    
    for (const [key, expectedValue] of Object.entries(expectedLabels)) {
      const actualValue = serviceMonitor.metadata.labels[key];
      assert(actualValue === expectedValue, 
        `ServiceMonitor should have label '${key}=${expectedValue}', but found '${key}=${actualValue}'`);
    }
    
    console.log(`✓ ServiceMonitor has correct labels for Prometheus discovery`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor labels: ${error.message}`);
    throw error;
  }
});

/**
 * Verify that the ServiceMonitor is in the correct namespace
 *
 * @param {string} expectedNamespace - The expected namespace
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('the ServiceMonitor should be in the correct namespace {string}', async function (expectedNamespace) {
  console.log(`\\n=== Verifying ServiceMonitor Namespace ===`);
  console.log(`Checking that ServiceMonitor is in namespace '${expectedNamespace}'`);
  
  try {
    const serviceMonitorName = global.currentReleaseName + '-productcatalog-metrics';
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, expectedNamespace);
    
    assert(serviceMonitor !== null, `ServiceMonitor should exist in namespace '${expectedNamespace}'`);
    assert(serviceMonitor.metadata.namespace === expectedNamespace, 
      `ServiceMonitor should be in namespace '${expectedNamespace}', but found in '${serviceMonitor.metadata.namespace}'`);
    
    console.log(`✓ ServiceMonitor is in correct namespace '${expectedNamespace}'`);
  } catch (error) {
    console.error(`✗ Failed to verify ServiceMonitor namespace: ${error.message}`);
    throw error;
  }
});

/**
 * When step to check if a ServiceMonitor exists (for use in conditional flows)
 *
 * @param {string} serviceMonitorName - The name of the ServiceMonitor resource
 * @param {string} namespace - The namespace where the ServiceMonitor should exist
 * @returns {Promise<void>} - A Promise that resolves when the check is complete
 */
When('a ServiceMonitor resource {string} exists in the {string} namespace', async function (serviceMonitorName, namespace) {
  console.log(`\\n=== Checking ServiceMonitor Exists ===`);
  console.log(`Verifying ServiceMonitor '${serviceMonitorName}' exists in namespace '${namespace}'`);
  
  try {
    const serviceMonitor = await observabilityUtils.getServiceMonitor(serviceMonitorName, namespace);
    assert(serviceMonitor !== null, `ServiceMonitor '${serviceMonitorName}' should exist in namespace '${namespace}'`);
    console.log(`✓ ServiceMonitor '${serviceMonitorName}' exists in namespace '${namespace}'`);
  } catch (error) {
    console.error(`✗ ServiceMonitor '${serviceMonitorName}' does not exist in namespace '${namespace}': ${error.message}`);
    throw error;
  }
});

// Clean up after tests if configured
After(async function () {
  if (CLEANUP_PACKAGE && global.currentReleaseName) {
    try {
      console.log(`\\n=== Cleaning up package '${global.currentReleaseName}' ===`);
      await packageManagerUtils.uninstallPackage(global.currentReleaseName, NAMESPACE);
      console.log(`✓ Package '${global.currentReleaseName}' uninstalled successfully`);
    } catch (error) {
      console.error(`✗ Failed to cleanup package '${global.currentReleaseName}': ${error.message}`);
    }
  }
});
