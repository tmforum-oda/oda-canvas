# API Operator for Istio - Introduction

The API operator for Istio takes the meta-data described in the api.oda.tmforum.org CRD and uses it to configure the Istio control-plane. In a production environment you would probably have an API gateway in front of the Service Mesh

Your kubernetes environment will need to have the Istio Service Mesh deployed and have a `gateway` resource deployed as part of the Canvas. The Operator creates Istio `Virtual Service` resources. These create traffic policies in Istio to route traffic (based on the API Path) to the correct micro-services. For this controller, we have named the `gateway` resource "component-gateway".



![Sequence diagram](sequenceDiagrams/apiOperatorIstio.png)



## optional configuration for DataDog using pod annotations

The API operator for Istio can be configured to use DataDog to monitor the API. The API Operator can take an environment variable PROMETHEUS_PATTERN which defaults to ServiceMonitor (for prometheus operator). If you set PROMETHEUS_PATTERN to DataDogAnnotations, the API Operator will add the DataDog annotations to the pod running the metrics API (which DataDog uses to scrape custom metrics).

```yaml

The component controller written in Python, using the KOPF (https://kopf.readthedocs.io/) framework to listen for API resources being deployed in the ODA Canvas. 


**Testing KOPF module**

Run: `kopf run --namespace=components --standalone .\apiOperatorIstio.py`
