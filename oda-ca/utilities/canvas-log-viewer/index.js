const k8s = require('@kubernetes/client-node');
var treeify = require('treeify');
const colors = require('colors');
const stream = require('stream');
const { exit } = require('process');

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

console.log('=================================================')
console.log('===           ODA Canvas Log Viewer           ===')
console.log('=================================================')

const argv = process.argv
const targetComponent = argv[2]
const canvasOperator = argv[3]

console.log('targetComponent:', targetComponent)
console.log('canvasOperator:', canvasOperator)

if (!targetComponent || !canvasOperator) {
    console.log('Usage: node index.js <targetComponent> <canvasOperatorPod>')
    exit(1)
}

const log = new k8s.Log(kc);

const logStream = new stream.PassThrough();
var logTreeObject = {}

var myListener = newLineStream( function (inMessage) {
    // console.log(message)
    var matches = inMessage.match(/(?<=\[)[^\][]*(?=])/g);
    if (!matches) {
        return
    }
    dateStamp = matches[0]
    try {  // try to parse the message

        type = matches[1].trim()
        var messageList = inMessage.split(']')
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
    } catch (error) {
        console.log('dateStamp:', dateStamp)
        console.log('type:', matches[1])
        console.log('message:', inMessage)
        componentName = 'Unknown'
        resourceName = 'Unknown'
        handlerName = 'Unknown'
        functionName = 'Unknown'  
        type == 'ERROR'
        message = inMessage
    }  
    
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


