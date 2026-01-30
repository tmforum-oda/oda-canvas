# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC016 @UC016-F001
Feature: UC016-F001 Component Registry Management
    As an ODA Canvas
    I want to maintain a registry of deployed ODA Components
    So that external systems can discover and interact with components


    @UC016-F001-001
    Scenario: Query all resources (Components and Exposed APIs)
        Given only the 'productcatalog-v1' package is installed
        When the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
        Then the Resource Inventory API should contain the following resources:
            | resource id                                           | category      |
            | ctk-productcatalogmanagement                          | ODAComponent  |
            | ctk-productcatalogmanagement-metrics                  | API           |
            | ctk-productcatalogmanagement-productcatalogmanagement | API           |

    @UC016-F001-002
    Scenario: Query a specific resource by id
        Given only the 'productcatalog-v1' package is installed
        When the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
        Then I can query the Resource Inventory API for each of the following resources:
            | resource id                                           | category      |
            | ctk-productcatalogmanagement                          | ODAComponent  |
            | ctk-productcatalogmanagement-productcatalogmanagement | API           |

    @UC016-F001-003
    Scenario: Query for resources matching a filter
        Given only the 'productcatalog-v1' package is installed
        When the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
        Then I can query the Resource Inventory API with a filter for each of the following:
            | filter                                | number of resources  |
            | $[?(@.category=='ODAComponent')]      | 1                    |
            | $[?(@.category=='API')]               | 3                    |





