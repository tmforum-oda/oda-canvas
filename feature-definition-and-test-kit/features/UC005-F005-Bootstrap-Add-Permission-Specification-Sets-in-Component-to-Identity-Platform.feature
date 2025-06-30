# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC005         # tagged as use case 5
@UC005-F005    # tagged as use feature 5 within use case 5
Feature: UC005-F005 Bootstrap: Add Permission Specification Sets in Component to Identity Platform

    Scenario: Bootstrap component with dynamic permission specification sets
        Given an example package 'productcatalog-dynamic-roles-v1' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'securityFunction' segment
        When I install the 'productcatalog-dynamic-roles-v1' package
        And the 'productcatalogmanagement' component has a deployment status of 'Complete'
        Then I should see the 'permissionspecificationset' ExposedAPI resource on the 'productcatalogmanagement' component with a url on the Service Mesh or Gateway

    Scenario: Add a new permission specification set via TMF672 API
        Given an example package 'productcatalog-dynamic-roles-v1' with a 'productcatalogmanagement' component with '1' ExposedAPI in its 'securityFunction' segment
        When I POST a new PermissionSpecificationSet with the following details:
             | name         | description                    | involvementRole |
             | DynamicRole1 | Test dynamic role for UC005    | TestRole        |
        Then the role 'DynamicRole1' should be created in the Identity Platform for client 'ctk-productcatalogmanagement'

    Scenario: Delete a permission specification set via TMF672 API
        Given the 'ctk-productcatalogmanagement' component has an existing PermissionSpecificationSet 'DynamicRole1'
        And the role 'DynamicRole1' exists in the Identity Platform
        When I DELETE the PermissionSpecificationSet 'DynamicRole1' from the TMF672 API
        Then the role 'DynamicRole1' should be removed from the Identity Platform for client 'ctk-productcatalogmanagement'

