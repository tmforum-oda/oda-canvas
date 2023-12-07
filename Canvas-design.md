# ODA Canvas Design

## What is the ODA Canvas?

The ODA Canvas is an execution environment for ODA Components and the release automation part of a CI/CD pipeline. The Canvas exists to support ODA Components and provides access to a set of cloud-native services that are required by ODA Components. For example, it provides access to an API Gateway and/or Service Mesh to enable components to expose their APIs in a standard way; it provides access to Observability services to enable components to be monitored and managed; it provides access to an Identity Management System to enable components to register the permissions they allow to be granted to users. 

There is not an explicit standard or specification for the Canvas: The standard is the ODA Component Specification. The Canvas is a platform that can consume ODA Components, read metadata from the component spec and then execute whatever lifecycle process is required to meet those requirements. 

We expect that there will be multiple implementations of the Canvas - this repository contains a Reference Implementation of a Canvas that teams can use to accelerate their own implementation. The Reference Implementation is a cloud-native application, and is designed to be deployed on Kubernetes. We do expect all Canvas implementations to exhibit a standard set of behaviours, and we have documented these behaviours at a high level in the use case library, and at a more detailed level using BDD (Behaviour-Driven Development) features and scenarios. The compliance test kit (CTK) for the Canvas will use these BDDs to create executable tests that can be used to validate a Canvas implementation.

![What is a Canvas](What-is-a-Canvas.png)

## How do I buy or build a Canvas?

There are multiple options to build or buy a Canvas:

* Public Cloud Offerings: Multiple Public Cloud Providers are offering a managed Canvas offering on top of their managed Kubernetes services. At DTW Copenhagen there were PoC demonstrations from AWS, Azure, China Mobile, Google Cloud and Oracle Cloud. These offerings are typically based on the Reference Implementation, but may have additional features or capabilities and will typically integrate with the Public Cloud Provider's other services (for API Management, Observability etc.).
* 'Roll your own' Canvas based on the Reference Implementation. The Reference Implementation Canvas is released as Apache 2.0 licensed assets that can be used to build your own Canvas. The Reference Implementation is designed to be extensible, and we expect that teams will add their own operators to support their own specific requirements. 
* Infrastructure software vendors and open source projects offering operators/managers for their software. Many infrastructure software vendors and open source projects have already adopted the Kubernetes Operator Pattern to manage their software. For example, [Istio](https://istio.io/latest/docs/setup/install/operator/) and [Kong](https://docs.konghq.com/kubernetes-ingress-controller/2.0.x/deployment/kubernetes-operator/) both offer operators that can be used to manage their software on Kubernetes. These operators can be used as the basis for a Canvas implementation.

The ODA Canvas is itself a modular architecture, so you can mix & match these options to create your own Canvas. 

![Canvas Options](How-do-I-build-or-buy-a-Canvas.png)

## Canvas Design structure

This is an outline of how the Canvas design is documented, and a pointer to the different design artefacts:
* The highest level documentation describing the services a Canvas should provide to an ODA Component is in the [Canvas use case library](usecase-library/README.md). The use case library outlines the assumptions for each use case and sequence diagrams for the interactions between an example ODA Component and the ODA Canvas.
* The next level of details of the features required to be a fully compliant ODA Canvas is in the [Compliance Test Kit](compliance-test-kit/README.md). These are documented as business-friendly pseudo-code in the form of BDD (Behaviour-Driven Development) features and scenarios. BDD Features should refer to use cases in the Canvas use case library (creating or amending them as required). There is a style guide for creating BDDs at [TAC-353 BDD Style Guide](https://projects.tmforum.org/jira/browse/TAC-353).
* The use cases and features are Level 2 standards and should be implementation agnostic. For the Level 3 Reference Implementation, to turn the BDD features into executable compliance tests, there are a set of TDD (Test-Driven Development) tests that define tests for each BDD scenario (embedded within each BDD). These are in the [Compliance Test Kit](compliance-test-kit/README.md).
* Specific design decisions where we assess options and make a decision are documented in the [Architecture Decision Log](https://github.com/tmforum-oda/oda-ca-docs/tree/master/Decision-Log/README.md).
* To organise the backlog of work for the team, we use [GitHub issues](https://github.com/tmforum-oda/oda-canvas/issues). Issues may describe new features, bugs or refactoring of work. Contributors self-assign to issues to indicate who is working on what. 
* Finally, the [source code](../source/README.md) contains the source code, helm charts and configuration files that form the reference implementation for the Canvas. Source code should embed [docstrings](https://en.wikipedia.org/wiki/Docstring) so that it becomes part of the documentation of the system. The source code comprises:
1. [Software operators](/source/operators) - this is the key part of the Canvas. Operators manage ODA Components by reading the Component's requirements as metadata in the component spec and then executing whatever lifecycle process is required to meet those requirements. Operators execute the initial deployment of a Component, as well as ongoing maintenance and upgrade processes. Operators are responsible for monitoring the health of the component and taking remedial action if required. The Reference Implementation implements operators following the [Kubernetes Operator Pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/). Operators could be described as management-plane functions, and are the cloud-native equivalent of Network Element Managers.
2. [Webhooks](/source/webhooks) - The Reference implementation Canvas utilizes webhooks to integrate with the Kubernetes Control Plane. The initial use of this is for the Canvas to support multiple versions of the ODA Component Standard, allowing seamless upgrades of components and appropriate deprecation warnings.
3. [Utilities](/source/utilities) - The reference implementation includes some simple utilities to help with the development of the Canvas. These are not part of the Canvas itself, but are useful for development and troubleshooting. We may in the future support a command-line interface to the Canvas, similar to [kubectl](https://kubernetes.io/docs/reference/kubectl/) (for Kubernetes) or [istioctl](https://istio.io/latest/docs/ops/diagnostic-tools/istioctl/) (for Istio).

## Interaction with ODA Component standard

The Canvas reads the Component requirements as metadata in the Component spec. We may need to propose changes to the Component standard to meet the Canvas requirements. The Canvas should be able to support any Component that meets the Component standard, but not every Component will necessarily use all the features of the Canvas. The Component design guidelines are documented at [ODA Component Design Guidelines](../oda-ca-docs/ODAComponentDesignGuidelines.md).

## Summary

The documentation approach for the Canvas is summarised in the diagram below:

![Canvas Documentation](CanvasDocumentation.png)

## Design Epics

The Canvas design is split into the following epics:

* [Epic 1: Authentication](Authentication-design.md)
* [Epic 2: Event based integration](Event-based-integration-design.md)
* [Epic 3: Observability](Observability-design.md)
