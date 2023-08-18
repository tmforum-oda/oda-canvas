# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

Feature: UC016-F001 Seamless upgrade: Installing component using previous version

    Scenario: Installing a component using a previous (N-1) version
        Given An example component 'productcatalog-v1beta1' with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1beta1' component
        Then I can query the 'v1beta2' spec version of the 'productcatalog' component
    
    Scenario: Installing a component using a previous (N-2) version
        Given An example component 'productcatalog-v1alpha4' with '1' API in its 'coreFunction' segment
        When I install the 'productcatalog-v1alpha4' component
        Then I can query the 'v1beta2' spec version of the 'productcatalog' component
    



