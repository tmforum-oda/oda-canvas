# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC014         # tagged as use case 14
@UC014-F003    # tagged as use feature 3 within use case 14
Feature: UC014-F003 : Managing API Authentication (JWT)

    Scenario: Apply JWT Authentication Plugin
        Given JWT authentication is enabled with configuration
        When the 'manage_apiauthentication()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then a JWT authentication plugin named 'plugin_name' is created or updated in the Kubernetes namespace 'namespace' with respective settings

    Scenario: Disable JWT Authentication Plugin
        Given JWT authentication is disabled
        When the 'manage_apiauthentication()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then the JWT authentication plugin associated with 'name' in namespace 'namespace' is removed or not created

     Scenario: JWT Authentication Plugin Already Exists
        Given a JWT authentication plugin named 'plugin_name' already exists in Kubernetes namespace 'namespace'
        When the 'manage_apiauthentication()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then the existing JWT authentication plugin 'plugin_name' is updated with the new configuration specified in 'spec'

     Scenario: Update HTTPRoute Annotations with JWT Authentication
        Given JWT authentication annotations are provided to update for an existing HTTPRoute resource
        When the 'update_httproute_annotations()' function is called with 'name', 'namespace', and 'annotations'
        Then annotations for the HTTPRoute 'name' in namespace 'namespace' are updated successfully to include 'plugin_name'
        

      
