# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC017         # tagged as use case 17 (PDB Management)
@UC017-F003    # tagged as feature 3 within use case 17
Feature: UC017-F003 PDB Management - Webhook Validation

    Background:
        Given the PDB Management Operator is deployed in the 'canvas' namespace
        And the operator is running and ready
        And webhooks are enabled for the operator

    Scenario: Validate AvailabilityPolicy creation with valid configuration
        When I create an AvailabilityPolicy with valid configuration:
            | name              | valid-policy            |
            | namespace         | components              |
            | availabilityClass | high-availability       |
            | enforcement       | strict                  |
            | priority          | 100                     |
        Then the AvailabilityPolicy should be created successfully
        And the webhook should validate the policy configuration

    Scenario: Reject AvailabilityPolicy with invalid availability class
        When I create an AvailabilityPolicy with configuration:
            | name              | invalid-class-policy    |
            | namespace         | components              |
            | availabilityClass | invalid-class           |
            | enforcement       | strict                  |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'supported values'

    Scenario: Reject AvailabilityPolicy with invalid enforcement mode
        When I create an AvailabilityPolicy with configuration:
            | name              | invalid-enforcement     |
            | namespace         | components              |
            | availabilityClass | standard                |
            | enforcement       | invalid-mode            |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'supported values'

    Scenario: Validate custom PDB configuration constraints
        When I create an AvailabilityPolicy with custom PDB config:
            | name              | custom-invalid          |
            | namespace         | components              |
            | availabilityClass | custom                  |
            | minAvailable      | 2                       |
            | maxUnavailable    | 1                       |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'cannot specify both minAvailable and maxUnavailable'

    Scenario: Default values for optional fields
        When I create an AvailabilityPolicy with minimal configuration:
            | name              | minimal-policy          |
            | namespace         | components              |
            | availabilityClass | standard                |
        Then the AvailabilityPolicy should be created successfully
        And the policy should have default enforcement mode 'advisory'
        And the policy should have default priority '50'

    Scenario: Validate maintenance window format
        When I create an AvailabilityPolicy with invalid maintenance window:
            | name              | bad-maintenance         |
            | namespace         | components              |
            | availabilityClass | standard                |
            | maintenanceWindow | invalid-format          |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'should match'

    Scenario: Validate selector configuration
        When I create an AvailabilityPolicy without any selector:
            | name              | no-selector             |
            | namespace         | components              |
            | availabilityClass | standard                |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'must specify at least one selection criteria'

    Scenario: Validate priority range
        When I create an AvailabilityPolicy with invalid priority:
            | name              | invalid-priority        |
            | namespace         | components              |
            | availabilityClass | standard                |
            | priority          | -1                      |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'priority must be between 0 and 1000'

    Scenario: Update validation provides warnings for policy changes
        Given an AvailabilityPolicy 'existing-policy' exists with priority '100'
        When I update the AvailabilityPolicy 'existing-policy' changing availability class to 'high-availability'
        Then the AvailabilityPolicy update should be successful
        And the webhook should provide warnings about policy changes

    Scenario: Validate flexible enforcement minimum class
        When I create an AvailabilityPolicy with flexible enforcement:
            | name              | flex-invalid            |
            | namespace         | components              |
            | availabilityClass | standard                |
            | enforcement       | flexible                |
            | minimumClass      | mission-critical        |
        Then the AvailabilityPolicy creation should be rejected
        And the webhook should return error message containing 'minimumClass cannot be higher than availabilityClass'