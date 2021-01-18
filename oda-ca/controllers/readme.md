# Reference Implementation Operator

The Operator is a type of Kubernetes Controller that can manage the ODA Component resources. The ODA Component resources are created by following the instructions in https://github.com/tmforum-rand/oda-component-definitions/tree/master/validation

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


(Optionally build the component operator in the `componentOperator` folder by building the dockerfile and uploading to a docker repository - you will need permission to upload the image; you also need to adjust the image name in the odacontroller-manifest.yaml file).
```bash
cd componentOperator
docker build -f dockerfile -t lesterthomas/odacomponentcontroller:0.22 .
docker push  lesterthomas/odacomponentcontroller:0.22
```

Deploy the operator in Kubernetes.

```bash
kubectl apply -f componentOperator/componentOperator-manifest.yaml
```
