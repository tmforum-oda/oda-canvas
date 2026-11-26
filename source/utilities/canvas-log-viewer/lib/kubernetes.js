// Kubernetes helpers for the Canvas Log Viewer. These take the API clients as
// arguments so they can be unit tested with simple fakes.

export const CANVAS_NAMESPACE = 'canvas';
export const OPERATOR_LABEL_SELECTOR = 'app=component-operator';
export const OPERATOR_CONTAINER = 'component-operator';

/**
 * Find the name of the component operator pod.
 *
 * @param {object} coreApi a @kubernetes/client-node CoreV1Api client
 * @param {string} namespace the namespace to search
 * @param {string} labelSelector the label selector identifying the operator pod
 * @returns {Promise<string>} the name of the first matching pod
 * @throws {Error} if no matching pod is found
 */
export async function findOperatorPod(coreApi, namespace = CANVAS_NAMESPACE, labelSelector = OPERATOR_LABEL_SELECTOR) {
    // @kubernetes/client-node 1.x takes request parameters as a single object
    // and resolves directly to the response body.
    const podList = await coreApi.listNamespacedPod({ namespace, labelSelector });
    const pods = podList?.items ?? [];
    if (pods.length === 0) {
        throw new Error(`No pod found in namespace '${namespace}' matching '${labelSelector}'`);
    }
    return pods[0].metadata.name;
}
