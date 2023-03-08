# API Operator for Istio/Prometheus - Introduction

This **API operator** for is designed to manage a Canvas environment that incluides the Istio Service Mesh as well as Prometheus monitoring and act as a reference implementation of an API Operator. In other canvas environment, (with a different combination of Service Mesh/API Gateway/Monitoring solution) the SRE (Site Reliability Engineering) team would need to write their own API Operator.

Both **Istio** and **Prometheus** can be configured using Kubernetes Custom Resource Definitions (CRD). The API Operators for Istio and Prometheus use the Kubernetes API to listen for changes to the CRDs and then configures Istio and Prometheus accordingly.

Istio uses `VirtualService` resources (https://istio.io/latest/docs/reference/config/networking/virtual-service/) to configure traffic routing in the Istio control plane.

Prometheus uses `ServiceMonitor` resources (https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md) to configure the Prometheus monitoring system.

This makes the logic required to create an API Operator relatively simple. The API Operator listens for new/updated/deleted `oda.tmforum.org/API` resources and then creates/updates/deletes the corresponding Virtual Service and Service Monitor resources. The API Operator also listens for status updates from Istio and Prometheus and updates the status of the `oda.tmforum.org/API` resource accordingly.

![API Operator](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-ca/master/controllers/apiOperatorIstio/sequenceDiagrams/apiOperatorIstio.puml)
[plantUML code](sequenceDiagrams/apiOperatorIstio.puml)


## Istio configuration

Your kubernetes environment will need to have the Istio Service Mesh deployed and have a `gateway` resource deployed as part of the Canvas. The Operator creates Istio `VirtualService` resources. These create traffic policies in Istio to route traffic (based on the API Path) to the correct micro-services. For this controller, we have named the `gateway` resource `component-gateway`.


### Listening for API status updates

The sequence diagram above includes *Listen for updates to the external URL/IP Address*. The API resource is expecting two updates:
* It expects an update with the external URL or IP Address where the API is exposed.
* It expects an update with the readiness status of the API (i.e. is the API ready to receive traffic).

For the Istio Virtual service, the URL/IP address is determined form the Istio `gateway` resource. The API Operator includes lookup to get the external URL/IP address from the status of the `gateway` resource. If you used a different API Gatway or Service Mesh combination, you may need to lookup the external address using different resources or using APIs on the API Gatway itself. 

For the readiness status of the API, the API Operator listens for update to `EndPointSlice` resources. The `EndPointSlice` resource is created by kubernetes when a service is deployed. The `EndPointSlice` resource tracks the readiness of all the pods that are part of the service. The API Operator listens for updates to the `EndPointSlice` resource and updates the status of the API resource accordingly.


## optional configuration for DataDog using pod annotations

The API operator for Istio can be configured to use DataDog to monitor the API. The API Operator can take an environment variable `OPENMETRICS_IMPLEMENTATION` which defaults to `ServiceMonitor` (for prometheus operator). If you set `OPENMETRICS_IMPLEMENTATION` to `DataDogAnnotations`, the API Operator will add the DataDog annotations to the pod running the metrics API (which DataDog uses to scrape custom metrics) instead of creating the `ServiceMonitor` resource.

### Implementation


This operator is written in Python, using the KOPF (https://kopf.readthedocs.io/) framework to listen for API resources being deployed in the ODA Canvas. 


### Testing KOPF module

Run: `kopf run --namespace=components --standalone .\apiOperatorIstio.py`
