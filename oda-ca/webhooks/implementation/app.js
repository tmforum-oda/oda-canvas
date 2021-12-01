var fs = require('fs');
var https = require('https');
var privateKey  = fs.readFileSync('/etc/secret-volume/tls.key', 'utf8');
var certificate = fs.readFileSync('/etc/secret-volume/tls.crt', 'utf8');

var credentials = {key: privateKey, cert: certificate};
var express = require('express');
var app = express();
app.use(express.json())    // <==== parse request body as JSON

// your express configuration here
var httpsServer = https.createServer(credentials, app);



app.post("/", (req, res, next) => {

  console.log(JSON.stringify(req.body, null, 2))
  var uid = req.body.request.uid;
  var desiredAPIVersion = req.body.request.desiredAPIVersion;
  var objectsArray = req.body.request.objects

  for (var key in objectsArray) {
    objectsArray[key].metadata.annotations.webhookconverted = "Webhook converted From " + objectsArray[key].apiVersion + " to " + desiredAPIVersion;
    console.log('Comparing old version ' + objectsArray[key].apiVersion + ' and desired version ' + desiredAPIVersion);
    if ((["oda.tmforum.org/v1alpha3", "oda.tmforum.org/v1alpha4"].includes(objectsArray[key].apiVersion)) && (["oda.tmforum.org/v1alpha2", "oda.tmforum.org/v1alpha1"].includes(desiredAPIVersion))) {
      console.log("convert dependentAPIs to dependantAPIs")
      if (objectsArray[key].spec.coreFunction.dependentAPIs) {
        console.log("converting ")
        objectsArray[key].spec.coreFunction.dependantAPIs = objectsArray[key].spec.coreFunction.dependentAPIs;
        delete objectsArray[key].spec.coreFunction.dependentAPIs
      }
    }
    if ((["oda.tmforum.org/v1alpha2", "oda.tmforum.org/v1alpha1"].includes(objectsArray[key].apiVersion)) && (["oda.tmforum.org/v1alpha3", "oda.tmforum.org/v1alpha4"].includes(desiredAPIVersion))) {
      console.log("convert depandantAPIs to dependentAPIs")
      if (objectsArray[key].spec.coreFunction.dependantAPIs) {
        console.log("converting ")
        objectsArray[key].spec.coreFunction.dependentAPIs = objectsArray[key].spec.coreFunction.dependantAPIs;
        delete objectsArray[key].spec.coreFunction.dependantAPIs
      }
    }

    objectsArray[key].apiVersion = desiredAPIVersion;
  }

    var response = {
        "apiVersion": "apiextensions.k8s.io/v1beta1",
        "kind": "ConversionReview",
        "response": {
          "uid": uid, // must match <request.uid>
          "result": {
            "status": "Success"
          },  
        "convertedObjects": objectsArray 
        }  
    }
    console.log(JSON.stringify(response, null, 2))


/* 
    {
        "apiVersion": "apiextensions.k8s.io/v1",
        "kind": "ConversionReview",
        "response": {
          # must match <request.uid>
          "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
          "result": {
            "status": "Success"
          },
          # Objects must match the order of request.objects, and have apiVersion set to <request.desiredAPIVersion>.
          # kind, metadata.uid, metadata.name, and metadata.namespace fields must not be changed by the webhook.
          # metadata.labels and metadata.annotations fields may be changed by the webhook.
          # All other changes to metadata fields by the webhook are ignored.
          "convertedObjects": [
            {
              "kind": "CronTab",
              "apiVersion": "example.com/v1",
              "metadata": {
                "creationTimestamp": "2019-09-04T14:03:02Z",
                "name": "local-crontab",
                "namespace": "default",
                "resourceVersion": "143",
                "uid": "3415a7fc-162b-4300-b5da-fd6083580d66"
              },
              "host": "localhost",
              "port": "1234"
            },
            {
              "kind": "CronTab",
              "apiVersion": "example.com/v1",
              "metadata": {
                "creationTimestamp": "2019-09-03T13:02:01Z",
                "name": "remote-crontab",
                "resourceVersion": "12893",
                "uid": "359a83ec-b575-460d-b553-d859cedde8a0"
              },
              "host": "example.com",
              "port": "2345"
            }
          ]
        }
      }
     */
    //console.log(JSON.stringify(response, null, 2))
    res.json(response);
   });

app.get("/", (req, res, next) => {
  var response = {
      "test": "success"
  }
  res.json(response);
  });

     
httpsServer.listen(8443, () => {
  console.log("Server running on port 8443");
 });
