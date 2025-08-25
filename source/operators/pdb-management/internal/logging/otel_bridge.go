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

	"github.com/go-logr/logr"
	"go.opentelemetry.io/otel/trace"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// WithOpenTelemetryFields adds OpenTelemetry-compliant fields to the logger
func WithOpenTelemetryFields(ctx context.Context) context.Context {
	span := trace.SpanFromContext(ctx)

	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()

		// Store trace info in context for later retrieval
		ctx = context.WithValue(ctx, contextKey("trace_id"), spanContext.TraceID().String())
		ctx = context.WithValue(ctx, contextKey("span_id"), spanContext.SpanID().String())

		// Get current logger and ensure trace fields are present
		logger := log.FromContext(ctx)
		logger = EnsureTraceFields(ctx, logger)

		// Update context with enriched logger
		ctx = log.IntoContext(ctx, logger)
	}

	return ctx
}

// ExtractTraceContext extracts trace context from incoming requests (for webhook/HTTP handlers)
func ExtractTraceContext(ctx context.Context, traceHeader string) context.Context {
	if traceHeader == "" {
		return ctx
	}

	// Parse W3C Trace Context header format: version-traceid-spanid-traceflags
	// Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
	parts := parseTraceHeader(traceHeader)
	if parts == nil {
		return ctx
	}

	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"trace_id", parts["trace_id"],
		"span_id", parts["span_id"],
		"parent_span_id", parts["span_id"], // The incoming span becomes parent
	)

	return log.IntoContext(ctx, logger)
}

// GetTraceID retrieves the trace ID from context (not just from span)
func GetTraceID(ctx context.Context) string {
	// First try to get from context value
	if traceID, ok := ctx.Value(contextKey("trace_id")).(string); ok && traceID != "" {
		return traceID
	}

	// Fall back to span
	span := trace.SpanFromContext(ctx)
	if span != nil && span.SpanContext().IsValid() {
		return span.SpanContext().TraceID().String()
	}
	return ""
}

// GetSpanID retrieves the span ID from the current span
func GetSpanID(ctx context.Context) string {
	span := trace.SpanFromContext(ctx)
	if span != nil && span.SpanContext().IsValid() {
		return span.SpanContext().SpanID().String()
	}
	return ""
}

// EnrichLoggerWithTrace creates a logger enriched with trace information
func EnrichLoggerWithTrace(ctx context.Context) logr.Logger {
	logger := log.FromContext(ctx)

	if traceID := GetTraceID(ctx); traceID != "" {
		logger = logger.WithValues("trace_id", traceID)
	}

	if spanID := GetSpanID(ctx); spanID != "" {
		logger = logger.WithValues("span_id", spanID)
	}

	if correlationID := GetCorrelationID(ctx); correlationID != "" {
		logger = logger.WithValues("correlationID", correlationID)
	}

	return logger
}

// EnsureTraceFields ensures trace fields are present in the logger
func EnsureTraceFields(ctx context.Context, logger logr.Logger) logr.Logger {
	span := trace.SpanFromContext(ctx)

	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()

		// Always add trace fields (these should be unique)
		logger = logger.WithValues(
			"trace_id", spanContext.TraceID().String(),
			"span_id", spanContext.SpanID().String(),
		)

		// Add trace flags if sampled
		if spanContext.IsSampled() {
			logger = logger.WithValues("trace_flags", "01")
		}
	}

	// Add correlation ID if present (only if not already present)
	if correlationID := GetCorrelationID(ctx); correlationID != "" {
		logger = logger.WithValues("correlationID", correlationID)
	}

	return logger
}

// parseTraceHeader parses W3C Trace Context header
func parseTraceHeader(header string) map[string]string {
	// Simplified parser - in production, use a proper W3C parser
	// Format: version-traceid-spanid-traceflags
	const expectedParts = 4
	const traceIDLen = 32
	const spanIDLen = 16

	parts := make(map[string]string)

	// Basic validation
	if len(header) < 55 { // minimum valid length
		return nil
	}

	// Extract trace ID (32 hex chars)
	if len(header) > 3+traceIDLen {
		parts["trace_id"] = header[3 : 3+traceIDLen]
	}

	// Extract span ID (16 hex chars)
	if len(header) > 36+spanIDLen {
		parts["span_id"] = header[36 : 36+spanIDLen]
	}

	return parts
}

// ConvertCorrelationToTraceID converts a UUID correlation ID to a valid trace ID
// OpenTelemetry trace IDs are 16 bytes (32 hex characters)
func ConvertCorrelationToTraceID(correlationID string) string {
	// Remove hyphens from UUID
	cleanID := ""
	for _, c := range correlationID {
		if c != '-' {
			cleanID += string(c)
		}
	}

	// Ensure it's exactly 32 characters
	if len(cleanID) == 32 {
		return cleanID
	}

	// If not 32 chars, generate a valid trace ID from the correlation ID
	// by hashing or padding as needed
	return padOrTruncate(cleanID, 32)
}

func padOrTruncate(s string, length int) string {
	if len(s) >= length {
		return s[:length]
	}
	// Pad with zeros
	for len(s) < length {
		s += "0"
	}
	return s
}
