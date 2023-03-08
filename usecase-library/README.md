# ODA Canvas - use-case library

This use-case library defines the interactions between a generic **ODA Component** and the **ODA Canvas**. The ODA Canvas provides access to a range of common services (for identity management, authentication, observability etc) and has a set of **Software Operators** that automatically configure these services based on requirements defined in the ODA Component YAML specification. 

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas use-case inventory. The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are open-source and freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies.

## ODA Software Operators

This is a list of the Canvas operators (including status of whether this has been tested in the Canvas referernce implementation).

| Operator            | Description                     |
| ------------------- | ------------------------------- |
| Component Management | The Component operator manages the de-composition of an ODA component into APIs and Events (that are processed by their corresponding operators). |
| API Exposure | Configures the Service Providers API Gateway and/or Service Mesh to provide security, throttling and other non-functional services to allow API endpoints to be exposed to external consumers |
| API Discovery | Provides discovery for APIs where a component has declared a dependency. Internally it uses the Service Providers discovery capabilities to identify and give access to the appropriate API to fill a dependency. The component us updated via a ServiceActivationConfiguration Open-API call |
| License Manager | Audits compliance of component usage against licensing agreements |
| Identity | Provides identity management to grant system and user access to components. |
| Observability | Captures observability data and allows alarming, tracing and root-cause analysis of issues. |
| Event Hub | Enables components to publish and subscribe to asynchronous events |


## Use-case list

| ID  |   use-case          | Description           |
| --- | ------------------- | --------------------- |
| UC001 | [Bootstrap role for component](UC001-Bootstrap-role-for-component.md) | When a new instance of a component is deployed or deleted, integrate with the Canvas Identity service and bootstrap the initial role and clean-up the bootstraped role. |
| UC002 | [Expose APIs for Component](UC002-Expose-APIs-for-Component.md) | When a component is deployed, updated or deleted, integrate with the Service Mesh and/or API Gateway to configure and expose the API Endpoints |
| UC003 | [Discover dependent APIs for Component](UC003-Discover-dependent-APIs-for-Component.md) | When a component is deployed, updated or deleted, search for any declared dependent APIs and update the component via a ServiceActivationConfiguration Open-API call |
| UC004 | [Configure Observability](UC004-Configure-Observability.md) | When a component is deployed, updated or deleted, configure the observability service. || Authentication | When an external consumer calls an exposed API for a component, manage the authenticate the consumer and pass the authenticated request (including authentication token) to the component. |
| UC005 | [View Baseline Observability](UC005-View-Baseline-Observability.md) | When a component is deployed, view the baseline metrics such as HTTP Requests per second etc using the observability service management dashboard.|
| UC006 | [View Custom Observability](UC006-View-Custom-Observability.md) | When a component is deployed, view the custom business metrics such creation,status events etc using the observability service management dashboard.|
| UC007 | [Authentication - external](UC007-Authentication-external.md) | When an external client wants to call an API exposed by a Component, how they Authenticate and get a token. |
| UC008 | [Authentication - internal](UC008-Authentication-internal.md) | When an internal client wants to call an API exposed by a Component, how they Authenticate and get a token. |
| UC009 | [Authorization](UC009-Authorization.md) | After a client has been authenticated, verify their authorization for the specific API and data.|
| UC010 | [Token Refresh](UC010-Token-Refresh.md) | After a client token expires, refresh the token and resubmit API request.|
| UC011 | [License Metrics Observability](UC011-License-Metrics-Observability.md) | Capture a tamper-proof stream of metrics that can drive the commercial license agreements with Component Vendors.|
| UC012 | [Enable event publishing](UC012-Enable-Event-Publishing.md)      | When a component is deployed, configure the Component so that it can publish events |
| UC013 | [Enable event subscription](UC013-Enable-Event-Subscription.md)  | When a component is deployed, configure the subscription on the event hub|
| UC014 | [Create Topic](UC014-Create-Topic.md)                            | When a Topic is created, configure security, Publishers and Subscribers|
| UC015 | [Delete Topic](UC015-Delete-Topic.md)                            | When a Topic is deleted, unconfigure security, Publishers and Subscribers|

The corresponding Behavour Driven Design (BDD) features and scenarious can be found here: [BDD Features and Scenarios](../compliance-test-kit/BDD-and-TDD/README.md)
