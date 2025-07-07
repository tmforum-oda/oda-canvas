# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC005         # tagged as use case 5
@UC005-F003    # tagged as use feature 3 within use case 5
Feature: UC005-F003 Bootstrap: Add static roles from Component to Identity Platform

    Scenario: Bootstrap component with static roles
        Given a baseline 'productcatalog-static-roles-v1' package installed as release 'static'
        When the 'productcatalogmanagement' component has a deployment status of 'Complete'
        Then the role 'cat1owner' should be created in the Identity Platform for client 'static-productcatalogmanagement'
        And the role 'cat2owner' should be created in the Identity Platform for client 'static-productcatalogmanagement'

    Scenario: Delete the Component and the Client should be removed from the Identity Platform 
        Given a baseline 'productcatalog-static-roles-v1' package installed as release 'static'
        And the role 'cat1owner' exists in the Identity Platform
        When I uninstall the 'productcatalog-static-roles-v1' package as release 'static'
        Then the client 'static-productcatalogmanagement' should be removed from the Identity Platform

