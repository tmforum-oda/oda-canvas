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
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"go.opentelemetry.io/otel/trace/noop"
)

func TestLogEntryStructure(t *testing.T) {
	now := time.Now().UTC()
	entry := LogEntry{
		Level:     "info",
		Timestamp: now,
		Message:   "test message",
		Controller: ControllerInfo{
			Type:  "DeploymentController",
			Name:  "deployment-controller",
			Group: "apps",
			Kind:  "Deployment",
		},
		Resource: ResourceInfo{
			Type:      "Deployment",
			Name:      "my-deployment",
			Namespace: "default",
			UID:       "12345",
			Version:   "v1",
			Labels: map[string]string{
				"app": "test",
			},
		},
		ReconcileID:       "reconcile-123",
		ParentReconcileID: "parent-456",
		CorrelationID:     "corr-789",
		Trace: &TraceInfo{
			TraceID: "trace-abc",
			SpanID:  "span-def",
		},
		Details: map[string]any{
			"key1": "value1",
			"key2": 42,
		},
	}

	assert.Equal(t, "info", entry.Level)
	assert.Equal(t, now, entry.Timestamp)
	assert.Equal(t, "test message", entry.Message)
	assert.Equal(t, "DeploymentController", entry.Controller.Type)
	assert.Equal(t, "deployment-controller", entry.Controller.Name)
	assert.Equal(t, "apps", entry.Controller.Group)
	assert.Equal(t, "Deployment", entry.Controller.Kind)
	assert.Equal(t, "Deployment", entry.Resource.Type)
	assert.Equal(t, "my-deployment", entry.Resource.Name)
	assert.Equal(t, "default", entry.Resource.Namespace)
	assert.Equal(t, "12345", entry.Resource.UID)
	assert.Equal(t, "v1", entry.Resource.Version)
	assert.Equal(t, "test", entry.Resource.Labels["app"])
	assert.Equal(t, "reconcile-123", entry.ReconcileID)
	assert.Equal(t, "parent-456", entry.ParentReconcileID)
	assert.Equal(t, "corr-789", entry.CorrelationID)
	assert.Equal(t, "trace-abc", entry.Trace.TraceID)
	assert.Equal(t, "span-def", entry.Trace.SpanID)
	assert.Equal(t, "value1", entry.Details["key1"])
	assert.Equal(t, 42, entry.Details["key2"])
}

func TestNewStructuredLogger(t *testing.T) {
	ctx := context.Background()

	logger := NewStructuredLogger(ctx)

	assert.NotNil(t, logger)
	assert.NotNil(t, logger.Logger)
	assert.Equal(t, ctx, logger.ctx)
}

func TestStructuredLoggerLogOperatorEvent(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	tests := []struct {
		name  string
		entry LogEntry
	}{
		{
			name: "minimal entry",
			entry: LogEntry{
				Level:     "info",
				Timestamp: time.Now().UTC(),
				Message:   "test message",
			},
		},
		{
			name: "full entry",
			entry: LogEntry{
				Level:             "info",
				Timestamp:         time.Now().UTC(),
				Message:           "full test message",
				ParentReconcileID: "parent-123",
				CorrelationID:     "corr-456",
				Trace: &TraceInfo{
					TraceID: "trace-789",
					SpanID:  "span-abc",
				},
				Details: map[string]any{
					"key": "value",
				},
			},
		},
		{
			name: "entry without optional fields",
			entry: LogEntry{
				Level:       "debug",
				Timestamp:   time.Now().UTC(),
				Message:     "debug message",
				ReconcileID: "reconcile-123",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			logger.LogOperatorEvent(tt.entry)
		})
	}
}

func TestStructuredLoggerCreateLogEntry(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	entry := logger.CreateLogEntry("info", "test message", map[string]any{"key": "value"})

	assert.Equal(t, "info", entry.Level)
	assert.Equal(t, "test message", entry.Message)
	assert.Equal(t, "value", entry.Details["key"])
	assert.False(t, entry.Timestamp.IsZero())
}

