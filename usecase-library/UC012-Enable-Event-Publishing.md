# Configure Event Publishing for Component use-case

This use-case describes how a component is configured for publishing its Notifications and other Events for other components and/or clients to subscribe to.  When a component is deployed, updated or deleted, this use-case describes how the Canvas integrates with the Event Management component to configure Event Publishing on a topic. The use case uses the following assumptions:

* The Notifications to be published are an explicit part of the ODA Component definition. The Golden Components will include this as part of their definition and the Event Publication can also be tested by the Component CTK.
* The ODA Components are **not** given raised priveleges to publish their Notifications directly; Instead, software operators in the Canvas read the Component definition and configure the component. This model allows the component vendor to express their requirement for publishing Notification in the component definition, and allows the SRE (Site Reliability Team) for the operator to determine how the Notifications are published. 
* Whilst the reference implementation will provide a reference `Event Publishing Operator`, in typical implementations this will be specific to the Operations team that is running their Canvas, and will link to their own standards and policies. It is also possible that Event Management vendors (or open-source communities) develop standard `Event Publishing Operators` for their own API Gateway.

## Install component

![enableEventPublishing](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventPublishing.puml)
[plantUML code](pumlFiles/enableEventPublishing.puml)

## Upgrade component - with changed publishedNotifications

The use-case above is for the install of a new component. If you upgrade a component and change the schema of a publishedNotification, the configuration of the Topic on the Event Management system should change.

![enableEventPublishing](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventPublishing-with-modify.puml)
[plantUML code](pumlFiles/enableEventPublishing-with-modify.puml)

## Upgrade component - with additional publishedNotifications

If you upgrade a component and the new component has a new publishedNotification, the Event Management system should be reconfigured.

![enableEventPublishing](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventPublishing-with-add.puml)
[plantUML code](pumlFiles/enableEventPublishing-with-add.puml)

## Upgrade component - with deleted publishedNotifications

If you upgrade a component and the new component has a new publishedNotification, the Event Management system should be reconfigured.


![enableEventPublishing](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventPublishing-with-delete.puml)
[plantUML code](pumlFiles/enableEventPublishing-with-delete.puml)

## Delete component 

If you delete a component a cleanup of the used resources is required.

![enableEventPublishing](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas-ctk/main/usecase-library/pumlFiles/enableEventPublishing-delete.puml)
[plantUML code](pumlFiles/enableEventPublishing-delete.puml)

## TODO What if no event manager exists

