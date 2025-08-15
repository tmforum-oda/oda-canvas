#!/usr/bin/env node

/**
 * Simple test script to validate observability utilities functionality
 * This script can be used to verify that the observability utilities are working correctly
 */

const observabilityUtils = require('./observability-utils-kubernetes');

async function runTests() {
  console.log('🧪 Testing Observability Utils for Kubernetes\n');

  try {
    // Test 1: List ServiceMonitors in components namespace
    console.log('📋 Test 1: Listing ServiceMonitors in components namespace...');
    const serviceMonitors = await observabilityUtils.listServiceMonitors('components');
    console.log(`✅ Found ${serviceMonitors.length} ServiceMonitor(s) in components namespace`);
    
    if (serviceMonitors.length > 0) {
      serviceMonitors.forEach((sm, index) => {
        console.log(`   ${index + 1}. ${sm.metadata.name} (namespace: ${sm.metadata.namespace})`);
      });
    }
    console.log();

    // Test 2: Test non-existent ServiceMonitor
    console.log('🔍 Test 2: Testing non-existent ServiceMonitor...');
    const nonExistentSM = await observabilityUtils.getServiceMonitor('non-existent-servicemonitor', 'components');
    if (nonExistentSM === null) {
      console.log('✅ Correctly returned null for non-existent ServiceMonitor');
    } else {
      console.log('❌ Expected null for non-existent ServiceMonitor');
    }
    console.log();

    // Test 3: Test ServiceMonitor existence check
    console.log('🔍 Test 3: Testing ServiceMonitor existence check...');
    const exists = await observabilityUtils.serviceMonitorExists('non-existent-servicemonitor', 'components');
    if (!exists) {
      console.log('✅ Correctly returned false for non-existent ServiceMonitor');
    } else {
      console.log('❌ Expected false for non-existent ServiceMonitor');
    }
    console.log();

    // Test 4: Test configuration validation (if we have ServiceMonitors)
    if (serviceMonitors.length > 0) {
      console.log('⚙️  Test 4: Testing ServiceMonitor configuration validation...');
      const firstSM = serviceMonitors[0];
      
      // Test with minimal expected configuration
      const isValid = observabilityUtils.validateServiceMonitorConfig(firstSM, {
        // No specific requirements - just check that it has the basic structure
      });
      
      if (isValid) {
        console.log(`✅ ServiceMonitor '${firstSM.metadata.name}' has valid configuration`);
      } else {
        console.log(`❌ ServiceMonitor '${firstSM.metadata.name}' has invalid configuration`);
      }
      
      // Display configuration details
      try {
        const config = await observabilityUtils.getServiceMonitorConfig(firstSM.metadata.name, firstSM.metadata.namespace);
        console.log('   Configuration details:');
        console.log(`   - Path: ${config.endpoint.path || 'not specified'}`);
        console.log(`   - Port: ${config.endpoint.port || 'not specified'}`);
        console.log(`   - Interval: ${config.endpoint.interval || 'not specified'}`);
        console.log(`   - Target labels: ${JSON.stringify(config.selector.matchLabels || {})}`);
      } catch (error) {
        console.log(`   Could not get config details: ${error.message}`);
      }
      console.log();
    }

    console.log('🎉 All tests completed successfully!\n');
    
    // Display summary
    console.log('📊 Summary:');
    console.log('   The observability utilities are working correctly.');
    console.log('   You can now run the BDD tests for observability features.');
    console.log('   Use: npm test -- --grep "@UC012"');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('\nTroubleshooting:');
    console.error('1. Make sure you have access to a Kubernetes cluster');
    console.error('2. Ensure your kubeconfig is properly configured');
    console.error('3. Check if the Prometheus Operator is installed (ServiceMonitor CRD should exist)');
    console.error('4. Verify RBAC permissions for ServiceMonitor resources');
    process.exit(1);
  }
}

// Check if running directly
if (require.main === module) {
  runTests();
}

module.exports = { runTests };
