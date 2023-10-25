# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC002         # tagged as use case 2
@UC002-F005    # tagged as feature 5 within use case 2
Feature: UC002-F005 Expose APIs: Upgrade component with removed API

    Background:
        Given An example package 'productcatalog-enhanced-v1beta2' with a 'productcatalog' component with '2' API in its 'coreFunction' segment
        When I install the 'productcatalog-enhanced-v1beta2' package
        # And the 'productcatalog' component has a deployment status of 'Complete' - won't work at the moment as there is no API implementation for promotionmanagement
     
    Scenario: Upgrade component with removed API in coreFunction
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I upgrade the 'productcatalog-v1beta2' package
        Then I should not see the 'promotionmanagement' API resource on the 'productcatalog' component