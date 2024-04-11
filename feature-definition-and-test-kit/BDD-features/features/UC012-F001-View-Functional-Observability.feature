# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC012         # tagged as use case 12
@UC012-F001    # tagged as feature 1 within use case 12
Feature: UC012-F001 View Functional Observability

    Scenario: Install component and test Observability config
        Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
        When the component 'ctk-productcatalog' has a deployment status of 'Complete'
        Then the Observability platform monitors the 'metrics' endpoint 

    Scenario: Uninstall component and test Observability config is cleaned up
        Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
        And the component 'ctk-productcatalog' has a deployment status of 'Complete'
        When I uninstall the package with release 'ctk'
        Then the Observability platform does not monitor the 'metrics' endpoint 

    Scenario Outline: Install component and view Observability metrics
        Given I install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
        And the component 'ctk-productcatalog' has a deployment status of 'Complete'
        When A user creates a '<Resource>' in the 'productcatalog' component
        Then the Observability platform shows the '<Event>' metrics

    Examples:
       | Resource | Event          |
       | category | createCategory |
       | catalog  | createCatalog  |
