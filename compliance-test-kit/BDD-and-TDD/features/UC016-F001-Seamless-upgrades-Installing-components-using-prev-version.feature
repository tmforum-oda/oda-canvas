# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC016         # tagged as use case 16
@UC016-F001    # tagged as use feature 1 within use case 16
Feature: UC016-F001 Seamless upgrade: Installing component using previous version

    Scenario: Installing a component using a previous (N-1) version
        Given An example package 'productcatalog-v1beta1' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta1' package
        Then I can query the 'v1beta2' spec version of the 'productcatalog' component
    
    Scenario: Installing a component using a previous (N-2) version
        Given An example package 'productcatalog-v1alpha4' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1alpha4' package
        Then I can query the 'v1beta2' spec version of the 'productcatalog' component
    



