package controller

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
)

// Test helper functions

func TestContainsString(t *testing.T) {
	tests := []struct {
		name     string
		slice    []string
		s        string
		expected bool
	}{
		{
			name:     "string exists in slice",
			slice:    []string{"a", "b", "c"},
			s:        "b",
			expected: true,
		},
		{
			name:     "string does not exist in slice",
			slice:    []string{"a", "b", "c"},
			s:        "d",
			expected: false,
		},
		{
			name:     "empty slice",
			slice:    []string{},
			s:        "a",
			expected: false,
		},
		{
			name:     "empty string in slice",
			slice:    []string{"", "a"},
			s:        "",
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := containsString(tt.slice, tt.s)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestRemoveString(t *testing.T) {
	tests := []struct {
		name        string
		slice       []string
		s           string
		expected    []string
		expectEmpty bool
	}{
		{
			name:     "remove existing string",
			slice:    []string{"a", "b", "c"},
			s:        "b",
			expected: []string{"a", "c"},
		},
		{
			name:     "remove first string",
			slice:    []string{"a", "b", "c"},
			s:        "a",
			expected: []string{"b", "c"},
		},
		{
			name:     "remove last string",
			slice:    []string{"a", "b", "c"},
			s:        "c",
			expected: []string{"a", "b"},
		},
		{
			name:     "string not in slice",
			slice:    []string{"a", "b", "c"},
			s:        "d",
			expected: []string{"a", "b", "c"},
		},
		{
			name:        "empty slice",
			slice:       []string{},
			s:           "a",
			expectEmpty: true,
		},
		{
			name:        "single element slice - remove",
			slice:       []string{"a"},
			s:           "a",
			expectEmpty: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := removeString(tt.slice, tt.s)
			if tt.expectEmpty {
				assert.Empty(t, result)
			} else {
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestIsValidAvailabilityClass(t *testing.T) {
	tests := []struct {
		name     string
		class    availabilityv1alpha1.AvailabilityClass
		expected bool
	}{
		{"non-critical", availabilityv1alpha1.NonCritical, true},
		{"standard", availabilityv1alpha1.Standard, true},
		{"high-availability", availabilityv1alpha1.HighAvailability, true},
		{"mission-critical", availabilityv1alpha1.MissionCritical, true},
		{"custom", availabilityv1alpha1.Custom, true},
		{"invalid", availabilityv1alpha1.AvailabilityClass("invalid-class"), false},
		{"empty", availabilityv1alpha1.AvailabilityClass(""), false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reconciler := &DeploymentReconciler{}
			result := reconciler.isValidAvailabilityClass(tt.class)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGetDescriptionForClass(t *testing.T) {
	tests := []struct {
		name  string
		class availabilityv1alpha1.AvailabilityClass
	}{
		{"non-critical", availabilityv1alpha1.NonCritical},
		{"standard", availabilityv1alpha1.Standard},
		{"high-availability", availabilityv1alpha1.HighAvailability},
		{"mission-critical", availabilityv1alpha1.MissionCritical},
		{"custom", availabilityv1alpha1.Custom},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reconciler := &DeploymentReconciler{}
			result := reconciler.getDescriptionForClass(tt.class)
			assert.NotEmpty(t, result, "Description should not be empty")
		})
	}
}

func TestInferComponentFunction(t *testing.T) {
	tests := []struct {
		name           string
		deploymentName string
		labels         map[string]string
		annotations    map[string]string
		expected       availabilityv1alpha1.ComponentFunction
	}{
		{
			name:           "auth in name",
			deploymentName: "auth-service",
			expected:       availabilityv1alpha1.SecurityFunction,
		},
		{
			name:           "security in name",
			deploymentName: "security-gateway",
			expected:       availabilityv1alpha1.SecurityFunction,
		},
		{
			name:           "controller in name",
			deploymentName: "nginx-controller",
			expected:       availabilityv1alpha1.ManagementFunction,
		},
		{
			name:           "operator in name",
			deploymentName: "cert-manager-operator",
			expected:       availabilityv1alpha1.ManagementFunction,
		},
		{
			name:           "api in name",
			deploymentName: "api-gateway",
			expected:       availabilityv1alpha1.CoreFunction,
		},
		{
			name:           "regular deployment",
			deploymentName: "frontend",
			expected:       availabilityv1alpha1.CoreFunction,
		},
		{
			name:           "with security annotation",
			deploymentName: "my-service",
			annotations:    map[string]string{AnnotationComponentFunction: "security"},
			expected:       availabilityv1alpha1.SecurityFunction,
		},
		{
			name:           "annotation takes precedence over name",
			deploymentName: "auth-service",
			annotations:    map[string]string{AnnotationComponentFunction: "core"},
			expected:       availabilityv1alpha1.CoreFunction,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reconciler := &DeploymentReconciler{}
			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:        tt.deploymentName,
					Labels:      tt.labels,
					Annotations: tt.annotations,
				},
			}
			result := reconciler.inferComponentFunction(deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSelectorsOverlap(t *testing.T) {
	tests := []struct {
		name      string
		selector1 *metav1.LabelSelector
		selector2 *metav1.LabelSelector
		expected  bool
	}{
		{
			name: "identical selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			expected: true,
		},
		{
			name: "overlapping selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test", "env": "prod"},
			},
			expected: true,
		},
		{
			name: "non-overlapping selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test1"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test2"},
			},
			expected: false,
		},
		{
			name:      "nil selector1",
			selector1: nil,
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			expected: false,
		},
		{
			name: "nil selector2",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			selector2: nil,
			expected:  false,
		},
		{
			name: "empty selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reconciler := &DeploymentReconciler{}
			result := reconciler.selectorsOverlap(tt.selector1, tt.selector2)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSelectorEquals(t *testing.T) {
	tests := []struct {
		name      string
		selector1 *metav1.LabelSelector
		selector2 *metav1.LabelSelector
		expected  bool
	}{
		{
			name: "identical selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			expected: true,
		},
		{
			name: "different selectors",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test1"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test2"},
			},
			expected: false,
		},
		{
			name: "different number of labels",
			selector1: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test", "env": "prod"},
			},
			expected: false,
		},
		{
			name:      "nil selector1",
			selector1: nil,
			selector2: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			expected: false,
		},
		{
			name:      "both nil selectors",
			selector1: nil,
			selector2: nil,
			expected:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// selectorEquals is a standalone function
			result := selectorEquals(tt.selector1, tt.selector2)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDetectInvalidConfiguration(t *testing.T) {
	tests := []struct {
		name        string
		annotations map[string]string
		expectError bool
	}{
		{
			name: "valid configuration",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
			expectError: false,
		},
		{
			name: "invalid availability class",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "invalid-class",
			},
			expectError: true,
		},
		{
			name:        "no annotations",
			annotations: map[string]string{},
			expectError: false,
		},
		{
			name: "custom class is valid",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "custom",
			},
			expectError: false, // detectInvalidConfiguration only validates the class value, not config requirements
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reconciler := &DeploymentReconciler{}
			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:        "test-deployment",
					Namespace:   "default",
					Annotations: tt.annotations,
				},
			}
			errMsg := reconciler.detectInvalidConfiguration(deployment)
			if tt.expectError {
				assert.NotEmpty(t, errMsg, "Expected error message")
			} else {
				assert.Empty(t, errMsg, "Expected no error")
			}
		})
	}
}

func TestCalculateDeploymentFingerprint(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(3); return &i }(),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "test"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "test",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	config := &AvailabilityConfig{
		AvailabilityClass: availabilityv1alpha1.HighAvailability,
		MinAvailable:      intstr.FromString("66%"),
	}

	scheme := SetupTestScheme()
	reconciler := &DeploymentReconciler{
		Client:              CreateFakeClient(deployment),
		Scheme:              scheme,
		lastDeploymentState: make(map[types.NamespacedName]string),
		mu:                  sync.RWMutex{},
	}
	fingerprint, err := reconciler.calculateDeploymentFingerprint(ctx, deployment, config)
	require.NoError(t, err)
	assert.NotEmpty(t, fingerprint, "Fingerprint should not be empty")

	// Same deployment should produce same fingerprint
	fingerprint2, err := reconciler.calculateDeploymentFingerprint(ctx, deployment, config)
	require.NoError(t, err)
	assert.Equal(t, fingerprint, fingerprint2, "Same deployment should produce same fingerprint")

	// Different deployment should produce different fingerprint
	deployment2 := deployment.DeepCopy()
	deployment2.Spec.Replicas = func() *int32 { i := int32(5); return &i }()
	fingerprint3, err := reconciler.calculateDeploymentFingerprint(ctx, deployment2, config)
	require.NoError(t, err)
	assert.NotEqual(t, fingerprint, fingerprint3, "Different deployment should produce different fingerprint")
}

func TestHasDeploymentStateChanged(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:       "test-deployment",
			Namespace:  "default",
			Generation: 1,
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(3); return &i }(),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
	}

	config := &AvailabilityConfig{
		AvailabilityClass: availabilityv1alpha1.HighAvailability,
		MinAvailable:      intstr.FromString("66%"),
	}

	reconciler := &DeploymentReconciler{
		Client:              CreateFakeClient(deployment),
		lastDeploymentState: make(map[types.NamespacedName]string),
		mu:                  sync.RWMutex{},
	}

	// First call - no previous state
	changed, err := reconciler.hasDeploymentStateChanged(ctx, deployment, config)
	require.NoError(t, err)
	assert.True(t, changed, "First call should indicate change (no previous state)")

	// Store state
	err = reconciler.updateDeploymentState(ctx, deployment, config)
	require.NoError(t, err)

	// Same deployment - no change
	changed, err = reconciler.hasDeploymentStateChanged(ctx, deployment, config)
	require.NoError(t, err)
	assert.False(t, changed, "Same deployment should not indicate change")

	// Modified deployment - should indicate change
	deployment.Spec.Replicas = func() *int32 { i := int32(5); return &i }()
	changed, err = reconciler.hasDeploymentStateChanged(ctx, deployment, config)
	require.NoError(t, err)
	assert.True(t, changed, "Modified deployment should indicate change")
}

func TestUpdateAndClearDeploymentState(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:       "test-deployment",
			Namespace:  "default",
			Generation: 1,
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(3); return &i }(),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
	}

	config := &AvailabilityConfig{
		AvailabilityClass: availabilityv1alpha1.HighAvailability,
		MinAvailable:      intstr.FromString("66%"),
	}

	reconciler := &DeploymentReconciler{
		Client:              CreateFakeClient(deployment),
		lastDeploymentState: make(map[types.NamespacedName]string),
		mu:                  sync.RWMutex{},
	}

	// Update state
	err := reconciler.updateDeploymentState(ctx, deployment, config)
	require.NoError(t, err)
	key := types.NamespacedName{Name: deployment.Name, Namespace: deployment.Namespace}
	reconciler.mu.RLock()
	_, exists := reconciler.lastDeploymentState[key]
	reconciler.mu.RUnlock()
	assert.True(t, exists, "State should be stored")

	// Clear state
	reconciler.clearDeploymentState(deployment)
	reconciler.mu.RLock()
	_, exists = reconciler.lastDeploymentState[key]
	reconciler.mu.RUnlock()
	assert.False(t, exists, "State should be cleared")
}

