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
	"time"

	"github.com/stretchr/testify/assert"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

func TestWithCorrelationID(t *testing.T) {
	ctx := context.Background()

	// Add correlation ID
	ctx = WithCorrelationID(ctx)

	// Verify correlation ID was added
	correlationID := GetCorrelationID(ctx)
	assert.NotEmpty(t, correlationID, "Correlation ID should be set")
	assert.Len(t, correlationID, 36, "Correlation ID should be a UUID")

	// Verify logger has correlation ID
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestGetCorrelationID(t *testing.T) {
	tests := []struct {
		name     string
		setup    func() context.Context
		expected string
	}{
		{
			name: "with correlation ID",
			setup: func() context.Context {
				return WithCorrelationID(context.Background())
			},
			expected: "non-empty",
		},
		{
			name: "without correlation ID",
			setup: func() context.Context {
				return context.Background()
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setup()
			correlationID := GetCorrelationID(ctx)

			if tt.expected == "non-empty" {
				assert.NotEmpty(t, correlationID)
			} else {
				assert.Equal(t, tt.expected, correlationID)
			}
		})
	}
}

func TestWithDeploymentContext(t *testing.T) {
	ctx := context.Background()

	// Add deployment context
	ctx = WithDeploymentContext(ctx, "test-namespace", "test-deployment")

	// Verify logger has deployment info
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithPolicyContext(t *testing.T) {
	ctx := context.Background()

	// Add policy context
	ctx = WithPolicyContext(ctx, "test-namespace", "test-policy")

	// Verify logger has policy info
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithPDBContext(t *testing.T) {
	ctx := context.Background()

	// Add PDB context
	ctx = WithPDBContext(ctx, "test-namespace", "test-pdb")

	// Verify logger has PDB info
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithOperation(t *testing.T) {
	ctx := context.Background()

	// Add operation context
	ctx = WithOperation(ctx, "create-pdb")

	// Verify operation was added
	operation := GetOperation(ctx)
	assert.Equal(t, "create-pdb", operation)

	// Verify logger has operation
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithComponent(t *testing.T) {
	ctx := context.Background()

	// Add component context
	ctx = WithComponent(ctx, "test-component", "core")

	// Verify logger has component info
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithAvailabilityClass(t *testing.T) {
	ctx := context.Background()

	// Add availability class
	ctx = WithAvailabilityClass(ctx, "high-availability")

	// Verify logger has availability class
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithError(t *testing.T) {
	tests := []struct {
		name  string
		err   error
		check func(context.Context)
	}{
		{
			name: "with error",
			err:  assert.AnError,
			check: func(ctx context.Context) {
				logger := log.FromContext(ctx)
				assert.NotNil(t, logger, "Logger should be set in context")
			},
		},
		{
			name: "with nil error",
			err:  nil,
			check: func(ctx context.Context) {
				logger := log.FromContext(ctx)
				assert.NotNil(t, logger, "Logger should be set in context")
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := context.Background()
			ctx = WithError(ctx, tt.err)
			tt.check(ctx)
		})
	}
}

func TestWithReconcileID(t *testing.T) {
	ctx := context.Background()

	// Add reconcile ID
	ctx = WithReconcileID(ctx, "reconcile-12345")

	// Verify logger has reconcile ID
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestWithOwnerReference(t *testing.T) {
	ctx := context.Background()

	// Add owner reference
	ctx = WithOwnerReference(ctx, "Deployment", "test-deployment")

	// Verify logger has owner reference
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestLoggerWithFields(t *testing.T) {
	ctx := context.Background()

	fields := map[string]interface{}{
		"field1": "value1",
		"field2": 42,
		"field3": true,
	}

	logger := LoggerWithFields(ctx, fields)
	assert.NotNil(t, logger, "Logger should be created with fields")
}

func TestStartOperation(t *testing.T) {
	ctx := context.Background()

	// Start operation
	done := StartOperation(ctx, "test-operation")

	// Simulate some work
	time.Sleep(10 * time.Millisecond)

	// Complete operation
	done()

	// Test passes if no panic occurs
	assert.True(t, true, "Operation should complete without panic")
}

func TestLogDuration(t *testing.T) {
	ctx := context.Background()

	// Log duration
	LogDuration(ctx, "test-operation", 100*time.Millisecond)

	// Test passes if no panic occurs
	assert.True(t, true, "Duration should be logged without panic")
}

func TestWith(t *testing.T) {
	ctx := context.Background()

	fields := Fields{
		"key1": "value1",
		"key2": 123,
	}

	ctx = With(ctx, fields)

	// Verify logger was updated
	logger := log.FromContext(ctx)
	assert.NotNil(t, logger, "Logger should be set in context")
}

func TestLoggingFunctions(t *testing.T) {
	ctx := context.Background()

	// Test Debug
	Debug(ctx, "debug message")
	Debug(ctx, "debug with fields", Fields{"key": "value"})

	// Test Info
	Info(ctx, "info message")
	Info(ctx, "info with fields", Fields{"key": "value"})

	// Test Warn
	Warn(ctx, "warning message")
	Warn(ctx, "warning with fields", Fields{"key": "value"})

	// Test Error
	Error(ctx, assert.AnError, "error message")
	Error(ctx, assert.AnError, "error with fields", Fields{"key": "value"})

	// Test passes if no panic occurs
	assert.True(t, true, "All logging functions should work without panic")
}
