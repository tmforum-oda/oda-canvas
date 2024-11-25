// This TDD interact with the technical implementation of Apisix/Kong API Gateway with the technical implementation of a specific canvas.

const { execSync } = require('child_process');
const k8s = require('@kubernetes/client-node');
const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const k8sApi = kc.makeApiClient(k8s.ApiextensionsV1Api);

/**
 * Check if Kong Gateway is deployed and required CRDs (e.g., ReferenceGrant) are present.
 * @returns {Promise<boolean>} - True if Kong Gateway and required Gateway API CRDs are deployed, false otherwise.
 */
const isKongGatewayDeployed = async () => {
  try {
    console.log('Checking Kong Gateway deployment...');
    
    // Step 1: Check Helm deployment status for Kong
    const helmListOutput = execSync('helm list --all-namespaces --output json').toString();
    const helmReleases = JSON.parse(helmListOutput);
    const kongRelease = helmReleases.find(
      release => release.name.includes('kong') && release.status === 'deployed'
    );
    if (!kongRelease) {
      console.error('Kong Gateway Helm deployment not found.');
      return false;
    }
    console.log('Kong Gateway Helm deployment found:', kongRelease);

    // Step 2: Check for ReferenceGrant CRD , kong requires this steps as there is dependency on Gateway API CRDs
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
    return false; // Assume not deployed if there's an error
  }
};

/**
 * Check if Apisix Gateway is deployed.
 * @returns {Promise<boolean>} - True if Apisix Gateway is deployed, false otherwise.
 */
const isApisixGatewayDeployed = async () => {
  try {
    console.log('Checking Apisix Gateway deployment...');
    
    // Step 1: Check Helm deployment status for Apisix
    const helmListOutput = execSync('helm list --all-namespaces --output json').toString();
    const helmReleases = JSON.parse(helmListOutput);
    const apisixRelease = helmReleases.find(
      release => release.name.includes('apisix') && release.status === 'deployed'
    );
    if (!apisixRelease) {
      console.error('Apisix Gateway Helm deployment not found.');
      return false;
    }
    console.log('Apisix Gateway Helm deployment found:', apisixRelease);
    return true;
  } catch (error) {
    console.error('Error checking Apisix Gateway deployment:', error.message);
    return false; // Assume not deployed if there's an error
  }
};

module.exports = {
  isKongGatewayDeployed,
  isApisixGatewayDeployed
};