func TestStructuredLoggerCreateLogEntryWithTrace(t *testing.T) {
	ctx := context.Background()
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	logger := NewStructuredLogger(ctx)
	entry := logger.CreateLogEntry("info", "test message", nil)

	assert.Equal(t, "info", entry.Level)
	assert.Equal(t, "test message", entry.Message)
	// No-op tracer doesn't produce valid span context, so Trace should be nil
}

func TestStructuredLoggerCreateLogEntryWithCorrelationID(t *testing.T) {
	ctx := context.Background()
	ctx = WithCorrelationID(ctx)

	logger := NewStructuredLogger(ctx)
	entry := logger.CreateLogEntry("info", "test message", nil)

	assert.NotEmpty(t, entry.CorrelationID)
}

func TestStructuredLoggerInfo(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Should not panic
	logger.Info("info message", nil)
	logger.Info("info with details", map[string]any{"key": "value"})
}

func TestStructuredLoggerError(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Should not panic
	logger.Error(nil, "error message without error", nil)
	logger.Error(errors.New("test error"), "error message with error", nil)
	logger.Error(errors.New("test error"), "error message with details", map[string]any{"key": "value"})
}

func TestStructuredLoggerDebug(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Should not panic
	logger.Debug("debug message", nil)
	logger.Debug("debug with details", map[string]any{"key": "value"})
}

func TestStructuredLoggerAuditStructured(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	tests := []struct {
		name         string
		action       string
		resource     string
		resourceType string
		namespace    string
		resName      string
		result       AuditResult
		metadata     map[string]interface{}
	}{
		{
			name:         "success audit",
			action:       "CREATE",
			resource:     "test-pdb",
			resourceType: "PodDisruptionBudget",
			namespace:    "default",
			resName:      "test-deploy",
			result:       AuditResultSuccess,
			metadata:     nil,
		},
		{
			name:         "failure audit",
			action:       "UPDATE",
			resource:     "test-pdb",
			resourceType: "PodDisruptionBudget",
			namespace:    "default",
			resName:      "test-deploy",
			result:       AuditResultFailure,
			metadata:     map[string]interface{}{"error": "update failed"},
		},
		{
			name:         "skipped audit",
			action:       "DELETE",
			resource:     "test-pdb",
			resourceType: "PodDisruptionBudget",
			namespace:    "default",
			resName:      "test-deploy",
			result:       AuditResultSkipped,
			metadata:     nil,
		},
		{
			name:         "audit with metadata",
			action:       "POLICY_APPLY",
			resource:     "test-policy",
			resourceType: "AvailabilityPolicy",
			namespace:    "default",
			resName:      "test-policy",
			result:       AuditResultSuccess,
			metadata:     map[string]interface{}{"affectedCount": 5},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			logger.AuditStructured(tt.action, tt.resource, tt.resourceType, tt.namespace, tt.resName, tt.result, tt.metadata)
		})
	}
}

func TestCreateStructuredLogger(t *testing.T) {
	ctx := context.Background()

	logger := CreateStructuredLogger(
		ctx,
		"DeploymentController",
		"deployment-controller",
		"apps",
		"Deployment",
		"Deployment",
		"my-deployment",
		"default",
		"reconcile-123",
		"corr-456",
	)

	assert.NotNil(t, logger)
}

func TestCreateStructuredLoggerWithTrace(t *testing.T) {
	ctx := context.Background()
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	logger := CreateStructuredLogger(
		ctx,
		"PolicyController",
		"policy-controller",
		"availability.pdb-management.io",
		"AvailabilityPolicy",
		"AvailabilityPolicy",
		"my-policy",
		"production",
		"reconcile-789",
		"corr-101112",
	)

	assert.NotNil(t, logger)
}

func TestGetStructuredLoggerFromContext(t *testing.T) {
	ctx := context.Background()

	logger := GetStructuredLoggerFromContext(ctx)

	assert.NotNil(t, logger)
}

func TestStructuredLoggerToLogr(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	logrLogger := logger.ToLogr()

	assert.NotNil(t, logrLogger)
}

