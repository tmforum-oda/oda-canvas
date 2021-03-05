# Reference Implementation Kubernetes Controllers

The ODA Reference implamantation contains Kubernetes Controllers that can manage the ODA Component and ODA API resources. The  Custom Resource Definitions (CRDs) that these controllers manage are installed as part of the canvas helm charts [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts). The controller/CRD combination is refered to as a Kubernetes Operator (see https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)

The ODA Component YAML files are created by following the instructions in https://github.com/tmforum-oda/oda-ca-docs/tree/master/ODAComponentDesignGuidelines.md

The Reference Implementaiton Controllers are created using the KOPF (Kubernetes Operator Pythonic Framework - https://github.com/zalando-incubator/kopf). This provides a simple framework in python for creating Operators. 

## Installation

For the production environments, the controller is installed by Helm charts in the [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts) repository. The instructions below allow you to install a development environmnet to further develop these controllers.

Install the CRDs (Custom Resource Definitions) by following the instructions in [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts).

The KOPF controller source code is in sub-folders. At present there is a:
1. ComponentController that manages the Component CRD. This creates API CRDs for each API a component wants to expose. 
2. Two reference implementations of an API controller: You deploy one of these two options depending on your Canvas. The simplest example is the simpleIngress controller that uses a Kubernetes ingress to expose the APIs (this is only suitable for development environments as an Ingress doesn't provide any of the standard security or throttling of a proper API Gateway). The other example is a WSO2 controller that will configure a WSO2 API gateway (that needs to be installed separately in the Canvas.
3. A SecurityController that manages the security part of the Component definition. At present the security controller configures a Keycloak identity service using roles that are defined by the component. Keycloak needs to be installed separately in the canvas. 

For the KOPF framework controllers, we deploy these into a single Docker image. We have two docker files that deploy:
* The component controller, simpleIngress API controller and security controller into a single docker image;
* The component controller, WSO2 API controller and security controller into a single docker image.

The security controller also includes a separate API Listener image (that listens to partyrole events from each component). In the Canvas Helm charts the KOPF doker image and the API Listener image are deployed into a single Pod.


To install a development environment:
 

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
docker build --file component-WSO2Controller-dockerfile -t lesterthomas/odacomponentcontroller-WSO2:0.6 -t lesterthomas/odacomponentcontroller-WSO2:latest .
docker push lesterthomas/odacomponentcontroller-ingress --all-tags
docker push lesterthomas/odacomponentcontroller-WSO2  --all-tags
```

Deploy the operator in Kubernetes.

```bash
kubectl apply -f componentOperator/componentOperator-manifest.yaml
```
