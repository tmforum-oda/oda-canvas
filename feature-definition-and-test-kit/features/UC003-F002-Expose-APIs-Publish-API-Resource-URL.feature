# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC003         # tagged as use case 3
@UC003-F002    # tagged as feature 2 within use case 3
Feature: UC003-F002 Expose APIs: Publish API Resource URL

    Scenario: Test API Resource URL for Core API
        Given an example package 'productcatalog-v1beta4' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta4' package
        Then I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Management API
        Given an example package 'productcatalog-v1beta4' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'managementFunction' segment
        When I install the 'productcatalog-v1beta4' package
        Then I should see the 'metrics' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

    Scenario: Test API Resource URL for Security API
        Given an example package 'productcatalog-v1beta4' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'securityFunction' segment
        When I install the 'productcatalog-v1beta4' package
        Then I should see the 'partyrole' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway



