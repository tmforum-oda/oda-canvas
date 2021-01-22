# Reference Implementation Operator

The Operator is a type of Kubernetes Controller that can manage the ODA Component resources. The ODA Component resources are created by following the instructions in https://github.com/tmforum-rand/oda-ca/tree/master/custom-resource-definitions

The Reference Implementaiton Operator is created using the KOPF (Kubernetes Operator Pythonic Framework - https://github.com/zalando-incubator/kopf). This provides a simple framework in python for creating Operators. 

## Installation

Install the CRDs (Custom Resource Definitions) by following the instructions in https://github.com/tmforum-rand/oda-component-definitions/tree/master/validation

Then install the required libraries:

```bash
pip install -r requirements.txt
```

Install the additional Custom Resource Definitions used by KOPF:

```bash
kubectl apply -f peering.yaml
```

Create the Service Account that is used by the operators to interact with the Kubernetes APIs. The resources the operators are allowed in manage are closely controlled using name-spaces in this rbas manifest.

```bash
kubectl apply -f rbac.yaml
```


(Optionally build the component operator in the `componentOperator` folder by building the dockerfile and uploading to a docker repository - you will need permission to upload the image; you also need to adjust the image name in the odacontroller-manifest.yaml file). At the moment you can choose between two controllers: The first uses Kubernetes ingress to expose APIs (instead of a real API gateway - this is simple to set-up, but not suitable for any production environmnets); The second uses the WS02 API Gateway (you need to have WS02 installed as part of your Canvas and then the controller configures APIs into WSO2 based on the Component Envelope meta-data).

```bash
cd componentOperator
docker build --file component-IngressController-dockerfile -t lesterthomas/odacomponentcontroller-ingress:0.6 -t lesterthomas/odacomponentcontroller-ingress:latest .
docker build --file component-wso2Controller-dockerfile -t lesterthomas/odacomponentcontroller-wso2:0.6 -t lesterthomas/odacomponentcontroller-wso2:latest .
docker push lesterthomas/odacomponentcontroller-ingress --all-tags
docker push lesterthomas/odacomponentcontroller-wso2  --all-tags
```

Deploy the operator in Kubernetes.

```bash
kubectl apply -f componentOperator/componentOperator-manifest.yaml
```