// Tests for AvailabilityPolicy controller helper functions

func TestValidateMaintenanceWindow(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	tests := []struct {
		name        string
		window      availabilityv1alpha1.MaintenanceWindow
		expectError bool
	}{
		{
			name: "valid window",
			window: availabilityv1alpha1.MaintenanceWindow{
				Start:    "02:00",
				End:      "04:00",
				Timezone: "UTC",
			},
			expectError: false,
		},
		{
			name: "invalid start time",
			window: availabilityv1alpha1.MaintenanceWindow{
				Start:    "25:00",
				End:      "04:00",
				Timezone: "UTC",
			},
			expectError: true,
		},
		{
			name: "invalid end time",
			window: availabilityv1alpha1.MaintenanceWindow{
				Start:    "02:00",
				End:      "invalid",
				Timezone: "UTC",
			},
			expectError: true,
		},
		{
			name: "invalid timezone",
			window: availabilityv1alpha1.MaintenanceWindow{
				Start:    "02:00",
				End:      "04:00",
				Timezone: "Invalid/Timezone",
			},
			expectError: true,
		},
		{
			name: "empty timezone defaults to UTC",
			window: availabilityv1alpha1.MaintenanceWindow{
				Start:    "02:00",
				End:      "04:00",
				Timezone: "",
			},
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := reconciler.validateMaintenanceWindow(tt.window)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestValidatePolicy(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	tests := []struct {
		name        string
		policy      *availabilityv1alpha1.AvailabilityPolicy
		expectError bool
	}{
		{
			name: "valid policy with standard class",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			expectError: false,
		},
		{
			name: "custom class without config",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Custom,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			expectError: true,
		},
		{
			name: "custom class with config",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Custom,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					CustomPDBConfig: &availabilityv1alpha1.PodDisruptionBudgetConfig{
						MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "50%"},
					},
				},
			},
			expectError: false,
		},
		{
			name: "invalid availability class",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.AvailabilityClass("invalid"),
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
			},
			expectError: true,
		},
		{
			name: "empty component selector",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{},
				},
			},
			expectError: true,
		},
		{
			name: "custom class with empty PDB config",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Custom,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
					CustomPDBConfig: &availabilityv1alpha1.PodDisruptionBudgetConfig{
						// Neither MinAvailable nor MaxUnavailable
					},
				},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := reconciler.validatePolicy(tt.policy)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestUpdateConditions(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	tests := []struct {
		name           string
		hasMatches     bool
		expectedStatus metav1.ConditionStatus
		expectedReason string
	}{
		{
			name:           "has matches",
			hasMatches:     true,
			expectedStatus: metav1.ConditionTrue,
			expectedReason: "ComponentsMatched",
		},
		{
			name:           "no matches",
			hasMatches:     false,
			expectedStatus: metav1.ConditionFalse,
			expectedReason: "NoComponentsMatched",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			policy := &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-policy",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "test"},
					},
				},
				Status: availabilityv1alpha1.AvailabilityPolicyStatus{},
			}

			if tt.hasMatches {
				policy.Status.AppliedToComponents = []string{"component1"}
			}

			reconciler.updateConditions(policy, tt.hasMatches)

			// Find Ready condition
			var readyCondition *metav1.Condition
			for _, c := range policy.Status.Conditions {
				if c.Type == "Ready" {
					readyCondition = &c
					break
				}
			}

			require.NotNil(t, readyCondition, "Should have Ready condition")
			assert.Equal(t, tt.expectedStatus, readyCondition.Status)
			assert.Equal(t, tt.expectedReason, readyCondition.Reason)
		})
	}
}

