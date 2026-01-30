// This TDD uses a utility library to interact with the technical implementation of a specific canvas.
// Replace the library with your own implementation library if you use a different implementation technology.
const packageManagerUtils = require('package-manager-utils-helm');
const observabilityUtils = require('observability-utils-kubernetes');
const { isServiceMonitorDeployed } = require('./OpenMetricsCheck');

const { Given, When, Then, After, setDefaultTimeout, Before } = require('@cucumber/cucumber');
const chai = require('chai');
const assert = require('assert');
chai.use(require('chai-http'));

const NAMESPACE = 'components';
const DEFAULT_RELEASE_NAME = 'ctk';
const SERVICEMONITOR_TIMEOUT = 30 * 1000; // 30 seconds
const CLEANUP_PACKAGE = false; // set to true to uninstall the package after each Scenario

setDefaultTimeout(20 * 1000);

// Allow skipping tests by adding @SkipTest to BDD scenario
Before({ tags: '@SkipTest' }, async function () {
  console.log('Skipping scenario.');
  return 'skipped';
});


// Skip if there is no Service Monitor for open-metrics collection
Before({ tags: '@ServiceMonitor' }, async function () {
  console.log('\n=== Service Monitor Check ===');
  console.log('Checking if Service Monitor for open-metrics collection is deployed...');

  try {
    const serviceMonitorDeployed = await isServiceMonitorDeployed();

    if (!serviceMonitorDeployed) {
      console.log('Service Monitor for open-metrics collection is not deployed. Skipping scenario.');
      return 'skipped';
    }

    console.log('✅ Service Monitor for open-metrics collection is deployed. Proceeding with scenario.');
    console.log('=== Service Monitor Check Complete ===');

  } catch (error) {
    console.warn(`⚠️ Warning checking Service Monitor deployment: ${error.message}`);
    console.warn('Possible causes:');
    console.warn('- Service Monitor not installed or configured properly');
    console.warn('- Kubernetes cluster access issues');
    console.warn('- Required Gateway API CRDs not installed');
    throw error;
  }
});

// Skip if there is no OpenTelemetry Collector deployed
Before({ tags: '@OpenTelemetryCollector' }, async function () {
  console.log('\n=== OpenTelemetry Collector Check ===');
  console.log('Checking if OpenTelemetry Collector is deployed and reachable...');

  try {
    const collectorReachable = await observabilityUtils.isCollectorReachable(4318);

    if (!collectorReachable) {
      console.log('OpenTelemetry Collector is not deployed or reachable. Skipping scenario.');
      return 'skipped';
    }

    console.log('✅ OpenTelemetry Collector is deployed and reachable. Proceeding with scenario.');
    console.log('=== OpenTelemetry Collector Check Complete ===');

  } catch (error) {
    console.warn(`⚠️ Warning checking OpenTelemetry Collector deployment: ${error.message}`);
    console.warn('Possible causes:');
    console.warn('- OpenTelemetry Collector not installed or configured properly');
    console.warn('- Kubernetes cluster access issues');
    console.warn('- Port-forwarding not set up (kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 4318:4318)');
    return 'skipped';
  }
});



/**
 * Verify that a ServiceMonitor resource exists for the component
 *
 * @param {string} serviceMonitorName - The name of the ServiceMonitor resource
 * @param {string} namespace - The namespace where the ServiceMonitor should exist
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('a ServiceMonitor resource {string} should exist in the {string} namespace', async function (serviceMonitorName, namespace) {
  console.log(`\n=== Verifying ServiceMonitor Exists ===`);
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

/**
 * Store baseline metrics before performing API operations
 */
let baselineMetrics = null;

/**
 * Capture baseline OpenTelemetry metrics before API operations
 *
 * @returns {Promise<void>} - A Promise that resolves when baseline is captured
 */
When('I capture the baseline OpenTelemetry metrics', async function () {
  console.log(`\n=== Capturing Baseline OpenTelemetry Metrics ===`);
  
  try {
    // First verify the collector is reachable
    const isReachable = await observabilityUtils.isCollectorReachable(4318);
    assert(isReachable, 'OpenTelemetry collector should be running and reachable');
    
    // Capture baseline metrics
    baselineMetrics = await observabilityUtils.getCollectorTelemetryMetrics();
    
    console.log('✓ Baseline metrics captured:');
    console.log(`  Baseline spans: ${baselineMetrics.receivedSpans}`);
    console.log(`  Baseline metrics: ${baselineMetrics.receivedMetricPoints}`);
    console.log(`  Baseline logs: ${baselineMetrics.receivedLogRecords}`);
    
  } catch (error) {
    console.error(`✗ Failed to capture baseline metrics: ${error.message}`);
    
    // Check if it's a connection issue to the metrics endpoint
    if (error.message.includes('Connection failed') || 
        error.message.includes('ECONNREFUSED') ||
        error.message.includes('Request timeout') ||
        error.message.includes('localhost:8888')) {
      
      console.error('');
      console.error('❌ SETUP ERROR: Cannot access OpenTelemetry Collector metrics endpoint');
      console.error('');
      console.error('🔧 REQUIRED ACTION: Please start port-forwarding for the OpenTelemetry Collector:');
      console.error('');
      console.error('   1. Use deployment-based port-forwarding:');
      console.error('      kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888');
      console.error('');
      console.error('   2. Verify the endpoint is accessible:');
      console.error('      curl http://localhost:8888/metrics');
      console.error('');
      
      throw new Error('OpenTelemetry Collector metrics endpoint not accessible. Please start port-forwarding as shown above.');
    }
    
    throw error;
  }
});


