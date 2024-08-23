# Manage Components use case

This use-case describes the Lifecycle Management when an ODA Component is Installed, Updated or Uninstalled.

It uses the following assumptions:

* The ODA Component describes the requirements (for its Core Function, Management and Security) in a machine-readible specification conforming to the [Component Design Guidelines](https://github.com/tmforum-oda/oda-ca-docs/blob/master/ODAComponentDesignGuidelines.md).
* The ODA Component conforms to the latest [ODA Component API Specification](https://github.com/tmforum-oda/oda-canvas/blob/master/charts/oda-crds/templates/oda-component-crd.yaml) or the previous (N-1) or (N-2) version.
* The Component Operator decomposes the ODA Component resource into multiple sub-resources (for Exposed APIs, Dependent APIs, Published Events, Subscribed Events, Observability, Identity etc). These sub-resources are processed by their corresponding operators.
* The Component Operator summarises the status of the sub-resources and the overall status of the ODA Component. The component will have a status of 'In-Progress' until all the sub-resource updates are complete. The component will then have a status of 'Complete'. 

## Install component

![manage-components-install](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/manage-components-install.puml)
[plantUML code](pumlFiles/manage-components-install.puml)

## Upgrade component

The upgrade could include new, updated or deleted Exposed APIs, Dependent APIs, Published Events or Subscribed Events.
It can also include updates to the Observability, Identity or Secrets metadata etc.

![manage-components-update](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/manage-components-update.puml)
[plantUML code](pumlFiles/manage-components-update.puml)

## Delete component

The component deletion should clean-up all the resources created during the installation of the component. If any of the clean-up processes fail, the component deletion should be cancelled.

![manage-components-uninstall](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/tmforum-oda/oda-canvas/master/usecase-library/pumlFiles/manage-components-uninstall.puml)
[plantUML code](pumlFiles/manage-components-uninstall.puml)

## Error scenarios

The component only creates the sub-resources and retrieves status updates from them. The component will have a status of 'In-Progress' until all the sub-resource updates are complete. The component will then have a status of 'Complete'. 
For troubleshooting, you need to check each of the sub-resources. The sub-resources will also have an 'In-Progress' and 'Complete' statuses. The sub-resources may also implement a 'In-Progress-Retry-Backoff' state if it has failed multiple times. This state reflexts that it is retrying more infrequently and that there is likely an issue that needs to be resolved.

