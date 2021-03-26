#!/usr/bin/env node
const k8s = require('@kubernetes/client-node');
const { printTable, Table  } = require('console-table-printer');
const colors = require('colors');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

// get namespace from Environment variable or command-line
var namespace = 'default'
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

var intervalTimer = setInterval(displayComponent, 2000)

function displayComponent() {

    try {
        const customk8sApi = kc.makeApiClient(k8s.CustomObjectsApi);
        console.clear()

        customk8sApi.listNamespacedCustomObject('oda.tmforum.org', 'v1alpha2', namespace, 'components').then((res) => {
            for (var key in res.body.items) {
                var item = res.body.items[key]
                console.log('')
                console.log('')
                console.log('Component: %s', item.metadata.name)
                console.log('Namespace: %s', namespace)

                var deployment_status = 'Starting'
                if (item.hasOwnProperty('status')) {
                    if (item.status.hasOwnProperty('deployment_status')) {
                        deployment_status = item.status.deployment_status
                    } 
                }
                if (deployment_status == "Complete") {
                    console.log('Deployment Status: %s', deployment_status.green)
                }
                else if (deployment_status == "Starting") {
                    console.log('Deployment Status: %s', deployment_status.red)
                }
                else {
                    console.log('Deployment Status: %s', deployment_status.yellow)
                }
                //console.log('APIs: ')
                var apiList = []
                if (item.hasOwnProperty('status')) {
                    if (item.status.hasOwnProperty('exposedAPIs')) {
                        for (var apiKey in item.status.exposedAPIs) {
                            var api = item.status.exposedAPIs[apiKey]
                            apiList.push({type: 'core-function', name: api.name, url: api.url, ready: api.ready})
                        }
                    }
                    if (item.status.hasOwnProperty('securityAPIs')) {
                        for (var apiKey in item.status.securityAPIs) {
                            var api = item.status.securityAPIs[apiKey]
                            apiList.push({type: 'security', name: api.name, url: api.url, ready: api.ready})
                        }
                    }
                }
                // fix formatting
                for (var key in apiList){
                    var api = apiList[key]
                    if (!api.url) {
                        api.url = 'Not created yet'.yellow
                    } else {
                        api.url = api.url.green
                    }

                    if (api.ready == true) {
                        api.ready = 'true'.green
                    } else {
                        api.ready = 'false'.yellow
                    }
                }

                if (apiList.length>0) {
                    const table = new Table({
                        title: "APIs"
                    });
                    
                    table.addRows(apiList)
                    table.printTable();
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