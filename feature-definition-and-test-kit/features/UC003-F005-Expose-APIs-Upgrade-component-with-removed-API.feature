# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC003         # tagged as use case 3
@UC003-F005    # tagged as feature 5 within use case 3
Feature: UC003-F005 Expose APIs: Upgrade component with removed API

    Background:
        Given An example package 'productcatalog-enhanced-v1beta3' with a 'productcatalogmanagement' component with '2' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-enhanced-v1beta3' package
        # And the 'productcatalog' component has a deployment status of 'Complete' - won't work at the moment as there is no ExposedAPI implementation for promotionmanagement
     
    Scenario: Upgrade component with removed ExposedAPI in coreFunction
        Given An example package 'productcatalog-v1beta3' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        When I upgrade the 'productcatalog-v1beta3' package
        Then I should not see the 'promotionmanagement' ExposedAPI resource on the 'productcatalogmanagement' component