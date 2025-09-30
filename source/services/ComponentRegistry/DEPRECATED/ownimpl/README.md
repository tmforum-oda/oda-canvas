# Component Registry

The Component Registry is a service for registering and querying components.

## Usage

## Data Model

### componentRegistry

* name
* url
* type (upstream/downstream/self)
* arrayOfLabels
** labelKey
** labelValue


### Component

* registryName
* componentName
* arrayOfLabels
** labelKey
** labelValue
* arrayOfExposedAPIs


### Exposed API

* registryName
* componentName
* oasSpecification
* url
* visibility
* arrayOfLabels
** labelKey
** labelValue


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
