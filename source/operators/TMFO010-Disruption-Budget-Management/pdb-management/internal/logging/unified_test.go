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
	"go.opentelemetry.io/otel/trace/noop"
)

func TestUnifiedLoggerCreation(t *testing.T) {
	// Create test context with trace
	ctx := context.Background()
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	// Test NewUnifiedLogger
	logger := NewUnifiedLogger(ctx,
		"deployment-pdb",        // controllerType
		"deployment-controller", // controllerName
		"apps",                  // group
		"Deployment",            // kind
		"deployment",            // resourceType
		"test-deployment",       // name
		"test-namespace",        // namespace
		"test-reconcile-id",     // reconcileID
		"test-correlation-id",   // correlationID
	)

	// Verify logger was created successfully
	assert.NotNil(t, logger, "Logger should not be nil")
	assert.NotNil(t, logger.entry, "Logger entry should not be nil")
	assert.Equal(t, "test-reconcile-id", logger.entry.ReconcileID, "ReconcileID should match")
	assert.Equal(t, "test-correlation-id", logger.entry.CorrelationID, "CorrelationID should match")
	assert.Equal(t, "deployment-pdb", logger.entry.Controller.Type, "Controller type should match")
	assert.Equal(t, "deployment-controller", logger.entry.Controller.Name, "Controller name should match")
	assert.Equal(t, "test-deployment", logger.entry.Resource.Name, "Resource name should match")
	assert.Equal(t, "test-namespace", logger.entry.Resource.Namespace, "Resource namespace should match")
}

func TestUnifiedLoggerWithDetails(t *testing.T) {
	ctx := context.Background()

	logger := NewUnifiedLogger(ctx,
		"deployment-pdb",
		"deployment-controller",
		"apps",
		"Deployment",
		"deployment",
		"test-deployment",
		"test-namespace",
		"test-reconcile-id",
		"test-correlation-id",
	)

	// Test WithDetails
	loggerWithDetails := logger.WithDetails(map[string]any{
		"availabilityClass": "high-availability",
		"componentFunction": "api",
		"replicas":          3,
	})

	// Verify details were added
	assert.NotNil(t, loggerWithDetails, "Logger with details should not be nil")
	assert.Equal(t, "high-availability", loggerWithDetails.entry.Details["availabilityClass"], "Details should be preserved")
	assert.Equal(t, "api", loggerWithDetails.entry.Details["componentFunction"], "Details should be preserved")
	assert.Equal(t, 3, loggerWithDetails.entry.Details["replicas"], "Details should be preserved")
}

func TestCreateUnifiedLogger(t *testing.T) {
	ctx := context.Background()

	// Test CreateUnifiedLogger
	logger := CreateUnifiedLogger(ctx,
		"deployment-pdb",
		"deployment-controller",
		"apps",
		"Deployment",
		"deployment",
		"test-deployment",
		"test-namespace",
		"test-reconcile-id",
		"test-correlation-id",
	)

	// Verify logger was created successfully
	assert.NotNil(t, logger, "Logger should not be nil")
	assert.NotNil(t, logger.entry, "Logger entry should not be nil")
	assert.Equal(t, "test-reconcile-id", logger.entry.ReconcileID, "ReconcileID should match")
}

func TestUnifiedLogEntryStructure(t *testing.T) {
	// Test the UnifiedLogEntry structure
	entry := UnifiedLogEntry{
		Level:       "info",
		Timestamp:   time.Now().UTC(),
		Message:     "Test message",
		ReconcileID: "test-reconcile-id",
		Controller: ControllerInfo{
			Type:  "test-controller",
			Name:  "test-controller-name",
			Group: "test-group",
			Kind:  "TestKind",
		},
		Resource: ResourceInfo{
			Type:      "test-resource",
			Name:      "test-resource-name",
			Namespace: "test-namespace",
		},
		Details: map[string]any{
			"testKey": "testValue",
		},
	}

	// Verify structure
	assert.Equal(t, "info", entry.Level, "Level should match")
	assert.Equal(t, "Test message", entry.Message, "Message should match")
	assert.Equal(t, "test-reconcile-id", entry.ReconcileID, "ReconcileID should match")
	assert.Equal(t, "test-controller", entry.Controller.Type, "Controller type should match")
	assert.Equal(t, "test-resource", entry.Resource.Type, "Resource type should match")
	assert.Equal(t, "testValue", entry.Details["testKey"], "Details should match")
}