/**
 * Verify that OpenTelemetry events are being received by the OpenTelemetry Collector
 * This checks for new events since the baseline was captured
 *
 * @returns {Promise<void>} - A Promise that resolves when the verification is complete
 */
Then('I should see new OpenTelemetry events in the OpenTelemetry Collector', async function () {
  console.log(`\n=== Verifying OpenTelemetry Events in Collector ===`);
  
  if (!baselineMetrics) {
    console.log('No baseline metrics captured, capturing now...');
    await this.capture_baseline_opentelemetry_metrics();
    // Wait a moment for any immediate telemetry to settle
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  const maxRetries = 10;
  const retryDelay = 3000; // 3 seconds
  let newEventsDetected = false;
  
  try {
    // First verify the collector is reachable
    const isReachable = await observabilityUtils.isCollectorReachable(4318);
    assert(isReachable, 'OpenTelemetry collector should be running and reachable');
    console.log('✓ OpenTelemetry collector is reachable');
    
    // Check for new events with retries
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      console.log(`Checking for new OpenTelemetry events (attempt ${attempt}/${maxRetries})...`);
      
      try {
        // Get current metrics from the collector
        const currentMetrics = await observabilityUtils.getCollectorTelemetryMetrics();
        
        // Calculate increases since baseline
        const spansIncrease = currentMetrics.receivedSpans - baselineMetrics.receivedSpans;
        const metricsIncrease = currentMetrics.receivedMetricPoints - baselineMetrics.receivedMetricPoints;
        const logsIncrease = currentMetrics.receivedLogRecords - baselineMetrics.receivedLogRecords;
        
        console.log(`  New spans since baseline: ${spansIncrease}`);
        console.log(`  New metrics since baseline: ${metricsIncrease}`);
        console.log(`  New logs since baseline: ${logsIncrease}`);
        console.log(`  Current totals - Spans: ${currentMetrics.receivedSpans}, Metrics: ${currentMetrics.receivedMetricPoints}, Logs: ${currentMetrics.receivedLogRecords}`);
        
        // Check if any new telemetry data has been received since baseline
        if (spansIncrease > 0 || metricsIncrease > 0 || logsIncrease > 0) {
          newEventsDetected = true;
          console.log('✓ New OpenTelemetry events detected since API operations');
          
          // Also check for any refused events
          const refusedSpans = currentMetrics.refusedSpans || 0;
          const refusedMetrics = currentMetrics.refusedMetricPoints || 0;
          const refusedLogs = currentMetrics.refusedLogRecords || 0;
          
          if (refusedSpans > 0 || refusedMetrics > 0 || refusedLogs > 0) {
            console.log(`⚠️  Warning: Some events were refused (Spans: ${refusedSpans}, Metrics: ${refusedMetrics}, Logs: ${refusedLogs})`);
          }
          
          // Log export success/failure rates
          if (currentMetrics.exportedSpans > 0 || currentMetrics.failedSpans > 0) {
            console.log(`  Export status - Spans: ${currentMetrics.exportedSpans} exported, ${currentMetrics.failedSpans} failed`);
          }
          
          break;
        }
      } catch (metricsError) {
        console.log(`  Unable to retrieve metrics: ${metricsError.message}`);
        
        // Check if it's a connection issue to the metrics endpoint
        if (metricsError.message.includes('Connection failed') || 
            metricsError.message.includes('ECONNREFUSED') ||
            metricsError.message.includes('Request timeout') ||
            metricsError.message.includes('localhost:8888')) {
          
          console.error('');
          console.error('❌ CONNECTION ERROR: Lost connection to OpenTelemetry Collector metrics endpoint');
          console.error('');
          console.error('🔧 REQUIRED ACTION: Please ensure port-forwarding is still running:');
          console.error('');
          console.error('   Check if port-forward is running:');
          console.error('   ps aux | grep "port-forward.*8888"');
          console.error('');
          console.error('   If not running, restart port-forwarding:');
          console.error('   kubectl port-forward -n monitoring deployment/observability-opentelemetry-collector 8888:8888');
          console.error('');
          
          throw new Error('Lost connection to OpenTelemetry Collector metrics endpoint. Please restart port-forwarding.');
        }
      }
      
      if (attempt < maxRetries) {
        console.log(`  No new events detected yet, waiting ${retryDelay/1000} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
    
    assert(newEventsDetected, 'No new OpenTelemetry events were received by the collector since the API operations. This suggests the component is not properly instrumented or telemetry is not being exported.');
    
  } catch (error) {
    console.error(`✗ Failed to verify OpenTelemetry events: ${error.message}`);
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
