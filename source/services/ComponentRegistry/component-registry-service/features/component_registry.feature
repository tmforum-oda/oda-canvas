Feature: Component Registry Management
  As a platform administrator
  I want to manage Component Registries
  So that I can organize and access ODA Components

  Background:
    Given the Component Registry Service is running

  Scenario: Create a new Component Registry
    Given no Component Registries exist
    When I create a Component Registry named "production-registry"
    Then the request should succeed with status code 200
    And the response should contain the registry "production-registry"

  Scenario: Create Component Registry with duplicate name
    Given a Component Registry named "existing-registry" exists
    When I create a Component Registry named "existing-registry"
    Then the request should fail with status code 400
    And the response should indicate already exists error

  Scenario: Create Component Registry with invalid data
    Given no Component Registries exist
    When I try to create a Component Registry with an invalid name ""
    Then the request should fail with status code 422
    And the response should indicate validation error

  Scenario: Retrieve all Component Registries
    Given a Component Registry named "registry-1" exists
    And a Component Registry named "registry-2" exists
    When I request all Component Registries
    Then the request should succeed with status code 200
    And the response should contain 2 registries
    And the response should contain the registry "registry-1"
    And the response should contain the registry "registry-2"

  Scenario: Retrieve specific Component Registry
    Given a Component Registry named "test-registry" exists
    When I request the Component Registry "test-registry"
    Then the request should succeed with status code 200
    And the response should contain the registry "test-registry"

  Scenario: Retrieve non-existent Component Registry
    Given no Component Registries exist
    When I request the Component Registry "non-existent"
    Then the request should fail with status code 404
    And the response should indicate not found error

  Scenario: Update Component Registry
    Given a Component Registry named "update-registry" exists
    When I update the Component Registry "update-registry" with new URL "https://updated.example.com/api"
    Then the request should succeed with status code 200
    And the registry "update-registry" should have URL "https://updated.example.com/api"

  Scenario: Update non-existent Component Registry
    Given no Component Registries exist
    When I update the Component Registry "non-existent" with new URL "https://new.example.com/api"
    Then the request should fail with status code 404
    And the response should indicate not found error

  Scenario: Delete Component Registry
    Given a Component Registry named "delete-registry" exists
    When I delete the Component Registry "delete-registry"
    Then the request should succeed with status code 200
    And the response should indicate successful deletion

  Scenario: Delete non-existent Component Registry
    Given no Component Registries exist
    When I delete the Component Registry "non-existent"
    Then the request should fail with status code 404
    And the response should indicate not found error