# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC012         # tagged as use case 12
@UC012-F001    # tagged as feature 1 within use case 12
Feature: UC012-F001 View Functional Observability

    Scenario: Install component and test Observability config
        Given You install a package 'productcatalog' with a metrics API 'metrics' and release name 'ctk'
        When the component 'ctk-productcatalog' has a deployment status of 'Complete'
        Then the 'metrics' endpoint should be monitored by the Observability platform

    Scenario: Uninstall component and test Observability config is cleaned up
        Given A package 'productcatalog' with a metrics API 'metrics' and release name 'ctk' has been installed
        And the component 'ctk-productcatalog' has a deployment status of 'Complete'
        When the package with release 'ctk' is uninstalled
        Then the 'metrics' endpoint should not be monitored by the Observability platform

    Scenario: Install component and view Observability metrics
        Given A package 'productcatalog' with a metrics API 'metrics' and release name 'ctk' has been installed
        And the component 'ctk-productcatalog' has a deployment status of 'Complete'
        When traffic is sent to the 'productcatalog' component to trigger metrics
        Then you observe metrics in the Observability platform