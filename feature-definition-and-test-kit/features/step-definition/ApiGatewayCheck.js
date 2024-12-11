// This TDD interact with the technical implementation of Apisix/Kong API Gateway with the technical implementation of a specific canvas.

const { execSync } = require('child_process');
const k8s = require('@kubernetes/client-node');
const http = require('http');
const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const k8sApi = kc.makeApiClient(k8s.ApiextensionsV1Api);
const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);
const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);

/**
 * Check if Kong Gateway is deployed and required CRDs (e.g., ReferenceGrant) are present.
 * @returns {Promise<boolean>} - True if Kong Gateway and required Gateway API CRDs are deployed, false otherwise.
 */
const isKongGatewayDeployed = async () => {
  try {
    console.log('Checking Kong Gateway deployment...');

    // Step 1: Listing all services in all namespaces
    const services = await k8sCoreApi.listServiceForAllNamespaces();
    const kongGatewaySvc = services.body.items.find(
      svc => svc.metadata.name.includes('kong-proxy')
    );

    if (!kongGatewaySvc) {
      console.error('Kong Gateway service not found.');
      return false;
    }

    console.log('Kong Gateway service found:', kongGatewaySvc.metadata.name);

    // Step 2: Checking if the service has an external IP
    const externalIPs = kongGatewaySvc.status.loadBalancer?.ingress;
    if (!externalIPs || externalIPs.length === 0) {
      console.error('Kong Gateway service does not have an external IP assigned.');
      return false;
    }

    const externalIP = externalIPs[0].ip || externalIPs[0].hostname;
    console.log('External IP assigned to Kong Gateway:', externalIP);

    // Step 3: Checking if Kong Gateway deployment is running
    console.log('Checking Kong Gateway deployment status...');
    const namespace = kongGatewaySvc.metadata.namespace; 
    const deployments = await k8sAppsApi.listNamespacedDeployment(namespace);
    const kongDeployment = deployments.body.items.find(deployment =>
      deployment.metadata.name.includes('kong')
    );

    if (!kongDeployment) {
      console.error('Kong Gateway deployment not found in namespace:', namespace);
      return false;
    }

    const readyReplicas = kongDeployment.status.readyReplicas || 0;
    const replicas = kongDeployment.status.replicas || 0;

    console.log(
      `Kong Gateway deployment found: ${kongDeployment.metadata.name}. Ready replicas: ${readyReplicas}/${replicas}`
    );

    if (readyReplicas !== replicas) {
      console.error(
        `Kong Gateway deployment is not fully ready. (${readyReplicas}/${replicas} replicas ready)`
      );
      return false;
    }

    console.log('Kong Gateway deployment is running successfully.');



    // Step 4: Checking for ReferenceGrant CRD
    console.log('Checking for ReferenceGrant CRD...');
    const crdList = await k8sApi.listCustomResourceDefinition();
    const referenceGrantCRD = crdList.body.items.find(crd => crd.metadata.name === 'referencegrants.gateway.networking.k8s.io');

    if (!referenceGrantCRD) {
      console.error('ReferenceGrant CRD is not present. Ensure the required Gateway API CRDs are installed. Refer to Kong Installation instructions - https://github.com/tmforum-oda/oda-canvas/tree/main/installation');
      return false;
    }

    console.log('ReferenceGrant CRD is present.');
    return true;
  } catch (error) {
    console.error('Error checking Kong Gateway deployment:', error.message);
    return false;
  }
};
/**
 * Check if Apisix Gateway service is present and external IP is assigned.
 * Then perform a health check on the Apisix admin endpoint.
 * @returns {Promise<boolean>} - True if Apisix Gateway is ready, false otherwise.
 */
const isApisixGatewayDeployed = async () => {
  try {
    console.log('Checking Apisix Gateway deployment...');

    // Step 1: Listing all services in all namespaces
    const services = await k8sCoreApi.listServiceForAllNamespaces();
    const apisixGatewaySvc = services.body.items.find(
      svc => svc.metadata.name.includes('apisix-gateway')
    );

    if (!apisixGatewaySvc) {
      console.error('Apisix Gateway service not found.');
      return false;
    }

    console.log('Apisix Gateway service found:', apisixGatewaySvc.metadata.name);

    // Step 2: Checking if the service has an external IP
    const externalIPs = apisixGatewaySvc.status.loadBalancer?.ingress;
    if (!externalIPs || externalIPs.length === 0) {
      console.error('Apisix Gateway service does not have an external IP assigned.');
      return false;
    }

    const externalIP = externalIPs[0].ip || externalIPs[0].hostname;
    console.log('External IP assigned to Apisix Gateway:', externalIP);


    // Step 3: Checking if Apisix Gateway pods are running
    console.log('Checking Apisix Gateway deployment status...');
    const namespace = apisixGatewaySvc.metadata.namespace; // Using the namespace of the service
    const deployments = await k8sAppsApi.listNamespacedDeployment(namespace);
    const apisixDeployment = deployments.body.items.find(deployment =>
      deployment.metadata.name.includes('apisix')
    );

    if (!apisixDeployment) {
      console.error('Apisix Gateway deployment not found in namespace:', namespace);
      return false;
    }

    const readyReplicas = apisixDeployment.status.readyReplicas || 0;
    const replicas = apisixDeployment.status.replicas || 0;

    console.log(
      `Apisix Gateway deployment found: ${apisixDeployment.metadata.name}. Ready replicas: ${readyReplicas}/${replicas}`
    );

    if (readyReplicas !== replicas) {
      console.error(
        `Apisix Gateway deployment is not fully ready. (${readyReplicas}/${replicas} replicas ready)`
      );
      return false;
    }

    console.log('Apisix Gateway deployment is running successfully.');
    return true;
  } catch (error) {
    console.error('Error checking Apisix Gateway deployment:', error.message);
    return false;
  }
};

module.exports = {
  isKongGatewayDeployed,
  isApisixGatewayDeployed
};