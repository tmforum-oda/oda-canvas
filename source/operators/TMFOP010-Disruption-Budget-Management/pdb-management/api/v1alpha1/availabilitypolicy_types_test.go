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
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestAvailabilityClassConstants(t *testing.T) {
	assert.Equal(t, AvailabilityClass("non-critical"), NonCritical)
	assert.Equal(t, AvailabilityClass("standard"), Standard)
	assert.Equal(t, AvailabilityClass("high-availability"), HighAvailability)
	assert.Equal(t, AvailabilityClass("mission-critical"), MissionCritical)
	assert.Equal(t, AvailabilityClass("custom"), Custom)
}

func TestEnforcementModeConstants(t *testing.T) {
	assert.Equal(t, EnforcementMode("strict"), EnforcementStrict)
	assert.Equal(t, EnforcementMode("flexible"), EnforcementFlexible)
	assert.Equal(t, EnforcementMode("advisory"), EnforcementAdvisory)
}

func TestComponentFunctionConstants(t *testing.T) {
	assert.Equal(t, ComponentFunction("core"), CoreFunction)
	assert.Equal(t, ComponentFunction("management"), ManagementFunction)
	assert.Equal(t, ComponentFunction("security"), SecurityFunction)
}

func TestGetEnforcement(t *testing.T) {
	tests := []struct {
		name        string
		spec        AvailabilityPolicySpec
		expectedEnf EnforcementMode
	}{
		{
			name: "returns advisory when empty (backward compatibility)",
			spec: AvailabilityPolicySpec{
				Enforcement: "",
			},
			expectedEnf: EnforcementAdvisory,
		},
		{
			name: "returns strict when set to strict",
			spec: AvailabilityPolicySpec{
				Enforcement: EnforcementStrict,
			},
			expectedEnf: EnforcementStrict,
		},
		{
			name: "returns flexible when set to flexible",
			spec: AvailabilityPolicySpec{
				Enforcement: EnforcementFlexible,
			},
			expectedEnf: EnforcementFlexible,
		},
		{
			name: "returns advisory when set to advisory",
			spec: AvailabilityPolicySpec{
				Enforcement: EnforcementAdvisory,
			},
			expectedEnf: EnforcementAdvisory,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.spec.GetEnforcement()
			assert.Equal(t, tt.expectedEnf, result)
		})
	}
}

func TestGetMinAvailableForClass(t *testing.T) {
	tests := []struct {
		name     string
		class    AvailabilityClass
		function ComponentFunction
		expected string
	}{
		{
			name:     "non-critical core function",
			class:    NonCritical,
			function: CoreFunction,
			expected: "20%",
		},
		{
			name:     "standard core function",
			class:    Standard,
			function: CoreFunction,
			expected: "50%",
		},
		{
			name:     "high-availability core function",
			class:    HighAvailability,
			function: CoreFunction,
			expected: "75%",
		},
		{
			name:     "mission-critical core function",
			class:    MissionCritical,
			function: CoreFunction,
			expected: "90%",
		},
		{
			name:     "non-critical management function",
			class:    NonCritical,
			function: ManagementFunction,
			expected: "20%",
		},
		{
			name:     "standard management function",
			class:    Standard,
			function: ManagementFunction,
			expected: "50%",
		},
		{
			name:     "non-critical security function - upgraded to 50%",
			class:    NonCritical,
			function: SecurityFunction,
			expected: "50%",
		},
		{
			name:     "standard security function - upgraded to 75%",
			class:    Standard,
			function: SecurityFunction,
			expected: "75%",
		},
		{
			name:     "high-availability security function",
			class:    HighAvailability,
			function: SecurityFunction,
			expected: "75%",
		},
		{
			name:     "mission-critical security function",
			class:    MissionCritical,
			function: SecurityFunction,
			expected: "90%",
		},
		{
			name:     "custom class defaults to standard (50%)",
			class:    Custom,
			function: CoreFunction,
			expected: "50%",
		},
		{
			name:     "unknown class defaults to standard (50%)",
			class:    AvailabilityClass("unknown"),
			function: CoreFunction,
			expected: "50%",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetMinAvailableForClass(tt.class, tt.function)
			assert.Equal(t, tt.expected, result.String())
		})
	}
}

