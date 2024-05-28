# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
 
@UC005         # tagged as use case 5
@UC005-F007    # tagged as use feature 7 within use case 5
Feature: UC001-F007 Bootstrap: Create,Update and Delete PartyRoles as Businees/Job Roles in the Identity Platform
 
    Scenario: Creation of PartyRoles as business/job roles in the identity platform 
        Given an installed package '<PackageName>' called '<ComponentName>'
		    When I create a new permission specification set '<partyrole>' in the '<ComponentName>' component
		    Then I should see '<partyroleName>' created in the identity platform

    Scenario: Updation of PartyRoles as business/job roles in the identity platform 
        Given an installed package '<PackageName>' called '<ComponentName>'
		    When I update a permission specification set '<partyrole>' in the '<ComponentName>' component
		    Then I should see the updated '<partyroleName>' in the identity platform

    Scenario: Deletion of PartyRoles as business/job roles in the identity platform 
        Given an installed package '<PackageName>' called '<ComponentName>'
		    When I Delte a  permission specification set '<partyrole>' in the '<ComponentName>' component
		    Then I should not be able see '<partyroleName>' in the identity platform
