# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC014         # tagged as use case 14
@UC014-F001    # tagged as use feature 1 within use case 14
Feature: UC014-F001 : Managing Rate Limit

    Scenario: Apply Rate Limit Plugin
        Given the rate limiting feature is enabled
        When the 'manage_ratelimit()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then a rate limit plugin named 'plugin_name' is created or updated in the Kubernetes namespace 'namespace'

    Scenario: Disable Rate Limit Plugin
        Given the rate limiting feature is disabled
        When the 'manage_ratelimit()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then the rate limit plugin associated with 'name' in namespace 'namespace' is removed or not created.

     Scenario: Rate Limit Plugin Already Exists
        Given a rate limit plugin named 'plugin_name' already exists in Kubernetes namespace 'namespace'.
        When the 'manage_ratelimit()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then the existing rate limit plugin 'plugin_name' is updated with the new configuration specified in 'spec'.

     Scenario: Update HTTPRoute Annotations with Rate Limit
        Given rate limit annotations are provided to update for an existing HTTPRoute resource.
        When the 'update_httproute_annotations()' function is called with 'name', 'namespace', and 'annotations'.
        Then annotations for the HTTPRoute 'name' in namespace 'namespace' are updated successfully to include 'plugin_name'.

     Scenario: Delete API Resource with Rate Limit
        Given an API resource 'name' with an associated rate limit plugin exists in Kubernetes namespace 'namespace'.
        When the API resource is deleted
        Then the ExposedAPI 'name' is deleted, and the associated rate limit plugin 'plugin_name' is automatically deleted as a child resource.

     
     
        
