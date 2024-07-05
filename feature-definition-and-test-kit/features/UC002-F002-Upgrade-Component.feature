# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F002    # tagged as use feature 2 within use case 2
Feature: UC002-F002 Upgrade Component

    Scenario Outline: Updated component with added ExposedAPI resources
        Given A baseline 'productcatalog-v1beta3' package installed as release 'pc'
        Given An example package 'productcatalog-enhanced-v1beta3' with a 'productcatalogmanagement' component with '2' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog-enhanced-v1beta3' package as release 'pc'
        Then I should see the 'promotionmanagement' ExposedAPI resource on the 'productcatalogmanagement' component

    Scenario Outline: Updated component with removed ExposedAPI resources
        Given A baseline 'productcatalog-enhanced-v1beta3' package installed as release 'pc'
        Given An example package 'productcatalog-v1beta3' with a 'productcatalogmanagement' component with '1' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog-v1beta3' package as release 'pc'
        Then I should not see the 'promotionmanagement' ExposedAPI resource on the 'productcatalogmanagement' component

    Scenario Outline: Updated component with updated ExposedAPI resources
        Given A baseline 'productcatalog-v1beta3' package installed as release 'pc'
        Given An example package 'productcatalog-updated-v1beta3' with a 'productcatalogmanagement' component with '1' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog-updated-v1beta3' package as release 'pc'
        Then I should see the 'productcatalogmanagement' ExposedAPI resource on the 'productcatalogmanagement' component with specification 'https://raw.githubusercontent.com/tmforum-apis/TMF620_ProductCatalog/master/TMF620-ProductCatalog-v4.0.1.swagger.json'
