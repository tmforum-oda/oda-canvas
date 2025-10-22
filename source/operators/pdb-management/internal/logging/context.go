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
	"fmt"
	"time"

	"github.com/go-logr/logr"
	"github.com/google/uuid"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// Context keys for storing values
type contextKey string

const (
	correlationIDKey contextKey = "correlationID"
	operationKey     contextKey = "operation"
	reconcileIDKey   contextKey = "reconcileID"
)

// WithCorrelationID adds a correlation ID to the logger and context
func WithCorrelationID(ctx context.Context) context.Context {
	correlationID := uuid.New().String()

	// Add to context
	ctx = context.WithValue(ctx, correlationIDKey, correlationID)

	// Add to logger
	logger := log.FromContext(ctx)
	logger = logger.WithValues("correlationID", correlationID)

	// Update context with logger
	ctx = log.IntoContext(ctx, logger)

	return ctx
}

// GetCorrelationID retrieves the correlation ID from context
func GetCorrelationID(ctx context.Context) string {
	if id, ok := ctx.Value(correlationIDKey).(string); ok {
		return id
	}
	return ""
}

// WithReconcileID adds a reconcile ID to the logger and links it to the span
func WithReconcileID(ctx context.Context, reconcileID string) context.Context {
	// Add to context
	ctx = context.WithValue(ctx, reconcileIDKey, reconcileID)

	logger := log.FromContext(ctx)

	// Add reconcile ID to logger
	logger = logger.WithValues("reconcileID", reconcileID)

	// If we have a span, add it as an attribute
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("reconcile.id", reconcileID),
		)
	}

	return log.IntoContext(ctx, logger)
}

// GetReconcileID retrieves the reconcile ID from context
func GetReconcileID(ctx context.Context) string {
	if id, ok := ctx.Value(reconcileIDKey).(string); ok {
		return id
	}
	return ""
}

// WithDeploymentContext adds deployment information to the logger
func WithDeploymentContext(ctx context.Context, namespace, name string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"deployment.name", name,
		"deployment.namespace", namespace,
		"resource.type", "deployment", // OpenTelemetry semantic convention
	)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("k8s.deployment.name", name),
			attribute.String("k8s.namespace.name", namespace),
			attribute.String("k8s.resource.type", "deployment"),
		)
	}

	return log.IntoContext(ctx, logger)
}

// WithPolicyContext adds policy information to the logger
func WithPolicyContext(ctx context.Context, namespace, name string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"policy.name", name,
		"policy.namespace", namespace,
		"resource.type", "availabilitypolicy", // OpenTelemetry semantic convention
	)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("k8s.policy.name", name),
			attribute.String("k8s.namespace.name", namespace),
			attribute.String("k8s.resource.type", "availabilitypolicy"),
		)
	}

	return log.IntoContext(ctx, logger)
}

// WithPDBContext adds PDB information to the logger
func WithPDBContext(ctx context.Context, namespace, name string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"pdb.name", name,
		"pdb.namespace", namespace,
		"resource.type", "poddisruptionbudget", // OpenTelemetry semantic convention
	)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("k8s.pdb.name", name),
			attribute.String("k8s.namespace.name", namespace),
			attribute.String("k8s.resource.type", "poddisruptionbudget"),
		)
	}

	return log.IntoContext(ctx, logger)
}

// WithOperation adds operation context
func WithOperation(ctx context.Context, operation string) context.Context {
	// Add to context
	ctx = context.WithValue(ctx, operationKey, operation)

	// Add to logger
	logger := log.FromContext(ctx)
	logger = logger.WithValues("operation", operation)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(attribute.String("operation.name", operation))
	}

	return log.IntoContext(ctx, logger)
}

// GetOperation retrieves the current operation from context
func GetOperation(ctx context.Context) string {
	if op, ok := ctx.Value(operationKey).(string); ok {
		return op
	}
	return ""
}

// WithComponent adds component information to the logger
func WithComponent(ctx context.Context, componentName, componentFunction string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"component.name", componentName,
		"component.function", componentFunction,
	)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("component.name", componentName),
			attribute.String("component.function", componentFunction),
		)
	}

	return log.IntoContext(ctx, logger)
}

// WithAvailabilityClass adds availability class to the logger
func WithAvailabilityClass(ctx context.Context, class string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues("availabilityClass", class)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(attribute.String("availability.class", class))
	}

	return log.IntoContext(ctx, logger)
}

// WithError adds error information to the logger
func WithError(ctx context.Context, err error) context.Context {
	if err == nil {
		return ctx
	}

	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"error", err.Error(),
		"errorType", fmt.Sprintf("%T", err),
	)

	// Record error in span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.RecordError(err)
	}

	return log.IntoContext(ctx, logger)
}

// WithOwnerReference adds owner reference information
func WithOwnerReference(ctx context.Context, kind, name string) context.Context {
	logger := log.FromContext(ctx)
	logger = logger.WithValues(
		"owner.kind", kind,
		"owner.name", name,
	)

	// Add to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.String("k8s.owner.kind", kind),
			attribute.String("k8s.owner.name", name),
		)
	}

	return log.IntoContext(ctx, logger)
}

// LoggerWithFields creates a logger with multiple fields
func LoggerWithFields(ctx context.Context, fields map[string]interface{}) logr.Logger {
	logger := log.FromContext(ctx)

	// Convert map to alternating key-value slice
	keysAndValues := make([]interface{}, 0, len(fields)*2)
	for k, v := range fields {
		keysAndValues = append(keysAndValues, k, v)
	}

	return logger.WithValues(keysAndValues...)
}

// StartOperation logs the start of an operation and returns a function to log completion
func StartOperation(ctx context.Context, operation string) func() {
	startTime := time.Now()
	logger := log.FromContext(ctx)

	logger.V(1).Info("Starting operation",
		"operation", operation,
		"startTime", startTime.Format(time.RFC3339))

	// Add event to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.AddEvent("operation.start", trace.WithAttributes(
			attribute.String("operation.name", operation),
		))
	}

	return func() {
		duration := time.Since(startTime)
		logger.V(1).Info("Completed operation",
			"operation", operation,
			"duration", duration.String(),
			"durationMs", duration.Milliseconds())

		// Add completion event to span if available
		if span != nil && span.IsRecording() {
			span.AddEvent("operation.complete", trace.WithAttributes(
				attribute.String("operation.name", operation),
				attribute.Int64("operation.duration_ms", duration.Milliseconds()),
			))
		}
	}
}

// LogDuration logs the duration of an operation
func LogDuration(ctx context.Context, operation string, duration time.Duration) {
	logger := log.FromContext(ctx)
	logger.V(1).Info("Operation duration",
		"operation", operation,
		"duration", duration.String(),
		"durationMs", duration.Milliseconds())

	// Add metric to span if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(
			attribute.Int64(fmt.Sprintf("%s.duration_ms", operation), duration.Milliseconds()),
		)
	}
}

// Helpers for structured logging

// Fields represents structured log fields
type Fields map[string]interface{}

// With adds fields to the logger
func With(ctx context.Context, fields Fields) context.Context {
	logger := LoggerWithFields(ctx, fields)
	return log.IntoContext(ctx, logger)
}

// Debug logs a debug message with optional fields
func Debug(ctx context.Context, msg string, fields ...Fields) {
	logger := log.FromContext(ctx)
	if len(fields) > 0 {
		logger = LoggerWithFields(ctx, fields[0])
	}
	logger.V(2).Info(msg)
}

// Info logs an info message with optional fields
func Info(ctx context.Context, msg string, fields ...Fields) {
	logger := log.FromContext(ctx)
	if len(fields) > 0 {
		logger = LoggerWithFields(ctx, fields[0])
	}
	logger.Info(msg)
}

// Warn logs a warning message with optional fields
func Warn(ctx context.Context, msg string, fields ...Fields) {
	logger := log.FromContext(ctx)
	if len(fields) > 0 {
		logger = LoggerWithFields(ctx, fields[0])
	}
	logger.Info(msg, "level", "warning")
}

// Error logs an error message with optional fields
func Error(ctx context.Context, err error, msg string, fields ...Fields) {
	logger := log.FromContext(ctx)
	if len(fields) > 0 {
		logger = LoggerWithFields(ctx, fields[0])
	}
	logger.Error(err, msg)
}
