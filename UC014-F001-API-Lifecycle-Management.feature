# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
@UC014         # tagged as use case 14
@UC014-F001    # tagged as use feature 1 within use case 14
Feature: UC014-F001 : API Lifecycle Management

    Scenario Outline: Successfully Managing API Lifecycle
        Given a valid API specification, name, namespace, status, and metadata
        When the function manage_api_lifecycle is called
        Then the HTTPRoute is successfully created or updated
        And plugins (rate limit, API key verification, CORS, and plugins from URL) are successfully managed
        And annotations are updated for the HTTPRoute with plugin names
        And log messages indicate successful operations

        
        
        

