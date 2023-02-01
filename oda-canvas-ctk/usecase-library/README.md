# ODA Canvas - use-case library

This folder contains a complete use-case library that defines the interactions between a generic ODA Component and the ODA Canvas.

For each operator in the ODA canvas, we identify a set of use-cases that cover all the interactions with an ODA Component.

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


The corresponding Behavour Driven Design (BDD) features and scenarious can be found here: [BDD Features and Scenarios](../BDD-and-TDD/README.md)
