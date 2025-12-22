# UC016 - ODA Component and API Inventory

## Use Case Overview

**Title:** Component and API Inventory   
**ID:** UC016  
**Actor:** ODA Canvas Operators, External Systems, Management Tools  
**Goal:** Provide a centralized registry of deployed ODA Components, their exposed APIs, and management capabilities  

## Description

The Resource Inventory serves as a read-only registry that provides visibility into the current state of the ODA Canvas. It maintains an up-to-date catalog of all deployed ODA Components, their exposed APIs, operational status, and management endpoints. This enables discovery, monitoring, and integration capabilities for both internal Canvas operations and external management tools.


## Preconditions

- ODA Canvas is deployed and operational (including Resource Inventory microservice)
- There are some Components deployed in Canvas


## Main Flow

![resource-inventory-registry](./pumlFiles/resource-inventory-registry.svg)
[plantUML code](pumlFiles/resource-inventory-registry.puml)


## Requirements

- **REQ-REG-001:** Registry MUST provide read-only access to component and API information
- **REQ-REG-002:** Registry MUST support filtering and pagination for large datasets
- **REQ-REG-003:** Registry MUST publish events for all lifecycle changes

## Related Use Cases

- UC002-Manage-Components: Components registered through this use case appear in the registry
- UC003-Configure-Exposed-APIs: APIs configured through this use case are registered

## Test Scenarios

The detailed test scenarios for this use case are defined in the BDD features:
- UC016-F001-Component-Registry-Management.feature
- UC016-F002-Exposed-API-Registry-Management.feature  
- UC016-F003-Component-and-API-Discovery.feature
- UC016-F004-Registry-Event-Publishing.feature
- UC016-F005-Canvas-Integration-and-Management-Tools.feature

## Implementation Notes

- The Resource Inventory implements the TMF639 Resource Inventory Management specification
- Registry data follows TMF639 data models with Canvas-specific Characteristics
- Events follow the TMF688 Event Management specification
- Authentication integrates with Canvas Identity Management services
