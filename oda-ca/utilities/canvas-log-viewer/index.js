const k8s = require('@kubernetes/client-node');
var treeify = require('treeify');
const colors = require('colors');
const stream = require('stream');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const argv = process.argv
const targetComponent = argv[2]
const canvasOperator = argv[3]

const log = new k8s.Log(kc);

const logStream = new stream.PassThrough();
var logTreeObject = {}

var myListener = newLineStream( function (message) {
    // console.log(message)
    var matches = message.match(/(?<=\[)[^\][]*(?=])/g);
    if (!matches) {
        return
    }
    dateStamp = matches[0]
    type = matches[1].trim()
    var messageList = message.split(']')
    message = messageList[messageList.length-1].trim()
    var controller = messageList[1].split('[')[0].trim()
    if (matches.length == 3) {
        labelsList = matches[2].split('|')
        if (controller == 'kopf.objects') {
            resourceName = labelsList[1]
            componentName = 'Unknown'
            handlerName = 'Unknown'
            functionName = 'Unknown'
            } else {
            componentName = labelsList[0]
            resourceName = labelsList[1]
            handlerName = labelsList[2]
            functionName = labelsList[3]    
        }
    } else {
        componentName = 'Unknown'
        resourceName = 'Unknown'
        handlerName = 'Unknown'
        functionName = 'Unknown'
    }
    // console.log('controller:', controller);
    // console.log('dateStamp:', dateStamp);
    // console.log('type:', type);
    // console.log('resourceName:', resourceName);
    // console.log('namespace:', namespace);
    // console.log('functionName:', functionName);
    
    if (type == 'INFO') {
        message = message.green
    } else if (type == 'ERROR') {
        message = message.red
    } else if (type == 'WARNING') {
        message = message.yellow
    }
    message = dateStamp.gray + ' ' + functionName + ": " + message

    if (targetComponent == componentName) {
        if (logTreeObject.hasOwnProperty(resourceName)) {
            if (logTreeObject[resourceName].hasOwnProperty(controller)) {
                if (logTreeObject[resourceName][controller].hasOwnProperty(handlerName)) {
                    logTreeObject[resourceName][controller][handlerName].push(message)
                } else {
                    logTreeObject[resourceName][controller][handlerName] = [message]
                }
            } else {
                logTreeObject[resourceName][controller] = {}
                logTreeObject[resourceName][controller][handlerName] = [message]
            }
        } else {
            logTreeObject[resourceName] = {}
            logTreeObject[resourceName][controller] = {}
            logTreeObject[resourceName][controller][handlerName] = [message]
        }
        consoleLogTree()
    }

});

// add listener to "data" event
logStream.on('data', myListener);

log.log('canvas', canvasOperator, 'oda-controller-ingress', logStream, {follow: true, tailLines: 500, pretty: false, timestamps: false})
.catch(err => {
        console.log(err);
        process.exit(1);
})
.then(req => {
    /*
	// disconnects after 5 seconds
	if (req) {
		setTimeout(function(){
            consoleLogTree()
			req.abort();
		}, 5000);
	} */
});


function consoleLogTree() {

    console.clear()
    console.log('')
    console.log('')
    console.log('')
    console.log('')
    console.log('')
    console.log('=================================================')
    console.log('===           ODA Canvas Log Viewer           ===')
    console.log('=================================================')
    console.log('')

    console.log( treeify.asTree(logTreeObject, true))
}
// returns a function that spits out messages to a callback 
// function; those messages have been split by newline
function newLineStream(callback) {
	var buffer = '';
	return (function (chunk) {
		var i = 0, piece = '', offset = 0;
		buffer += chunk;
		while ( (i = buffer.indexOf('\n', offset)) !== -1) {
			piece = buffer.substr(offset, i - offset);
			offset = i + 1;
			callback(piece);
		}
		buffer = buffer.substr(offset);
	});
} // newLineStream






/*// get namespace from Environment variable or command-line
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
*/

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
