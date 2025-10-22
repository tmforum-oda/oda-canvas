# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC003         # tagged as use case 3
@UC003-F005    # tagged as feature 5 within use case 3
Feature: UC003-F005 Expose APIs: Upgrade component with removed API

    Background:
        Given an example package 'productcatalog-enhanced-v1' with '2' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-enhanced-v1' package
        And the 'ctk-productcatalogmanagement' component has a deployment status of 'Complete'
     
    Scenario: Upgrade component with removed ExposedAPI in coreFunction
        Given an example package 'productcatalog-v1' with '1' ExposedAPI in its 'coreFunction' segment
        When I upgrade the 'productcatalog-v1' package
        Then I should not see the 'promotionmanagement' ExposedAPI resource on the 'ctk-productcatalogmanagement' component