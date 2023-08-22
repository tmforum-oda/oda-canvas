# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F003    # tagged as feature 3 within use case 2
Feature: UC002-F003 Expose APIs: Verify API implementation is ready

    Scenario: Verify API Resource is ready for Core API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'productcatalogmanagement' API resource with an implementation ready status on the Service Mesh or Gateway

    Scenario: Verify API Resource is ready for Management API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'managementFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'metrics' API resource with an implementation ready status on the Service Mesh or Gateway

    Scenario: Verify API Resource is ready for Security API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'securityFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'partyrole' API resource with an implementation ready status on the Service Mesh or Gateway