func TestSetCondition(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	conditions := []metav1.Condition{}

	// Set first condition
	condition1 := metav1.Condition{
		Type:               "TestCondition",
		Status:             metav1.ConditionTrue,
		Reason:             "TestReason",
		Message:            "Test message",
		LastTransitionTime: metav1.Now(),
		ObservedGeneration: 1,
	}
	reconciler.setCondition(&conditions, condition1)

	require.Len(t, conditions, 1)
	assert.Equal(t, "TestCondition", conditions[0].Type)
	assert.Equal(t, metav1.ConditionTrue, conditions[0].Status)
	assert.Equal(t, "TestReason", conditions[0].Reason)

	// Update existing condition
	condition2 := metav1.Condition{
		Type:               "TestCondition",
		Status:             metav1.ConditionFalse,
		Reason:             "NewReason",
		Message:            "New message",
		LastTransitionTime: metav1.Now(),
		ObservedGeneration: 1,
	}
	reconciler.setCondition(&conditions, condition2)

	require.Len(t, conditions, 1)
	assert.Equal(t, metav1.ConditionFalse, conditions[0].Status)
	assert.Equal(t, "NewReason", conditions[0].Reason)

	// Add another condition
	condition3 := metav1.Condition{
		Type:               "AnotherCondition",
		Status:             metav1.ConditionTrue,
		Reason:             "Reason2",
		Message:            "Message 2",
		LastTransitionTime: metav1.Now(),
		ObservedGeneration: 1,
	}
	reconciler.setCondition(&conditions, condition3)

	require.Len(t, conditions, 2)
}

