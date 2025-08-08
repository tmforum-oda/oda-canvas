# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC012         # tagged as use case 12
@UC012-F001    # tagged as feature 1 within use case 12
Feature: UC012-F001 View Functional Observability

    Scenario: Install component and verify ServiceMonitor is created
        Given An example package 'productcatalog-v1' with a 'metrics' ExposedAPI in its 'managementFunction' segment
        When I install the 'productcatalog-v1' package with release name 'ctk'
        And the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
        Then a ServiceMonitor resource 'ctk-productcatalogmanagement-metrics' should exist in the 'components' namespace
        And the ServiceMonitor 'ctk-productcatalogmanagement-metrics' should be configured to scrape the 'metrics' endpoint

    Scenario: Uninstall component and verify ServiceMonitor is removed
        Given An example package 'productcatalog-v1' with a 'metrics' ExposedAPI in its 'managementFunction' segment
        When I install the 'productcatalog-v1' package with release name 'ctk'
        And the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
        When I uninstall the release 'ctk'
        Then the ServiceMonitor resource 'ctk-productcatalogmanagement-metrics' should not exist in the 'components' namespace



