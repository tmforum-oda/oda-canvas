// Utility helpers for detecting FlexGateway operator deployment state.
// Imported by FlexGatewayManagementSteps.js Before hooks.
//
// isFlexGatewayDeployed()
//   Returns true if the flexgateway-operator Deployment exists in the
//   'operators' namespace and has at least one ready replica.
//
// isFlexGatewayFlexModeActive()
//   Returns true when the operator is running AND Anypoint credentials are
//   non-empty.  Credentials are stored in a K8s Secret referenced by the
//   ANYPOINT_CLIENT_ID secretKeyRef env var on the operator container.
//   In ISTIO_ONLY_MODE the secret either does not exist or holds empty values.

const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const k8sCoreApi  = kc.makeApiClient(k8s.CoreV1Api);
const k8sAppsApi  = kc.makeApiClient(k8s.AppsV1Api);

const OPERATOR_NAMESPACE = 'operators';

const isFlexGatewayDeployed = async () => {
  try {
    console.log('=== FlexGateway Deployment Check ===');
    const deps = await k8sAppsApi.listNamespacedDeployment(OPERATOR_NAMESPACE);
    const fgDep = deps.body.items.find(d =>
      d.metadata.name.toLowerCase().includes('flexgateway-operator')
    );

    if (!fgDep) {
      console.log('FlexGateway operator Deployment not found in namespace:', OPERATOR_NAMESPACE);
      return false;
    }

    const ready = fgDep.status?.readyReplicas || 0;
    const total = fgDep.status?.replicas || 0;
    console.log(`FlexGateway operator: ${fgDep.metadata.name}  ready=${ready}/${total}`);

    if (ready < 1) {
      console.log('FlexGateway operator has no ready replicas — skipping.');
      return false;
    }

    console.log('✅ FlexGateway operator is deployed and ready.');
    console.log('=== FlexGateway Deployment Check Complete ===');
    return true;
  } catch (error) {
    console.error('❌ Error checking FlexGateway deployment:', error.message);
    return false;
  }
};

const isFlexGatewayFlexModeActive = async () => {
  try {
    console.log('=== FlexGateway Flex-mode Credential Check ===');

    const deps = await k8sAppsApi.listNamespacedDeployment(OPERATOR_NAMESPACE);
    const fgDep = deps.body.items.find(d =>
      d.metadata.name.toLowerCase().includes('flexgateway-operator')
    );
    if (!fgDep) {
      console.log('FlexGateway operator not found — cannot determine mode.');
      return false;
    }

    const ready = fgDep.status?.readyReplicas || 0;
    if (ready < 1) {
      console.log('FlexGateway operator not ready — skipping Flex-mode check.');
      return false;
    }

    // Locate the ANYPOINT_CLIENT_ID env var on the first container.
    const containers = fgDep.spec.template.spec.containers || [];
    if (containers.length === 0) return false;

    const envVars = containers[0].env || [];
    const clientIdEnv = envVars.find(e => e.name === 'ANYPOINT_CLIENT_ID');

    if (!clientIdEnv) {
      console.log('ANYPOINT_CLIENT_ID env var not configured — ISTIO_ONLY_MODE assumed.');
      return false;
    }

    // Case 1: direct value (uncommon in production, handled for completeness).
    if (clientIdEnv.value !== undefined) {
      const active = clientIdEnv.value.trim().length > 0;
      console.log(`ANYPOINT_CLIENT_ID (direct value): ${active ? 'non-empty → Flex mode' : 'empty → ISTIO_ONLY_MODE'}`);
      return active;
    }

    // Case 2: value from a Secret (standard deployment via Helm chart).
    if (clientIdEnv.valueFrom?.secretKeyRef) {
      const { name: secretName, key } = clientIdEnv.valueFrom.secretKeyRef;
      console.log(`Checking Secret '${OPERATOR_NAMESPACE}/${secretName}' key '${key}'`);

      try {
        const secret = await k8sCoreApi.readNamespacedSecret(secretName, OPERATOR_NAMESPACE);
        const valB64 = secret.body.data?.[key];
        if (!valB64) {
          console.log(`Secret key '${key}' is absent or empty — ISTIO_ONLY_MODE.`);
          return false;
        }
        const val = Buffer.from(valB64, 'base64').toString('utf-8').trim();
        const active = val.length > 0;
        console.log(`Secret '${key}': ${active ? 'non-empty → Flex mode ✅' : 'empty → ISTIO_ONLY_MODE'}`);
        console.log('=== FlexGateway Flex-mode Credential Check Complete ===');
        return active;
      } catch (secretErr) {
        console.log(`Could not read Secret '${secretName}': ${secretErr.message} — treating as ISTIO_ONLY_MODE.`);
        return false;
      }
    }

    console.log('ANYPOINT_CLIENT_ID has no value or secretKeyRef — ISTIO_ONLY_MODE assumed.');
    return false;
  } catch (error) {
    console.error('❌ Error checking FlexGateway Flex-mode credentials:', error.message);
    return false;
  }
};

module.exports = { isFlexGatewayDeployed, isFlexGatewayFlexModeActive };
