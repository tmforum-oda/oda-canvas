# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.
 
@UC005         # tagged as use case 5
@UC005-F007    # tagged as use feature 7 within use case 5
Feature: UC005-F007 Bootstrap: Create,Update and Delete PartyRoles as Businees/Job Roles and Mapping with Technical Roles in the Identity Platform
 
    Scenario: Creation of PartyRoles as Business Roles in the Identity Platform
        Given An installed package '<PackageName>' called '<ComponentName>'
	When I create a new business role '<businessrole>' in the identity platform
	Then I should see '<businessrole>' created in the identity platform
 
    Scenario: Updation of PartyRoles as Business Roles in the Identity Platform
        Given An installed package '<PackageName>' called '<ComponentName>'
	When I update a business role '<businessrole>' in the identity platform
 	Then I should see the updated '<businessrole>' in the identity platform
 
    Scenario: Deletion of PartyRoles as Business Roles in the Identity Platform
        Given An installed package '<PackageName>' called '<ComponentName>'
	When I delete a  business role '<businessrole>' in the identity platform
	Then I should not be able to see '<businessrole>' in the identity platform

    Scenario: Mapping of Technical roles to Business Roles in the Identity Platform
        Given An installed package '<PackageName>' called '<ComponentName>'
	And Technical role '<RoleName>' is present in the identity platform
 	And Business role '<businessrole>' is present in the identity platform
	When I map a '<RoleName>' to '<businessrole>' in the identity platform
	Then I should be able to see the mapping between '<RoleName>' & '<businessrole>' in the identity platform

    Scenario: Update Mapping of Technical roles to Business Roles in the Identity Platform
        Given an installed package '<PackageName>' called '<ComponentName>' 
	And Technical roles '<RoleName>' and '<RoleName1>' is present in the identity platform
 	And Business role '<businessrole>' is present in the identity platform
  	And '<RoleName>' is mapped with '<businessrole>' in the identity platform
	When I update the mapping with new '<RoleName1>' to '<businessrole>' in the identity platform
	Then I should be able see the updated mapping between '<RoleName1>' & '<businessrole>' in the identity platform

    Scenario: Delete Mapping of Technical roles to Business Roles in the Identity Platform
        Given An installed package '<PackageName>' called '<ComponentName>'
	And Technical role '<RoleName1>' is present in the identity platform
 	And Business role '<businessrole>' is present in the identity platform
  	And '<RoleName1>' is mapped with '<businessrole>' in the identity platform
   	When I delete a mapping with '<RoleName1>' to '<businessrole>' in the identity platform
   	Then I should not be able see the mapping between '<RoleName1>' & '<businessrole>' in the identity platform
   
    Examples:
       | Type   | PackageName                         | ComponentName            | RoleName  | businessrole | RoleName1 |
       | static | productcatalog-static-roles-v1 | productcatalogmanagement | cat1owner | Brole        | cat2owner |
