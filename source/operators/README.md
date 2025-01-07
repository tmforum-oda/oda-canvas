ODA Canvas Operators
====================

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas [use-case library](../../usecase-library/). The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies. 

## How do I buy or build an ODA Canvas?

[![How do I buy or build an ODA Canvas?](https://img.youtube.com/vi/dYyyCDPlVHY/0.jpg)](https://youtu.be/dYyyCDPlVHY?si=n8-NRN-rDFA_Sin4)

## Types of Operators

There are several types of operator in the ODA Canvas. For each type of operator, there may be multiple technical implementations. The list below shows the types of operator available in the ODA Canvas reference implementation. This list is not exhaustive and we foresee new operator types becoming available as the ODA Canvas matures.


* [Component Management](./component-management): Manages lifecycle of a component, and the de-composition into ExposedAPIs, PublishedEvents and other sub-resources (that are processed by their corresponding operators). 
* [API Management](./api-management#api-management-operators): Configures the API Gateway and/or Service Mesh to provide security, throttling and other non-functional services to allow API endpoints to be exposed to external consumers.
* [Identity Config](./identity-config#Identity-Config-Operators): Configures the Identity Management Services made available through the Canvas.
* [Secrets Management](./secretsmanagementOperator-hc): Manages a secure secrets vault and allows components to store and retrieve passwords and other sensitive information.
* [Dependency Management](./dependentApiSimpleOperator): Provides services to allow a Component to discover API dependencies.
* Event Management (planned): Similar to the API Management, but for Event based integration with Components publishing or subscribing to Events. 
* AI Management (planned): Allow components to declare requirements for custom AI or foundational AI services.
* Carbon control (planned): Measures energy and carbon use by components and offers services for components to optimise their use.
* Cost control (planned): Measures license and cloud resource costs and enables components to optimize their costs.
* Database Management (planned): Allow components to declare requirements for database-as-a-service for Relational, Key-Value, Document, Graph, Vector and other database types.


The ODA Reference implemantation contains Operators that can manage the **Component**, **ExposedAPI** and other resources. The [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) (CRDs) that these operators manage are installed as part of the [canvas installation](../../installation/README.md). 

The ODA Component YAML files are created by following the instructions in [tmforum-oda/oda-ca-docs/ODAComponentDesignGuidelines](https://github.com/tmforum-oda/oda-ca-docs/tree/master/ODAComponentDesignGuidelines.md).

The Canvas Operators can be created in any language. Some of the reference operators are created using the KOPF (Kubernetes Operator Pythonic Framework - [https://github.com/zalando-incubator/kopf](https://github.com/zalando-incubator/kopf)). The Canvas can support operators created in other languages (e.g. Java) as long as they support the Kubernetes Operator pattern.

## Operator Container Images

For instructions on how to create the Container Images for the Canvas operators, refer to [Working with Docker images](../../docs/developer/work-with-dockerimages.md).


