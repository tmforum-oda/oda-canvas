import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
    COMPONENT_GROUP,
    COMPONENT_PLURAL,
    findComponentsCrdVersion,
    listComponents,
} from '../lib/kubernetes.js';

const componentsCrd = {
    spec: {
        group: COMPONENT_GROUP,
        names: { plural: COMPONENT_PLURAL },
        versions: [{ name: 'v1beta4', storage: false }, { name: 'v1', storage: true }],
    },
    status: { storedVersions: ['v1'] },
};

function fakeCustomApi({ crds = [], components = [] } = {}) {
    const calls = [];
    return {
        calls,
        async listClusterCustomObject(params) {
            calls.push(['listClusterCustomObject', params]);
            return { items: crds };
        },
        async listNamespacedCustomObject(params) {
            calls.push(['listNamespacedCustomObject', params]);
            return { items: components };
        },
    };
}

describe('findComponentsCrdVersion', () => {
    it('lists CRDs using the 1.x object-style parameters', async () => {
        const customApi = fakeCustomApi({ crds: [componentsCrd] });
        await findComponentsCrdVersion(customApi);
        assert.deepEqual(customApi.calls, [[
            'listClusterCustomObject',
            { group: 'apiextensions.k8s.io', version: 'v1', plural: 'customresourcedefinitions' },
        ]]);
    });

    it('returns the version of the components CRD', async () => {
        const customApi = fakeCustomApi({ crds: [componentsCrd] });
        assert.equal(await findComponentsCrdVersion(customApi), 'v1');
    });

    it('ignores a components CRD from another API group', async () => {
        const otherCrd = { spec: { group: 'example.com', names: { plural: 'components' } }, status: { storedVersions: ['v9'] } };
        const customApi = fakeCustomApi({ crds: [otherCrd, componentsCrd] });
        assert.equal(await findComponentsCrdVersion(customApi), 'v1');
    });

    it('returns null when the components CRD is not installed', async () => {
        const otherCrd = { spec: { group: 'example.com', names: { plural: 'widgets' } } };
        assert.equal(await findComponentsCrdVersion(fakeCustomApi({ crds: [otherCrd] })), null);
    });

    it('propagates API errors', async () => {
        const customApi = {
            async listClusterCustomObject() {
                throw new Error('forbidden');
            },
        };
        await assert.rejects(findComponentsCrdVersion(customApi), /forbidden/);
    });
});

describe('listComponents', () => {
    it('lists components using the 1.x object-style parameters', async () => {
        const customApi = fakeCustomApi();
        await listComponents(customApi, 'v1', 'my-namespace');
        assert.deepEqual(customApi.calls, [[
            'listNamespacedCustomObject',
            { group: COMPONENT_GROUP, version: 'v1', namespace: 'my-namespace', plural: COMPONENT_PLURAL },
        ]]);
    });

    it('returns the component items', async () => {
        const components = [{ metadata: { name: 'a' } }, { metadata: { name: 'b' } }];
        const customApi = fakeCustomApi({ components });
        assert.deepEqual(await listComponents(customApi, 'v1', 'components'), components);
    });

    it('returns an empty list when the response has no items', async () => {
        const customApi = { async listNamespacedCustomObject() { return {}; } };
        assert.deepEqual(await listComponents(customApi, 'v1', 'components'), []);
    });
});
