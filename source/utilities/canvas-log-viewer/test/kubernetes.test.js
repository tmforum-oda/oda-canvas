import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
    CANVAS_NAMESPACE,
    OPERATOR_LABEL_SELECTOR,
    findOperatorPod,
} from '../lib/kubernetes.js';

function fakeCoreApi(items) {
    const calls = [];
    return {
        calls,
        async listNamespacedPod(params) {
            calls.push(params);
            return { items };
        },
    };
}

describe('findOperatorPod', () => {
    it('lists pods using the 1.x object-style parameters', async () => {
        const api = fakeCoreApi([{ metadata: { name: 'component-operator-abc123' } }]);
        await findOperatorPod(api);
        assert.deepEqual(api.calls, [{ namespace: CANVAS_NAMESPACE, labelSelector: OPERATOR_LABEL_SELECTOR }]);
    });

    it('returns the name of the first matching pod', async () => {
        const api = fakeCoreApi([
            { metadata: { name: 'component-operator-first' } },
            { metadata: { name: 'component-operator-second' } },
        ]);
        assert.equal(await findOperatorPod(api), 'component-operator-first');
    });

    it('passes through a custom namespace and selector', async () => {
        const api = fakeCoreApi([{ metadata: { name: 'pod' } }]);
        await findOperatorPod(api, 'other-ns', 'app=other');
        assert.deepEqual(api.calls, [{ namespace: 'other-ns', labelSelector: 'app=other' }]);
    });

    it('throws a descriptive error when no pod matches', async () => {
        const api = fakeCoreApi([]);
        await assert.rejects(findOperatorPod(api), /No pod found in namespace 'canvas' matching 'app=component-operator'/);
    });

    it('propagates API errors', async () => {
        const api = {
            async listNamespacedPod() {
                throw new Error('forbidden');
            },
        };
        await assert.rejects(findOperatorPod(api), /forbidden/);
    });
});
