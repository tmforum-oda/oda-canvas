# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC012         # tagged as use case 12
@UC012-F002    # tagged as feature 2 within use case 12
Feature: UC012-F002 Configure Open-Metrics collection

    # Skip this scenario if Service Monitor CRD and Prometheus Operator are not deployed
    @ServiceMonitor 
    Scenario: Install component and verify Open-Metrics collection is configured
        Given An example package 'productcatalog-v1' with a 'metrics' ExposedAPI in its 'managementFunction' segment
        When I install the 'productcatalog-v1' package with release name 'obs'
        And the 'obs-productcatalogmanagement' component has a deployment status of 'Complete'
        Then a ServiceMonitor resource 'obs-productcatalogmanagement-metrics' should exist in the 'components' namespace
        And the ServiceMonitor 'obs-productcatalogmanagement-metrics' should be configured to scrape the 'metrics' endpoint

    # Skip this scenario if Service Monitor CRD and Prometheus Operator are not deployed
    @ServiceMonitor 
    Scenario: Uninstall component and verify Open-Metrics collection is removed
        Given An example package 'productcatalog-v1' with a 'metrics' ExposedAPI in its 'managementFunction' segment
        When I install the 'productcatalog-v1' package with release name 'obs'
        And the 'obs-productcatalogmanagement' component has a deployment status of 'Complete'
        When I uninstall the release 'obs'
        Then the ServiceMonitor resource 'obs-productcatalogmanagement-metrics' should not exist in the 'components' namespace



