ODA Canvas Operators
====================

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas use-case inventory. The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are open-source and freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies.

## List of Operators

This is the target list of the Canvas operators. Some are still in development and others are not yet defined. The list is subject to change as the Canvas evolves.

| Operator            | Description                     |
| ------------------- | ------------------------------- |
| Component Management | The Component operator manages the de-composition of an ODA component into APIs and Events (that are processed by their corresponding operators). |
| API Exposure | Configures the Service Providers API Gateway and/or Service Mesh to provide security, throttling and other non-functional services to allow API endpoints to be exposed to external consumers |
| API Discovery [TBD] | Provides discovery for APIs where a component has declared a dependency. Internally it uses the Service Providers discovery capabilities to identify and give access to the appropriate API to fill a dependency. The component us updated via a ServiceActivationConfiguration Open-API call |
| License Manager [TBD] | Audits compliance of component usage against licensing agreements |
| Identity | Provides identity management to grant system and user access to components. |
| Observability (Implemented as part of API Operator) | Captures observability data and allows alarming, tracing and root-cause analysis of issues. |
| Event Hub [In progress] | Enables components to publish and subscribe to asynchronous events |


The ODA Reference implemantation contains Operators that can manage the **ODA Component**, **ODA API** and other resources. The [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) (CRDs) that these operators manage are installed as part of the [canvas installation](../../installation/README.md). 

The ODA Component YAML files are created by following the instructions in [tmforum-oda/oda-ca-docs/ODAComponentDesignGuidelines](https://github.com/tmforum-oda/oda-ca-docs/tree/master/ODAComponentDesignGuidelines.md).

The Reference Implementaiton Controllers are created using the KOPF (Kubernetes Operator Pythonic Framework - [https://github.com/zalando-incubator/kopf](https://github.com/zalando-incubator/kopf)). This provides a simple framework in python for creating Operators. The Canvas can support operators created in other languages (e.g. Java) as long as support the Kubernetes Operator pattern.


Docker Images
-------------

The operator source code is in sub-folders. At present there is a:
1. **ComponentController** that manages the Component CRD. This creates API CRDs for each API a component wants to expose. 
2. Multiple reference implementations of an **API controller**: You deploy one of these options depending on your Canvas. The simplest example is the `apiOperatorSimpleIngress` controller that uses a Kubernetes ingress to expose the APIs (this is only suitable for development environments as an Ingress doesn't provide any of the standard security or throttling of a proper API Gateway). There are two API operators that configure proper API Gateways: The first is for the WhaleCloud API Gateway `apiOperatorApig`, the second is for the WSO2 API gateway `apiOperatorWSO2`. (For each of these the respective API Gatways needs to be installed separately in the Canvas.). There is a final API Operator `apiOperatorIstio` that uses the Istio Service Mesh to control access to APIs. (The Istio Service Mesh needs to be installed separately on the Canvas). A production Canvas would use an API Gateway for the external exposure of APIs; It may also use a Service Mesh for greater internal control, particularly in a shared Kubernetes cluster. 
3. A **SecurityController** (should be renamed to identity operator) that manages the identity and role management part of the Component definition. At present the security controller configures a Keycloak identity service using roles that are defined by the component. Keycloak needs to be installed separately in the canvas. 

For the KOPF framework controllers, we deploy these into a single Docker image. We have two docker files that deploy:
* The component controller, simpleIngress API controller and security controller into a single docker image;
* The component controller, WSO2 API controller and security controller into a single docker image.

The security controller also includes a separate API Listener image (that listens to partyrole events from each component). In the Canvas Helm charts the KOPF doker image and the API Listener image are deployed into a single Pod.

