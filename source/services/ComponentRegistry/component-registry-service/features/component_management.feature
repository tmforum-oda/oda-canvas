Feature: Component Management
  As a component developer
  I want to manage Components in registries
  So that I can publish and discover ODA Components

  Background:
    Given the Component Registry Service is running
    And a Component Registry named "test-registry" exists

  Scenario: Create a new Component
    Given no Components exist in registry "test-registry"
    When I create a Component "user-service" in registry "test-registry"
    Then the request should succeed with status code 200
    And the response should contain the component "user-service"

  Scenario: Create Component with duplicate name
    Given a Component "existing-component" exists in registry "test-registry"
    When I create a Component "existing-component" in registry "test-registry"
    Then the request should fail with status code 400
    And the response should indicate already exists error

  Scenario: Create Component in non-existent registry
    When I create a Component "test-component" in registry "non-existent-registry"
    Then the request should fail with status code 400

  Scenario: Retrieve all Components
    Given a Component "component-1" exists in registry "test-registry"
    And a Component "component-2" exists in registry "test-registry"
    When I request all Components
    Then the request should succeed with status code 200
    And the response should contain 2 components
    And the response should contain the component "component-1"
    And the response should contain the component "component-2"

  Scenario: Retrieve Components for specific registry
    Given a Component "registry-component" exists in registry "test-registry"
    When I request all Components for registry "test-registry"
    Then the request should succeed with status code 200
    And the response should contain 1 components
    And the response should contain the component "registry-component"

  Scenario: Retrieve Components for non-existent registry
    When I request all Components for registry "non-existent-registry"
    Then the request should fail with status code 404
    And the response should indicate not found error

  Scenario: Registry with no Components
    When I request all Components for registry "test-registry"
    Then the request should succeed with status code 200
    And the response should contain 0 components