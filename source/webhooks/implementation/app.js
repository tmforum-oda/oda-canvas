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

const supportedAPIVersions = ["oda.tmforum.org/v1beta1", "oda.tmforum.org/v1beta2", "oda.tmforum.org/v1beta3", "oda.tmforum.org/v1beta4"]

// reference data to support functional block mapping
const PartyManagementComponents = ["TMFC020", "TMFC022", "TMFC023", "TMFC024", "TMFC025"]
const CoreCommerceComponents = ["TMFC001", "TMFC002", "TMFC003", "TMFC005", "TMFC027"]
const ProductionComponents = ["TMFC006", "TMFC007", "TMFC008", "TMFC009", "TMFC010", "TMFC010", "TMFC011", "TMFC012", "TMFC013", "TMFC014", "TMFC015"]


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
  try {
    var uid = req.body.request.uid;
    var desiredAPIVersion = req.body.request.desiredAPIVersion;
    var conversionReviewAPIVersion = req.body.apiVersion;
    var objectsArray = req.body.request.objects

    for (var key in objectsArray) {

      var currentAPIVersion = objectsArray[key].apiVersion

      // test if the currentAPIVersion is in the list of supported versions
      if (!supportedAPIVersions.includes(currentAPIVersion)) {
        throw new Error("The current API version " + currentAPIVersion + " is not supported")
      }
      // test if the desiredAPIVersion is in the list of supported versions
      if (!supportedAPIVersions.includes(desiredAPIVersion)) {
        throw new Error("The desired API version " + desiredAPIVersion + " is not supported")
      }

      // create APIVersion object based on objectsArray[key].apiVersion and desiredAPIVersion
      var apiVersion = new APIVersion(currentAPIVersion, desiredAPIVersion);

      objectsArray[key].metadata.annotations = objectsArray[key].metadata.annotations || {};
      objectsArray[key].metadata.annotations.webhookconverted = "Webhook converted From " + currentAPIVersion + " to " + desiredAPIVersion;
      console.log('Comparing old version ' + currentAPIVersion + ' and desired version ' + desiredAPIVersion);


      // ****************************************************
      // upgrade previous versions to the latest versions
      // ****************************************************

      // if the oldAPIVersion is v1beta1 and newVersion is v1beta2 or v1beta3 or v1beta4 then:
      // - add the metadata for functionalBlock
      // - rename security and management segments to securityFunction and managementFunction
      // - split type into two fields id and name
      if (apiVersion.mapOldToNew(["v1beta1"], ["v1beta2", "v1beta3", "v1beta4"])) {

        console.log("rename security and management segments to securityFunction and managementFunction")
        objectsArray[key].spec.managementFunction = objectsArray[key].spec.management
        delete objectsArray[key].spec.management
        objectsArray[key].spec.securityFunction = objectsArray[key].spec.security
        delete objectsArray[key].spec.security

        console.log("split type into two fields id and name")
        objectsArray[key].spec.id = objectsArray[key].spec.type.split('-')[0]
        objectsArray[key].spec.name = objectsArray[key].spec.type.split('-')[1]
        delete objectsArray[key].spec.type

        console.log("add the metadata for functionalBlock")
        if (!objectsArray[key].spec.functionalBlock) {
          if (CoreCommerceComponents.includes(objectsArray[key].spec.id)) {
            objectsArray[key].spec.functionalBlock = 'CoreCommerce'
          } else if (PartyManagementComponents.includes(objectsArray[key].spec.id)) {
            objectsArray[key].spec.functionalBlock = 'PartyManagement'
          } else if (ProductionComponents.includes(objectsArray[key].spec.id)) {
            objectsArray[key].spec.functionalBlock = 'Production'
          } else {
            objectsArray[key].spec.functionalBlock = 'Unknown'
          }
        }
      }

      // update the eventNotification segments and change exposedAPI specification to an array of 1 and apitype to apiType
      if (apiVersion.mapOldToNew(["v1beta1", "v1beta2"], ["v1beta3", "v1beta4"])) {
        console.log("Update eventNotification segments");
        
        if (objectsArray[key].spec.eventNotification) {
          if (objectsArray[key].spec.eventNotification.publishedEvents && 
            Array.isArray(objectsArray[key].spec.eventNotification.publishedEvents) && 
            objectsArray[key].spec.eventNotification.publishedEvents.length > 0
          ) {
            objectsArray[key].spec.eventNotification.publishedEvents.forEach(event => {
              try {
                var parts = new URL(event.href);
                delete event.href;
                event.description = "";
                event.apiType = "openapi";
                event.specification = "";
                event.implementation = parts.hostname;
                event.developerUI = "";
                event.hub = parts.pathname;
                event.port = parseInt(parts.port, 10) || 80;
              } catch (err) {
                console.log("EVENT PAYLOAD: " + JSON.stringify(event));
                console.log(err); 
              }
            })
          }

          if (objectsArray[key].spec.eventNotification.subscribedEvents && 
            Array.isArray(objectsArray[key].spec.eventNotification.subscribedEvents) && 
            objectsArray[key].spec.eventNotification.subscribedEvents.length > 0
          ) {
            objectsArray[key].spec.eventNotification.subscribedEvents.forEach(event => {
              try {
                var parts = new URL(event.href);
                delete event.href;
                event.description = "";
                event.apiType = "openapi";
                event.specification = "";
                event.implementation = parts.hostname;
                event.developerUI = "";
                event.callback = parts.pathname;
                event.port = parseInt(parts.port, 10) || 80;
                event.query = "";
              } catch (err) {
                console.log("EVENT PAYLOAD: " + JSON.stringify(event));
                console.log(err); 
              }
            })
          }
        }

        console.log("Change exposedAPI specification to an array of 1 and apitype to apiType");
        for (api in objectsArray[key].spec.coreFunction.exposedAPIs) {
          if (objectsArray[key].spec.coreFunction.exposedAPIs[api].specification) {
            objectsArray[key].spec.coreFunction.exposedAPIs[api].specification = [objectsArray[key].spec.coreFunction.exposedAPIs[api].specification];
          }
          if (objectsArray[key].spec.coreFunction.exposedAPIs[api].apitype) {
            objectsArray[key].spec.coreFunction.exposedAPIs[api].apiType = objectsArray[key].spec.coreFunction.exposedAPIs[api].apitype;
            delete objectsArray[key].spec.coreFunction.exposedAPIs[api].apitype;
          }
        }
        for (api in objectsArray[key].spec.managementFunction.exposedAPIs) {
          if (objectsArray[key].spec.managementFunction.exposedAPIs[api].specification) {
            objectsArray[key].spec.managementFunction.exposedAPIs[api].specification = [objectsArray[key].spec.managementFunction.exposedAPIs[api].specification];
          }
          if (objectsArray[key].spec.managementFunction.exposedAPIs[api].apitype) {
            objectsArray[key].spec.managementFunction.exposedAPIs[api].apiType = objectsArray[key].spec.managementFunction.exposedAPIs[api].apitype;
            delete objectsArray[key].spec.managementFunction.exposedAPIs[api].apitype;
          }
        }
        for (api in objectsArray[key].spec.securityFunction.exposedAPIs) {
          if (objectsArray[key].spec.securityFunction.exposedAPIs[api].specification) {
            objectsArray[key].spec.securityFunction.exposedAPIs[api].specification = [objectsArray[key].spec.securityFunction.exposedAPIs[api].specification];
          } 
          if (objectsArray[key].spec.securityFunction.exposedAPIs[api].apitype) {
            objectsArray[key].spec.securityFunction.exposedAPIs[api].apiType = objectsArray[key].spec.securityFunction.exposedAPIs[api].apitype;
            delete objectsArray[key].spec.securityFunction.exposedAPIs[api].apitype;
          }
        }
      }

      // move the properties to componentMetadata
      if (apiVersion.mapOldToNew(["v1beta1", "v1beta2", "v1beta3"], ["v1beta4"])) {
        console.log("move relevant properties to componentMetadata");

        objectsArray[key].spec.componentMetadata = {};
        if (objectsArray[key].spec.id) {
          objectsArray[key].spec.componentMetadata.id = objectsArray[key].spec.id;
          delete objectsArray[key].spec.id;
        }
        if (objectsArray[key].spec.name) {
          objectsArray[key].spec.componentMetadata.name = objectsArray[key].spec.name;
          delete objectsArray[key].spec.name;
        }
        if (objectsArray[key].spec.version) {
          objectsArray[key].spec.componentMetadata.version = objectsArray[key].spec.version;
          delete objectsArray[key].spec.version;
        }
        if (objectsArray[key].spec.description) {
          objectsArray[key].spec.componentMetadata.description = objectsArray[key].spec.description;
          delete objectsArray[key].spec.description;
        }
        if (objectsArray[key].spec.functionalBlock) {
          objectsArray[key].spec.componentMetadata.functionalBlock = objectsArray[key].spec.functionalBlock;
          delete objectsArray[key].spec.functionalBlock;
        }
        if (objectsArray[key].spec.publicationDate) {
          objectsArray[key].spec.componentMetadata.publicationDate = objectsArray[key].spec.publicationDate;
          delete objectsArray[key].spec.publicationDate;
        }
        if (objectsArray[key].spec.status) {
          objectsArray[key].spec.componentMetadata.status = objectsArray[key].spec.status;
          delete objectsArray[key].spec.status;
        }
        if (objectsArray[key].spec.maintainers) {
          objectsArray[key].spec.componentMetadata.maintainers = objectsArray[key].spec.maintainers;
          delete objectsArray[key].spec.maintainers;
        }
        if (objectsArray[key].spec.owners) {
          objectsArray[key].spec.componentMetadata.owners = objectsArray[key].spec.owners;
          delete objectsArray[key].spec.owners;
        }
      }        
      
 
      
      // ****************************************************
      // downgrade newer versions to the older versions
      // ****************************************************
      // move the properties from componentMetadata and remove apiSDO
      if (apiVersion.mapOldToNew(["v1beta4"], ["v1beta1", "v1beta2", "v1beta3"])) {
        if (objectsArray[key].spec.componentMetadata) {
          // for each property in componentMetadata, move it to the root level
          console.log("Move properties from componentMetadata to root");

          for (var property in objectsArray[key].spec.componentMetadata) {
            objectsArray[key].spec[property] = objectsArray[key].spec.componentMetadata[property];
          }
          delete objectsArray[key].spec.componentMetadata;
        }    
        
        // for each of coreFunction, managementFunction and securityFunction, remove the apiSDO from exposedAPIs and dependentAPIs array items
        console.log("Remove the apiSDO from exposedAPIs and dependentAPIs array items in coreFunction, managementFunction and securityFunction");
        if (objectsArray[key].spec.coreFunction) {
          for (api in objectsArray[key].spec.coreFunction.exposedAPIs) {
            delete objectsArray[key].spec.coreFunction.exposedAPIs[api].apiSDO;
          }
          for (api in objectsArray[key].spec.coreFunction.dependentAPIs) {
            delete objectsArray[key].spec.coreFunction.dependentAPIs[api].apiSDO;
          }
        }
        if (objectsArray[key].spec.managementFunction) {
          for (api in objectsArray[key].spec.managementFunction.exposedAPIs) {
            delete objectsArray[key].spec.managementFunction.exposedAPIs[api].apiSDO;
          }
          for (api in objectsArray[key].spec.managementFunction.dependentAPIs) {
            delete objectsArray[key].spec.managementFunction.dependentAPIs[api].apiSDO;
          }
        }
        if (objectsArray[key].spec.securityFunction) {
          for (api in objectsArray[key].spec.securityFunction.exposedAPIs) {
            delete objectsArray[key].spec.securityFunction.exposedAPIs[api].apiSDO;
          }
          for (api in objectsArray[key].spec.securityFunction.dependentAPIs) {
            delete objectsArray[key].spec.securityFunction.dependentAPIs[api].apiSDO;
          }
        }
      }  

      // change the eventNotification segments and change exposedAPI specification from an array to string
      if (apiVersion.mapOldToNew(["v1beta3", "v1beta4"], ["v1beta1", "v1beta2"])) {
        if (objectsArray[key].spec.eventNotification) {
          if (objectsArray[key].spec.eventNotification.publishedEvents && 
            Array.isArray(objectsArray[key].spec.eventNotification.publishedEvents) && 
            objectsArray[key].spec.eventNotification.publishedEvents.length > 0
          ) {
            objectsArray[key].spec.eventNotification.publishedEvents.forEach(event => {
              event.href = "http://" + event.implementation + ":" + event.port + event.hub;
              delete event.description;
              delete event.apitype;
              delete event.specification;
              delete event.implementation;
              delete event.developerUI;
              delete event.hub;
              delete event.port;
            })
          }

          if (objectsArray[key].spec.eventNotification.subscribedEvents && 
            Array.isArray(objectsArray[key].spec.eventNotification.subscribedEvents) && 
            objectsArray[key].spec.eventNotification.subscribedEvents.length > 0
          ) {
            objectsArray[key].spec.eventNotification.subscribedEvents.forEach(event => {
              event.href = "http://" + event.implementation + ":" + event.port + event.callback;
              delete event.description;
              delete event.apitype;
              delete event.specification;
              delete event.implementation;
              delete event.developerUI;
              delete event.callback;
              delete event.port;
              delete event.query;
            })
          }
        }

        console.log("Change exposedAPI specification from an array of 1 to a string and apiType to apitype");
        for (api in objectsArray[key].spec.coreFunction.exposedAPIs) {
          if ((objectsArray[key].spec.coreFunction.exposedAPIs[api].specification ) && (objectsArray[key].spec.coreFunction.exposedAPIs[api].specification.length > 0)) {
            objectsArray[key].spec.coreFunction.exposedAPIs[api].specification = objectsArray[key].spec.coreFunction.exposedAPIs[api].specification[0];
          }
          if (objectsArray[key].spec.coreFunction.exposedAPIs[api].apiType) {
            objectsArray[key].spec.coreFunction.exposedAPIs[api].apitype = objectsArray[key].spec.coreFunction.exposedAPIs[api].apiType;
            delete objectsArray[key].spec.coreFunction.exposedAPIs[api].apiType;
          }
        }

        for (api in objectsArray[key].spec.managementFunction.exposedAPIs) {
          if ((objectsArray[key].spec.managementFunction.exposedAPIs[api].specification ) && (objectsArray[key].spec.managementFunction.exposedAPIs[api].specification.length > 0)) {
            objectsArray[key].spec.managementFunction.exposedAPIs[api].specification = objectsArray[key].spec.managementFunction.exposedAPIs[api].specification[0];
          }
          if (objectsArray[key].spec.managementFunction.exposedAPIs[api].apiType) {
            objectsArray[key].spec.managementFunction.exposedAPIs[api].apitype = objectsArray[key].spec.managementFunction.exposedAPIs[api].apiType;
            delete objectsArray[key].spec.managementFunction.exposedAPIs[api].apiType;
          }
        }

        for (api in objectsArray[key].spec.securityFunction.exposedAPIs) {
          if ((objectsArray[key].spec.securityFunction.exposedAPIs[api].specification ) && (objectsArray[key].spec.securityFunction.exposedAPIs[api].specification.length > 0)) {
            objectsArray[key].spec.securityFunction.exposedAPIs[api].specification = objectsArray[key].spec.securityFunction.exposedAPIs[api].specification[0];
          }
          if (objectsArray[key].spec.securityFunction.exposedAPIs[api].apiType) {
            objectsArray[key].spec.securityFunction.exposedAPIs[api].apitype = objectsArray[key].spec.securityFunction.exposedAPIs[api].apiType;
            delete objectsArray[key].spec.securityFunction.exposedAPIs[api].apiType;
          }
        }    
      }  

      // if the oldAPIVersion is v1beta2, v1beta3, v1beta4 and newVersion is v1beta1 then:
      // - remove the metadata for functionalBlock
      // - rename securityFunction and managementFunction segments to security and management  
      // - join id and name fields to create type 
      if (apiVersion.mapOldToNew(["v1beta2", "v1beta3", "v1beta4"], ["v1beta1"])) {
        console.log("rename securityFunction and managementFunction segments to security and management")
        objectsArray[key].spec.management = objectsArray[key].spec.managementFunction
        delete objectsArray[key].spec.managementFunction
        objectsArray[key].spec.security = objectsArray[key].spec.securityFunction
        delete objectsArray[key].spec.securityFunction

        console.log("join id and name fields to create type")
        objectsArray[key].spec.type = objectsArray[key].spec.id + '-' + objectsArray[key].spec.name
        delete objectsArray[key].spec.id
        delete objectsArray[key].spec.name
        
        console.log("remove the metadata for functionalBlock")
        delete objectsArray[key].spec.functionalBlock
      }   
      
      objectsArray[key].apiVersion = desiredAPIVersion;
    }

      var response = {
          "apiVersion": conversionReviewAPIVersion,
          "kind": "ConversionReview",
          "response": {
            "uid": uid, // must match <request.uid>
            "result": {
              "status": "Success"
            },  
          "convertedObjects": objectsArray 
          }  
      }
      // console.log(JSON.stringify(response, null, 2))

      res.json(response);
  } catch (error) {
    console.log("");
    console.log("--------------------------------------------------------------");
    console.log("Error converting from ", currentAPIVersion, " to ",  desiredAPIVersion)
    console.log("trying to convert object:");
    console.log(objectsArray[key].spec)
    console.log("");
    console.log("Error message:");
    console.log(error);
    console.log("--------------------------------------------------------------");
    console.log("");

    var response = {
      "apiVersion": conversionReviewAPIVersion,
      "kind": "ConversionReview",
      "response": {
        "uid": uid, // must match <request.uid>
        "result": {
          "status": "Failure",
          "message": error.message
        }
      }
    }
    res.json(response);
    }
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

