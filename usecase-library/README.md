# ODA Canvas - use-case library

This use-case library defines the interactions between a generic **ODA Component** and the **ODA Canvas**. The ODA Canvas provides access to a range of common services (for identity management, authentication, observability etc) and has a set of **Software Operators** that automatically configure these services based on requirements defined in the ODA Component YAML specification. 

Software Operators are a key concept in the ODA Canvas. For more information, see the 2016 CoreOS blog post that introduced the concept: [Introducing Operators: Putting Operational Knowledge into Software](https://web.archive.org/web/20170129131616/https://coreos.com/blog/introducing-operators.html). There is a good definition of software operators at: [operatorhub.io/what-is-an-operator](https://operatorhub.io/what-is-an-operator).

The ODA canvas is itself a modular and extensible platform. The list below shows the operators that appear in the Canvas use-case inventory. The ODA-Component Accelerator is building a reference implementation of an ODA Canvas with a range of operators that are open-source and freely available for organizations to re-use, extend or replace with their own implementations. We expect a typical production implementation will use a combination of standard operators and custom operators that can implement that organizations specific operational policies.

## ODA Software Operators

This is a list of the Canvas operators (including status of whether this has been tested in the Canvas referernce implementation).

| Operator             | Description                     |
| -------------------- | ------------------------------- |
| Component Management | The Component operator manages the de-composition of an ODA component into APIs and Events (that are processed by their corresponding operators). |
| API Management       | Configures the API Gateway and/or Service Mesh to provide security, throttling and other non-functional services to allow API endpoints to be exposed |
| Event Management     | Configures event based integration to allow components to use asynchronous events (in addition to Rest based API integration). |
| Identity Management  | Configures an Identity Management Service based on requirements defined in ODA Components. |
| Observability Management | Configures observabiliy services for both technical and business metrics and events. Enables alarming, tracing and root-cause analysis of issues.|
| Secrets Management   | Configures a secrets vault to enable ODA Components to store secrets in a secure way |
| Carbon Management    | Configures a services to analyze carbon (and energy) usage of ODA Components and to provide API services to enable components to make intelligent decisions to minimise Carbon usage.  |
| Cost Management      | Configures services for cost control for both cloud consumption and license costs.  |
| Other                | Additional operators will be added over time.  |




## Use-case list

The use-cases are named based on the [use case naming conventions](use-case-naming-conventions.md)


- UC001: [Install Canvas](./UC001-Install-Canvas.md) - Install, upgrade and uninstall the ODA Canvas.
- UC002: [Manage Components](./UC002-Manage-Components.md) - When an ODA Component is Installed, Updated or Uninstalled, create the sub-resources and update the status of the component.
- UC003: [Configure Exposed APIs](./UC003-Configure-Exposed-APIs.md) - Integrate with the Service Mesh and/or API Gateway to configure and expose the API Endpoints for a Component.
- UC004: [Configure Published Events](./UC004-Configure-Published-Events.md) - Integrate with the Eventing Service to configure and publish the Events for an ODA Component.
- UC005: [Configure Users and Roles](./UC005-Configure-Users-and-Roles.md) - Integrate with the Identity Management System to configure users and roles.
- UC006: [Configure Observability](./UC006-Configure-Observability.md) - Integrate with the Observability solution to configure technical and business observability.
- UC007: [Configure Dependent APIs](./UC007-Configure-Dependent-APIs.md) - Configure components to be able to call APIs (on other ODA Components or external APIs).
- UC008: [Configure Subscribed Events](./UC008-Configure-Subscribed-Events.md) - Configure components to be able to subscribe to events.
- UC009: [Internal Authentication](./UC009-Internal-Authentication.md) - Authenticate API calls within the Canvas.
- UC010: [External Authentication](./UC010-External-Authentication.md) - Authenticate API calls originating outside the Canvas.
- UC011: [View Technical Observability](./UC011-View-Technical-Observability.md) - Run-time view of technical observability data.
- UC012: [View Business Observability](./UC012-View-Business-Observability.md) - Run-time view of business observability data.
- UC013: [Upgrade Canvas](./UC013-Upgrade-Canvas.md) - Seamless in-life upgrade of the ODA Canvas.
The corresponding Behavour Driven Design (BDD) features and scenarious can be found here: [BDD Features and Scenarios](../feature-definition-and-test-kit/README.md)
