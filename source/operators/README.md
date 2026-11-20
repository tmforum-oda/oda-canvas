# ODA Canvas Operators

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas [use-case library](../../usecase-library/README.md). The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies. 

## How do I buy or build an ODA Canvas?

[![How do I buy or build an ODA Canvas?](https://img.youtube.com/vi/fMXEmWalRFc/0.jpg)](https://youtu.be/fMXEmWalRFc)

## Types of Operators

There are several types of operator in the ODA Canvas. For each type of operator, there may be multiple technical implementations. The table below is the operator catalogue, with the status of each operator type in the reference implementation. The list isn't fixed: new operator types will be added as the ODA Canvas matures.

The established operators are in this repository. Newer operators are developed in their own repositories in the [tmforum-oda](https://github.com/tmforum-oda) organization, so that each can be versioned and released independently (see [ADR 0022 Modular, independent operators](https://github.com/tmforum-oda/oda-ca-docs/blob/main/Decision-Log/0022-modular-independent-operators.md)). Some of these repositories are not public yet.

| Operator | What it does | Status | Implementations |
|---|---|---|---|
| [TMFOP001 Component Management](./TMFOP001-Component-Management/README.md) | Manages the overall lifecycle of an ODA Component. It breaks the Component resource into sub-resources for the other operators to process. | Available | Component operator (installed with the Canvas) |
| [TMFOP002 API Management](./TMFOP002-API-Management/README.md) | Governs how ODA Component APIs are exposed and protected across the enterprise. | Available | Istio (installed with the Canvas by default), Kong and Apache APISIX (options in the Canvas chart), Azure API Management, Google Apigee, Whale Cloud API Management |
| [TMFOP003 Identity Config](./TMFOP003-Identity-Config/README.md) | Ensures every ODA Component's roles and permissions are registered in the enterprise Identity Management system. | Available | Keycloak (installed with the Canvas), Microsoft Entra ID |
| [TMFOP004 Credentials Management](./TMFOP004-Credentials-Management/README.md) | Automates the secure provisioning and lifecycle management of credentials for ODA Components. | Available | Credentials Management operator (separate chart) |
| [TMFOP005 Dependency Management](./TMFOP005-Dependency-Management/README.md) | Ensures ODA Components can discover and connect to the APIs they depend on. | Available | Simple dependency management (installed with the Canvas by default), dependency management using Keycloak authorization (an option in the Canvas chart) |
| [TMFOP006 Event Management](./TMFOP006-Event-Management/README.md) | Governs how ODA Components publish and subscribe to business events across the enterprise. | Experimental | Developed in [tmforum-oda/TMFOP006-Event-Management](https://github.com/tmforum-oda/TMFOP006-Event-Management), which has a reference component (TrapReceiver) that publishes TMF642 alarm events on Kafka |
| [TMFOP007 Secrets Management](./TMFOP007-Secrets-Management/README.md) | Provides secrets management for ODA Components by integrating with an external secrets vault. | Available | HashiCorp Vault (installed with the Canvas) |
| [TMFOP008 OAuth2 Config](./TMFOP008-OAuth2-Config/README.md) | Enforces token-based authentication at the service mesh level for traffic between components. | Prototype | Envoy filter for Istio (in `charts/experimental`; a reference, not for production use) |
| [TMFOP009 Model-as-a-Service](./TMFOP009-Model-as-a-Service/README.md) | Automates governed access to AI models through a model gateway, following responsible AI patterns. | Experimental | Developed in its own repository (not public yet). See [AI-Native Canvas design](../../AI-Native-Canvas-design.md). |
| [TMFOP010 Disruption Budget Management](./TMFOP010-Disruption-Budget-Management/README.md) | Protects ODA Component availability during planned maintenance, upgrades and cluster operations. | Available | PDB Management operator (installed with the Canvas) |
| [TMFOP011 Carbon Management](./TMFOP011-Carbon-Management/README.md) | Measures energy and carbon use by components, and scales carbon-aware workloads with the carbon intensity of the grid. | Experimental | Carbon Management operator (separate chart) |
| TMFOP012 Data Products Lifecycle Management | Lets components discover and use data products (for example Databricks data resources) and manages their lifecycle. | Experimental | Developed in its own repository (not public yet) |
| Cost Control | Measures license and cloud resource costs, and enables components to optimize their costs. | Planned | None yet |
| Database Management | Lets components declare requirements for database-as-a-service: relational, key-value, document, graph, vector and other database types. | Planned | None yet |

The status means:

* **Available**: implemented and released in the Canvas Helm charts. Most are covered by the [BDD test kit](../../feature-definition-and-test-kit/README.md).
* **Prototype**: a working reference that shows the approach, but isn't intended for production use.
* **Experimental**: being designed and built, often in its own repository. Its interfaces may change.
* **Planned**: on the roadmap, with a description of the operator but no implementation yet.


The ODA Reference implementation contains Operators that can manage the **Component**, **ExposedAPI** and other resources. The [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) (CRDs) that these operators manage are installed as part of the [canvas installation](../../installation/README.md). 

The ODA Component YAML files are created by following the instructions in [tmforum-oda/oda-ca-docs/ODAComponentDesignGuidelines](https://github.com/tmforum-oda/oda-ca-docs/blob/main/ODAComponentDesignGuidelines.md).

The Canvas Operators can be created in any language. Some of the reference operators are created using the KOPF (Kubernetes Operator Pythonic Framework - [https://github.com/zalando-incubator/kopf](https://github.com/zalando-incubator/kopf)). The Canvas can support operators created in other languages (e.g. Java) as long as they support the Kubernetes Operator pattern.

## Operator Container Images

For instructions on how to create the Container Images for the Canvas operators, refer to [Working with Docker images](../../docs/developer/work-with-dockerimages.md).


