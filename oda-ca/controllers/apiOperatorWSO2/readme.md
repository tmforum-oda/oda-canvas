# Reference Implementation Operator for API CRD's using a wso2 API Gateway

This operator requires Kubernetes v1.14 or greater (the REST API endpoint changed from v1.13 to v1.14).
The API operator takes the meta-data described in the api.oda.tmforum.org CRD and uses it to configure the wso2 API gateway.

The `apr-crd-sample.yaml` file shows what the wso2 is expecting. This sample references a configmap that embeds the swagger for the api. The sample
configmap can be generated using `configmap-swagger-sample.yaml`.


The process to create the wso2 Custom Resource definitions is as follows:
1. Create a ConfigMap resource containing the swagger for the API. For the next-productcatalog, the swagger is at http://next-pc:8191/ca
talogManagement/v3/api-docs.
2. Add additional attributes to the swagger:
```
    x-wso2-basePath: /catalogManagement
    x-wso2-production-endpoints:
      urls:
        - http://next-pc:8191/catalogManagement  
```
3. Create the api.wso2.com Custom Resource.




## Installation

The actual API Gateway is built into a single docker image together with the OPA-Component operator. See the `/controlers/buildControlers.sh` file for details.


## Demo video

There is a demo of wso2 at https://www.youtube.com/watch?v=gglNMMzzBRI
