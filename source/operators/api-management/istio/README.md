# API Operator for Istio

This **API operator** manages a Canvas environment that exposes APIs using Istio Service Mesh (without any API Gateway). It is a reference implementation of an API Operator. You are free to reuse, extend or replace with your own API operator.

It also configures custom resources and annotations to support Open Metrics observability data (using **Prometheus** or a managed service that can work with the Open Metrics standard)

Both **Istio** and **Prometheus** can be configured using Kubernetes Custom Resource Definitions (CRD). The API Operator uses the Kubernetes API to listen for changes to CRDs and then configures Istio and Prometheus accordingly.

Istio uses `VirtualService` resources (https://istio.io/latest/docs/reference/config/networking/virtual-service/) to configure traffic routing in the Istio control plane.

Prometheus uses `ServiceMonitor` resources (https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md) to configure the Prometheus monitoring system.

This makes the logic required to create an API Operator relatively simple. The API Operator listens for new/updated/deleted `oda.tmforum.org/ExposedAPI` resources and then creates/updates/deletes the corresponding Virtual Service and Service Monitor resources. The API Operator also listens for status updates from Istio and Prometheus and updates the status of the `oda.tmforum.org/ExposedAPI` resource accordingly.

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


## optional configuration for DataDog or different Prometheus implementations

The API operator for Istio can be configured to use annotations instead of Service Monitor resources. The API Operator can take an environment variable `OPENMETRICS_IMPLEMENTATION` which can be set to:
* `ServiceMonitor` (default) Uses Service Monitor custom resources to configure Prometheus (using prometheus operator). 
* `DataDogAnnotations` Uses Pod annotations in format used by DataDog (which DataDog uses to scrape custom metrics) instead of creating the `ServiceMonitor` resource.
* `PrometheusAnnotation` Uses Pod annotations in format used by Prometheus (without Prometheus operator) instead of creating the `ServiceMonitor` resource. This is used by some managed Prometheus services (like Azure managed Prometheus https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/prometheus-metrics-overview).


### Implementation

This operator is written in Python, using the KOPF (https://kopf.readthedocs.io/) framework to listen for API resources being deployed in the ODA Canvas. 

**Interactive development and Testing of operator using KOPF**

The production operator will execute inside a Kubernetes Pod. For development and testing, it is possible to run the operator on the command-line (or inside a debugger). Kopf includes a `--standalone` attribute to allow the operator to execute in a standalone mode. This means that the operator will run independently, without relying on any external controllers or frameworks. It is particularly useful for development and debugging purposes, as it allows you to run and test your operator locally on your machine.

Run locally in command-line: 
```
kopf run --namespace=components --standalone .\apiOperatorIstio.py
```

This mode will use the kubeconfig file (typically located at `$HOME/.kube/config`) to as long as `kubectl` is correctly configured for your cluster, the operator should work. 

You need to ensure you turn-off the operator execusing in Kubernetes (for example, by setting the replicas to 0 in the operator Deployment).

The command above will execute just the ExposedAPI operator. You will also need to execute the other operators relevant for your Canvas implementation - these can be executed in separate terminal command-lines.

