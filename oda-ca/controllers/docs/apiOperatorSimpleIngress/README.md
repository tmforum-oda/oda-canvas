# API Operator - Introduction

The API operator takes the meta-data described in the api.oda.tmforum.org CRD and uses it to configure an API gateway. The actual API gateway used may vary, and so the Reference Implementation will eventually have multiple operators (you choose which one to deploy for your own canvas environment). This operator dempnstrates a very simple example using kubernetes Ingress to give access to the APIs (it is not a real API gateway and should not be used in any production deployments - it just demonstrates the concept and will allow access to REST APIs running in the component).

Your kubernetes environment will need an Ingress Controller (typically you install the relavant ingress controller of the specific cloud environment).



![Sequence diagram](sequenceDiagrams/apiOperatorSimpleIngress.png)



The component controller written in Python, using the KOPF (https://kopf.readthedocs.io/) framework to listen for API resources being deployed in the ODA Canvas. 


**Testing KOPF module**

Run: `kopf run --namespace=components --standalone .\apiOperator-simpleIngress.py`
