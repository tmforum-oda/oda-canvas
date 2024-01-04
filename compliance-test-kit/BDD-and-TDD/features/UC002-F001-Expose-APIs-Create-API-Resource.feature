# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F001    # tagged as use feature 1 within use case 2
Feature: UC002-F001 Expose APIs: Create API Resource

    Scenario: Create API Resource for Core API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'productcatalogmanagement' API resource on the 'productcatalog' component

    Scenario: Create API Resource for Management API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'managementFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'metrics' API resource on the 'productcatalog' component

    Scenario: Create API Resource for Security API
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'securityFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I should see the 'partyrole' or 'permissionSpecificationSet' API resource on the 'productcatalog' component



