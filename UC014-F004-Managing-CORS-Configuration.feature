# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC014         # tagged as use case 14
@UC014-F004    # tagged as use feature 4 within use case 14
Feature: UC014-F004 : Managing CORS Configuration

     Scenario:  Apply CORS Plugin
         Given CORS is enabled with respective configuration
         When the 'manage_cors()' function is called with 'spec', 'name', 'namespace', and 'meta'
         Then a CORS plugin named 'plugin_name' is created or updated in the Kubernetes namespace 'namespace'

      Scenario:  Disable CORS Plugin
         Given CORS is enabled with respective configuration
         When the 'manage_cors()' function is called with 'spec', 'name', 'namespace', and 'meta'
         Then the CORS plugin associated with 'name' in namespace 'namespace' is removed or not created

       Scenario:  CORS Plugin Already Exists
         Given a CORS plugin named 'plugin_name' already exists in Kubernetes namespace 'namespace'
         When the 'manage_cors()' function is called with 'spec', 'name', 'namespace', and 'meta'
         Then the existing CORS plugin 'plugin_name' is updated with the new configuration specified in 'spec'

        Scenario: Update HTTPRoute Annotations with CORS
         Given CORS annotations are provided to update for an existing HTTPRoute resource
         When  the 'update_httproute_annotations()' function is called with 'name', 'namespace', and 'annotations'
         Then annotations for the HTTPRoute 'name' in namespace 'namespace' are updated successfully to include 'plugin_name'
    
