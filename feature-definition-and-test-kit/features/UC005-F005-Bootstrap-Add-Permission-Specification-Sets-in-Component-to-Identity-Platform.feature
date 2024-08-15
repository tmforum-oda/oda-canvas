# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC005         # tagged as use case 5
@UC005-F005    # tagged as use feature 5 within use case 5
Feature: UC005-F005 Bootstrap: Add Permission Specification Sets in Component to Identity Platform

    Scenario Outline: Add Permission Specification Sets in Component to Identity Platform
        Given an example package '<PackageName>' with a '<ComponentName>' component with '<Number>' existing roles
        And '<PackageName>' exposes permission specification sets using '<Type>'
        When I install the '<PackageName>' package
        Then I should see all '<Number>' roles listed against the client '<PackageName>' in the Identity Platform

    Examples:
       | Type      | PackageName                         | ComponentName            | Number |
       | static    | productcatalog-static-roles-v1beta3 | productcatalogmanagement | 3      |
       | partyrole | productcatalog-enhanced-v1beta3     | productcatalogmanagement | 3      |
