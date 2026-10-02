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

package logging

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.opentelemetry.io/otel/trace/noop"
)

func TestWithOpenTelemetryFields(t *testing.T) {
	ctx := context.Background()

	// Without span
	newCtx := WithOpenTelemetryFields(ctx)
	assert.NotNil(t, newCtx)

	// With span
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	newCtx = WithOpenTelemetryFields(ctx)
	assert.NotNil(t, newCtx)
}

func TestExtractTraceContext(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name        string
		traceHeader string
		expectSame  bool
	}{
		{
			name:        "empty header",
			traceHeader: "",
			expectSame:  true,
		},
		{
			name:        "valid W3C trace header",
			traceHeader: "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
			expectSame:  false,
		},
		{
			name:        "invalid header - too short",
			traceHeader: "00-invalid",
			expectSame:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			newCtx := ExtractTraceContext(ctx, tt.traceHeader)
			assert.NotNil(t, newCtx)
			if tt.expectSame {
				// Context should be the same (or minimally modified)
				assert.NotNil(t, newCtx)
			}
		})
	}
}

func TestGetTraceID(t *testing.T) {
	ctx := context.Background()

	// Without trace context
	traceID := GetTraceID(ctx)
	assert.Equal(t, "", traceID)

	// With context value
	ctx = context.WithValue(ctx, contextKey("trace_id"), "test-trace-id-123")
	traceID = GetTraceID(ctx)
	assert.Equal(t, "test-trace-id-123", traceID)

	// With span (no-op tracer returns invalid span context)
	ctx = context.Background()
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	// No-op tracer doesn't produce valid span context
	traceID = GetTraceID(ctx)
	assert.Equal(t, "", traceID)
}

func TestGetSpanID(t *testing.T) {
	ctx := context.Background()

	// Without span
	spanID := GetSpanID(ctx)
	assert.Equal(t, "", spanID)

	// With span (no-op tracer returns invalid span context)
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	// No-op tracer doesn't produce valid span context
	spanID = GetSpanID(ctx)
	assert.Equal(t, "", spanID)
}

func TestEnrichLoggerWithTrace(t *testing.T) {
	ctx := context.Background()

	// Without any trace info
	logger := EnrichLoggerWithTrace(ctx)
	assert.NotNil(t, logger)

	// With correlation ID
	ctx = WithCorrelationID(ctx)
	logger = EnrichLoggerWithTrace(ctx)
	assert.NotNil(t, logger)

	// With trace context value
	ctx = context.WithValue(ctx, contextKey("trace_id"), "test-trace-id")
	logger = EnrichLoggerWithTrace(ctx)
	assert.NotNil(t, logger)
}

func TestEnsureTraceFields(t *testing.T) {
	ctx := context.Background()

	// Without span
	logger := EnrichLoggerWithTrace(ctx)
	result := EnsureTraceFields(ctx, logger)
	assert.NotNil(t, result)

	// With correlation ID
	ctx = WithCorrelationID(ctx)
	result = EnsureTraceFields(ctx, logger)
	assert.NotNil(t, result)

	// With span
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	result = EnsureTraceFields(ctx, logger)
	assert.NotNil(t, result)
}

func TestParseTraceHeader(t *testing.T) {
	tests := []struct {
		name         string
		header       string
		expectNil    bool
		expectFields map[string]string
	}{
		{
			name:      "valid W3C header",
			header:    "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
			expectNil: false,
			expectFields: map[string]string{
				"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
				"span_id":  "00f067aa0ba902b7",
			},
		},
		{
			name:      "header too short",
			header:    "00-short",
			expectNil: true,
		},
		{
			name:      "empty header",
			header:    "",
			expectNil: true,
		},
		{
			name:      "minimum valid length",
			header:    "00-12345678901234567890123456789012-1234567890123456-01",
			expectNil: false,
			expectFields: map[string]string{
				"trace_id": "12345678901234567890123456789012",
				"span_id":  "1234567890123456",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parseTraceHeader(tt.header)
			if tt.expectNil {
				assert.Nil(t, result)
			} else {
				assert.NotNil(t, result)
				for k, v := range tt.expectFields {
					assert.Equal(t, v, result[k])
				}
			}
		})
	}
}

func TestConvertCorrelationToTraceID(t *testing.T) {
	tests := []struct {
		name          string
		correlationID string
		expectedLen   int
	}{
		{
			name:          "valid UUID",
			correlationID: "550e8400-e29b-41d4-a716-446655440000",
			expectedLen:   32,
		},
		{
			name:          "UUID without hyphens",
			correlationID: "550e8400e29b41d4a716446655440000",
			expectedLen:   32,
		},
		{
			name:          "short ID",
			correlationID: "short-id",
			expectedLen:   32,
		},
		{
			name:          "very long ID",
			correlationID: "this-is-a-very-long-correlation-id-that-exceeds-32-characters",
			expectedLen:   32,
		},
		{
			name:          "empty ID",
			correlationID: "",
			expectedLen:   32,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ConvertCorrelationToTraceID(tt.correlationID)
			assert.Equal(t, tt.expectedLen, len(result))
		})
	}
}

func TestPadOrTruncate(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		length   int
		expected string
	}{
		{
			name:     "exact length",
			input:    "hello",
			length:   5,
			expected: "hello",
		},
		{
			name:     "needs padding",
			input:    "hi",
			length:   5,
			expected: "hi000",
		},
		{
			name:     "needs truncation",
			input:    "hello world",
			length:   5,
			expected: "hello",
		},
		{
			name:     "empty string",
			input:    "",
			length:   3,
			expected: "000",
		},
		{
			name:     "zero length",
			input:    "hello",
			length:   0,
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := padOrTruncate(tt.input, tt.length)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestWithOpenTelemetryFieldsPreservesContext(t *testing.T) {
	ctx := context.Background()

	// Add a value to context
	type customKey string
	ctx = context.WithValue(ctx, customKey("test"), "value")

	// Add correlation ID
	ctx = WithCorrelationID(ctx)

	// Apply OTEL fields
	newCtx := WithOpenTelemetryFields(ctx)

	// Original value should still be present
	assert.Equal(t, "value", newCtx.Value(customKey("test")))
}

func TestExtractTraceContextWithValidHeader(t *testing.T) {
	ctx := context.Background()

	// Valid W3C Trace Context header
	header := "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
	newCtx := ExtractTraceContext(ctx, header)

	assert.NotNil(t, newCtx)
	// The context should now have a logger with trace info
}

func TestGetTraceIDWithContextValue(t *testing.T) {
	ctx := context.Background()

	// Set trace ID in context
	expectedTraceID := "4bf92f3577b34da6a3ce929d0e0e4736"
	ctx = context.WithValue(ctx, contextKey("trace_id"), expectedTraceID)

	traceID := GetTraceID(ctx)
	assert.Equal(t, expectedTraceID, traceID)
}

func TestEnrichLoggerWithTraceAllFields(t *testing.T) {
	ctx := context.Background()

	// Set all possible trace fields
	ctx = context.WithValue(ctx, contextKey("trace_id"), "test-trace-id")
	ctx = WithCorrelationID(ctx)

	logger := EnrichLoggerWithTrace(ctx)
	assert.NotNil(t, logger)
}
