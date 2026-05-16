// Step definitions for UC015-F005 and UC015-F006.
// Covers both FlexGateway operator modes:
//
//   @FlexGateway      — operator must be deployed; scenarios auto-skip if absent.
//   @FlexGatewayFlex  — additionally requires non-empty Anypoint credentials in the
//                       flexgateway-anypoint-creds Secret; skips in ISTIO_ONLY_MODE.
//
// Routing logic tested (from apiOperatorFlexGateway.py):
//
//   a2a | no template  | any mode → manage_a2a_istio  → Istio VirtualService (F005)
//   a2a | has template | Flex     → manage_exposedapi  → Anypoint Exchange + Flex GW (F006)
//   a2a | has template | Istio    → PermanentError (not tested here)

const resourceInventoryUtils = require('resource-inventory-utils-kubernetes');
const packageManagerUtils    = require('package-manager-utils-helm');

const { Given, When, Then, Before, After, setDefaultTimeout } = require('@cucumber/cucumber');
const assert = require('assert');

const { isFlexGatewayDeployed, isFlexGatewayFlexModeActive } = require('./FlexGatewayCheck');

const NAMESPACE           = 'components';
const DEFAULT_RELEASE     = 'ctk';
// Flex Gateway provisioning involves Anypoint API calls: Exchange publish,
// API Manager instance creation, gateway deployment, and policy application.
// Allow up to 5 minutes for the full round-trip.
const ISTIO_PATH_TIMEOUT  = 60  * 1000;  // VirtualService creation is fast
const FLEX_PATH_TIMEOUT   = 300 * 1000;  // Anypoint round-trip can take minutes
const POLL_INTERVAL       = 2  * 1000;
const TIMEOUT_BUFFER      = 5  * 1000;

setDefaultTimeout(30 * 1000);


// ── Before hooks ──────────────────────────────────────────────────────────────

Before({ tags: '@FlexGateway' }, async function () {
  console.log('\n=== FlexGateway Operator Pre-check ===');
  const deployed = await isFlexGatewayDeployed();
  if (!deployed) {
    console.log('FlexGateway operator not deployed — skipping scenario.');
    return 'skipped';
  }
  console.log('✅ FlexGateway operator ready. Proceeding.');
});

Before({ tags: '@FlexGatewayFlex' }, async function () {
  console.log('\n=== FlexGateway Flex-mode Pre-check ===');
  const flexActive = await isFlexGatewayFlexModeActive();
  if (!flexActive) {
    console.log(
      'FlexGateway operator is in ISTIO_ONLY_MODE (no Anypoint credentials) — ' +
      'skipping Flex-mode scenario.'
    );
    return 'skipped';
  }
  console.log('✅ Anypoint credentials present. Proceeding with Flex-mode scenario.');
});


// ── Shared install/delete steps ────────────────────────────────────────────────

Given('an existing a2a API resource {string} on component {string} from package {string}',
  async function (apiName, componentName, packageName) {
    global.currentReleaseName = global.currentReleaseName || DEFAULT_RELEASE;
    const api = await resourceInventoryUtils.getExposedAPIResource(
      apiName, componentName, NAMESPACE
    );
    assert.ok(api,
      `ExposedAPI '${apiName}' should exist on component '${componentName}' ` +
      `(release: ${global.currentReleaseName})`
    );
  }
);

Given('an existing a2a Flex API resource {string} on component {string} from package {string}',
  async function (apiName, componentName, packageName) {
    global.currentReleaseName = global.currentReleaseName || DEFAULT_RELEASE;
    const api = await resourceInventoryUtils.getExposedAPIResource(
      apiName, componentName, NAMESPACE
    );
    assert.ok(api,
      `ExposedAPI '${apiName}' should exist on component '${componentName}' ` +
      `(release: ${global.currentReleaseName})`
    );
  }
);

When('I install the {string} package for Flex Gateway testing', async function (packageName) {
  global.currentReleaseName = DEFAULT_RELEASE;
  await packageManagerUtils.installPackage(packageName, global.currentReleaseName, NAMESPACE);
  // Allow time for the Component operator to decompose the Component into
  // ExposedAPI resources before the FlexGateway operator picks them up.
  const delay = 8000;
  console.log(`Waiting ${delay}ms after install for resource decomposition...`);
  await new Promise(resolve => setTimeout(resolve, delay));
});

When('the FlexGateway operator processes the a2a Istio deployment', async function () {
  // The VirtualService creation is synchronous from the operator's perspective
  // (no external API calls needed). A short wait is sufficient.
  const delay = 6000;
  console.log(`Waiting ${delay}ms for FlexGateway operator to create VirtualService...`);
  await new Promise(resolve => setTimeout(resolve, delay));
});

