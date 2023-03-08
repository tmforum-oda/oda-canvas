#!/usr/bin/env node
const k8s = require('@kubernetes/client-node');
var treeify = require('treeify');
const colors = require('colors');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

// get namespace from Environment variable or command-line
var namespace = 'components'
if (process.env.NAMESPACE) {
    namespace = process.env.NAMESPACE
}
process.argv.forEach(function (val, index, array) {
    if ((val == '-n') || (val == '--namespace')) {
        if (array[index+1]) {
            namespace = array[index+1]
        } else {
            console.error('Please provide the namespace value after %s', val)
            process.exit(1)
        }
    }
    if ((val == '-h') || (val == '--help')) {
        console.log('')
        console.log('ODA Component Viewer')
        console.log('--------------------')
        console.log('')
        console.log('Displays the status of ODA Components deployed in the kubernetes cluster (based on kubeconfig). By default it uses the `default` namespace. Alternative namespace can be set with NAMESPACE environment variable or -n <namespace>. ')
        console.log('')
        process.exit(0)
    }
  });

displayComponentTree()

function displayComponentTree() {

    try {
        const customk8sApi = kc.makeApiClient(k8s.CustomObjectsApi);

        customk8sApi.listNamespacedCustomObject('oda.tmforum.org', 'v1alpha4', namespace, 'components').then((res) => {
            console.clear()
            for (var key in res.body.items) {
                var item = res.body.items[key]
                console.log('')
                console.log('')
                console.log('Component: %s'.gray, item.metadata.name.white)
                console.log('Namespace: %s'.gray, namespace.white)

                var deployment_status = 'Starting'
                if (item.hasOwnProperty('status')) {
                    if (item.status.hasOwnProperty('summary/status')) {
                        deployment_status = item.status['summary/status'].deployment_status
                    } 
                }
                if (deployment_status == "Complete") {
                    console.log('Deployment Status: %s'.gray, deployment_status.green)
                }
                else if (deployment_status == "Starting") {
                    console.log('Deployment Status: %s'.gray, deployment_status.red)
                }
                else {
                    console.log('Deployment Status: %s'.gray, deployment_status.yellow)
                }
                var apiObj = {}
                if (item.hasOwnProperty('status')) {
                    // console.log(item.status)
                    if (item.status.hasOwnProperty('exposedAPIs')) {
                        if (item.status.exposedAPIs.length > 0) {
                            apiObj['core-function'.gray] = formatTreeObject(item.status.exposedAPIs)
                        }
                    }
                    if (item.status.hasOwnProperty('managementAPIs')) {
                        if (item.status.managementAPIs.length > 0) {
                            apiObj['management'.gray] = formatTreeObject(item.status.managementAPIs)
                        }
                    }
                    if (item.status.hasOwnProperty('securityAPIs')) {
                        if (Object.keys(item.status.securityAPIs).length > 0) {
                            apiObj['security'.gray] = formatTreeObject(item.status.securityAPIs)
                        }
                    }
                }

                treeJSON = {}
                if (Object.keys(apiObj).length>0) {
                    console.log( treeify.asTree(apiObj, true) )
                }
                console.log('')
            }
            if (res.body.items.length == 0) {
                console.log('No ODA Components to view in namespace %s', namespace)
            }
        });
    } 
    catch (err) {
        clearInterval(intervalTimer);
        console.error(err)
    }
}

function formatTreeObject(inputStatusObject) {
    var outputStatusObject = {}
    for (var key in inputStatusObject) {
        var status = inputStatusObject[key]
        // fix formatting
        if (!status.url) {
            status.url = 'Not created yet'.yellow
        } else {
            status.url = status.url.blue
        }
        if (status.ready == true) {
            status.ready = 'true'.green
        } else {
            status.ready = 'false'.yellow
        }
        outputStatusObject[status.name] = {url: status.url, ready: status.ready}
        if (status.developerUI) {
            outputStatusObject[status.name].developerUI = status.developerUI.blue
        }
    }
    return outputStatusObject
}
