@UC012-F004 @EndToEnd @Tracing @Observability
Feature: UC012-F004 - Verify End-to-End Tracing Pipeline

  As a platform operator
  I want to verify that traces can flow end-to-end through the complete observability pipeline
  So that I can ensure authentication events will be properly captured and visible in Jaeger

  Background:
    # Given the observability stack is installed
    # And the OpenTelemetry collector is running

  # Scenario: Send test trace through complete observability pipeline
    # When I send a test trace to the collector endpoint
    # Then the trace should be successfully received by the collector
    # And the trace should appear in Jaeger within 30 seconds
    # And the trace should have the correct service name
    # And the trace should have the correct span information

  # Scenario: Verify multiple traces can be processed
    # When I send 5 test traces to the collector endpoint
    # Then all traces should be successfully received by the collector
    # And all traces should appear in Jaeger within 60 seconds
    # And each trace should be uniquely identifiable
    # And the traces should be searchable by service name

  # Scenario: Verify component trace integration
    # Given a component "ctk-productcatalogmanagement" is installed with tracing enabled
    # When I make an API call to the component endpoint "/tmf-api/productCatalogManagement/v4/catalog"
    # Then traces should be generated for the API call
    # And the traces should appear in Jaeger within 30 seconds
    # And the service should be visible in Jaeger services list
    # And the trace should contain HTTP request information

  # Scenario: Verify trace search and filtering
    # Given traces exist in Jaeger for service "test-service"
    # When I search for traces by service name "test-service"
    # Then I should find at least 1 trace
    # And the traces should have valid trace IDs
    # And the traces should have proper timestamp information
    # And I should be able to view trace details