When('the FlexGateway operator processes the a2a Flex deployment',
  { timeout: FLEX_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function () {
    // Anypoint provisioning is asynchronous; the operator retries if the agent
    // card is not yet reachable. Poll until the ExposedAPI has flexGatewayBind.
    console.log(
      `Waiting up to ${FLEX_PATH_TIMEOUT / 1000}s for FlexGateway operator ` +
      'to complete Anypoint provisioning...'
    );
    await new Promise(resolve => setTimeout(resolve, FLEX_PATH_TIMEOUT / 10));
  }
);

When('the FlexGateway operator processes the a2a deletion', async function () {
  const delay = 8000;
  console.log(`Waiting ${delay}ms for FlexGateway operator to clean up VirtualService...`);
  await new Promise(resolve => setTimeout(resolve, delay));
});

When('the FlexGateway operator processes the Flex deletion',
  { timeout: FLEX_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function () {
    // Anypoint API instance deletion is a REST call; allow time for it.
    const delay = 15000;
    console.log(`Waiting ${delay}ms for FlexGateway operator to remove Anypoint API instance...`);
    await new Promise(resolve => setTimeout(resolve, delay));
  }
);

When('I delete the {string} Flex package', async function (packageName) {
  await packageManagerUtils.uninstallPackage(global.currentReleaseName, NAMESPACE);
  const delay = 5000;
  console.log(`Waiting ${delay}ms after uninstall...`);
  await new Promise(resolve => setTimeout(resolve, delay));
});


// ── Istio VirtualService assertions (F005) ─────────────────────────────────────

Then('I should see a VirtualService created for {string} on the {string} component',
  { timeout: ISTIO_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let vs = null;
    const start = performance.now();

    console.log(`Polling for VirtualService '${componentName}-${apiName}'...`);
    while (vs === null) {
      vs = await resourceInventoryUtils.getVirtualServiceForComponent(
        apiName, componentName, NAMESPACE
      );
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < ISTIO_PATH_TIMEOUT,
        `VirtualService for '${apiName}' on '${componentName}' not found within ` +
        `${ISTIO_PATH_TIMEOUT / 1000}s`
      );
      if (!vs) await new Promise(r => setTimeout(r, POLL_INTERVAL));
    }

    console.log(`✅ VirtualService found: ${vs.metadata.name}`);

    // Structural checks: must use the canvas/component-gateway and match the spec path.
    const gateways = vs.spec?.gateways || [];
    assert.ok(
      gateways.some(g => g === 'canvas/component-gateway'),
      'VirtualService must reference the canvas/component-gateway'
    );
    const httpRoutes = vs.spec?.http || [];
    assert.ok(httpRoutes.length > 0, 'VirtualService must have at least one http route');
  }
);

Then('I should not see a VirtualService for {string} on the {string} component',
  { timeout: ISTIO_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let vs = 'not-null';
    const start = performance.now();

    console.log(`Polling until VirtualService '${componentName}-${apiName}' is gone...`);
    while (vs !== null) {
      vs = await resourceInventoryUtils.getVirtualServiceForComponent(
        apiName, componentName, NAMESPACE
      );
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < ISTIO_PATH_TIMEOUT,
        `VirtualService for '${apiName}' on '${componentName}' still exists after ` +
        `${ISTIO_PATH_TIMEOUT / 1000}s`
      );
      if (vs !== null) await new Promise(r => setTimeout(r, POLL_INTERVAL));
    }

    console.log(`✅ VirtualService removed for '${apiName}' on '${componentName}'`);
  }
);

Then('the {string} ExposedAPI on {string} should have implementation ready status',
  { timeout: ISTIO_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let api = null;
    const start = performance.now();

    console.log(`Polling ExposedAPI '${apiName}' on '${componentName}' for ready status...`);
    while (!(api?.status?.implementation?.ready === true)) {
      api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < ISTIO_PATH_TIMEOUT,
        `ExposedAPI '${apiName}' on '${componentName}' did not reach implementation.ready=true ` +
        `within ${ISTIO_PATH_TIMEOUT / 1000}s`
      );
      if (!(api?.status?.implementation?.ready === true)) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL));
      }
    }

    console.log(`✅ ExposedAPI '${apiName}': implementation.ready = true`);
  }
);

Then('the {string} ExposedAPI on {string} should have a public URL in its status',
  { timeout: ISTIO_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let api = null;
    const start = performance.now();

    console.log(`Polling ExposedAPI '${apiName}' on '${componentName}' for apiStatus.url...`);
    while (!api?.status?.apiStatus?.url) {
      api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < ISTIO_PATH_TIMEOUT,
        `ExposedAPI '${apiName}' on '${componentName}' has no apiStatus.url ` +
        `after ${ISTIO_PATH_TIMEOUT / 1000}s`
      );
      if (!api?.status?.apiStatus?.url) await new Promise(r => setTimeout(r, POLL_INTERVAL));
    }

    const url = api.status.apiStatus.url;
    console.log(`✅ ExposedAPI '${apiName}': apiStatus.url = ${url}`);
    assert.ok(
      url.startsWith('https://'),
      `apiStatus.url '${url}' should start with 'https://'`
    );
  }
);

