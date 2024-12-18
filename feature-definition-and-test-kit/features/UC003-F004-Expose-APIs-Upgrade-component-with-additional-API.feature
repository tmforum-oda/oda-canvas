# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC003         # tagged as use case 3
@UC003-F004    # tagged as feature 4 within use case 3
Feature: UC003-F004 Expose APIs: Upgrade component with additional ExposedAPI

    Background:
        Given an example package 'productcatalog-v1' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-v1' package
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'
     
    Scenario: Upgrade component with additional ExposedAPI in coreFunction
        Given an example package 'productcatalog-enhanced-v1' with a 'productcatalogmanagement' component with '2' ExposedAPI in its 'coreFunction' segment
        When I upgrade the 'productcatalog-enhanced-v1' package
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'
        Then I should see the 'promotionmanagement' ExposedAPI resource on the 'productcatalogmanagement' component