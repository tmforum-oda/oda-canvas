# Reference Implementation Operator for API CRD's using a simple ingress

This operator requires Kubernetes v1.14 or greater (the REST API endpoint changed from v1.13 to v1.14).
The API operator takes the meta-data described in the api.oda.tmforum.org CRD and uses it to configure an API gateway. The actual API gateway used may vary, and so the Reference Implementation will eventually have multiple operators (you choose which one to deploy for your own canvas environment). This operator dempnstrates a very simple example using kubernetes Ingress to give access to the APIs (it is not a real API gateway and should not be used in any production deployments - it just demonstrates the concept and will allow access to REST APIs running in the component).

## Installation

Build the api operator by building the dockerfile and uploading to a docker repository - you will need permission to upload the image; you also need to adjust the image name in the odacontroller-manifest.yaml file).
```bash
docker build -f dockerfile -t lesterthomas/apioperator-simpleingress:0.1 .
docker push  lesterthomas/odacomponentcontroller:0.1
```

Deploy the operator in Kubernetes.

```bash
kubectl apply -f apicontroller-simpleingress-manifest.yaml
```
