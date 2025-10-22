# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC012         # tagged as use case 12
@UC012-F001    # tagged as use case 12 - feature 1
Feature: UC012-F001 - OpenTelemetry Collector configuration

    # Skip this scenario if Open Telemetry collector is not deployed
    @OpenTelemetryCollector 
    Scenario: Verify OpenTelemetry metrics and logs are collected

        Given I install the 'productcatalog-v1' package with release name 'obs'
        And the 'obs-productcatalogmanagement' component has a deployment status of 'Complete'
        And I capture the baseline OpenTelemetry metrics
        When the 'obs-productcatalogmanagement' component has the following 'category' data:
            | name                      | description                                       |
            | IoT line of product       | IoT devices and solutions                         |
        Then I should see new OpenTelemetry events in the OpenTelemetry Collector


