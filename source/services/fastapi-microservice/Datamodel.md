## Data Model


### Registry

* name
* type - upstream/downstream/self
* url
* arrayOfLabels
* arrayOfComponents


### Component

* registryName
* name
* arrayOfLabels
* arrayOfExposedAPIs


### ExposedAPI

* registryName
* componentName
* name
* url
* oasSpecification
* status - pending/ready
* arrayOfLabels


### Label

A label is a simple Key-Value Pair

* key
* value




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
