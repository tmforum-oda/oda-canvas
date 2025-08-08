@UC012-F003 @OpenTelemetry @Jaeger @Observability
Feature: UC012-F003 - Verify OpenTelemetry Collector Integration

  As a platform operator
  I want to verify that the OpenTelemetry collector is properly integrated with Jaeger
  So that traces from components can flow through the observability pipeline for authentication logging

  Background:
    # Given the observability stack is installed

  # Scenario: Verify OpenTelemetry collector is configured for Jaeger
    # When I check the OpenTelemetry collector configuration
    # Then the collector should be configured to export traces to Jaeger
    # And the collector should be reachable on port 4318
    # And the collector should be sending traces to "observability-jaeger-collector:4317"

  # Scenario: Verify OpenTelemetry collector pipeline configuration
    # Given the OpenTelemetry collector is running
    # When I check the collector pipeline configuration
    # Then the collector should have OTLP HTTP receiver on port 4318
    # And the collector should have OTLP gRPC receiver on port 4317
    # And the collector should have batch processor configured
    # And the collector should have Jaeger OTLP exporter configured

  # Scenario: Verify OpenTelemetry collector service discovery
    # Given the OpenTelemetry collector is running
    # When I check the collector service endpoints
    # Then the collector service should be discoverable as "observability-opentelemetry-collector"
    # And the collector should be accessible from within the "monitoring" namespace
    # And the collector should be accessible from other namespaces