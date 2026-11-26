// Kubernetes helpers for the Component Viewer. These take the API client as an
// argument so they can be unit tested with simple fakes.
//
// @kubernetes/client-node 1.x takes request parameters as a single object and
// resolves directly to the response body.

import { getCrdVersion } from './componentTree.js';

export const COMPONENT_GROUP = 'oda.tmforum.org';
export const COMPONENT_PLURAL = 'components';

/**
 * Find the version of the ODA components CRD installed in the cluster.
 *
 * @param {object} customApi a @kubernetes/client-node CustomObjectsApi client
 * @returns {Promise<string|null>} the version to use, or null if the CRD is not installed
 */
export async function findComponentsCrdVersion(customApi) {
    const crdList = await customApi.listClusterCustomObject({
        group: 'apiextensions.k8s.io',
        version: 'v1',
        plural: 'customresourcedefinitions',
    });
    const crd = (crdList?.items ?? []).find(
        (item) => item.spec?.group === COMPONENT_GROUP && item.spec?.names?.plural === COMPONENT_PLURAL,
    );
    return crd ? getCrdVersion(crd) : null;
}

/**
 * List the ODA Components in a namespace.
 *
 * @param {object} customApi a @kubernetes/client-node CustomObjectsApi client
 * @param {string} version the components CRD version
 * @param {string} namespace the namespace to list
 * @returns {Promise<object[]>} the component custom resources
 */
export async function listComponents(customApi, version, namespace) {
    const componentList = await customApi.listNamespacedCustomObject({
        group: COMPONENT_GROUP,
        version,
        namespace,
        plural: COMPONENT_PLURAL,
    });
    return componentList?.items ?? [];
}
