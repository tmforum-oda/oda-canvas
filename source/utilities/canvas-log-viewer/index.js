#!/usr/bin/env -S node

import * as k8s from '@kubernetes/client-node';
import treeify from 'treeify';
import stream from 'node:stream';
import { parseLogLine, addToTree, newLineStream } from './lib/logTree.js';
import {
    CANVAS_NAMESPACE,
    OPERATOR_CONTAINER,
    findOperatorPod,
} from './lib/kubernetes.js';

const logTreeObject = {};

function printBanner() {
    console.log('=================================================');
    console.log('===           ODA Canvas Log Viewer           ===');
    console.log('=================================================');
}

function consoleLogTree() {
    console.clear();
    console.log('\n\n\n\n');
    printBanner();
    console.log('');
    console.log(treeify.asTree(logTreeObject, true));
}

async function mainFunction() {
    const kc = new k8s.KubeConfig();
    kc.loadFromDefault();

    printBanner();

    const targetComponent = process.argv[2];
    if (!targetComponent) {
        console.log('Usage: kubectl canvas-logs <targetComponent>');
        process.exit(1);
    }
    console.log('targetComponent:', targetComponent);

    let canvasOperator;
    try {
        canvasOperator = await findOperatorPod(kc.makeApiClient(k8s.CoreV1Api));
    } catch (err) {
        console.error('Error listing pods:', err.message ?? err);
        process.exit(1);
    }
    console.log('Canvas Operator:', canvasOperator);

    const logStream = new stream.PassThrough();
    logStream.on('data', newLineStream((line) => {
        const entry = parseLogLine(line);
        if (entry && entry.componentName === targetComponent) {
            addToTree(logTreeObject, entry);
            consoleLogTree();
        }
    }));

    const log = new k8s.Log(kc);
    try {
        await log.log(CANVAS_NAMESPACE, canvasOperator, OPERATOR_CONTAINER, logStream, {
            follow: true,
            tailLines: 500,
            pretty: false,
            timestamps: false,
        });
    } catch (err) {
        console.log(err);
        process.exit(1);
    }
}

mainFunction();