func TestCompareAvailabilityClasses(t *testing.T) {
	tests := []struct {
		name     string
		a        AvailabilityClass
		b        AvailabilityClass
		expected int
	}{
		{
			name:     "non-critical < standard",
			a:        NonCritical,
			b:        Standard,
			expected: -1,
		},
		{
			name:     "standard < high-availability",
			a:        Standard,
			b:        HighAvailability,
			expected: -1,
		},
		{
			name:     "high-availability < mission-critical",
			a:        HighAvailability,
			b:        MissionCritical,
			expected: -1,
		},
		{
			name:     "mission-critical < custom",
			a:        MissionCritical,
			b:        Custom,
			expected: -1,
		},
		{
			name:     "standard == standard",
			a:        Standard,
			b:        Standard,
			expected: 0,
		},
		{
			name:     "high-availability > standard",
			a:        HighAvailability,
			b:        Standard,
			expected: 1,
		},
		{
			name:     "mission-critical > non-critical",
			a:        MissionCritical,
			b:        NonCritical,
			expected: 3,
		},
		{
			name:     "custom > standard",
			a:        Custom,
			b:        Standard,
			expected: 3,
		},
		{
			name:     "unknown class treated as 0",
			a:        AvailabilityClass("unknown"),
			b:        NonCritical,
			expected: -1,
		},
		{
			name:     "both unknown classes",
			a:        AvailabilityClass("unknown1"),
			b:        AvailabilityClass("unknown2"),
			expected: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := CompareAvailabilityClasses(tt.a, tt.b)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMaintenanceWindowStructure(t *testing.T) {
	window := MaintenanceWindow{
		Start:      "02:00",
		End:        "04:00",
		Timezone:   "America/New_York",
		DaysOfWeek: []int{0, 6}, // Sunday and Saturday
	}

	assert.Equal(t, "02:00", window.Start)
	assert.Equal(t, "04:00", window.End)
	assert.Equal(t, "America/New_York", window.Timezone)
	assert.Equal(t, []int{0, 6}, window.DaysOfWeek)
}

func TestPodDisruptionBudgetConfigStructure(t *testing.T) {
	config := PodDisruptionBudgetConfig{
		UnhealthyPodEvictionPolicy: "IfHealthyBudget",
	}

	assert.Equal(t, "IfHealthyBudget", config.UnhealthyPodEvictionPolicy)
}

func TestComponentSelectorStructure(t *testing.T) {
	selector := ComponentSelector{
		MatchLabels: map[string]string{
			"app": "test",
		},
		ComponentNames:     []string{"component-1", "component-2"},
		ComponentFunctions: []ComponentFunction{CoreFunction, SecurityFunction},
		Namespaces:         []string{"default", "production"},
	}

	assert.Equal(t, "test", selector.MatchLabels["app"])
	assert.Equal(t, []string{"component-1", "component-2"}, selector.ComponentNames)
	assert.Equal(t, []ComponentFunction{CoreFunction, SecurityFunction}, selector.ComponentFunctions)
	assert.Equal(t, []string{"default", "production"}, selector.Namespaces)
}

func TestAvailabilityPolicySpecStructure(t *testing.T) {
	enforceTrue := true
	allowOverrideTrue := true
	overrideRequiresReasonFalse := false

	spec := AvailabilityPolicySpec{
		AvailabilityClass: HighAvailability,
		ComponentSelector: ComponentSelector{
			MatchLabels: map[string]string{"tier": "frontend"},
		},
		Priority:                   100,
		Enforcement:                EnforcementFlexible,
		MinimumClass:               Standard,
		EnforceMinReplicas:         &enforceTrue,
		AllowOverride:              &allowOverrideTrue,
		OverrideRequiresAnnotation: "pdb.example.com/allow-override",
		OverrideRequiresReason:     &overrideRequiresReasonFalse,
	}

	assert.Equal(t, HighAvailability, spec.AvailabilityClass)
	assert.Equal(t, int32(100), spec.Priority)
	assert.Equal(t, EnforcementFlexible, spec.Enforcement)
	assert.Equal(t, Standard, spec.MinimumClass)
	assert.True(t, *spec.EnforceMinReplicas)
	assert.True(t, *spec.AllowOverride)
	assert.Equal(t, "pdb.example.com/allow-override", spec.OverrideRequiresAnnotation)
	assert.False(t, *spec.OverrideRequiresReason)
}

func TestAvailabilityPolicyStatusStructure(t *testing.T) {
	status := AvailabilityPolicyStatus{
		AppliedToComponents: []string{"deploy-1", "deploy-2"},
		PDBsManaged:         []string{"pdb-1", "pdb-2"},
		ObservedGeneration:  5,
	}

	assert.Equal(t, []string{"deploy-1", "deploy-2"}, status.AppliedToComponents)
	assert.Equal(t, []string{"pdb-1", "pdb-2"}, status.PDBsManaged)
	assert.Equal(t, int64(5), status.ObservedGeneration)
}
