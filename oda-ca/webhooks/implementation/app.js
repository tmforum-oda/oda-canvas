/* 

Webhook to automatically convert between versions for the Component CRD
The Webhook receives a POST request containing a ConversionReview resource.
It returns an updated ConversionReview resource with the converted object

Example response:
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

var fs = require('fs');
var https = require('https');
var http = require('http');
var express = require('express');
var app = express();
app.use(express.json())    // <==== parse request body as JSON
var httpsServer, httpServer;

// get command line arguments
var args = process.argv.slice(2);

// the first argument shows if we are in test mode or not
var testMode = args[0] === 'test';

if (testMode) {
    console.log('Running in test mode');
    var httpServer = http.createServer(app);

} else {
    console.log('Running in production mode');
    var privateKey  = fs.readFileSync('/etc/secret-volume/tls.key', 'utf8');
    var certificate = fs.readFileSync('/etc/secret-volume/tls.crt', 'utf8');
    var credentials = {key: privateKey, cert: certificate};
    var httpsServer = https.createServer(credentials, app);
}

app.post("/", (req, res, next) => {

  console.log(JSON.stringify(req.body, null, 2))
  var uid = req.body.request.uid;
  var desiredAPIVersion = req.body.request.desiredAPIVersion;
  var objectsArray = req.body.request.objects

  for (var key in objectsArray) {

    // create APIVersion object based on objectsArray[key].apiVersion and desiredAPIVersion
    var apiVersion = new APIVersion(objectsArray[key].apiVersion, desiredAPIVersion);

    objectsArray[key].metadata.annotations.webhookconverted = "Webhook converted From " + objectsArray[key].apiVersion + " to " + desiredAPIVersion;
    console.log('Comparing old version ' + objectsArray[key].apiVersion + ' and desired version ' + desiredAPIVersion);

    // if the oldAPIVersion is v1alpha3 or v1alpha4 and newVersion is v1alpha2 or v1alpha1 then convert dependentAPIs dependantAPIs
    if (apiVersion.mapOldToNew(["v1alpha3", "v1alpha4"], ["v1alpha2", "v1alpha1"])) {
      console.log("convert dependentAPIs to dependantAPIs")
      if (objectsArray[key].spec.coreFunction.dependentAPIs) {
        objectsArray[key].spec.coreFunction.dependantAPIs = objectsArray[key].spec.coreFunction.dependentAPIs;
        delete objectsArray[key].spec.coreFunction.dependentAPIs
      }
    }

    // if the oldAPIVersion is v1alpha2 or v1alpha1 and newVersion is v1alpha3 or v1alpha4 then convert dependantAPIs dependentAPIs
    if (apiVersion.mapOldToNew(["v1alpha2", "v1alpha1"], ["v1alpha3", "v1alpha4"])) {
      console.log("convert depandantAPIs to dependentAPIs")
      if (objectsArray[key].spec.coreFunction.dependantAPIs) {
        objectsArray[key].spec.coreFunction.dependentAPIs = objectsArray[key].spec.coreFunction.dependantAPIs;
        delete objectsArray[key].spec.coreFunction.dependantAPIs
      }
    }

    // if the oldAPIVersion is v1alpha1, v1alpha2, v1alpha3 or v1alpha4 and newVersion is v1beta1 then remove the componentKinds
    // and add dependentAPIs to the management and security segments
    if (apiVersion.mapOldToNew(["v1alpha1", "v1alpha2", "v1alpha3", "v1alpha4"], ["v1beta1"])) {
      console.log("remove componentKinds")
      if (objectsArray[key].spec.componentKinds) {
        delete objectsArray[key].spec.componentKinds
      }

      console.log("add dependentAPIs to management segment")
      managementArray = objectsArray[key].spec.management
      delete objectsArray[key].spec.management
      objectsArray[key].spec.management = {dependentAPIs: []}
      objectsArray[key].spec.management.exposedAPIs = managementArray

      console.log("add dependentAPIs to security segment")
      objectsArray[key].spec.security.dependentAPIs = []
      objectsArray[key].spec.security.exposedAPIs = []

      if (objectsArray[key].spec.security.partyrole) {
        console.log("move the partyrole to the exposedAPIs")
        // add the partyrole to the exposedAPIs
        objectsArray[key].spec.security.partyrole.name = "partyrole"
        objectsArray[key].spec.security.exposedAPIs.push(objectsArray[key].spec.security.partyrole)
        delete objectsArray[key].spec.security.partyrole
      }
    }

    // if the oldAPIVersion is v1beta1 and newVersion is v1alpha1, v1alpha2, v1alpha3 or v1alpha4 then add the componentKinds
    // and remove dependentAPIs from the management and security segments
    if (apiVersion.mapOldToNew(["v1beta1"], ["v1alpha1", "v1alpha2", "v1alpha3", "v1alpha4"])) {
      console.log("add componentKinds")
      objectsArray[key].spec.componentKinds = []

      console.log("remove dependentAPIs from management segment")
      managementArray = objectsArray[key].spec.management.exposedAPIs
      delete objectsArray[key].spec.management
      objectsArray[key].spec.management = managementArray

      // find the partyrole in the exposedAPIs and add it to the security
      for (var i = 0; i < objectsArray[key].spec.security.exposedAPIs.length; i++) {
        if (objectsArray[key].spec.security.exposedAPIs[i].name === "partyrole") {
          console.log("move the partyrole from the exposedAPIs")
          objectsArray[key].spec.security.partyrole = objectsArray[key].spec.security.exposedAPIs[i]
        }
      }
      delete objectsArray[key].spec.security.exposedAPIs

      console.log("remove dependentAPIs from security segment")
      delete objectsArray[key].spec.security.dependentAPIs
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

    res.json(response);
   });

app.get("/", (req, res, next) => {
  var response = {
      "test": "success"
  }
  res.json(response);
  });

if (testMode) {
  httpServer.listen(8002, () => {
    console.log("Server running on port 8002");
   });
  } else {
  httpsServer.listen(8443, () => {
    console.log("Server running on port 8443");
    });
  }

     
// Class to capture the old and new API versions
class APIVersion {
  constructor(oldAPIVersion, newAPIVersion) {
    this.oldAPIVersion = oldAPIVersion.split('/')[1]; // only use the version part of the API version i.e. remove ''
    this.newAPIVersion = newAPIVersion.split('/')[1];
  }

  // test if array of oldAPIVersions contains the oldAPIVersion and array of newAPIVersions contains the newAPIVersion
  mapOldToNew(oldAPIVersionList, newAPIVersionList) {
    if (oldAPIVersionList.includes(this.oldAPIVersion) && newAPIVersionList.includes(this.newAPIVersion)) {
      return true;
    } else {
      return false;
    }
  }
}

