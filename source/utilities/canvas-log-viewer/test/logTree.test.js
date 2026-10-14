import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { stripVTControlCharacters as strip } from 'node:util';
import colors from 'colors';
import {
    UNKNOWN,
    parseLogLine,
    formatMessage,
    addToTree,
    newLineStream,
} from '../lib/logTree.js';

// colors disables itself when stdout is not a TTY (e.g. in CI); force it on so
// the colour assertions are deterministic.
colors.enable();

const OPERATOR_LINE =
    '[2024-11-17 13:05:34,612] SManOP               [INFO    ] ' +
    '[demo-a-productcatalogmanagement|SMan/demo-a-productcatalogmanagement|secretsmanagementDelete|deleteSecret] ' +
    'Delete called with namespace: components';

const KOPF_LINE =
    '[2024-11-17 13:05:35,001] kopf.objects         [INFO    ] ' +
    '[components/demo-a-productcatalogmanagement] Handler \'deleteSecret\' succeeded.';

describe('parseLogLine', () => {
    it('returns null for a line with no bracketed fields', () => {
        assert.equal(parseLogLine('plain text with no brackets'), null);
        assert.equal(parseLogLine(''), null);
    });

    it('parses a fully labelled operator log line', () => {
        const entry = parseLogLine(OPERATOR_LINE);
        assert.deepEqual(entry, {
            dateStamp: '2024-11-17 13:05:34,612',
            type: 'INFO',
            controller: 'SManOP',
            componentName: 'demo-a-productcatalogmanagement',
            resourceName: 'SMan/demo-a-productcatalogmanagement',
            handlerName: 'secretsmanagementDelete',
            functionName: 'deleteSecret',
            message: 'Delete called with namespace: components',
        });
    });

    it('parses a kopf.objects line using the single label as the resource', () => {
        const entry = parseLogLine(KOPF_LINE);
        assert.equal(entry.controller, 'kopf.objects');
        assert.equal(entry.type, 'INFO');
        assert.equal(entry.resourceName, 'components/demo-a-productcatalogmanagement');
        assert.equal(entry.componentName, UNKNOWN);
        assert.equal(entry.handlerName, UNKNOWN);
        assert.equal(entry.functionName, UNKNOWN);
        assert.equal(entry.message, 'Handler \'deleteSecret\' succeeded.');
    });

    it('marks labels as Unknown when the label group is missing', () => {
        const entry = parseLogLine('[2024-11-17 13:05:36,000] compop [WARNING ] something odd happened');
        assert.equal(entry.type, 'WARNING');
        assert.equal(entry.controller, 'compop');
        assert.equal(entry.componentName, UNKNOWN);
        assert.equal(entry.resourceName, UNKNOWN);
        assert.equal(entry.message, 'something odd happened');
    });

    it('fills missing trailing labels with Unknown', () => {
        const entry = parseLogLine('[2024-11-17 13:05:36,000] compop [ERROR   ] [mycomp|myresource] failed');
        assert.equal(entry.type, 'ERROR');
        assert.equal(entry.componentName, 'mycomp');
        assert.equal(entry.resourceName, 'myresource');
        assert.equal(entry.handlerName, UNKNOWN);
        assert.equal(entry.functionName, UNKNOWN);
    });

    it('treats a line with only a timestamp as an error carrying the whole line', () => {
        const line = '[2024-11-17 13:05:36,000] Traceback (most recent call last):';
        const entry = parseLogLine(line);
        assert.equal(entry.dateStamp, '2024-11-17 13:05:36,000');
        assert.equal(entry.type, 'ERROR');
        assert.equal(entry.componentName, UNKNOWN);
        assert.equal(entry.message, line);
    });
});

describe('formatMessage', () => {
    const base = { dateStamp: '2024-11-17 13:05:34,612', functionName: 'fn', message: 'hello' };

    it('prefixes the message with the date stamp and function name', () => {
        assert.equal(strip(formatMessage({ ...base, type: 'INFO' })), '2024-11-17 13:05:34,612 fn: hello');
    });

    for (const [type, colour] of [['INFO', 32], ['ERROR', 31], ['WARNING', 33]]) {
        it(`colours ${type} messages`, () => {
            const formatted = formatMessage({ ...base, type });
            assert.ok(formatted.includes(`\u001b[${colour}mhello\u001b[39m`), JSON.stringify(formatted));
        });
    }

    it('does not colour messages of other levels', () => {
        const formatted = formatMessage({ ...base, type: 'DEBUG' });
        assert.ok(formatted.endsWith('fn: hello'));
    });
});

describe('addToTree', () => {
    it('groups entries by resource, controller and handler', () => {
        const tree = {};
        const first = parseLogLine(OPERATOR_LINE);
        const second = { ...first, message: 'second message' };
        const otherHandler = { ...first, handlerName: 'otherHandler' };
        const otherResource = { ...first, resourceName: 'other/resource' };

        addToTree(tree, first);
        addToTree(tree, second);
        addToTree(tree, otherHandler);
        const result = addToTree(tree, otherResource);

        assert.equal(result, tree);
        assert.deepEqual(Object.keys(tree), ['SMan/demo-a-productcatalogmanagement', 'other/resource']);

        const handlers = tree['SMan/demo-a-productcatalogmanagement'].SManOP;
        assert.deepEqual(Object.keys(handlers), ['secretsmanagementDelete', 'otherHandler']);
        assert.deepEqual(handlers.secretsmanagementDelete.map(strip), [
            '2024-11-17 13:05:34,612 deleteSecret: Delete called with namespace: components',
            '2024-11-17 13:05:34,612 deleteSecret: second message',
        ]);
        assert.equal(handlers.otherHandler.length, 1);
        assert.equal(tree['other/resource'].SManOP.secretsmanagementDelete.length, 1);
    });
});

describe('newLineStream', () => {
    it('emits one callback per complete line', () => {
        const lines = [];
        const handler = newLineStream((line) => lines.push(line));
        handler('one\ntwo\nthree\n');
        assert.deepEqual(lines, ['one', 'two', 'three']);
    });

    it('buffers partial lines across chunks', () => {
        const lines = [];
        const handler = newLineStream((line) => lines.push(line));
        handler('par');
        assert.deepEqual(lines, []);
        handler('tial\nnext');
        assert.deepEqual(lines, ['partial']);
        handler(' line\n');
        assert.deepEqual(lines, ['partial', 'next line']);
    });

    it('accepts Buffer chunks', () => {
        const lines = [];
        const handler = newLineStream((line) => lines.push(line));
        handler(Buffer.from('from a buffer\n'));
        assert.deepEqual(lines, ['from a buffer']);
    });

    it('emits empty strings for blank lines', () => {
        const lines = [];
        const handler = newLineStream((line) => lines.push(line));
        handler('a\n\nb\n');
        assert.deepEqual(lines, ['a', '', 'b']);
    });
});
