# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
 
@UC005         # tagged as use case 5
@UC005-F007    # tagged as use feature 7 within use case 5
Feature: UC005-F007 Bootstrap: Create,Update and Delete PartyRoles as Businees/Job Roles in the Identity Platform
 
    Scenario: Creation of PartyRoles as business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>'
	When I create a new permission specification set '<businessrole>' in the identity platform
	Then I should see '<businessrole>' created in the identity platform
 
   Scenario: Updation of PartyRoles as business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>'
	When I update a permission specification set '<businessrole>' in the identity platform
 	Then I should see the updated '<businessrole>' in the identity platform
 
   Scenario: Deletion of PartyRoles as business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>'
	When I Delete a  permission specification set '<businessrole>' in the identity platform
	Then I should not be able to see '<businessrole>' in the identity platform

   Scenario: Mapping of technical roles to business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>'
	When I map a '<RoleName>'  to '<businessrole>' in the identity platform
	Then I should be able see the mapping between '<RoleName>' & '<businessrole>' in the identity platform

   Scenario: Update Mapping of technical roles to business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>' 
	When I update a mapping with new  '<RoleName1>'  to '<businessrole>' in the identity platform
	Then I should be able see the updated mapping between '<RoleName1>' & '<businessrole>' in the identity platform

   Scenario :Deletion Mapping of technical roles to business/job roles in the identity platform
        Given an installed package '<PackageName>' called '<ComponentName>'
   	When I delete a mapping with '<RoleName1>'  to '<businessrole>' in the identity platform
   	Then I should not be able see the mapping between '<RoleName1>' & '<businessrole>' in the identity platform
   
   Examples:
      | Type   | PackageName                         | ComponentName            | RoleName  | businessrole |
      | static | productcatalog-static-roles-v1beta3 | productcatalogmanagement | cat1owner | Brole        |

