// This TDD interacts with the technical implementation of Service Monitor for open-metrics collection.

const { execSync } = require('child_process');
const k8s = require('@kubernetes/client-node');
const http = require('http');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const k8sApi = kc.makeApiClient(k8s.ApiextensionsV1Api);
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);

const DEBUG_LOGS = false; // set to true for verbose debugging

/**
 * Check if Service Monitor for open-metrics collection is deployed and Prometheus Operator CRDs are present.
 * @returns {Promise<boolean>} - True if Service Monitor and required Prometheus Operator CRDs are deployed, false otherwise.
 */
const isServiceMonitorDeployed = async () => {
  try {
    console.log('=== Starting Service Monitor Deployment Verification ===');

    // Step 1: Check for ServiceMonitor CRD
    console.log('Checking for ServiceMonitor CRD...');
    const crdList = await k8sApi.listCustomResourceDefinition();
    const serviceMonitorCRD = crdList.body.items.find(crd => 
      crd.metadata.name === 'servicemonitors.monitoring.coreos.com'
    );

    if (!serviceMonitorCRD) {
      console.error('❌ ServiceMonitor CRD is not present. Ensure the Prometheus Operator is installed.');
      return false;
    }

    console.log('✅ ServiceMonitor CRD is present.');

    // Step 2: Check for Prometheus Operator deployment
    console.log('Checking for Prometheus Operator deployment...');
    const allDeployments = await k8sAppsApi.listDeploymentForAllNamespaces();
    const prometheusOperatorDeployment = allDeployments.body.items.find(deployment =>
      deployment.metadata.name.includes('prometheus-operator') ||
      deployment.metadata.name.includes('kube-prometheus-operator')
    );

    if (!prometheusOperatorDeployment) {
      console.error('❌ Prometheus Operator deployment not found.');
      return false;
    }

    const namespace = prometheusOperatorDeployment.metadata.namespace;
    const readyReplicas = prometheusOperatorDeployment.status.readyReplicas || 0;
    const replicas = prometheusOperatorDeployment.status.replicas || 0;

    console.log(
      `Prometheus Operator deployment found: ${prometheusOperatorDeployment.metadata.name} in namespace: ${namespace}. Ready replicas: ${readyReplicas}/${replicas}`
    );

    if (readyReplicas !== replicas) {
      console.error(
        `❌ Prometheus Operator deployment is not fully ready. (${readyReplicas}/${replicas} replicas ready)`
      );
      return false;
    }

    console.log('✅ Prometheus Operator deployment is running successfully.');

    // Step 3: Check for Prometheus instance
    console.log('Checking for Prometheus instance...');
    const allServices = await k8sCoreApi.listServiceForAllNamespaces();
    const prometheusService = allServices.body.items.find(svc =>
      svc.metadata.name.includes('prometheus') &&
      (svc.metadata.labels?.['app.kubernetes.io/name'] === 'prometheus' ||
       svc.metadata.labels?.app === 'prometheus')
    );

    if (!prometheusService) {
      console.error('❌ Prometheus service not found.');
      return false;
    }

    console.log(`✅ Prometheus service found: ${prometheusService.metadata.name} in namespace: ${prometheusService.metadata.namespace}`);

    // Step 4: Check for existing ServiceMonitor resources (optional verification)
    console.log('Checking for existing ServiceMonitor resources...');
    try {
      const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);
      const serviceMonitors = await customObjectsApi.listClusterCustomObject(
        'monitoring.coreos.com',
        'v1',
        'servicemonitors'
      );

      const serviceMonitorCount = serviceMonitors.body.items ? serviceMonitors.body.items.length : 0;
      console.log(`✅ Found ${serviceMonitorCount} ServiceMonitor resource(s) in the cluster.`);

    } catch (error) {
      console.warn(`⚠️ Could not list ServiceMonitor resources: ${error.message}`);
      // This is not a failure condition, just informational
    }

    console.log('=== Service Monitor Deployment Verification Complete ===');
    return true;
    
  } catch (error) {
    console.error(`❌ Error checking Service Monitor deployment: ${error.message}`);
    console.error('Error details:');
    console.error(`- Error type: ${error.constructor.name}`);
    
    if (error.response) {
      console.error('HTTP Response error details:');
      console.error(`- Status: ${error.response.status}`);
      console.error(`- Headers: ${JSON.stringify(error.response.headers, null, 2)}`);
      console.error(`- Body: ${JSON.stringify(error.response.body, null, 2)}`);
    }
    
    console.error('Possible causes:');
    console.error('- Prometheus Operator not installed or configured properly');
    console.error('- ServiceMonitor CRD not installed');
    console.error('- Kubernetes cluster access issues');
    console.error('- RBAC permissions insufficient for cluster resource access');
    console.error('- Observability stack (Prometheus/Grafana) not deployed');
    
    return false;
  }
};

module.exports = {
  isServiceMonitorDeployed
};
