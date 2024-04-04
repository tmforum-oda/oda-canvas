# Manage Components use case

This use-case describes the initial actions that take place when an ODA Component is Installed, Updated or Uninstalled.

It uses the following assumptions:

* The ODA Component describes the requirements (for its Core Function, Management and Security) in a machine-readible specification conforming to the [Component Design Guidelines](https://github.com/tmforum-oda/oda-ca-docs/blob/master/ODAComponentDesignGuidelines.md).
* The ODA Component conforms to the latest [ODA Component API Specification](https://github.com/tmforum-oda/oda-canvas/blob/master/charts/oda-crds/templates/oda-component-crd.yaml) or the previous (N-1) or (N-2) version.
* The Component Operator decomposes the ODA Component resource into multiple sub-resources (for Exposed APIs, Dependent APIs, Published Events, Subscribed Events, Observability, Identity etc). These sub-resources are processed by their corresponding operators.
* The Component Operator summarises the status of the sub-resources and the overall status of the ODA Component.

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

The component status should be set to one of the Error status codes (i.e. `Error-Configuring-APIs`, `Error-Configuring-Events`, `Error-Configuring-IDM`, `Error-Configuring-Observability`, `Error-Configuring-Secrets`, `Error-Configuring-Dependencies`) if any of the sub-resources fail to be created, updated or deleted. Each operator should re-try a configurable number of times before setting the relavant Error status.


