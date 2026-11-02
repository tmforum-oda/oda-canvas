# Component-Registry

The Component-Registry maintains a state of the deployed ODA Components and Exposed APIs of an ODA Canvas.
Its purpose is to serve as an inventory which allows resolving API dependencies between ODA Components.

It is also prepared to support Multi-Canvas scenarios, where an upstream Component-Registry allows resolving dependencies between different ODA Canvas installations.
 


## Prerequisites

ODA Canvas is installed with default values.  
(compreg not yet released. So, install from main branch is neccessary)


## Port-Forward Component-Registry UI

to access the UI of the Component-Registry a port-forwarding (or any other kind of ingress) has to be established to make the UI accessible:

```
kubectl port-forward -n canvas svc/canvas-compreg 8080:80
```

Now the UI can be opened in a Browser:

http://localhost:8080

<kbd><img src="images/compreg-01-empty.png" alt="Empty Component-Registry" height="500" /></kbd>


## Deploy ODA Component r-cat

From the BDD tests we can deploy the Retail-Catalog "r-cat": 

```
helm upgrade --install r-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-v1
```

After a few seconds the UI shows the new ODA Component r-cat together with its exposed APIs:

<kbd><img src="images/compreg-02-r-cat.png" alt="r-cat" /></kbd>


### Exposed API Information

In the column "Exposed APIs" additional info for each endpoint is shown.

The name of the Exposed API is a link which can be clicked and shows the raw TMF-639 data for this endpoint in the same way as clicking on "View Details" in the endpoint list below.

<table>

<tr><td><img src="images/button-openapi.png" alt="openapi" height="18" /></td>
<td>The exposed API is of format Open-Api. Clicking on the icon will open the link in a new tab.</td></tr>

<tr><td><img src="images/button-prometheus.png" alt="prometheus" height="18" /></td>
<td>The exposed API is of format Prometheus for scraping metrics.</td></tr>

<tr><td></td>
<td></td></tr>

<tr><td><img src="images/button-url.png" alt="URL" height="18" /></td>
<td>URL to the API endpoint. Klicking the icon opens the URL in a new tab.</td></tr>

<tr><td><img src="images/button-dev-ui.png" alt="Dev UI" height="18" /></td>
<td>URL to the Swagger UI. Klicking the icon opens the Swagger UI in a new tab.</td></tr>

<tr><td><img src="images/button-available.png" alt="available" height="18" /></td>
<td>Shows thet the Exposed API is available. If unavailable a red icon is shown.</td></tr>

</table>

As we can see, r-cat is exposing the Open-API `https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.0.swagger.json`.


## Resolve a Dependent-API

Next we want to see how dependency resolution works in the ODA Canvas.

Therefore we deploy another ODA Component "f-cat" which has a dependency to the exposed API of "r-cat":

```
helm upgrade --install f-cat -n components --create-namespace feature-definition-and-test-kit/testData/productcatalog-dependendent-API-v1
```

To see the dependency resolution we look into the logfile of the Depent-API Operator logs:

```
kubectl logs -n canvas deployment/canvas-depapi-op
```

As this is hard to read we can also use the pretty printed output of the [kubectl canvaslogs plugin](/source/utilities/canvas-log-viewer/python_alternative/README.md): 

```
kubectl canvaslogs depapi
```

<kbd><img src="images/depapi-log.png" alt="Dependent API Operator log" /></kbd>


In the red marked block we can see that the Dependant-API Operator contacted the cluster local Component-Registry 
and got one matching endpoint r-cat-productcatalogmanagement.

We can see the details in the DependentAPI custom resource:
 

```
$ kubectl get DependentAPI -n components   # or shorter: kubectl get depapi -n components

NAME                                                         READY   AGE   SVCINVID
URL
f-cat-productcatalogmanagement-downstreamproductcatalog-v4   true    38m   64c513db-2fb1-42b5-9fdb-cb60024fe2e5
https://11.22.33.44/r-cat-productcatalogmanagement/tmf-api/productCatalogManagement/v4
```

# Multi-Canvas Support

The Component-Registry supports replication to an upstream Component-Registry.
This allows a setup where multiple ODA Canvas instances replicate there exposed APIs
into a central Component-Registry. For our scenario it looks like this:

<kbd><img src="images/BDD-UC007-F002-Multicanvas.png" alt="Multi-Canvas Scenario" /></kbd>

