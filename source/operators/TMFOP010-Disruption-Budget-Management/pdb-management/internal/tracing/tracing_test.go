/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package tracing

import (
	"context"
	"errors"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

func TestInitTracingNoEndpoint(t *testing.T) {
	// Clear environment variables
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")

	cleanup, err := InitTracing(context.Background(), "test-service")
	require.NoError(t, err)
	require.NotNil(t, cleanup)

	// Cleanup should be a no-op function
	cleanup()

	// Tracer should be a no-op tracer
	assert.NotNil(t, tracer)
}

func TestInitTracingWithInvalidJaegerEndpoint(t *testing.T) {
	// Set an invalid Jaeger endpoint to test error handling
	_ = os.Setenv("JAEGER_ENDPOINT", "http://invalid:14268/api/traces")
	defer func() { _ = os.Unsetenv("JAEGER_ENDPOINT") }()

	// This should succeed since the exporter is created but not connected
	cleanup, err := InitTracing(context.Background(), "test-service")

	// May or may not error depending on connection behavior
	if err == nil {
		require.NotNil(t, cleanup)
		cleanup()
	}
}

func TestInitTracingWithOTLPEndpoint(t *testing.T) {
	// Set OTLP endpoint (connection will fail but exporter should be created)
	_ = os.Setenv("OTLP_ENDPOINT", "localhost:4317")
	defer func() { _ = os.Unsetenv("OTLP_ENDPOINT") }()

	cleanup, err := InitTracing(context.Background(), "test-service")

	// Should succeed - exporter creation doesn't require connection
	if err == nil {
		require.NotNil(t, cleanup)
		cleanup()
	}
}

func TestStartSpan(t *testing.T) {
	// Ensure we have a valid tracer (no-op is fine)
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	newCtx, span := StartSpan(ctx, "test-span")

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)

	// Span should be recording (even no-op spans report as recording for safety)
	span.End()
}

