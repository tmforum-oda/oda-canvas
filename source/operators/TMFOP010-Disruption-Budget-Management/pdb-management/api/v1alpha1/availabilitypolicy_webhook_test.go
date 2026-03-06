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

package v1alpha1

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

func TestAvailabilityPolicyWebhookInterfaces(t *testing.T) {
	// Verify that webhook handlers implement the correct interfaces
	defaulter := &AvailabilityPolicyCustomDefaulter{}
	validator := &AvailabilityPolicyCustomValidator{}

	// Check CustomDefaulter interface
	var _ admission.CustomDefaulter = defaulter

	// Check CustomValidator interface
	var _ admission.CustomValidator = validator

	// This test will fail to compile if the interfaces are not properly implemented
	t.Log("AvailabilityPolicy webhook handlers correctly implement interfaces")
}

func TestAvailabilityPolicyDefault(t *testing.T) {
	defaulter := &AvailabilityPolicyCustomDefaulter{}
	ctx := context.Background()

	tests := []struct {
		name     string
		policy   *AvailabilityPolicy
		expected *AvailabilityPolicy
	}{
		{
			name: "sets default priority",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			expected: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority:           50,
					EnforceMinReplicas: func() *bool { b := true; return &b }(),
				},
			},
		},
		{
			name: "sets default maintenance window timezone",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					MaintenanceWindows: []MaintenanceWindow{
						{
							Start: "02:00",
							End:   "04:00",
						},
					},
				},
			},
			expected: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority:           50,
					EnforceMinReplicas: func() *bool { b := true; return &b }(),
					MaintenanceWindows: []MaintenanceWindow{
						{
							Start:      "02:00",
							End:        "04:00",
							Timezone:   "UTC",
							DaysOfWeek: []int{0, 1, 2, 3, 4, 5, 6},
						},
					},
				},
			},
		},
		{
			name: "sets default unhealthy pod eviction policy for custom class",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Custom,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					CustomPDBConfig: &PodDisruptionBudgetConfig{
						MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "80%"},
					},
				},
			},
			expected: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Custom,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority:           50,
					EnforceMinReplicas: func() *bool { b := true; return &b }(),
					CustomPDBConfig: &PodDisruptionBudgetConfig{
						MinAvailable:               &intstr.IntOrString{Type: intstr.String, StrVal: "80%"},
						UnhealthyPodEvictionPolicy: "IfHealthyBudget",
					},
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			policy := tt.policy.DeepCopy()
			err := defaulter.Default(ctx, policy)
			require.NoError(t, err)

			assert.Equal(t, tt.expected.Spec.Priority, policy.Spec.Priority)
			assert.Equal(t, tt.expected.Spec.EnforceMinReplicas, policy.Spec.EnforceMinReplicas)

			if len(tt.expected.Spec.MaintenanceWindows) > 0 {
				require.Len(t, policy.Spec.MaintenanceWindows, len(tt.expected.Spec.MaintenanceWindows))
				assert.Equal(t, tt.expected.Spec.MaintenanceWindows[0].Timezone, policy.Spec.MaintenanceWindows[0].Timezone)
				assert.Equal(t, tt.expected.Spec.MaintenanceWindows[0].DaysOfWeek, policy.Spec.MaintenanceWindows[0].DaysOfWeek)
			}

			if tt.expected.Spec.CustomPDBConfig != nil {
				require.NotNil(t, policy.Spec.CustomPDBConfig)
				assert.Equal(t, tt.expected.Spec.CustomPDBConfig.UnhealthyPodEvictionPolicy, policy.Spec.CustomPDBConfig.UnhealthyPodEvictionPolicy)
			}
		})
	}
}

func TestAvailabilityPolicyValidateCreate(t *testing.T) {
	validator := &AvailabilityPolicyCustomValidator{}
	ctx := context.Background()

	tests := []struct {
		name        string
		policy      *AvailabilityPolicy
		wantErr     bool
		errContains string
		wantWarning bool
	}{
		{
			name: "valid policy",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority: 100,
				},
			},
			wantErr: false,
		},
		{
			name: "invalid availability class",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: "invalid-class",
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			wantErr:     true,
			errContains: "must be one of",
		},
		{
			name: "custom class without config",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Custom,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			wantErr:     true,
			errContains: "custom availability class requires customPDBConfig",
		},
		{
			name: "no component selector",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{},
				},
			},
			wantErr:     true,
			errContains: "must specify at least one selection criteria",
		},
		{
			name: "invalid priority",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority: 1001,
				},
			},
			wantErr:     true,
			errContains: "priority must be between 0 and 1000",
		},
		{
			name: "warning for zero priority",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					Priority: 0,
				},
			},
			wantErr:     false,
			wantWarning: true,
		},
		{
			name: "invalid maintenance window",
			policy: &AvailabilityPolicy{
				Spec: AvailabilityPolicySpec{
					AvailabilityClass: Standard,
					ComponentSelector: ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					MaintenanceWindows: []MaintenanceWindow{
						{
							Start:    "25:00", // Invalid time
							End:      "04:00",
							Timezone: "UTC",
						},
					},
				},
			},
			wantErr:     true,
			errContains: "must be in HH:MM format",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			warnings, err := validator.ValidateCreate(ctx, tt.policy)

			if tt.wantErr {
				require.Error(t, err)
				if tt.errContains != "" {
					assert.Contains(t, err.Error(), tt.errContains)
				}
			} else {
				assert.NoError(t, err)
			}

			if tt.wantWarning {
				assert.NotEmpty(t, warnings)
			}
		})
	}
}

func TestHasSelectionCriteria(t *testing.T) {
	tests := []struct {
		name     string
		selector ComponentSelector
		expected bool
	}{
		{
			name:     "empty selector",
			selector: ComponentSelector{},
			expected: false,
		},
		{
			name: "has component names",
			selector: ComponentSelector{
				ComponentNames: []string{"my-component"},
			},
			expected: true,
		},
		{
			name: "has component functions",
			selector: ComponentSelector{
				ComponentFunctions: []ComponentFunction{CoreFunction},
			},
			expected: true,
		},
		{
			name: "has match labels",
			selector: ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			expected: true,
		},
		{
			name: "has all criteria",
			selector: ComponentSelector{
				ComponentNames:     []string{"my-component"},
				ComponentFunctions: []ComponentFunction{CoreFunction},
				MatchLabels:        map[string]string{"app": "test"},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.selector.HasSelectionCriteria()
			assert.Equal(t, tt.expected, result)
		})
	}
}
