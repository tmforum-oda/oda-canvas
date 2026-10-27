// Pure functions for turning ODA Component custom resources into the text
// displayed by the Component Viewer. Kept free of any Kubernetes dependencies
// so they can be unit tested in isolation.

import colors from 'colors';

export const DEFAULT_NAMESPACE = 'components';

// Description shown for each deployment_status set by the component operator.
// 'Starting' is used when the operator has not written a status yet.
export const DEPLOYMENT_STATUS_DESCRIPTIONS = {
    'Starting': 'Component controller not started processing yet',
    'In-Progress-CompCon': 'Component controller configuring APIs',
    'In-Progress-IDConfOp': 'Component controller configuring Identity Management',
    'In-Progress-SecretMan': 'Component controller configuring Secrets Management',
    'In-Progress-DepApi': 'Component controller configuring Dependent APIs',
};

// The identity config operator status was previously written under this key.
const LEGACY_IDENTITY_STATUS_KEY = 'security_client_add/status.summary/status.deployment_status';

const API_TYPES = [
    ['coreAPIs', 'coreFunction'],
    ['managementAPIs', 'managementFunction'],
    ['securityAPIs', 'securityFunction'],
];

const TROUBLESHOOTING = colors.grey('Troubleshooting: ');

/**
 * Parse the command-line arguments and environment.
 *
 * @param {string[]} argv the arguments after the script name
 * @param {object} env the process environment
 * @returns {{namespace: string, help: boolean, error?: string}}
 */
export function parseArgs(argv, env = {}) {
    const options = { namespace: env.NAMESPACE || DEFAULT_NAMESPACE, help: false };
    for (let i = 0; i < argv.length; i++) {
        const val = argv[i];
        if (val === '-n' || val === '--namespace') {
            if (!argv[i + 1]) {
                options.error = `Please provide the namespace value after ${val}`;
                return options;
            }
            options.namespace = argv[++i];
        } else if (val === '-h' || val === '--help') {
            options.help = true;
        }
    }
    return options;
}

/**
 * Pick the version of the components CRD to query: the storage version if the
 * CRD spec is available, otherwise the most recent stored version.
 *
 * @param {object} crd the components CustomResourceDefinition
 * @returns {string} the version name, e.g. 'v1'
 */
export function getCrdVersion(crd) {
    const storageVersion = crd.spec?.versions?.find((v) => v.storage);
    if (storageVersion) {
        return storageVersion.name;
    }
    const storedVersions = crd.status?.storedVersions ?? [];
    return storedVersions[storedVersions.length - 1];
}

/**
 * @param {object} component an ODA Component custom resource
 * @returns {string} its deployment status, or 'Starting' if none is set yet
 */
export function getDeploymentStatus(component) {
    return component.status?.['summary/status']?.deployment_status ?? 'Starting';
}

/**
 * @param {string} deploymentStatus a deployment status from getDeploymentStatus
 * @returns {string} the coloured 'Deployment Status' line
 */
export function formatDeploymentStatus(deploymentStatus) {
    const label = colors.gray('Deployment Status: ');
    if (deploymentStatus === 'Complete') {
        return label + colors.green(deploymentStatus);
    }
    const description = DEPLOYMENT_STATUS_DESCRIPTIONS[deploymentStatus];
    if (description) {
        return label + colors.yellow(`${deploymentStatus} : ${description}`);
    }
    return label + colors.red(`Unknown (${deploymentStatus})`);
}

/**
 * Convert a list of API statuses into the tree format, keyed by API name.
 *
 * @param {object[]|object} apiStatuses the APIs from the component status
 * @returns {object} the tree nodes for the APIs
 */
export function formatApiStatuses(apiStatuses) {
    const output = {};
    for (const status of Object.values(apiStatuses ?? {})) {
        const node = {
            url: status.url ? colors.blue(status.url) : colors.yellow('Not created yet'),
            ready: status.ready === true ? colors.green('true') : colors.yellow('false'),
        };
        if (status.developerUI) {
            node.developerUI = colors.blue(status.developerUI);
        }
        output[status.name] = node;
    }
    return output;
}

/**
 * @param {object} status the component status
 * @returns {object|undefined} the identity config status, if present
 */
function getIdentityStatus(status) {
    return status.identityConfig ?? status[LEGACY_IDENTITY_STATUS_KEY];
}

/**
 * Build the treeify object describing the APIs and Identity Management of a
 * component.
 *
 * @param {object} component an ODA Component custom resource
 * @returns {object} the tree object
 */
export function buildComponentTree(component) {
    const status = component.status ?? {};
    const tree = {};

    const apiObj = {};
    for (const [statusKey, label] of API_TYPES) {
        if (status[statusKey] && Object.keys(status[statusKey]).length > 0) {
            apiObj[colors.gray(label)] = formatApiStatuses(status[statusKey]);
        }
    }
    if (Object.keys(apiObj).length > 0) {
        tree[colors.gray('APIs')] = apiObj;
    }

    const identity = getIdentityStatus(status);
    if (identity && typeof identity === 'object') {
        const identityNode = {};
        if (identity.identityProvider) {
            identityNode.identityProvider = colors.blue(identity.identityProvider);
        }
        if (identity.listenerRegistered === true) {
            identityNode.status = colors.green('registered');
        }
        tree[colors.gray('Identity Management')] = identityNode;
    }
    return tree;
}

function allApis(status) {
    return API_TYPES.flatMap(([statusKey]) => Object.values(status?.[statusKey] ?? {}));
}

/**
 * Create troubleshooting hints for components that are stuck in progress.
 *
 * @param {string} deploymentStatus the component's deployment status
 * @param {object} component an ODA Component custom resource
 * @returns {string} the troubleshooting text, or '' if there is nothing to add
 */
export function createTroubleshootingText(deploymentStatus, component) {
    let text = '';
    if (deploymentStatus === 'In-Progress-CompCon') {
        text += TROUBLESHOOTING + colors.yellow('Component controller is still configuring APIs.') + '\n';
        const apis = allApis(component.status);
        if (!apis.every((api) => api.url)) {
            text += TROUBLESHOOTING
                + colors.yellow('Not all APIs have a valid URL. If this problem persists, check the ')
                + 'api.oda.tmforum.org'
                + colors.yellow(' custom resource and the configuration of any Service Mesh and/or API Gateway that is being used.')
                + '\n';
        }
        if (!apis.every((api) => api.ready)) {
            text += TROUBLESHOOTING
                + colors.yellow('Not all APIs are ready. If this problem persists, check Pods that are implementing the API. Check they are ready to receive HTTP traffic at the configured port.')
                + '\n';
        }
    }

    if (deploymentStatus === 'In-Progress-IDConfOp') {
        text += TROUBLESHOOTING + colors.yellow('Component controller is still configuring Identity Management.') + '\n';
        text += TROUBLESHOOTING + colors.yellow('If this problem persists, check the configuration of the Identity Management system and the logs of the Component Controller.') + '\n';
    }
    return text;
}