func TestEvaluateLabelSelectorRequirement(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	tests := []struct {
		name        string
		labels      map[string]string
		requirement metav1.LabelSelectorRequirement
		expected    bool
	}{
		{
			name:   "In operator - matches",
			labels: map[string]string{"env": "prod"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpIn,
				Values:   []string{"prod", "staging"},
			},
			expected: true,
		},
		{
			name:   "In operator - no match",
			labels: map[string]string{"env": "dev"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpIn,
				Values:   []string{"prod", "staging"},
			},
			expected: false,
		},
		{
			name:   "NotIn operator - matches",
			labels: map[string]string{"env": "dev"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpNotIn,
				Values:   []string{"prod", "staging"},
			},
			expected: true,
		},
		{
			name:   "Exists operator - matches",
			labels: map[string]string{"env": "prod"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpExists,
			},
			expected: true,
		},
		{
			name:   "Exists operator - no match",
			labels: map[string]string{"other": "value"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpExists,
			},
			expected: false,
		},
		{
			name:   "DoesNotExist operator - matches",
			labels: map[string]string{"other": "value"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpDoesNotExist,
			},
			expected: true,
		},
		{
			name:   "DoesNotExist operator - no match",
			labels: map[string]string{"env": "prod"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpDoesNotExist,
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.evaluateLabelSelectorRequirement(tt.requirement, tt.labels)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestEvaluateMatchExpression(t *testing.T) {
	reconciler := &DeploymentReconciler{}

	tests := []struct {
		name        string
		labels      map[string]string
		requirement metav1.LabelSelectorRequirement
		expected    bool
	}{
		{
			name:   "In operator - matches",
			labels: map[string]string{"env": "prod"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpIn,
				Values:   []string{"prod", "staging"},
			},
			expected: true,
		},
		{
			name:   "NotIn operator - matches",
			labels: map[string]string{"env": "dev"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpNotIn,
				Values:   []string{"prod", "staging"},
			},
			expected: true,
		},
		{
			name:   "Exists operator - matches",
			labels: map[string]string{"env": "anything"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpExists,
			},
			expected: true,
		},
		{
			name:   "DoesNotExist operator - matches",
			labels: map[string]string{"other": "value"},
			requirement: metav1.LabelSelectorRequirement{
				Key:      "env",
				Operator: metav1.LabelSelectorOpDoesNotExist,
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.evaluateMatchExpression(tt.requirement, tt.labels)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDeploymentMatchesSelector(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app":  "myapp",
				"tier": "frontend",
			},
			Annotations: map[string]string{
				AnnotationComponentName: "my-component",
			},
		},
	}

	tests := []struct {
		name     string
		selector availabilityv1alpha1.ComponentSelector
		expected bool
	}{
		{
			name: "match by labels",
			selector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "myapp"},
			},
			expected: true,
		},
		{
			name: "no match by labels",
			selector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "other"},
			},
			expected: false,
		},
		{
			name: "match by component name",
			selector: availabilityv1alpha1.ComponentSelector{
				ComponentNames: []string{"my-component"},
			},
			expected: true,
		},
		{
			name: "match by multiple criteria",
			selector: availabilityv1alpha1.ComponentSelector{
				MatchLabels:    map[string]string{"app": "myapp"},
				ComponentNames: []string{"my-component"},
			},
			expected: true,
		},
		{
			name: "match expressions - In operator",
			selector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "tier",
						Operator: metav1.LabelSelectorOpIn,
						Values:   []string{"frontend", "backend"},
					},
				},
			},
			expected: true,
		},
		{
			name: "match expressions - NotIn operator - no match",
			selector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "tier",
						Operator: metav1.LabelSelectorOpNotIn,
						Values:   []string{"frontend", "backend"},
					},
				},
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.deploymentMatchesSelector(tt.selector, deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestPolicyMatchesDeployment(t *testing.T) {
	tests := []struct {
		name       string
		deployment *appsv1.Deployment
		policy     *availabilityv1alpha1.AvailabilityPolicy
		expected   bool
	}{
		{
			name: "matches by labels",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-deployment",
					Namespace: "default",
					Labels:    map[string]string{"app": "myapp"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-policy",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "myapp"},
					},
				},
			},
			expected: true,
		},
		{
			name: "no match",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-deployment",
					Namespace: "default",
					Labels:    map[string]string{"app": "other"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-policy",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"app": "myapp"},
					},
				},
			},
			expected: false,
		},
		{
			name: "matches with expressions",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-deployment",
					Namespace: "default",
					Labels:    map[string]string{"env": "prod"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-policy",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchExpressions: []metav1.LabelSelectorRequirement{
							{
								Key:      "env",
								Operator: metav1.LabelSelectorOpIn,
								Values:   []string{"prod", "staging"},
							},
						},
					},
				},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tr := CreateTestReconcilers(tt.deployment, tt.policy)
			result := tr.DeploymentReconciler.policyMatchesDeployment(tt.policy, tt.deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestIsInMaintenanceWindow(t *testing.T) {
	reconciler := &DeploymentReconciler{}
	logger := ctrl.Log.WithName("test")

	// Create a maintenance window that spans a specific time
	now := time.Now().UTC()
	startTime := now.Add(-1 * time.Hour).Format("15:04")
	endTime := now.Add(1 * time.Hour).Format("15:04")

	tests := []struct {
		name     string
		config   *AvailabilityConfig
		expected bool
	}{
		{
			name: "within maintenance window",
			config: &AvailabilityConfig{
				MaintenanceWindow: startTime + "-" + endTime + " UTC",
			},
			expected: true,
		},
		{
			name: "outside maintenance window",
			config: &AvailabilityConfig{
				MaintenanceWindow: "03:00-04:00 UTC",
			},
			expected: false,
		},
		{
			name: "no maintenance window",
			config: &AvailabilityConfig{
				MaintenanceWindow: "",
			},
			expected: false,
		},
		{
			name: "invalid maintenance window format",
			config: &AvailabilityConfig{
				MaintenanceWindow: "invalid",
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.isInMaintenanceWindow(tt.config, logger)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGetConfigFromAnnotations(t *testing.T) {
	reconciler := &DeploymentReconciler{}
	logger := ctrl.Log.WithName("test")

	tests := []struct {
		name        string
		annotations map[string]string
		hasConfig   bool
		class       availabilityv1alpha1.AvailabilityClass
	}{
		{
			name: "has availability class annotation",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
			hasConfig: true,
			class:     availabilityv1alpha1.HighAvailability,
		},
		{
			name:        "no annotations",
			annotations: map[string]string{},
			hasConfig:   false,
		},
		{
			name: "with component function annotation",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentFunction: "security",
			},
			hasConfig: true,
			class:     availabilityv1alpha1.Standard,
		},
		{
			name: "with maintenance window annotation",
			annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationMaintenanceWindow: "02:00-04:00 UTC",
			},
			hasConfig: true,
			class:     availabilityv1alpha1.Standard,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:        "test-deployment",
					Namespace:   "default",
					Annotations: tt.annotations,
				},
			}

			config := reconciler.getConfigFromAnnotations(deployment, logger)

			if tt.hasConfig {
				require.NotNil(t, config)
				assert.Equal(t, tt.class, config.AvailabilityClass)
			} else {
				assert.Nil(t, config)
			}
		})
	}
}

