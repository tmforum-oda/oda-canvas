# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

# As part of use case 1 the Bootstrap process will assign an Admin role to the Canvas `seccon` user. 
# This user will be used for all subsequent API calls from the Canvas. The `seccon` user was created as part of the Canvas setup. See issue 85

@UC005         # tagged as use case 5
@UC005-F001    # tagged as use feature 1 within use case 5
Feature: UC005-F001 Bootstrap:Apply Standard Defined Role to Canvas Admin user

    Scenario: Create role for security user in the identity platform
        Given an example package 'productcatalog-v1beta3' has been installed
        When the 'productcatalogmanagement' component has a deployment status of 'Complete'
        Then I should see the predefined role assigned to the 'seccon' user for the 'productcatalogmanagement' component in the identity platform

