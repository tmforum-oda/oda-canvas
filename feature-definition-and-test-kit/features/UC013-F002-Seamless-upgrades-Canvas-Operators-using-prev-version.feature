# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC013         # tagged as use case 13
@UC013-F002    # tagged as use feature 2 within use case 13
Feature: UC013-F002 Seamless upgrade: Canvas operators using previous version

    Scenario: Installing a component and testing access using a previous (N-1) version
        Given An example package 'productcatalog-v1beta3' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta3' package
        Then I can query the 'v1beta2' spec version of the 'productcatalogmanagement' component
    
    Scenario: Installing a component and testing access using a previous (N-2) version
        Given An example package 'productcatalog-v1beta3' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta3' package
        Then I can query the 'v1beta1' spec version of the 'productcatalogmanagement' component

    


