# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC005         # tagged as use case 5
@UC005-F006    # tagged as use feature 6 within use case 5
Feature: UC005-F006 Bootstrap: Create,Update and Delete Corresponding Technical Roles in the Identity Platform

    Scenario Outline: Add Permission Specification Set in Component
        Given An installed package '<PackageName>' with a '<ComponentName>' component
        When I create a new permission specification set '<RoleName>' in the '<ComponentName>' component
        Then I should see '<RoleName>' created in the identity platform
        
    Scenario Outline: Change Permission Specification Set in Component
        Given An installed package '<PackageName>' with a '<ComponentName>' component
        When I change a permission specification set '<RoleName>' in the '<ComponentName>' component
        Then I should see '<RoleName>' changed in the identity platform

    Scenario Outline: Delete Permission Specification Set from Component
        Given An installed package '<PackageName>' with a '<ComponentName>' component
        When I delete a permission specification set '<RoleName>' from the '<ComponentName>' component
        Then I should see '<RoleName>' deleted from the identity platform
        
    Examples:
       | Type      | PackageName                         | ComponentName            | RoleName  |
       | static    | productcatalog-static-roles-v1beta3 | productcatalogmanagement | cat1owner |
       | partyrole | productcatalog-enhanced-v1beta3     | productcatalogmanagement | cat2owner |
