# Configure Event Subscription for Component use-case

This use-case describes how a component is configured for subscribing to Notifications and other Events published by other components.  When a component is deployed, updated or deleted, this use-case describes how the Canvas integrates with the Event Management component to configure Event Publishing on a topic. The use case uses the following assumptions:

* The Notifications to be published are an explicit part of the ODA Component definition. The Golden Components will include this as part of their definition and the Event Publication can also be tested by the Component CTK. The exposed APIs can be part of the **coreFunction**, **security** or **management** part of the component definition.
* The ODA Components are **not** given raised privelages to publish their Notifications directly; Instead, software operators in the Canvas read the Component definition and configure the component. This model allows the component vendor to express their requirement for publishing Notification in the component definition, and allows the SRE (Site Reliability Team) for the operator to determine how the Notifications are published. 
* Whilst the reference implementation will provide a reference `Event Publishing Operator`, in typical implementations this will be specific to the Operations team that is running their Canvas, and will link to their own standards and policies. It is also possible that Event Management vendors (or open-source communities) develop standard `Event Publishing Operators` for their own API Gateway.

## Install component

![enableEventSubscription](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventSubscription.puml)
[plantUML code](pumlFiles/enableEventSubscription.puml)

## Upgrade component - with changed API

The use-case above is for the install of a new component. If you upgrade a component and change an API, the configuration of the Service Mesh and/or API Gateway should change.

![enableEventSubscription](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventSubscription-with-modify.puml)
[plantUML code](pumlFiles/enableEventSubscription-with-modify.puml)

## Upgrade component - with additional API

![enableEventSubscription](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventSubscription-with-add.puml)
[plantUML code](pumlFiles/enableEventSubscription-with-add.puml)

## Upgrade component - with deleted API


![enableEventSubscription](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventSubscription-with-delete.puml)
[plantUML code](pumlFiles/enableEventSubscription-with-delete.puml)

## Delete component 

![enableEventSubscription](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventSubscription-delete.puml)
[plantUML code](pumlFiles/enableEventSubscription-delete.puml)
