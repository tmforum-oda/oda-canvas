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

func TestNewLogger(t *testing.T) {
	ctx := context.Background()

	logger := NewLogger(ctx)

	assert.NotNil(t, logger)
	assert.NotNil(t, logger.Logger)
	assert.Equal(t, ctx, logger.ctx)
}

func TestNewLoggerWithTraceContext(t *testing.T) {
	ctx := context.Background()
	tracer := noop.NewTracerProvider().Tracer("test")
	ctx, span := tracer.Start(ctx, "test-span")
	defer span.End()

	logger := NewLogger(ctx)

	assert.NotNil(t, logger)
}

func TestNewLoggerWithCorrelationID(t *testing.T) {
	ctx := context.Background()
	ctx = WithCorrelationID(ctx)

	logger := NewLogger(ctx)

	assert.NotNil(t, logger)
}

func TestLoggerWithValues(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithValues("key1", "value1", "key2", 42)

	assert.NotNil(t, newLogger)
	assert.NotEqual(t, logger, newLogger)
}

func TestLoggerWithName(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithName("test-logger")

	assert.NotNil(t, newLogger)
	assert.NotEqual(t, logger, newLogger)
}

func TestLoggerWithReconcileID(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithReconcileID("reconcile-12345")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithDeployment(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithDeployment("test-namespace", "test-deployment")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithPolicy(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithPolicy("test-namespace", "test-policy")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithPDB(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithPDB("test-namespace", "test-pdb")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithComponent(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithComponent("test-component", "core")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithAvailabilityClass(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithAvailabilityClass("high-availability")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithOperation(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithOperation("create-pdb")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithMCPRequest(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithMCPRequest("tools/list", "req-123")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithMCPTool(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	newLogger := logger.WithMCPTool("analyze_cluster_availability")

	assert.NotNil(t, newLogger)
}

func TestLoggerWithError(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// With error
	testErr := errors.New("test error")
	newLogger := logger.WithError(testErr)
	assert.NotNil(t, newLogger)

	// With nil error
	nilLogger := logger.WithError(nil)
	assert.Equal(t, logger, nilLogger)
}

func TestLoggerToLogr(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	logrLogger := logger.ToLogr()

	assert.NotNil(t, logrLogger)
}

func TestLoggerAudit(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	tests := []struct {
		name         string
		action       string
		resource     string
		resourceType string
		namespace    string
		resourceName string
		result       AuditResult
		metadata     map[string]interface{}
	}{
		{
			name:         "success audit",
			action:       "CREATE",
			resource:     "test-pdb",
			resourceType: "PodDisruptionBudget",
			namespace:    "default",
			resourceName: "test-deploy",
			result:       AuditResultSuccess,
			metadata:     nil,
		},
		{
			name:         "failure audit",
			action:       "UPDATE",
			resource:     "test-pdb",
			resourceType: "PodDisruptionBudget",
			namespace:    "default",
			resourceName: "test-deploy",
			result:       AuditResultFailure,
			metadata:     map[string]interface{}{"error": "update failed"},
		},
		{
			name:         "audit with metadata",
			action:       "POLICY_APPLY",
			resource:     "test-policy",
			resourceType: "AvailabilityPolicy",
			namespace:    "default",
			resourceName: "test-policy",
			result:       AuditResultSuccess,
			metadata:     map[string]interface{}{"affectedCount": 5},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			logger.Audit(tt.action, tt.resource, tt.resourceType, tt.namespace, tt.resourceName, tt.result, tt.metadata)
		})
	}
}

func TestLoggerAuditPDBCreation(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Should not panic
	logger.AuditPDBCreation("default", "test-deploy", "test-pdb", AuditResultSuccess, nil)
	logger.AuditPDBCreation("default", "test-deploy", "test-pdb", AuditResultFailure, map[string]interface{}{"error": "creation failed"})
}

func TestLoggerAuditPolicyApplication(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Should not panic
	logger.AuditPolicyApplication("default", "test-policy", []string{"deploy-1", "deploy-2"}, AuditResultSuccess)
	logger.AuditPolicyApplication("default", "test-policy", []string{}, AuditResultFailure)
}

func TestLoggerAuditReconciliation(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Should not panic
	logger.AuditReconciliation("DeploymentController", "default", "test-deploy", 100*time.Millisecond, AuditResultSuccess, nil)
	logger.AuditReconciliation("DeploymentController", "default", "test-deploy", 500*time.Millisecond, AuditResultFailure, errors.New("reconciliation failed"))
}

func TestLoggerAuditMCPRequest(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Should not panic
	logger.AuditMCPRequest("tools/list", "req-123", "ai-agent", 50*time.Millisecond, AuditResultSuccess, nil)
	logger.AuditMCPRequest("tools/call", "req-456", "ai-agent", 200*time.Millisecond, AuditResultFailure, errors.New("tool not found"))
}

func TestLoggerAuditMCPToolCall(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Should not panic
	logger.AuditMCPToolCall("analyze_cluster_availability", map[string]interface{}{"namespace": "default"}, AuditResultSuccess, nil)
	logger.AuditMCPToolCall("recommend_policies", map[string]interface{}{}, AuditResultSuccess, map[string]interface{}{"recommendationCount": 3})
}

func TestGetLoggerFromContext(t *testing.T) {
	ctx := context.Background()

	logger := GetLoggerFromContext(ctx)

	assert.NotNil(t, logger)
}

func TestGetLoggerFromContextWithValues(t *testing.T) {
	ctx := context.Background()

	logger := GetLoggerFromContextWithValues(ctx, "key1", "value1", "key2", 42)

	assert.NotNil(t, logger)
}

func TestInitializeLogger(t *testing.T) {
	logger, err := InitializeLogger(true, "debug")

	assert.NoError(t, err)
	assert.NotNil(t, logger)
}

func TestLoggerChaining(t *testing.T) {
	ctx := context.Background()
	logger := NewLogger(ctx)

	// Chain multiple methods
	chainedLogger := logger.
		WithName("test").
		WithDeployment("default", "my-deploy").
		WithOperation("reconcile").
		WithAvailabilityClass("high-availability")

	assert.NotNil(t, chainedLogger)
}
