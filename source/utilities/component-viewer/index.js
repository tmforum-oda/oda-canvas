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
        console.log('Displays the status of ODA Components deployed in the kubernetes cluster (based on kubeconfig). By default it uses the `components` namespace. Alternative namespace can be set with NAMESPACE environment variable or -n <namespace>. ')
        console.log('')
        process.exit(0)
    }
  });

displayComponentTree()

async function displayComponentTree() {

    try {
        const customk8sApi = kc.makeApiClient(k8s.CustomObjectsApi);

        // check the connected Kuberenets cluster has the components CRD installed
        const res = await customk8sApi.listClusterCustomObject('apiextensions.k8s.io', 'v1', 'customresourcedefinitions')

        const crds = res.body.items;
        const crdExists = crds.some(crd => crd.spec.names.plural === 'components');

        if (!crdExists) {
            console.log(`Components Custom Resource Definition does not exist. Check your canvas installation.`.red);
            process.exit(1);
        }
        const crd = crds.find(crd => crd.spec.names.plural === 'components');
        const storedVersions = crd.status.storedVersions;
        const mostRecentVersion = storedVersions[storedVersions.length - 1];
        console.log(`Using Components Custom Resource Definition: ${mostRecentVersion}`);

        customk8sApi.listNamespacedCustomObject('oda.tmforum.org', mostRecentVersion, namespace, 'components').then((res) => {
            
            for (var key in res.body.items) {
                var componentInstance = res.body.items[key]
                console.log('')
                console.log('')
                console.log('Component: %s'.gray, componentInstance.metadata.name.white)
                console.log('Namespace: %s'.gray, namespace.white)

                var deployment_status = 'Starting'
                if (componentInstance.hasOwnProperty('status')) {
                    if (componentInstance.status.hasOwnProperty('summary/status')) {
                        deployment_status = componentInstance.status['summary/status'].deployment_status
                    } 
                }
                if (deployment_status == "Starting") {
                    console.log('Deployment Status: %s'.gray, deployment_status.yellow, ': Component controller not started processing yet'.yellow)
                }
                if (deployment_status == "Complete") {
                    console.log('Deployment Status: %s'.gray, deployment_status.green)
                }
                else if (deployment_status == "In-Progress-CompCon") {
                    console.log('Deployment Status: %s'.gray, deployment_status.yellow, ': Component controller configuring APIs'.yellow)
                }
                else if (deployment_status == "In-Progress-SecCon") {
                    console.log('Deployment Status: %s'.gray, deployment_status.yellow, ': Component controller configuring Identity Management'.yellow)
                }
                else {
                    console.log('Deployment Status: %s'.gray, 'Unknown'.red)
                }

                var TroubleshootingText = createTroubleshootingText(deployment_status, componentInstance)
                var apiObj = {}
                if (componentInstance.hasOwnProperty('status')) {
                    // console.log(componentInstance.status)
                    if (componentInstance.status.hasOwnProperty('coreAPIs')) {
                        if (componentInstance.status.coreAPIs.length > 0) {
                            apiObj['coreFunction'.gray] = formatTreeObject(componentInstance.status.coreAPIs)
                        }
                    }
                    if (componentInstance.status.hasOwnProperty('managementAPIs')) {
                        if (componentInstance.status.managementAPIs.length > 0) {
                            apiObj['managementFunction'.gray] = formatTreeObject(componentInstance.status.managementAPIs)
                        }
                    }
                    if (componentInstance.status.hasOwnProperty('securityAPIs')) {
                        if (Object.keys(componentInstance.status.securityAPIs).length > 0) {
                            apiObj['securityFunction'.gray] = formatTreeObject(componentInstance.status.securityAPIs)
                        }
                    }
                }

                treeObj = {}
                if (Object.keys(apiObj).length>0) {
                    treeObj['APIs'.gray] = apiObj
                }
                if (componentInstance.status.hasOwnProperty('security_client_add/status.summary/status.deployment_status')) {
                    treeObj['Identity Management'.gray] = {}
                    if (componentInstance.status['security_client_add/status.summary/status.deployment_status'].hasOwnProperty('identityProvider')) {
                        treeObj['Identity Management'.gray]['identityProvider'] = componentInstance.status['security_client_add/status.summary/status.deployment_status']['identityProvider'].blue
                    }
                    if (componentInstance.status['security_client_add/status.summary/status.deployment_status'].hasOwnProperty('listenerRegistered')) {
                        if (componentInstance.status['security_client_add/status.summary/status.deployment_status'].listenerRegistered == true) {
                            treeObj['Identity Management'.gray]['status'] = 'registered'.green
                        }
                    }                    
                    // if (componentInstance.status['security_client_add/status.summary/status.deployment_status'].hasOwnProperty('identityProvider')) {
                
                }
                console.log( treeify.asTree(treeObj, true) )
                console.log('')

                if (TroubleshootingText) {
                    console.log(TroubleshootingText)
                }
            }
            if (res.body.items.length == 0) {
                console.log('No ODA Components to view in namespace %s', namespace)
            }
        });
    } 
    catch (err) {
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

function createTroubleshootingText(deployment_status, componentInstance) {

    var TroubleshootingText = ''
    if (deployment_status == "In-Progress-CompCon") {
        // check that all the APIs have a valid url
        TroubleshootingText += 'Troubleshooting: '.grey + 'Component controller is still configuring APIs.'.yellow + '\n'
        var allAPIsHaveURL = true
        for (var key in componentInstance.status.coreAPIs) {
            if (!componentInstance.status.coreAPIs[key].url) {
                allAPIsHaveURL = false
            }
        }
        for (var key in componentInstance.status.managementAPIs) {
            if (!componentInstance.status.managementAPIs[key].url) {
                allAPIsHaveURL = false
            }
        }
        for (var key in componentInstance.status.securityAPIs) {
            if (!componentInstance.status.securityAPIs[key].url) {
                allAPIsHaveURL = false
            }
        }
        
        if (!allAPIsHaveURL) {
            TroubleshootingText +='Troubleshooting: '.grey + 'Not all APIs have a valid URL. If this problem persists, check the '.yellow + 'api.oda.tmforum.org' + ' custom resource and the configuration of any Service Mesh and/or API Gateway that is being used.'.yellow + '\n'
        }

        // check that all the APIs are ready
        var allAPIsAreReady = true
        for (var key in componentInstance.status.coreAPIs) {
            if (!componentInstance.status.coreAPIs[key].ready) {
                allAPIsAreReady = false
            }
        }
        for (var key in componentInstance.status.managementAPIs) {
            if (!componentInstance.status.managementAPIs[key].ready) {
                allAPIsAreReady = false
            }
        }
        for (var key in componentInstance.status.securityAPIs) {
            if (!componentInstance.status.securityAPIs[key].ready) {
                allAPIsAreReady = false
            }
        }

        if (!allAPIsAreReady) {
            TroubleshootingText += 'Troubleshooting: '.grey + 'Not all APIs are ready. If this problem persists, check Pods that are implementing the API. Check they are ready to receive HTTP traffic at the configured port.'.yellow + '\n'
        }
    }  

    if (deployment_status == "In-Progress-SecCon") {
        // check that all the APIs have a valid url
        TroubleshootingText += 'Troubleshooting: '.grey + 'Component controller is still configuring Identity Management.'.yellow + '\n'
        TroubleshootingText += 'Troubleshooting: '.grey + 'If this problem persists, check the confurigation of the Identity Management system and the logs of the Component Controller.'.yellow + '\n'        
    }
    
    return TroubleshootingText
}