func TestStructuredLoggerWithController(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithController("DeploymentController", "deployment-controller", "apps", "Deployment")

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerWithResource(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithResource("Deployment", "my-deployment", "default")

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerWithTrace(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Without span - should return same logger
	sameLogger := logger.WithTrace()
	assert.NotNil(t, sameLogger)
	assert.Equal(t, logger, sameLogger)

	// With span
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	loggerWithSpan := NewStructuredLogger(ctx)
	// No-op tracer doesn't produce valid span context
	newLogger := loggerWithSpan.WithTrace()
	assert.NotNil(t, newLogger)
}

func TestStructuredLoggerWithReconcileID(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithReconcileID("reconcile-123")

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerWithCorrelationID(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithCorrelationID("corr-456")

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerWithDetails(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithDetails(map[string]any{
		"key1": "value1",
		"key2": 42,
	})

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerWithDetail(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	newLogger := logger.WithDetail("key", "value")

	assert.NotNil(t, newLogger)
	assert.NotNil(t, newLogger.Logger)
	assert.Equal(t, ctx, newLogger.ctx)
}

func TestStructuredLoggerChaining(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	chainedLogger := logger.
		WithController("DeploymentController", "deployment-controller", "apps", "Deployment").
		WithResource("Deployment", "my-deployment", "default").
		WithReconcileID("reconcile-123").
		WithCorrelationID("corr-456").
		WithDetail("key", "value")

	assert.NotNil(t, chainedLogger)
}

func TestControllerInfoStructure(t *testing.T) {
	info := ControllerInfo{
		Type:  "DeploymentController",
		Name:  "deployment-controller",
		Group: "apps",
		Kind:  "Deployment",
	}

	assert.Equal(t, "DeploymentController", info.Type)
	assert.Equal(t, "deployment-controller", info.Name)
	assert.Equal(t, "apps", info.Group)
	assert.Equal(t, "Deployment", info.Kind)
}

func TestResourceInfoStructure(t *testing.T) {
	info := ResourceInfo{
		Type:      "Deployment",
		Name:      "my-deployment",
		Namespace: "default",
		UID:       "12345",
		Version:   "v1",
		Labels: map[string]string{
			"app": "test",
		},
	}

	assert.Equal(t, "Deployment", info.Type)
	assert.Equal(t, "my-deployment", info.Name)
	assert.Equal(t, "default", info.Namespace)
	assert.Equal(t, "12345", info.UID)
	assert.Equal(t, "v1", info.Version)
	assert.Equal(t, "test", info.Labels["app"])
}

func TestTraceInfoStructure(t *testing.T) {
	info := TraceInfo{
		TraceID: "trace-123",
		SpanID:  "span-456",
	}

	assert.Equal(t, "trace-123", info.TraceID)
	assert.Equal(t, "span-456", info.SpanID)
}

func TestDetailsType(t *testing.T) {
	details := Details{
		"key1": "value1",
		"key2": 42,
		"key3": true,
	}

	assert.Equal(t, "value1", details["key1"])
	assert.Equal(t, 42, details["key2"])
	assert.Equal(t, true, details["key3"])
}

func TestStructuredLoggerErrorWithNilDetails(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Error with nil details but with error - should create details map
	err := errors.New("test error")
	logger.Error(err, "error message", nil)
}

func TestStructuredLoggerErrorWithExistingDetails(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	// Error with existing details
	err := errors.New("test error")
	details := map[string]any{"existing": "value"}
	logger.Error(err, "error message", details)
}

func TestLogOperatorEventWithAllOptionalFields(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	entry := LogEntry{
		Level:             "info",
		Timestamp:         time.Now().UTC(),
		Message:           "test message",
		ParentReconcileID: "parent-123",
		CorrelationID:     "corr-456",
		Trace: &TraceInfo{
			TraceID: "trace-789",
			SpanID:  "span-abc",
		},
		Details: map[string]any{
			"key": "value",
		},
	}

	// Should not panic
	logger.LogOperatorEvent(entry)
}

func TestLogOperatorEventWithNoOptionalFields(t *testing.T) {
	ctx := context.Background()
	logger := NewStructuredLogger(ctx)

	entry := LogEntry{
		Level:     "info",
		Timestamp: time.Now().UTC(),
		Message:   "test message",
	}

	// Should not panic
	logger.LogOperatorEvent(entry)
}
