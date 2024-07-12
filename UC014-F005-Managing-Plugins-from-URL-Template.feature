# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC014         # tagged as use case 14
@UC014-F005    # tagged as use feature 5 within use case 14
Feature: UC014-F005 : Managing Plugins from URL Template

    Scenario: Download and Apply Plugins from URL
        Given  a valid URL 'template_url' is provided to download plugin configurations in yaml format
        When the 'manage_plugins_from_url()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then plugins are downloaded from 'template_url', applied in Kubernetes namespace 'namespace', and their names are returned

    Scenario: Failed Template Download
        Given an invalid or unreachable URL 'template_url' is provided
        When the 'manage_plugins_from_url()' function is called with 'spec', 'name', 'namespace', and 'meta'
        Then template download fails, and an appropriate error message is logged