func TestFindMatchingDeployments(t *testing.T) {
	ctx := context.Background()

	// Create deployments with different labels
	deploy1 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "frontend-1",
			Namespace: "default",
			Labels:    map[string]string{"tier": "frontend", "app": "web"},
			Annotations: map[string]string{
				AnnotationComponentName: "frontend-component-1",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(3); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "web"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "web"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}
	deploy2 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "frontend-2",
			Namespace: "default",
			Labels:    map[string]string{"tier": "frontend", "app": "api"},
			Annotations: map[string]string{
				AnnotationComponentName: "frontend-component-2",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(2); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "api"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "api"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}
	deploy3 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "backend-1",
			Namespace: "default",
			Labels:    map[string]string{"tier": "backend", "app": "db"},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "db"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "db"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "postgres"}}},
			},
		},
	}

	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "frontend-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"tier": "frontend"},
			},
		},
	}

	fakeClient := CreateFakeClient(deploy1, deploy2, deploy3, policy)
	scheme := SetupTestScheme()
	reconciler := &AvailabilityPolicyReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	// Find matching deployments
	logger := ctrl.Log.WithName("test")
	matches, err := reconciler.findMatchingDeployments(ctx, policy, logger)
	require.NoError(t, err)

	// Should match 2 frontend deployments
	assert.Len(t, matches, 2, "Should find 2 frontend deployments")
}

