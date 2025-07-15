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

package metrics

import (
	"errors"
	"testing"
	"time"

	"github.com/prometheus/client_golang/prometheus/testutil"
	"github.com/stretchr/testify/assert"
)

func TestRecordReconciliation(t *testing.T) {
	tests := []struct {
		name       string
		controller string
		duration   time.Duration
		err        error
		wantError  bool
	}{
		{
			name:       "successful reconciliation",
			controller: "test-controller",
			duration:   100 * time.Millisecond,
			err:        nil,
			wantError:  false,
		},
		{
			name:       "failed reconciliation",
			controller: "test-controller",
			duration:   200 * time.Millisecond,
			err:        errors.New("test error"),
			wantError:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Record the metric
			RecordReconciliation(tt.controller, tt.duration, tt.err)

			// Check that the metric was recorded
			count := testutil.CollectAndCount(ReconciliationDuration, "pdb_management_reconciliation_duration_seconds")
			assert.Greater(t, count, 0, "Reconciliation duration should be recorded")

			if tt.wantError {
				errorCount := testutil.CollectAndCount(ReconciliationErrors, "pdb_management_reconciliation_errors_total")
				assert.Greater(t, errorCount, 0, "Reconciliation error should be recorded")
			}
		})
	}
}

func TestRecordPDBCreated(t *testing.T) {
	// Test recording PDB creation
	RecordPDBCreated("test-namespace", "high-availability", "core")

	// Check the metric
	count := testutil.CollectAndCount(PDBsCreated, "pdb_management_pdbs_created_total")
	assert.Greater(t, count, 0, "PDB creation should be recorded")
}

func TestUpdateManagedDeployments(t *testing.T) {
	// Test updating managed deployments gauge
	counts := map[string]map[string]int{
		"default": {
			"standard":          5,
			"high-availability": 3,
		},
		"production": {
			"mission-critical": 2,
		},
	}

	UpdateManagedDeployments(counts)

	// Check the metric
	count := testutil.CollectAndCount(ManagedDeployments, "pdb_management_deployments_managed")
	assert.Equal(t, 3, count, "Should have 3 gauge entries")
}

func TestUpdateComplianceStatus(t *testing.T) {
	tests := []struct {
		name       string
		namespace  string
		deployment string
		compliant  bool
		reason     string
		expected   float64
	}{
		{
			name:       "compliant deployment",
			namespace:  "default",
			deployment: "test-app",
			compliant:  true,
			reason:     "created",
			expected:   1.0,
		},
		{
			name:       "non-compliant deployment",
			namespace:  "default",
			deployment: "test-app",
			compliant:  false,
			reason:     "insufficient_replicas",
			expected:   0.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			UpdateComplianceStatus(tt.namespace, tt.deployment, tt.compliant, tt.reason)

			// Check the metric value
			value := testutil.ToFloat64(PDBComplianceStatus.WithLabelValues(tt.namespace, tt.deployment, tt.reason))
			assert.Equal(t, tt.expected, value, "Compliance status should match expected value")
		})
	}
}

func TestUpdateMaintenanceWindowStatus(t *testing.T) {
	tests := []struct {
		name       string
		namespace  string
		deployment string
		inWindow   bool
		expected   float64
	}{
		{
			name:       "in maintenance window",
			namespace:  "default",
			deployment: "test-app",
			inWindow:   true,
			expected:   1.0,
		},
		{
			name:       "not in maintenance window",
			namespace:  "default",
			deployment: "test-app",
			inWindow:   false,
			expected:   0.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			UpdateMaintenanceWindowStatus(tt.namespace, tt.deployment, tt.inWindow)

			// Check the metric value
			value := testutil.ToFloat64(MaintenanceWindowActive.WithLabelValues(tt.namespace, tt.deployment))
			assert.Equal(t, tt.expected, value, "Maintenance window status should match expected value")
		})
	}
}

func TestUpdateActivePoliciesCount(t *testing.T) {
	// Test updating active policies count
	counts := map[string]int{
		"default":    3,
		"production": 5,
		"staging":    2,
	}

	UpdateActivePoliciesCount(counts)

	// Check the metric
	count := testutil.CollectAndCount(AvailabilityPoliciesActive, "pdb_management_policies_active")
	assert.Equal(t, 3, count, "Should have 3 namespace entries")

	// Check specific values
	defaultValue := testutil.ToFloat64(AvailabilityPoliciesActive.WithLabelValues("default"))
	assert.Equal(t, 3.0, defaultValue, "Default namespace should have 3 policies")
}

func TestGetErrorType(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected string
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: "none",
		},
		{
			name:     "unknown error",
			err:      errors.New("some error"),
			expected: "unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := getErrorType(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}
