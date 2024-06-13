# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
@UC014         # tagged as use case 14
@UC014-F002    # tagged as use feature 2 within use case 14
Feature: UC014-F001 : Invoke Rate Limitting Plugin

    Scenario Outline: Successfully Managing Rate Limit
        Given a valid specification, name, namespace, metadata, and logger
        When the function manage_ratelimit is called
        Then the rate limiting plugin is successfully managed
        And log messages indicate successful plugin management
        