func TestResolveConfiguration(t *testing.T) {
	ctx := context.Background()
	logger := ctrl.Log.WithName("test")

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels:    map[string]string{"app": "myapp"},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(3); return &i }(),
		},
	}

	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "myapp"},
			},
			Enforcement: availabilityv1alpha1.EnforcementAdvisory,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	// Test advisory enforcement - annotation should win
	annotationConfig := &AvailabilityConfig{
		AvailabilityClass: availabilityv1alpha1.HighAvailability,
		Source:            "annotation",
	}
	policyConfig := &AvailabilityConfig{
		AvailabilityClass: availabilityv1alpha1.Standard,
		Source:            "policy",
		PolicyName:        policy.Name,
	}

	result := reconciler.resolveConfiguration(ctx, deployment, annotationConfig, policyConfig, policy, logger)
	assert.Equal(t, availabilityv1alpha1.HighAvailability, result.AvailabilityClass, "Advisory enforcement should prefer annotation")

	// Test strict enforcement - policy should win
	policy.Spec.Enforcement = availabilityv1alpha1.EnforcementStrict
	result = reconciler.resolveConfiguration(ctx, deployment, annotationConfig, policyConfig, policy, logger)
	assert.Equal(t, availabilityv1alpha1.Standard, result.AvailabilityClass, "Strict enforcement should use policy")

	// Test flexible enforcement with annotation meeting minimum
	policy.Spec.Enforcement = availabilityv1alpha1.EnforcementFlexible
	policy.Spec.MinimumClass = availabilityv1alpha1.Standard
	result = reconciler.resolveConfiguration(ctx, deployment, annotationConfig, policyConfig, policy, logger)
	assert.Equal(t, availabilityv1alpha1.HighAvailability, result.AvailabilityClass, "Flexible enforcement should accept annotation meeting minimum")

	// Test no policy - should use annotation
	result = reconciler.resolveConfiguration(ctx, deployment, annotationConfig, nil, nil, logger)
	require.NotNil(t, result)
	assert.Equal(t, availabilityv1alpha1.HighAvailability, result.AvailabilityClass, "No policy should use annotation")

	// Test no annotation, only policy
	result = reconciler.resolveConfiguration(ctx, deployment, nil, policyConfig, policy, logger)
	require.NotNil(t, result)
	assert.Equal(t, availabilityv1alpha1.Standard, result.AvailabilityClass, "No annotation should use policy")
}

func TestGetCacheStats(t *testing.T) {
	reconciler := &AvailabilityPolicyReconciler{}

	stats := reconciler.GetCacheStats()

	// Should return empty stats when no cache is configured
	assert.Equal(t, 0, stats.Entries, "Should have 0 entries when no cache")
}

// Tests for retry functions

