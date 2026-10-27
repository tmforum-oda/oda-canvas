#!/usr/bin/env node

import * as k8s from '@kubernetes/client-node';
import treeify from 'treeify';
import colors from 'colors';
import {
    parseArgs,
    getDeploymentStatus,
    formatDeploymentStatus,
    buildComponentTree,
    createTroubleshootingText,
} from './lib/componentTree.js';
import { findComponentsCrdVersion, listComponents } from './lib/kubernetes.js';

function printHelp() {
    console.log('');
    console.log('ODA Component Viewer');
    console.log('--------------------');
    console.log('');
    console.log('Displays the status of ODA Components deployed in the kubernetes cluster (based on kubeconfig). By default it uses the `components` namespace. Alternative namespace can be set with NAMESPACE environment variable or -n <namespace>. ');
    console.log('');
}

function printComponent(component, namespace) {
    console.log('');
    console.log('');
    console.log(colors.gray('Component: ') + colors.white(component.metadata.name));
    console.log(colors.gray('Namespace: ') + colors.white(namespace));

    const deploymentStatus = getDeploymentStatus(component);
    console.log(formatDeploymentStatus(deploymentStatus));
    console.log(treeify.asTree(buildComponentTree(component), true));
    console.log('');

    const troubleshootingText = createTroubleshootingText(deploymentStatus, component);
    if (troubleshootingText) {
        console.log(troubleshootingText);
    }
}

async function displayComponentTree(namespace) {
    const kc = new k8s.KubeConfig();
    kc.loadFromDefault();
    const customApi = kc.makeApiClient(k8s.CustomObjectsApi);

    // check the connected Kubernetes cluster has the components CRD installed
    const version = await findComponentsCrdVersion(customApi);
    if (!version) {
        console.log(colors.red('Components Custom Resource Definition does not exist. Check your canvas installation.'));
        process.exit(1);
    }
    console.log(`Using Components Custom Resource Definition: ${version}`);

    const components = await listComponents(customApi, version, namespace);
    for (const component of components) {
        printComponent(component, namespace);
    }
    if (components.length === 0) {
        console.log('No ODA Components to view in namespace %s', namespace);
    }
}

const options = parseArgs(process.argv.slice(2), process.env);
if (options.error) {
    console.error(options.error);
    process.exit(1);
}
if (options.help) {
    printHelp();
    process.exit(0);
}

displayComponentTree(options.namespace).catch((err) => {
    console.error(colors.red(`Error: ${err.message ?? err}`));
    process.exit(1);
});
