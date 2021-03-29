Introduction
============

Full documentation is available here: [Read the Docs](docs/_build/html/index.html)

The ODA Reference implemantation contains Kubernetes Operators that can manage the **ODA Component** and **ODA API** resources. The [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) (CRDs) that these operators manage are installed as part of the canvas helm charts [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts). 

The ODA Component YAML files are created by following the instructions in [tmforum-oda/oda-ca-docs/ODAComponentDesignGuidelines](https://github.com/tmforum-oda/oda-ca-docs/tree/master/ODAComponentDesignGuidelines.md).

The Reference Implementaiton Controllers are created using the KOPF (Kubernetes Operator Pythonic Framework - [https://github.com/zalando-incubator/kopf](https://github.com/zalando-incubator/kopf)). This provides a simple framework in python for creating Operators. 

Installation
------------

For the production environments, the controller and CRDs (Custom Resource Definitions) are installed by Helm charts in the [tmforum-oda/oda-canvas-charts](https://github.com/tmforum-oda/oda-canvas-charts) repository. The individual contollers can be run in developer mode (see readme in each sub-folder).


Docker Images
-------------

The KOPF controller source code is in sub-folders. At present there is a:
1. **ComponentController** that manages the Component CRD. This creates API CRDs for each API a component wants to expose. 
2. Two reference implementations of an **API controller**: You deploy one of these two options depending on your Canvas. The simplest example is the simpleIngress controller that uses a Kubernetes ingress to expose the APIs (this is only suitable for development environments as an Ingress doesn't provide any of the standard security or throttling of a proper API Gateway). The other example is a WSO2 controller that will configure a WSO2 API gateway (that needs to be installed separately in the Canvas.
3. A **SecurityController** that manages the security part of the Component definition. At present the security controller configures a Keycloak identity service using roles that are defined by the component. Keycloak needs to be installed separately in the canvas. 

For the KOPF framework controllers, we deploy these into a single Docker image. We have two docker files that deploy:
* The component controller, simpleIngress API controller and security controller into a single docker image;
* The component controller, WSO2 API controller and security controller into a single docker image.

The security controller also includes a separate API Listener image (that listens to partyrole events from each component). In the Canvas Helm charts the KOPF doker image and the API Listener image are deployed into a single Pod.

