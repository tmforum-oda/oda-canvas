# Component Registry

The Component Registry is a service for registering and querying components.

## Usage

## Data Model

### componentRegistry

* url
* upstream/downstream/self


### Component

* componentName
* arrayOfLabels
** labelName
** labelValue
* owningComponentRegistryRef


### Exposed API

* componentRef
** canvasIdRef
** componentNameRef
* oasSpecification
* url
* visibility


### Upstream Registries

* componentRegistryURL


## Methods

* create/updateComponent
* deleteComponent
* [opt] getComponent
* create/updateExposedAPI
* deleteExposedAPI
* [opt] getExposedAPI
* searchExposedAPI
** oasSpecification
** [opt] labelsSelector
* requestConnection
* registerUpstreamRegistry
* unregisterUpstreamRegistry
* syncToUpstream
* syncFromDownstream


## Events

# Sequence Diagram

```plantuml
@startuml

box "ODA Canvas"
entity "Component prodcat" as Component
participant "Component\nManagement\nOperator" as ComponentOperator
entity ExposedAPI
participant "API\nManagement\nOperator" as APIMgmtOperator
end box

box  "Local Registry"
participant "Component\nRegistry" as ComponentRegistry
end box

Component -> ComponentOperator : create
ComponentOperator -> ComponentRegistry : create(prodcat, labels[team:odafans])
ComponentOperator -> ExposedAPI : create(pcapi)
ExposedAPI -> APIMgmtOperator : on.create(pcapi)
APIMgmtOperator -> ComponentRegistry : createExposedAPI(prodcat, pcapi)
APIMgmtOperator -> APIMgmtOperator : ready(pcapi)
APIMgmtOperator -> ComponentRegistry : updateExposedAPI(prodcat, pcapi)

@enduml
```
