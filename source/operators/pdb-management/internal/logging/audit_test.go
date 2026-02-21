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
)

func TestAuditActionConstants(t *testing.T) {
	assert.Equal(t, AuditAction("CREATE"), AuditActionCreate)
	assert.Equal(t, AuditAction("UPDATE"), AuditActionUpdate)
	assert.Equal(t, AuditAction("DELETE"), AuditActionDelete)
	assert.Equal(t, AuditAction("RECONCILE"), AuditActionReconcile)
	assert.Equal(t, AuditAction("POLICY_APPLY"), AuditActionPolicyApply)
}

func TestAuditResultConstants(t *testing.T) {
	assert.Equal(t, AuditResult("SUCCESS"), AuditResultSuccess)
	assert.Equal(t, AuditResult("FAILURE"), AuditResultFailure)
	assert.Equal(t, AuditResult("SKIPPED"), AuditResultSkipped)
}

func TestAuditEntryStructure(t *testing.T) {
	now := time.Now().UTC()
	entry := AuditEntry{
		Timestamp:     now,
		Action:        AuditActionCreate,
		Resource:      "test-pdb",
		ResourceType:  "PodDisruptionBudget",
		Namespace:     "test-namespace",
		Name:          "test-deployment",
		Result:        AuditResultSuccess,
		CorrelationID: "corr-123",
		User:          "test-user",
		Reason:        "test reason",
		Metadata: map[string]interface{}{
			"key1": "value1",
			"key2": 42,
		},
	}

	assert.Equal(t, now, entry.Timestamp)
	assert.Equal(t, AuditActionCreate, entry.Action)
	assert.Equal(t, "test-pdb", entry.Resource)
	assert.Equal(t, "PodDisruptionBudget", entry.ResourceType)
	assert.Equal(t, "test-namespace", entry.Namespace)
	assert.Equal(t, "test-deployment", entry.Name)
	assert.Equal(t, AuditResultSuccess, entry.Result)
	assert.Equal(t, "corr-123", entry.CorrelationID)
	assert.Equal(t, "test-user", entry.User)
	assert.Equal(t, "test reason", entry.Reason)
	assert.Equal(t, "value1", entry.Metadata["key1"])
	assert.Equal(t, 42, entry.Metadata["key2"])
}

func TestAudit(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name  string
		entry AuditEntry
	}{
		{
			name: "success audit entry",
			entry: AuditEntry{
				Action:       AuditActionCreate,
				Resource:     "test-pdb",
				ResourceType: "PodDisruptionBudget",
				Namespace:    "default",
				Name:         "test-deploy",
				Result:       AuditResultSuccess,
			},
		},
		{
			name: "failure audit entry",
			entry: AuditEntry{
				Action:       AuditActionUpdate,
				Resource:     "test-pdb",
				ResourceType: "PodDisruptionBudget",
				Namespace:    "default",
				Name:         "test-deploy",
				Result:       AuditResultFailure,
				Reason:       "update failed",
			},
		},
		{
			name: "skipped audit entry",
			entry: AuditEntry{
				Action:       AuditActionReconcile,
				Resource:     "test-policy",
				ResourceType: "AvailabilityPolicy",
				Namespace:    "default",
				Name:         "test-policy",
				Result:       AuditResultSkipped,
			},
		},
		{
			name: "with metadata",
			entry: AuditEntry{
				Action:       AuditActionPolicyApply,
				Resource:     "test-policy",
				ResourceType: "AvailabilityPolicy",
				Namespace:    "default",
				Name:         "test-policy",
				Result:       AuditResultSuccess,
				Metadata: map[string]interface{}{
					"affectedCount": 5,
					"policyClass":   "high-availability",
				},
			},
		},
		{
			name: "with user and correlation ID",
			entry: AuditEntry{
				Action:        AuditActionDelete,
				Resource:      "test-pdb",
				ResourceType:  "PodDisruptionBudget",
				Namespace:     "default",
				Name:          "test-deploy",
				Result:        AuditResultSuccess,
				User:          "admin",
				CorrelationID: "abc-123",
			},
		},
		{
			name: "with timestamp",
			entry: AuditEntry{
				Timestamp:    time.Now().UTC(),
				Action:       AuditActionCreate,
				Resource:     "test-pdb",
				ResourceType: "PodDisruptionBudget",
				Namespace:    "default",
				Name:         "test-deploy",
				Result:       AuditResultSuccess,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			Audit(ctx, tt.entry)
		})
	}
}

