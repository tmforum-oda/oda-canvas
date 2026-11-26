import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { stripVTControlCharacters as strip } from 'node:util';
import colors from 'colors';
import {
    DEFAULT_NAMESPACE,
    DEPLOYMENT_STATUS_DESCRIPTIONS,
    parseArgs,
    getCrdVersion,
    getDeploymentStatus,
    formatDeploymentStatus,
    formatApiStatuses,
    buildComponentTree,
    createTroubleshootingText,
} from '../lib/componentTree.js';

// colors disables itself when stdout is not a TTY (e.g. in CI); force it on so
// the colour assertions are deterministic.
colors.enable();

// Recursively strip ANSI colour codes from the keys and values of a tree.
function stripTree(value) {
    if (typeof value === 'string') {
        return strip(value);
    }
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [strip(k), stripTree(v)]));
}

function api(name, overrides = {}) {
    return {
        name,
        url: `https://localhost/pc/${name}`,
        developerUI: `https://localhost/pc/${name}/docs`,
        ready: true,
        ...overrides,
    };
}

// Modelled on a deployed pc-productcatalogmanagement component.
function completeComponent() {
    return {
        metadata: { name: 'pc-productcatalogmanagement' },
        status: {
            'summary/status': { deployment_status: 'Complete' },
            coreAPIs: [api('productcatalogmanagement-v4'), api('promotionmanagement-v4')],
            managementAPIs: [api('metrics', { developerUI: undefined })],
            securityAPIs: [api('userrolesandpermissions-v5')],
            identityConfig: { identityProvider: 'Keycloak', listenerRegistered: true },
        },
    };
}

describe('parseArgs', () => {
    it('defaults to the components namespace', () => {
        assert.deepEqual(parseArgs([], {}), { namespace: DEFAULT_NAMESPACE, help: false });
    });

    it('uses the NAMESPACE environment variable', () => {
        assert.equal(parseArgs([], { NAMESPACE: 'from-env' }).namespace, 'from-env');
    });

    for (const flag of ['-n', '--namespace']) {
        it(`lets ${flag} override the environment`, () => {
            assert.equal(parseArgs([flag, 'from-arg'], { NAMESPACE: 'from-env' }).namespace, 'from-arg');
        });

        it(`returns an error when ${flag} has no value`, () => {
            assert.equal(parseArgs([flag], {}).error, `Please provide the namespace value after ${flag}`);
        });
    }

    for (const flag of ['-h', '--help']) {
        it(`recognises ${flag}`, () => {
            assert.equal(parseArgs([flag], {}).help, true);
        });
    }

    it('does not treat a namespace value as a flag', () => {
        assert.deepEqual(parseArgs(['-n', '-h'], {}), { namespace: '-h', help: false });
    });
});

describe('getCrdVersion', () => {
    it('prefers the storage version from the CRD spec', () => {
        const crd = {
            spec: { versions: [{ name: 'v1beta4', storage: false }, { name: 'v1', storage: true }] },
            status: { storedVersions: ['v1beta4'] },
        };
        assert.equal(getCrdVersion(crd), 'v1');
    });

    it('falls back to the most recent stored version', () => {
        const crd = { status: { storedVersions: ['v1beta3', 'v1beta4', 'v1'] } };
        assert.equal(getCrdVersion(crd), 'v1');
    });

    it('returns undefined when no version information is present', () => {
        assert.equal(getCrdVersion({}), undefined);
    });
});

describe('getDeploymentStatus', () => {
    it('reads the summary deployment status', () => {
        assert.equal(getDeploymentStatus(completeComponent()), 'Complete');
    });

    it('returns Starting when the component has no status yet', () => {
        assert.equal(getDeploymentStatus({ metadata: { name: 'new' } }), 'Starting');
    });

    it('returns Starting when the status has no summary yet', () => {
        assert.equal(getDeploymentStatus({ status: { coreAPIs: [] } }), 'Starting');
    });
});

describe('formatDeploymentStatus', () => {
    it('shows Complete in green', () => {
        const line = formatDeploymentStatus('Complete');
        assert.equal(strip(line), 'Deployment Status: Complete');
        assert.ok(line.includes(colors.green('Complete')));
    });

    for (const [status, description] of Object.entries(DEPLOYMENT_STATUS_DESCRIPTIONS)) {
        it(`describes ${status} in yellow`, () => {
            const line = formatDeploymentStatus(status);
            assert.equal(strip(line), `Deployment Status: ${status} : ${description}`);
            assert.ok(line.includes(colors.yellow(`${status} : ${description}`)));
        });
    }

    it('shows only one line for Starting (no trailing Unknown)', () => {
        assert.ok(!strip(formatDeploymentStatus('Starting')).includes('Unknown'));
    });

    it('shows unrecognised statuses as Unknown in red', () => {
        const line = formatDeploymentStatus('Something-New');
        assert.equal(strip(line), 'Deployment Status: Unknown (Something-New)');
        assert.ok(line.includes(colors.red('Unknown (Something-New)')));
    });
});

