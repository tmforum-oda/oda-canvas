ODA Canvas Operators
====================

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas [use-case library](../../usecase-library/README.md). The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies. 

## How do I buy or build an ODA Canvas?

[![How do I buy or build an ODA Canvas?](https://img.youtube.com/vi/dYyyCDPlVHY/0.jpg)](https://youtu.be/dYyyCDPlVHY?si=n8-NRN-rDFA_Sin4)

## Types of Operators

There are several types of operator in the ODA Canvas. For each type of operator, there may be multiple technical implementations. The list below shows the types of operator available in the ODA Canvas reference implementation. This list is not exhaustive and we foresee new operator types becoming available as the ODA Canvas matures.


* [TMFO001 Component Management](./TMFO001-Component-Management/README.md): Manages the overall lifecycle of an ODA Component. Technically it breaks the main ODA Component resource into sub-resources for the other operators to process.
* [TMFO002 API Management](./TMFO002-API-Management/README.md): Governs how ODA Component APIs are exposed and protected across the enterprise.
* [TMFO003 Identity Config](./TMFO003-Identity-Config/README.md): Ensures every ODA Component's roles and permissions are correctly registered in the enterprise Identity Management system.
* [TMFO004 Credentials Management](./TMFO004-Credentials-Management/README.md): Automates the secure provisioning and ongoing lifecycle management of credentials for ODA Components.
* [TMFO005 Dependency Management](./TMFO005-Dependency-Management/README.md): Ensures ODA Components can reliably discover and connect to the APIs they depend on.
* [TMFO006 Event Management](./TMFO006-Event-Management/README.md): Governs how ODA Components publish and subscribe to business events across the enterprise.
* [TMFO007 Secrets Management](./TMFO007-Secrets-Management/README.md): Provides enterprise-grade secrets management for ODA Components by integrating with an external secrets vault.
* [TMFO008 OAuth2 Config](./TMFO008-OAuth2-Config/README.md): Enforces token-based authentication at the service mesh level for inter-component traffic.
* [TMFO009 Model-as-a-Service](./TMFO009-Model-as-a-Service/README.md): Automates access to AI Models following responsible AI governance patterns.
* [TMFO010 Disruption Budget Management](./TMFO010-Disruption-Budget-Management/README.md): Protects ODA Component availability during planned maintenance, upgrades, and cluster operations.
* [TMFO011 Carbon Management](./TMFO011-Carbon-Management/README.md): Measures energy and carbon use by components and offers services for components to optimise their use.
* Cost control (planned): Measures license and cloud resource costs and enables components to optimize their costs.
* Database Management (planned): Allow components to declare requirements for database-as-a-service for Relational, Key-Value, Document, Graph, Vector and other database types.


The ODA Reference implemantation contains Operators that can manage the **Component**, **ExposedAPI** and other resources. The [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) (CRDs) that these operators manage are installed as part of the [canvas installation](../../installation/README.md). 

The ODA Component YAML files are created by following the instructions in [tmforum-oda/oda-ca-docs/ODAComponentDesignGuidelines](https://github.com/tmforum-oda/oda-ca-docs/tree/master/ODAComponentDesignGuidelines.md).

The Canvas Operators can be created in any language. Some of the reference operators are created using the KOPF (Kubernetes Operator Pythonic Framework - [https://github.com/zalando-incubator/kopf](https://github.com/zalando-incubator/kopf)). The Canvas can support operators created in other languages (e.g. Java) as long as they support the Kubernetes Operator pattern.

## Operator Container Images

For instructions on how to create the Container Images for the Canvas operators, refer to [Working with Docker images](../../docs/developer/work-with-dockerimages.md).


