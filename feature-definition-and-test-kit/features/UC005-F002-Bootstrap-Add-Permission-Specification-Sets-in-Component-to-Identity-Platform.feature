# The 'business stakeholders' for the canvas Behaviour Driven Design are the Engineering teams
# from the Vendor of a component, from a Systems Integrator who may be integrating and deploying 
# a component, or a Service Provider's Operations team who may be supporting a component.

@UC005         # tagged as use case 5
@UC005-F002    # tagged as use feature 2 within use case 5
Feature: UC005-F002 Bootstrap: Add Dynamic Roles from Component to Identity Platform
# The Dynamic Roles allow the component to add, update and delete roles at run-time by exposing a User Roles and Permissions API.
# The User Roles and Permissions API has a PermissionSpecificationSet resource that allows the component to define roles and permissions dynamically.

    Scenario: Bootstrap component with dynamic permission specification sets
        Given a baseline 'productcatalog-dynamic-roles-v1' package installed as release 'dynamic'
        When the 'dynamic-productcatalogmanagement' component has a deployment status of 'Complete'
        Then I should see the 'userrolesandpermissions' ExposedAPI resource on the 'dynamic-productcatalogmanagement' component with a url on the Service Mesh or Gateway

    Scenario: Add a new permission specification set via TMF672 API
        Given a baseline 'productcatalog-dynamic-roles-v1' package installed as release 'dynamic'
        When I POST a new PermissionSpecificationSet to the 'dynamic-productcatalogmanagement' component with the following details:
             | name         | description                    | involvementRole |
             | DynamicRole1 | Test dynamic role for UC005    | TestRole        |
             | DynamicRole2 | Test dynamic role for UC005    | TestRole        |
        Then the role 'DynamicRole1' should be created in the Identity Platform for 'dynamic-productcatalogmanagement' component
        And the role 'DynamicRole2' should be created in the Identity Platform for 'dynamic-productcatalogmanagement' component

    Scenario: Delete a permission specification set via TMF672 API
        Given the 'dynamic-productcatalogmanagement' component has an existing PermissionSpecificationSet 'DynamicRole1'
        And the role 'DynamicRole1' exists in the Identity Platform for 'dynamic-productcatalogmanagement' component
        When I DELETE the PermissionSpecificationSet 'DynamicRole1' from the 'dynamic-productcatalogmanagement' component
        Then the role 'DynamicRole1' should be removed from the Identity Platform for 'dynamic-productcatalogmanagement' component

    Scenario: Delete the Component and the Client should be removed from the Identity Platform 
        Given the 'dynamic-productcatalogmanagement' component has an existing PermissionSpecificationSet 'DynamicRole2'
        And the role 'DynamicRole2' exists in the Identity Platform for 'dynamic-productcatalogmanagement' component
        When I uninstall the release 'dynamic'
        Then the client 'dynamic-productcatalogmanagement' should be removed from the Identity Platform