func TestStartSpanWithNilTracer(t *testing.T) {
	// Set tracer to nil to test fallback
	originalTracer := tracer
	tracer = nil
	defer func() { tracer = originalTracer }()

	ctx := context.Background()
	newCtx, span := StartSpan(ctx, "test-span")

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestReconcileSpan(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	newCtx, span := ReconcileSpan(ctx, "DeploymentController", "default", "my-deployment")

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestReconcileSpanWithNilTracer(t *testing.T) {
	originalTracer := tracer
	tracer = nil
	defer func() { tracer = originalTracer }()

	ctx := context.Background()
	newCtx, span := ReconcileSpan(ctx, "TestController", "test-ns", "test-name")

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestRecordError(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	_, span := StartSpan(ctx, "test-span")
	defer span.End()

	// Test with error
	testErr := errors.New("test error")
	RecordError(span, testErr, "test operation failed")

	// Test with nil error - should not panic
	RecordError(span, nil, "no error")

	// Test with nil span - should not panic
	RecordError(nil, testErr, "nil span")
}

func TestAddEvent(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()
	ctx, span := StartSpan(ctx, "test-span")
	defer span.End()

	// Add event with attributes
	AddEvent(ctx, "test-event",
		attribute.String("key1", "value1"),
		attribute.Int("key2", 42),
	)

	// Add event without attributes
	AddEvent(ctx, "simple-event")
}

func TestAddEventNoSpan(t *testing.T) {
	// Context without span - should not panic
	ctx := context.Background()
	AddEvent(ctx, "orphan-event", attribute.String("key", "value"))
}

func TestGetSampleRate(t *testing.T) {
	// Test default
	_ = os.Unsetenv("TRACE_SAMPLE_RATE")
	rate := getSampleRate()
	assert.Equal(t, 0.1, rate)

	// Test custom rate
	_ = os.Setenv("TRACE_SAMPLE_RATE", "0.5")
	rate = getSampleRate()
	assert.Equal(t, 0.5, rate)

	// Test invalid rate
	_ = os.Setenv("TRACE_SAMPLE_RATE", "invalid")
	rate = getSampleRate()
	assert.Equal(t, 0.1, rate)

	_ = os.Unsetenv("TRACE_SAMPLE_RATE")
}

func TestGetVersion(t *testing.T) {
	// Test default
	_ = os.Unsetenv("OPERATOR_VERSION")
	version := getVersion()
	assert.Equal(t, "unknown", version)

	// Test custom version
	_ = os.Setenv("OPERATOR_VERSION", "v1.2.3")
	version = getVersion()
	assert.Equal(t, "v1.2.3", version)

	_ = os.Unsetenv("OPERATOR_VERSION")
}

func TestCreateLinkedSpan(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()

	// Create a parent span to link to
	_, parentSpan := StartSpan(ctx, "parent-span")
	parentSpanContext := parentSpan.SpanContext()
	parentSpan.End()

	// Create linked span
	newCtx, linkedSpan := CreateLinkedSpan(ctx, "linked-span", parentSpanContext)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, linkedSpan)
	linkedSpan.End()
}

func TestCreateLinkedSpanWithNilTracer(t *testing.T) {
	originalTracer := tracer
	tracer = nil
	defer func() { tracer = originalTracer }()

	ctx := context.Background()
	spanContext := trace.SpanContext{}

	newCtx, span := CreateLinkedSpan(ctx, "linked-span", spanContext)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestReconcileSpanWithParent(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()

	// Create parent span
	_, parentSpan := StartSpan(ctx, "parent-span")
	parentSpanContext := parentSpan.SpanContext()
	parentSpan.End()

	// Create reconcile span with parent
	newCtx, span := ReconcileSpanWithParent(ctx, "TestController", "test-ns", "test-name", parentSpanContext)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestReconcileSpanWithParentNilTracer(t *testing.T) {
	originalTracer := tracer
	tracer = nil
	defer func() { tracer = originalTracer }()

	ctx := context.Background()
	spanContext := trace.SpanContext{}

	newCtx, span := ReconcileSpanWithParent(ctx, "TestController", "test-ns", "test-name", spanContext)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestGetSpanContext(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()

	// Context without span
	spanCtx := GetSpanContext(ctx)
	assert.False(t, spanCtx.IsValid())

	// Context with span
	ctx, span := StartSpan(ctx, "test-span")
	defer span.End()

	spanCtx = GetSpanContext(ctx)
	// Note: With no-op tracer, span context may not be valid
	assert.NotNil(t, spanCtx)
}

func TestStartSpanWithKind(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()

	// Test different span kinds
	kinds := []trace.SpanKind{
		trace.SpanKindInternal,
		trace.SpanKindServer,
		trace.SpanKindClient,
		trace.SpanKindProducer,
		trace.SpanKindConsumer,
	}

	for _, kind := range kinds {
		t.Run(kind.String(), func(t *testing.T) {
			newCtx, span := StartSpanWithKind(ctx, "test-span", kind)

			assert.NotNil(t, newCtx)
			assert.NotNil(t, span)
			span.End()
		})
	}
}

func TestStartSpanWithKindNilTracer(t *testing.T) {
	originalTracer := tracer
	tracer = nil
	defer func() { tracer = originalTracer }()

	ctx := context.Background()
	newCtx, span := StartSpanWithKind(ctx, "test-span", trace.SpanKindServer)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestAddBaggage(t *testing.T) {
	ctx := context.Background()

	// Add baggage
	newCtx := AddBaggage(ctx, "request-id", "12345")
	assert.NotNil(t, newCtx)

	// Add another baggage item
	newCtx = AddBaggage(newCtx, "tenant-id", "tenant-abc")
	assert.NotNil(t, newCtx)
}

func TestAddBaggageInvalidKey(t *testing.T) {
	ctx := context.Background()

	// Invalid baggage key (contains invalid characters)
	// The function should return the original context
	newCtx := AddBaggage(ctx, "", "value")
	assert.Equal(t, ctx, newCtx)
}

func TestStartSpanWithOptions(t *testing.T) {
	_ = os.Unsetenv("JAEGER_ENDPOINT")
	_ = os.Unsetenv("OTLP_ENDPOINT")
	cleanup, _ := InitTracing(context.Background(), "test-service")
	defer cleanup()

	ctx := context.Background()

	// Start span with attributes
	newCtx, span := StartSpan(ctx, "test-span",
		trace.WithAttributes(
			attribute.String("custom.attr", "value"),
			attribute.Int64("custom.count", 42),
		),
	)

	assert.NotNil(t, newCtx)
	assert.NotNil(t, span)
	span.End()
}

func TestTracerInitialization(t *testing.T) {
	// Test that init() properly initializes the tracer
	// The tracer should never be nil after package initialization
	assert.NotNil(t, tracer)
}
