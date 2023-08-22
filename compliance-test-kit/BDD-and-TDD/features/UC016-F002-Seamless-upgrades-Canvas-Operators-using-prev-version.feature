# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC016         # tagged as use case 16
@UC016-F002    # tagged as use feature 2 within use case 16
Feature: UC016-F002 Seamless upgrade: Canvas operators using previous version

    Scenario: Installing a component and testing access using a previous (N-1) version
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I can query the 'v1beta1' spec version of the 'productcatalog' component
    
    Scenario: Installing a component and testing access using a previous (N-2) version
        Given An example package 'productcatalog-v1beta2' with a 'productcatalog' component with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta2' package
        Then I can query the 'v1alpha4' spec version of the 'productcatalog' component
    