func TestRetryableError(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
		{
			name:     "generic error",
			err:      assert.AnError,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := RetryableError(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestIsConflictError(t *testing.T) {
	assert.False(t, IsConflictError(nil), "nil should not be conflict")
	assert.False(t, IsConflictError(assert.AnError), "generic error should not be conflict")
}

func TestIsNotFoundError(t *testing.T) {
	assert.False(t, IsNotFoundError(nil), "nil should not be not found")
	assert.False(t, IsNotFoundError(assert.AnError), "generic error should not be not found")
}

func TestIsAlreadyExistsError(t *testing.T) {
	assert.False(t, IsAlreadyExistsError(nil), "nil should not be already exists")
	assert.False(t, IsAlreadyExistsError(assert.AnError), "generic error should not be already exists")
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
			name:     "generic error",
			err:      assert.AnError,
			expected: "unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetErrorType(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestFormatRetryError(t *testing.T) {
	err := FormatRetryError("test-operation", 3, assert.AnError)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "test-operation")
	assert.Contains(t, err.Error(), "3 attempts")
}

func TestDefaultRetryConfig(t *testing.T) {
	config := DefaultRetryConfig()
	assert.Equal(t, 5, config.MaxRetries)
	assert.Equal(t, 100*time.Millisecond, config.InitialDelay)
	assert.Equal(t, 30*time.Second, config.MaxDelay)
	assert.Equal(t, 2.0, config.BackoffFactor)
}

func TestRetryWithBackoff_Success(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	callCount := 0
	err := RetryWithBackoff(ctx, config, func() error {
		callCount++
		return nil
	})

	assert.NoError(t, err)
	assert.Equal(t, 1, callCount, "Should only call once on success")
}

func TestRetryWithBackoff_NonRetryableError(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	callCount := 0
	testErr := assert.AnError
	err := RetryWithBackoff(ctx, config, func() error {
		callCount++
		return testErr
	})

	assert.Error(t, err)
	assert.Equal(t, 1, callCount, "Should only call once for non-retryable error")
}

func TestRetryWithBackoff_ContextCancelled(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	config := RetryConfig{
		MaxRetries:    3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	err := RetryWithBackoff(ctx, config, func() error {
		return nil
	})

	assert.Error(t, err)
	assert.Equal(t, context.Canceled, err)
}

func TestRetryCreateWithBackoff(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    1,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "new-deployment",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "test"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "test"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	fakeClient := CreateFakeClient()
	err := RetryCreateWithBackoff(ctx, fakeClient, deployment, config)
	assert.NoError(t, err)
}

func TestRetryDeleteWithBackoff(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    1,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "delete-deployment",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "test"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "test"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	fakeClient := CreateFakeClient(deployment)
	err := RetryDeleteWithBackoff(ctx, fakeClient, deployment, config)
	assert.NoError(t, err)
}

func TestRetryGetWithBackoff(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    1,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "get-deployment",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "test"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "test"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	fakeClient := CreateFakeClient(deployment)
	key := types.NamespacedName{Name: "get-deployment", Namespace: "default"}
	result := &appsv1.Deployment{}
	err := RetryGetWithBackoff(ctx, fakeClient, key, result, config)
	assert.NoError(t, err)
	assert.Equal(t, "get-deployment", result.Name)
}

func TestRetryListWithBackoff(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "list-deployment",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "test"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "test"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	fakeClient := CreateFakeClient(deployment)
	list := &appsv1.DeploymentList{}
	err := RetryListWithBackoff(ctx, fakeClient, list)
	assert.NoError(t, err)
	assert.Len(t, list.Items, 1)
}

// Test for policyMatchesDeployment
func TestPolicyMatchesDeployment_AdditionalCases(t *testing.T) {
	reconciler := &DeploymentReconciler{
		Client: CreateFakeClient(),
		Scheme: SetupTestScheme(),
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app":  "myapp",
				"tier": "frontend",
			},
			Annotations: map[string]string{
				AnnotationComponentName:     "my-component",
				AnnotationComponentFunction: "core",
			},
		},
	}

	tests := []struct {
		name     string
		policy   *availabilityv1alpha1.AvailabilityPolicy
		expected bool
	}{
		{
			name: "policy matches by component function",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "policy1",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						ComponentFunctions: []availabilityv1alpha1.ComponentFunction{
							availabilityv1alpha1.CoreFunction,
						},
					},
				},
			},
			expected: true,
		},
		{
			name: "policy with different namespace - no match",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "policy2",
					Namespace: "other-namespace",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						Namespaces: []string{"other-namespace"},
					},
				},
			},
			expected: false,
		},
		{
			name: "policy with matching namespace",
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "policy3",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						Namespaces: []string{"default"},
					},
				},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.policyMatchesDeployment(tt.policy, deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Tests for findPoliciesForDeployment
func TestFindPoliciesForDeployment(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels:    map[string]string{"app": "myapp"},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "myapp"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "myapp"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "matching-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "myapp"},
			},
		},
	}

	fakeClient := CreateFakeClient(deployment, policy)
	scheme := SetupTestScheme()
	reconciler := &AvailabilityPolicyReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	requests := reconciler.findPoliciesForDeployment(ctx, deployment)
	assert.Len(t, requests, 1, "Should find one matching policy")
	assert.Equal(t, "matching-policy", requests[0].Name)
}

// Test for findPoliciesForDeployment with non-deployment object
func TestFindPoliciesForDeployment_NonDeployment(t *testing.T) {
	ctx := context.Background()

	// Pass a non-deployment object
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
	}

	fakeClient := CreateFakeClient()
	reconciler := &AvailabilityPolicyReconciler{
		Client: fakeClient,
		Scheme: SetupTestScheme(),
	}

	requests := reconciler.findPoliciesForDeployment(ctx, policy)
	assert.Nil(t, requests, "Should return nil for non-deployment object")
}

// Test for isPDBUpdateByUs - checks if last-modified annotation changed
func TestIsPDBUpdateByUs(t *testing.T) {
	tests := []struct {
		name     string
		oldPDB   *policyv1.PodDisruptionBudget
		newPDB   *policyv1.PodDisruptionBudget
		expected bool
	}{
		{
			name: "last-modified annotation changed",
			oldPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationLastModified: "2025-01-01T00:00:00Z",
					},
				},
			},
			newPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationLastModified: "2025-01-02T00:00:00Z",
					},
				},
			},
			expected: true,
		},
		{
			name: "same last-modified annotation",
			oldPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationLastModified: "2025-01-01T00:00:00Z",
					},
				},
			},
			newPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationLastModified: "2025-01-01T00:00:00Z",
					},
				},
			},
			expected: false,
		},
		{
			name: "no annotations",
			oldPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
				},
			},
			newPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
				},
			},
			expected: false,
		},
		{
			name: "new annotation added",
			oldPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
				},
			},
			newPDB: &policyv1.PodDisruptionBudget{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-pdb",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationLastModified: "2025-01-01T00:00:00Z",
					},
				},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isPDBUpdateByUs(tt.oldPDB, tt.newPDB)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Test for updateStatus in AvailabilityPolicy controller