func TestAuditWithCorrelationIDFromContext(t *testing.T) {
	ctx := context.Background()
	ctx = WithCorrelationID(ctx)

	entry := AuditEntry{
		Action:       AuditActionCreate,
		Resource:     "test-pdb",
		ResourceType: "PodDisruptionBudget",
		Namespace:    "default",
		Name:         "test-deploy",
		Result:       AuditResultSuccess,
	}

	// Should not panic and should use correlation ID from context
	Audit(ctx, entry)
}

func TestAuditPDBCreation(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name       string
		namespace  string
		deployment string
		pdbName    string
		result     AuditResult
		metadata   map[string]interface{}
	}{
		{
			name:       "successful PDB creation",
			namespace:  "default",
			deployment: "my-deployment",
			pdbName:    "my-deployment-pdb",
			result:     AuditResultSuccess,
			metadata:   nil,
		},
		{
			name:       "failed PDB creation",
			namespace:  "production",
			deployment: "critical-app",
			pdbName:    "critical-app-pdb",
			result:     AuditResultFailure,
			metadata: map[string]interface{}{
				"error": "PDB already exists",
			},
		},
		{
			name:       "PDB creation with metadata",
			namespace:  "staging",
			deployment: "test-app",
			pdbName:    "test-app-pdb",
			result:     AuditResultSuccess,
			metadata: map[string]interface{}{
				"minAvailable":      "75%",
				"availabilityClass": "high-availability",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			AuditPDBCreation(ctx, tt.namespace, tt.deployment, tt.pdbName, tt.result, tt.metadata)
		})
	}
}

func TestAuditPolicyApplication(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name               string
		policyNamespace    string
		policyName         string
		affectedComponents []string
		result             AuditResult
	}{
		{
			name:               "successful policy application",
			policyNamespace:    "default",
			policyName:         "standard-policy",
			affectedComponents: []string{"deploy-1", "deploy-2", "deploy-3"},
			result:             AuditResultSuccess,
		},
		{
			name:               "failed policy application",
			policyNamespace:    "production",
			policyName:         "critical-policy",
			affectedComponents: []string{},
			result:             AuditResultFailure,
		},
		{
			name:               "policy with single component",
			policyNamespace:    "staging",
			policyName:         "test-policy",
			affectedComponents: []string{"single-deploy"},
			result:             AuditResultSuccess,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			AuditPolicyApplication(ctx, tt.policyNamespace, tt.policyName, tt.affectedComponents, tt.result)
		})
	}
}

func TestAuditReconciliation(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name       string
		controller string
		namespace  string
		resName    string
		duration   time.Duration
		result     AuditResult
		err        error
	}{
		{
			name:       "successful reconciliation",
			controller: "DeploymentController",
			namespace:  "default",
			resName:    "my-deployment",
			duration:   100 * time.Millisecond,
			result:     AuditResultSuccess,
			err:        nil,
		},
		{
			name:       "failed reconciliation",
			controller: "PolicyController",
			namespace:  "production",
			resName:    "critical-policy",
			duration:   500 * time.Millisecond,
			result:     AuditResultFailure,
			err:        errors.New("reconciliation failed"),
		},
		{
			name:       "skipped reconciliation",
			controller: "DeploymentController",
			namespace:  "staging",
			resName:    "test-deploy",
			duration:   10 * time.Millisecond,
			result:     AuditResultSkipped,
			err:        nil,
		},
		{
			name:       "fast reconciliation",
			controller: "DeploymentController",
			namespace:  "default",
			resName:    "fast-deploy",
			duration:   1 * time.Millisecond,
			result:     AuditResultSuccess,
			err:        nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Should not panic
			AuditReconciliation(ctx, tt.controller, tt.namespace, tt.resName, tt.duration, tt.result, tt.err)
		})
	}
}

func TestAuditWithTracingContext(t *testing.T) {
	ctx := context.Background()
	ctx = WithCorrelationID(ctx)
	ctx = WithOperation(ctx, "test-operation")

	entry := AuditEntry{
		Action:       AuditActionCreate,
		Resource:     "test-resource",
		ResourceType: "TestType",
		Namespace:    "default",
		Name:         "test-name",
		Result:       AuditResultSuccess,
	}

	// Should not panic
	Audit(ctx, entry)
}