describe('formatApiStatuses', () => {
    it('keys APIs by name with url, ready and developerUI', () => {
        const result = stripTree(formatApiStatuses([api('a'), api('b', { developerUI: undefined })]));
        assert.deepEqual(result, {
            a: { url: 'https://localhost/pc/a', ready: 'true', developerUI: 'https://localhost/pc/a/docs' },
            b: { url: 'https://localhost/pc/b', ready: 'true' },
        });
    });

    it('flags APIs with no URL that are not ready', () => {
        const result = stripTree(formatApiStatuses([api('a', { url: undefined, ready: false, developerUI: undefined })]));
        assert.deepEqual(result, { a: { url: 'Not created yet', ready: 'false' } });
    });

    it('does not modify the input statuses', () => {
        const input = [api('a')];
        const copy = structuredClone(input);
        formatApiStatuses(input);
        assert.deepEqual(input, copy);
    });

    it('handles missing or object-shaped API lists', () => {
        assert.deepEqual(formatApiStatuses(undefined), {});
        assert.deepEqual(Object.keys(formatApiStatuses({ first: api('a') })), ['a']);
    });
});

describe('buildComponentTree', () => {
    it('builds the APIs and Identity Management tree for a complete component', () => {
        assert.deepEqual(stripTree(buildComponentTree(completeComponent())), {
            APIs: {
                coreFunction: {
                    'productcatalogmanagement-v4': {
                        url: 'https://localhost/pc/productcatalogmanagement-v4',
                        ready: 'true',
                        developerUI: 'https://localhost/pc/productcatalogmanagement-v4/docs',
                    },
                    'promotionmanagement-v4': {
                        url: 'https://localhost/pc/promotionmanagement-v4',
                        ready: 'true',
                        developerUI: 'https://localhost/pc/promotionmanagement-v4/docs',
                    },
                },
                managementFunction: {
                    metrics: { url: 'https://localhost/pc/metrics', ready: 'true' },
                },
                securityFunction: {
                    'userrolesandpermissions-v5': {
                        url: 'https://localhost/pc/userrolesandpermissions-v5',
                        ready: 'true',
                        developerUI: 'https://localhost/pc/userrolesandpermissions-v5/docs',
                    },
                },
            },
            'Identity Management': { identityProvider: 'Keycloak', status: 'registered' },
        });
    });

    it('returns an empty tree for a component with no status', () => {
        assert.deepEqual(buildComponentTree({ metadata: { name: 'new' } }), {});
    });

    it('omits empty API groups', () => {
        const component = completeComponent();
        component.status.managementAPIs = [];
        delete component.status.securityAPIs;
        assert.deepEqual(Object.keys(stripTree(buildComponentTree(component)).APIs), ['coreFunction']);
    });

    it('reads identity status from the legacy security_client_add key', () => {
        const component = completeComponent();
        delete component.status.identityConfig;
        component.status['security_client_add/status.summary/status.deployment_status'] = {
            identityProvider: 'Keycloak',
            listenerRegistered: true,
        };
        assert.deepEqual(stripTree(buildComponentTree(component))['Identity Management'], {
            identityProvider: 'Keycloak',
            status: 'registered',
        });
    });

    it('does not show registered until the listener is registered', () => {
        const component = completeComponent();
        component.status.identityConfig.listenerRegistered = false;
        assert.deepEqual(stripTree(buildComponentTree(component))['Identity Management'], {
            identityProvider: 'Keycloak',
        });
    });
});

describe('createTroubleshootingText', () => {
    it('returns no text for a complete component', () => {
        assert.equal(createTroubleshootingText('Complete', completeComponent()), '');
    });

    it('reports APIs still being configured', () => {
        const text = strip(createTroubleshootingText('In-Progress-CompCon', completeComponent()));
        assert.equal(text, 'Troubleshooting: Component controller is still configuring APIs.\n');
    });

    it('reports APIs without a URL', () => {
        const component = completeComponent();
        component.status.managementAPIs[0].url = undefined;
        const text = strip(createTroubleshootingText('In-Progress-CompCon', component));
        assert.match(text, /Not all APIs have a valid URL/);
        assert.doesNotMatch(text, /Not all APIs are ready/);
    });

    it('reports APIs that are not ready', () => {
        const component = completeComponent();
        component.status.securityAPIs[0].ready = false;
        const text = strip(createTroubleshootingText('In-Progress-CompCon', component));
        assert.match(text, /Not all APIs are ready/);
        assert.doesNotMatch(text, /Not all APIs have a valid URL/);
    });

    it('handles an in-progress component with no API status yet', () => {
        const text = strip(createTroubleshootingText('In-Progress-CompCon', { status: {} }));
        assert.equal(text, 'Troubleshooting: Component controller is still configuring APIs.\n');
    });

    it('reports Identity Management still being configured', () => {
        const text = strip(createTroubleshootingText('In-Progress-IDConfOp', completeComponent()));
        assert.equal(
            text,
            'Troubleshooting: Component controller is still configuring Identity Management.\n'
            + 'Troubleshooting: If this problem persists, check the configuration of the Identity Management system and the logs of the Component Controller.\n',
        );
    });
});
