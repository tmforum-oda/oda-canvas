# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC014         # tagged as use case 14
@UC014-F002    # tagged as use feature 2 within use case 14
Feature: UC014-F002 : API Lifecycle Management

    Scenario: Create API Resource
        Given a valid specification 'spec' for an API resource 'name' with necessary configurations
        When the API resource 'name' is created
        Then the operator creates an ExposedAPI custom resource in namespace 'namespace'
        And logs successful creation of ExposedAPI 'name'

    Scenario: Update API Resource
        Given an existing API resource 'name' with a modified specification 'spec'
        When the API resource 'name' is updated
        Then the operator updates the ExposedAPI custom resource in namespace 'namespace' with the new 'spec'
        And logs successful update of ExposedAPI 'name'

    Scenario: Delete API Resource
        Given an existing API resource 'name'
        When the API resource 'name' is deleted
        Then the operator deletes the ExposedAPI custom resource 'name' from namespace 'namespace'
        And logs successful deletion of ExposedAPI 'name'

    Scenario: Manage Plugins for API Resource
        Given an API resource 'name' with associated plugin configurations in its 'spec'
        When  the API resource 'name' is created or updated
        Then the operator applies the configured plugins (e.g., rate limit, JWT authentication, CORS) to the corresponding resources.
        And logs successful application of plugins for ExposedAPI 'name'


    

    

        
        
        