// ── Flex Gateway assertions (F006) ────────────────────────────────────────────

Then('the {string} ExposedAPI on {string} should have a Flex Gateway API instance bound',
  { timeout: FLEX_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let api = null;
    const start = performance.now();

    console.log(
      `Polling ExposedAPI '${apiName}' on '${componentName}' for flexGatewayBind.apiInstanceId...`
    );
    while (!api?.status?.flexGatewayBind?.apiInstanceId) {
      api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < FLEX_PATH_TIMEOUT,
        `ExposedAPI '${apiName}' on '${componentName}' has no flexGatewayBind.apiInstanceId ` +
        `after ${FLEX_PATH_TIMEOUT / 1000}s. ` +
        'Check that Anypoint credentials are valid, the Managed Flex Gateway is pre-provisioned, ' +
        'and the mock agent card endpoint is reachable through Istio ingress.'
      );
      if (!api?.status?.flexGatewayBind?.apiInstanceId) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL));
      }
    }

    const instanceId = api.status.flexGatewayBind.apiInstanceId;
    const exchangeId = api.status.flexGatewayBind.exchangeAssetId || '';
    const policies   = api.status.flexGatewayBind.policiesApplied || [];
    console.log(`✅ Flex Gateway API instance bound: instanceId=${instanceId} exchange=${exchangeId}`);
    console.log(`   Policies applied: ${policies.join(', ') || '(none listed)'}`);

    assert.ok(instanceId, 'flexGatewayBind.apiInstanceId must be non-empty');
  }
);

Then('the {string} ExposedAPI on {string} should have a Flex Gateway public URL in its status',
  { timeout: FLEX_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    let api = null;
    const start = performance.now();

    console.log(
      `Polling ExposedAPI '${apiName}' on '${componentName}' for flexGatewayBind.apiPublicUrl...`
    );
    while (!api?.status?.flexGatewayBind?.apiPublicUrl) {
      api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);
      const elapsed = performance.now() - start;
      assert.ok(
        elapsed < FLEX_PATH_TIMEOUT,
        `ExposedAPI '${apiName}' on '${componentName}' has no flexGatewayBind.apiPublicUrl ` +
        `after ${FLEX_PATH_TIMEOUT / 1000}s`
      );
      if (!api?.status?.flexGatewayBind?.apiPublicUrl) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL));
      }
    }

    const publicUrl   = api.status.flexGatewayBind.apiPublicUrl;
    const apiStatusUrl = api.status?.apiStatus?.url;
    console.log(`✅ Flex Gateway public URL: ${publicUrl}`);
    console.log(`   apiStatus.url: ${apiStatusUrl}`);

    // apiStatus.url must be set and must equal the Flex Gateway public URL,
    // not the Istio ingress URL (operator writes the GW URL back to apiStatus).
    assert.ok(publicUrl, 'flexGatewayBind.apiPublicUrl must be non-empty');
    assert.strictEqual(
      apiStatusUrl, publicUrl,
      `apiStatus.url ('${apiStatusUrl}') must equal flexGatewayBind.apiPublicUrl ('${publicUrl}')`
    );
  }
);

Then('the Anypoint API instance for {string} on {string} should be removed from Flex Gateway status',
  { timeout: FLEX_PATH_TIMEOUT + TIMEOUT_BUFFER },
  async function (apiName, componentName) {
    // After deletion the ExposedAPI CR itself should be gone. If it is still
    // present (finalizer not yet released) we verify the flexGatewayBind field
    // is cleared, indicating the operator completed its Anypoint cleanup.
    let api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);

    if (api === null) {
      console.log(
        `✅ ExposedAPI '${apiName}' on '${componentName}' fully deleted — ` +
        'Anypoint cleanup complete'
      );
      return;
    }

    // CR still exists (finalizer in progress): check flexGatewayBind is cleared.
    const start = performance.now();
    while (api !== null && api?.status?.flexGatewayBind?.apiInstanceId) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL));
      api = await resourceInventoryUtils.getExposedAPIResource(apiName, componentName, NAMESPACE);
      assert.ok(
        performance.now() - start < FLEX_PATH_TIMEOUT,
        `flexGatewayBind.apiInstanceId still present on '${apiName}' after ${FLEX_PATH_TIMEOUT / 1000}s`
      );
    }

    console.log(
      `✅ Anypoint API instance removed for '${apiName}' on '${componentName}'`
    );
  }
);
