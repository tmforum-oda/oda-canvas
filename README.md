# Open Digital Architecture Canvas

[![Supported-component-version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas%2Fmain%2Fcharts%2Fcanvas-oda%2FChart.yaml&query=%24.appVersion&label=Supported-component-version)](https://github.com/tmforum-oda/oda-canvas)
[![Canvas-version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas%2Fmain%2Fcharts%2Fcanvas-oda%2FChart.yaml&query=%24.version&label=Canvas-version)](https://github.com/tmforum-oda/oda-canvas)
[![License](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftmforum-oda%2Foda-canvas-ctk%2Fmain%2Fpackage.json&query=%24.license&label=License&color=%09%23a3ff00)](https://github.com/tmforum-oda/oda-canvas/blob/main/LICENSE)

![BDD](https://img.shields.io/badge/BDD_tests-8A2BE2?style=flat-square&color=grey&logo=cucumber)[![Passed](https://byob.yarr.is/tmforum-oda/oda-canvas/bdd-passed/byob-badges/bdd-passed.json)](https://github.com/tmforum-oda/oda-canvas/tree/byob-badges)[![Undefined](https://byob.yarr.is/tmforum-oda/oda-canvas/bdd-undefined/byob-badges/bdd-undefined.json)](https://github.com/tmforum-oda/oda-canvas/tree/byob-badges)[![Failed](https://byob.yarr.is/tmforum-oda/oda-canvas/bdd-failed/byob-badges/bdd-failed.json)](https://github.com/tmforum-oda/oda-canvas/tree/byob-badges)[![Skipped](https://byob.yarr.is/tmforum-oda/oda-canvas/bdd-skipped/byob-badges/bdd-skipped.json)](https://github.com/tmforum-oda/oda-canvas/tree/byob-badges)




The Open Digital Architecture (ODA) Canvas is an execution platform for ODA Components. This repository contains the Reference Implementation, open-source code, use cases and test-kit for a [TM Forum ODA Canvas](https://www.tmforum.org/oda/deployment-runtime/oda-canvas/). You are free to use this as a starting point for your own ODA Canvas implementation. Explore available ODA Components in the [ODA Component Directory](https://www.tmforum.org/oda/directory). The Reference Implementation of the ODA Canvas will be used for ODA Component certification. 



## Installation

see [Installation Guide](installation/README.md) for installation instructions.


## Introduction to ODA Canvas

This video is part 1 of the ODA Canvas training series. The [training videos](https://tmforum-oda.github.io/oda-ca-docs/docs/training-videos/index.html) page on the documentation site has every part, with chapters and a transcript.

[![Introduction to the ODA Canvas](https://img.youtube.com/vi/xLdFY9mGJxI/0.jpg)](https://youtu.be/xLdFY9mGJxI)

TM Forum Open APIs standardised the interfaces between telecom IT systems. Since the Open API programme launched in 2015 they have been downloaded almost 1.4 million times by nearly 72,000 developers (September 2026). Standard interfaces were not enough on their own, though: the industry also needed a standard way to package, deploy and operate the software behind them. That is what ODA Components and the ODA Canvas provide.

An **ODA Component** is an independently deployable unit of functionality. Alongside its business function, it declares its non-functional needs: the APIs it exposes and depends on, the events it publishes and subscribes to, its security roles and its observability. The **ODA Canvas** reads those declarations and configures the shared platform services that the component needs, so component developers can concentrate on business functionality.

### Composable IT

Together, components and the Canvas give you composable IT. Use cases are assembled from standard components, the components are deployed onto a Canvas, and the Canvas configures the underlying platform services: API gateways, service meshes, identity, observability and secrets. Those services can be open-source reference modules or commercial cloud services. When a new business need appears, you assemble existing building blocks instead of starting a new integration project.

### Agentic ODA

The same model extends to AI. In the **AI-Native Canvas**, AI agents are packaged as agentic components that follow the same component standard. Components can expose their APIs as tools for agents with the Model Context Protocol (`apiType: mcp`), and agents can describe themselves to other agents with the Agent2Agent protocol (`apiType: a2a`). The Canvas adds AI and data services, such as an AI gateway in front of the approved language models, so agents from many vendors can be governed, observed and cost-managed in one consistent way. For more information, see [AI-Native Canvas Design](AI-Native-Canvas-design.md).

### Canvas operators

The ODA Canvas is itself a modular architecture, with independent **operators** that embed the management and operations activities in software, following the Kubernetes operator pattern:

* The **Component Management** operator manages the lifecycle of each component. It breaks the component into sub-resources (`ExposedAPI`, `DependentAPI`, `IdentityConfig`, `SecretsManagement`, `PublishedNotification` and `SubscribedNotification`), and each one is handled by its own operator.
* The **API Management** operators configure the API gateway or service mesh, applying any policies the component declares (such as rate limits, API-key checks, CORS and OpenAPI validation). There are six implementations: Istio, Kong, Apache APISIX, Azure API Management, Google Apigee and Whale Cloud. You deploy the one that matches your gateway. The API operator also sets up metrics scraping, for example with a Prometheus `ServiceMonitor`.
* The **Identity Config** operator registers the component's roles in the identity platform (Keycloak or Microsoft Entra ID). Roles can be declared in the component YAML, or provided dynamically through the TMF672 User Roles and Permissions API.
* The **Credentials Management** and **Dependency Management** operators create each component's client credentials and connect it to the APIs it depends on.
* The **Secrets Management** operator gives each component its own vault (HashiCorp Vault in the reference implementation), which the component reaches with its Kubernetes workload identity rather than a bootstrap password.
* The **Disruption Budget Management** operator keeps components available during cluster maintenance and upgrades.

An **OAuth2 Config** operator is available as a prototype, and operators for Model-as-a-Service, data products and carbon-aware scaling are experimental. The [Software Operators](source/operators/README.md) page has the full catalogue, with the status of each operator.

The reference implementation operators are freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production Canvas to combine standard operators with custom operators that implement the organization's own operational policies.

### Maturity

The Canvas is generally available. Release 1.2.0 introduced the `v1` component specification (December 2024), and there have been regular releases since: the latest is 1.2.5 (March 2026), and 1.2.6 is in release candidates. Every change is checked by the [BDD test kit](feature-definition-and-test-kit/README.md), running against a real Kubernetes cluster (Kind) in the GitHub Actions workflows.

The Canvas has been tested on AWS EKS, Azure AKS, Google GKE, Rancher, MicroK8s, Minikube, Docker Desktop, Kind and K3s. See the [Installation Guide](installation/README.md) for the details of each platform.


## ODA Canvas Design

The ODA Canvas design is to allow ODA Components to declare their requirements for underlying capabilities in a technology-independent way. The Canvas manages these underlying capabilities using [Software Operators](source/operators/README.md) that follow the Kubernetes Operator Pattern.

<img width="978" height="733" alt="Image" src="https://github.com/user-attachments/assets/398ab2c9-ef91-445c-9dde-a970e827d4dd" />

The design (including ongoing work) of the ODA Canvas is documented in [ODA Canvas Design](Canvas-design.md). The [Use Case Library](usecase-library/README.md) shows how ODA Components interact with the ODA Canvas. The [Feature definition and Test Kit](feature-definition-and-test-kit/README.md) details the features required to be a fully compliant ODA Canvas and a set of tests that can be used to validate any ODA Canvas. The [source code](source/README.md) contains the source code for the operators that are part of the ODA Canvas.

Security principles for the ODA Canvas design are documented in [ODA Security Principles](SecurityPrinciples.md).


## Release notes


| Version    | Release notes                         |
|:----------:|---------------------------------------|
| 1.2.5      | March 2026 release ahead of Elevate                                              |
| 1.2.4      | October 2025 release ahead of Innovate Asia                                      |
| 1.2.3      | June 2025 release ahead of DTW                                                   |
| 1.2.2      | First update incorporating fixes since general availability launch               |
| 1.2.0      | Release of `v1` component specification and general availability of ODA Canvas   |
| 1.1.8      | Final changes to `v1beta4` component specification                               |
| 1.1.7      | Updated to `v1beta4` component specification                                     |
| 1.1.5      | Multiple fixes                                                                   |
| 1.1.4      | Added secretsmanagement-operator                                                 |
| 1.1.3      | Moved operators to use `tmforumodacanvas` docker repository                      |
| 1.1.2      | Added dependentApiSimpleOperator                                                 |
| 1.1.1      | Bug fix release - Webhook handles empty specification field for exposedAPI. Tested against kubernetes 1.29.        |
| 1.1.0      | Added support for multiple specifications of each Open-API. The v1beta3 `exposedAPI` object defines its `specification` property as an array. This is specifically designed to allow TM Forum Gen5 Open-APIs (which can be specified alongside Gen4 APIs).  <BR/> The [Webhook](./source/webhooks) will automatically convert v1beta2 and v1beta1 specifications to v1beta3 with an array of 1.          |
| 1.0.0      | First tracked release for component version v1beta3 (also supports N-2 versions i.e. v1beta2 and v1beta1).


## Additional Documentation

| | |
| ---- | ---- |
| [Component Registry](./docs/component-registry/README.md) | Not yet released, but will be included in the next release.<br> Contains documentation of Component Registry UI as well as how to install a standalone Component Registry for a multi-canvas scenario |
| [How To work with Dockerimages](./docs/developer/work-with-dockerimages.md) | For developers, documents the build and release process for Docker images in this repository | 
 