func TestUpdateStatus(t *testing.T) {
	ctx := context.Background()
	logger := ctrl.Log.WithName("test")

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels:    map[string]string{"app": "myapp"},
			Annotations: map[string]string{
				AnnotationComponentName: "my-component",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: func() *int32 { i := int32(1); return &i }(),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "myapp"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "myapp"}},
				Spec:       corev1.PodSpec{Containers: []corev1.Container{{Name: "c", Image: "nginx"}}},
			},
		},
	}

	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "myapp"},
			},
		},
	}

	fakeClient := CreateFakeClient(deployment, policy)
	scheme := SetupTestScheme()
	reconciler := &AvailabilityPolicyReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	result, err := reconciler.updateStatus(ctx, policy, logger)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	// The updateStatus function returns a requeue after 5 minutes
	assert.Equal(t, 5*time.Minute, result.RequeueAfter)
}

// Additional tests for policyMatchesDeployment covering more branches
func TestPolicyMatchesDeployment_AllBranches(t *testing.T) {
	reconciler := &DeploymentReconciler{
		Client: CreateFakeClient(),
		Scheme: SetupTestScheme(),
	}

	tests := []struct {
		name       string
		deployment *appsv1.Deployment
		policy     *availabilityv1alpha1.AvailabilityPolicy
		expected   bool
	}{
		{
			name: "match by component name",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationComponentName: "component-a",
					},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						ComponentNames: []string{"component-a", "component-b"},
					},
				},
			},
			expected: true,
		},
		{
			name: "no match by component name",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationComponentName: "component-c",
					},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						ComponentNames: []string{"component-a", "component-b"},
					},
				},
			},
			expected: false,
		},
		{
			name: "match by label expressions - In",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Labels:    map[string]string{"env": "prod"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchExpressions: []metav1.LabelSelectorRequirement{
							{
								Key:      "env",
								Operator: metav1.LabelSelectorOpIn,
								Values:   []string{"prod", "staging"},
							},
						},
					},
				},
			},
			expected: true,
		},
		{
			name: "no match by label expressions - NotIn",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Labels:    map[string]string{"env": "prod"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchExpressions: []metav1.LabelSelectorRequirement{
							{
								Key:      "env",
								Operator: metav1.LabelSelectorOpNotIn,
								Values:   []string{"prod", "staging"},
							},
						},
					},
				},
			},
			expected: false,
		},
		{
			name: "match by label expressions - Exists",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Labels:    map[string]string{"env": "anything"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchExpressions: []metav1.LabelSelectorRequirement{
							{
								Key:      "env",
								Operator: metav1.LabelSelectorOpExists,
							},
						},
					},
				},
			},
			expected: true,
		},
		{
			name: "match by label expressions - DoesNotExist",
			deployment: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "deploy1",
					Namespace: "default",
					Labels:    map[string]string{"other": "value"},
				},
			},
			policy: &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{Name: "p1", Namespace: "default"},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: availabilityv1alpha1.Standard,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchExpressions: []metav1.LabelSelectorRequirement{
							{
								Key:      "env",
								Operator: metav1.LabelSelectorOpDoesNotExist,
							},
						},
					},
				},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := reconciler.policyMatchesDeployment(tt.policy, tt.deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Tests for global retry configuration

func TestSetGetGlobalRetryConfig(t *testing.T) {
	// Save original config
	originalConfig := GetGlobalRetryConfig()
	defer SetGlobalRetryConfig(originalConfig)

	// Set new config
	newConfig := RetryConfig{
		MaxRetries:    10,
		InitialDelay:  200 * time.Millisecond,
		MaxDelay:      60 * time.Second,
		BackoffFactor: 1.5,
	}
	SetGlobalRetryConfig(newConfig)

	// Get and verify
	retrieved := GetGlobalRetryConfig()
	assert.Equal(t, 10, retrieved.MaxRetries)
	assert.Equal(t, 200*time.Millisecond, retrieved.InitialDelay)
	assert.Equal(t, 60*time.Second, retrieved.MaxDelay)
	assert.Equal(t, 1.5, retrieved.BackoffFactor)
}

func TestRetryWithBackoffWithMetrics_Success(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	callCount := 0
	err := RetryWithBackoffWithMetrics(ctx, config, "test-operation", func() error {
		callCount++
		return nil
	})

	assert.NoError(t, err)
	assert.Equal(t, 1, callCount, "Should only call once on success")
}

func TestRetryWithBackoffWithMetrics_NonRetryableError(t *testing.T) {
	ctx := context.Background()
	config := RetryConfig{
		MaxRetries:    3,
		InitialDelay:  1 * time.Millisecond,
		MaxDelay:      10 * time.Millisecond,
		BackoffFactor: 2.0,
	}

	callCount := 0
	testErr := assert.AnError
	err := RetryWithBackoffWithMetrics(ctx, config, "test-operation", func() error {
		callCount++
		return testErr
	})

	assert.Error(t, err)
	assert.Equal(t, 1, callCount, "Should only call once for non-retryable error")
}
