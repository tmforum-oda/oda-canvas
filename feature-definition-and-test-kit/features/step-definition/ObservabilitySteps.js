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
