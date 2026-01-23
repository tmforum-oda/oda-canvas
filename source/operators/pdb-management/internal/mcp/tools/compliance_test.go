package tools

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes/fake"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/utils/ptr"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestComplianceTools_ValidatePolicyCompliance(t *testing.T) {
	tests := []struct {
		name             string
		deployments      []appsv1.Deployment
		policies         []v1alpha1.AvailabilityPolicy
		pdbs             []policyv1.PodDisruptionBudget
		params           ValidatePolicyComplianceParams
		expectViolations int
		expectCompliant  int
	}{
		{
			name: "deployment violates policy - missing PDB",
			deployments: []appsv1.Deployment{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "test-app",
						Namespace: "default",
						Annotations: map[string]string{
							"oda.tmforum.org/availability-class": "high-availability",
						},
					},
					Spec: appsv1.DeploymentSpec{
						Replicas: ptr.To(int32(3)),
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "test-app"},
						},
					},
				},
			},
			policies: []v1alpha1.AvailabilityPolicy{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "high-availability-policy",
						Namespace: "default",
					},
					Spec: v1alpha1.AvailabilityPolicySpec{
						AvailabilityClass: v1alpha1.HighAvailability,
						Enforcement:       v1alpha1.EnforcementStrict,
						Priority:          100,
						ComponentSelector: v1alpha1.ComponentSelector{
							MatchLabels: map[string]string{},
						},
					},
				},
			},
			pdbs: []policyv1.PodDisruptionBudget{}, // No PDB - should violate
			params: ValidatePolicyComplianceParams{
				Namespace: "default",
			},
			expectViolations: 1,
			expectCompliant:  0,
		},
		{
			name: "deployment compliant with policy",
			deployments: []appsv1.Deployment{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "compliant-app",
						Namespace: "default",
						Annotations: map[string]string{
							"oda.tmforum.org/availability-class": "high-availability",
						},
					},
					Spec: appsv1.DeploymentSpec{
						Replicas: ptr.To(int32(5)),
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "compliant-app"},
						},
					},
				},
			},
			policies: []v1alpha1.AvailabilityPolicy{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "high-availability-policy",
						Namespace: "default",
					},
					Spec: v1alpha1.AvailabilityPolicySpec{
						AvailabilityClass: v1alpha1.HighAvailability,
						Enforcement:       v1alpha1.EnforcementStrict,
						Priority:          100,
						ComponentSelector: v1alpha1.ComponentSelector{
							MatchLabels: map[string]string{},
						},
					},
				},
			},
			pdbs: []policyv1.PodDisruptionBudget{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "compliant-app-pdb",
						Namespace: "default",
					},
					Spec: policyv1.PodDisruptionBudgetSpec{
						MinAvailable: &intstr.IntOrString{
							Type:   intstr.String,
							StrVal: "50%", // High availability expects 50%
						},
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "compliant-app"},
						},
					},
				},
			},
			params: ValidatePolicyComplianceParams{
				Namespace: "default",
			},
			expectViolations: 0,
			expectCompliant:  1,
		},
		{
			name: "deployment compliant with custom PDB config",
			deployments: []appsv1.Deployment{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "custom-app",
						Namespace: "default",
						Annotations: map[string]string{
							"oda.tmforum.org/availability-class": "custom",
						},
					},
					Spec: appsv1.DeploymentSpec{
						Replicas: ptr.To(int32(3)),
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "custom-app"},
						},
					},
				},
			},
			policies: []v1alpha1.AvailabilityPolicy{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "custom-policy",
						Namespace: "default",
					},
					Spec: v1alpha1.AvailabilityPolicySpec{
						AvailabilityClass: v1alpha1.Custom,
						Enforcement:       v1alpha1.EnforcementStrict,
						Priority:          100,
						ComponentSelector: v1alpha1.ComponentSelector{
							MatchLabels: map[string]string{},
						},
						CustomPDBConfig: &v1alpha1.PodDisruptionBudgetConfig{
							MinAvailable: &intstr.IntOrString{
								Type:   intstr.String,
								StrVal: "90%",
							},
						},
					},
				},
			},
			pdbs: []policyv1.PodDisruptionBudget{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "custom-app-pdb",
						Namespace: "default",
					},
					Spec: policyv1.PodDisruptionBudgetSpec{
						MinAvailable: &intstr.IntOrString{
							Type:   intstr.String,
							StrVal: "90%", // Matches custom config
						},
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "custom-app"},
						},
					},
				},
			},
			params: ValidatePolicyComplianceParams{
				Namespace: "default",
			},
			expectViolations: 0,
			expectCompliant:  1,
		},
		{
			name: "filtered by specific deployment",
			deployments: []appsv1.Deployment{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "target-app",
						Namespace: "default",
						Annotations: map[string]string{
							"oda.tmforum.org/availability-class": "high-availability",
						},
					},
					Spec: appsv1.DeploymentSpec{
						Replicas: ptr.To(int32(3)),
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "target-app"},
						},
					},
				},
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "other-app",
						Namespace: "default",
						Annotations: map[string]string{
							"oda.tmforum.org/availability-class": "high-availability",
						},
					},
					Spec: appsv1.DeploymentSpec{
						Replicas: ptr.To(int32(3)),
						Selector: &metav1.LabelSelector{
							MatchLabels: map[string]string{"app": "other-app"},
						},
					},
				},
			},
			policies: []v1alpha1.AvailabilityPolicy{
				{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "high-availability-policy",
						Namespace: "default",
					},
					Spec: v1alpha1.AvailabilityPolicySpec{
						AvailabilityClass: v1alpha1.HighAvailability,
						Enforcement:       v1alpha1.EnforcementStrict,
						Priority:          100,
						ComponentSelector: v1alpha1.ComponentSelector{
							MatchLabels: map[string]string{},
						},
					},
				},
			},
			pdbs: []policyv1.PodDisruptionBudget{}, // No PDBs
			params: ValidatePolicyComplianceParams{
				Namespace:   "default",
				Deployments: []string{"target-app"}, // Only check target-app
			},
			expectViolations: 1, // Only target-app should be checked
			expectCompliant:  0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create scheme and add types
			testScheme := runtime.NewScheme()
			err := v1alpha1.AddToScheme(testScheme)
			require.NoError(t, err)
			err = clientgoscheme.AddToScheme(testScheme)
			require.NoError(t, err)

			// Convert objects to runtime.Object for fake client
			objects := make([]runtime.Object, 0)
			for i := range tt.deployments {
				objects = append(objects, &tt.deployments[i])
			}
			for i := range tt.policies {
				objects = append(objects, &tt.policies[i])
			}
			for i := range tt.pdbs {
				objects = append(objects, &tt.pdbs[i])
			}

			fakeClient := clientfake.NewClientBuilder().
				WithScheme(testScheme).
				WithRuntimeObjects(objects...).
				Build()

			fakeKubeClient := fake.NewSimpleClientset()

			// Create compliance tools instance
			logger := zap.New(zap.UseDevMode(true))
			complianceTools := NewComplianceTools(fakeClient, fakeKubeClient, logger)

			// Convert params to JSON
			paramsJSON, err := json.Marshal(tt.params)
			require.NoError(t, err)

			// Execute the function
			result, err := complianceTools.ValidatePolicyCompliance(context.Background(), paramsJSON)
			require.NoError(t, err)
			require.NotNil(t, result)

			// Parse the result
			var validationResult ValidatePolicyComplianceResult
			resultJSON, err := json.Marshal(result.Content)
			require.NoError(t, err)
			err = json.Unmarshal(resultJSON, &validationResult)
			require.NoError(t, err)

			// Verify expectations
			assert.Len(t, validationResult.Violations, tt.expectViolations, "Expected %d violations, got %d", tt.expectViolations, len(validationResult.Violations))
			assert.Len(t, validationResult.Compliant, tt.expectCompliant, "Expected %d compliant deployments, got %d", tt.expectCompliant, len(validationResult.Compliant))

			// Verify that policies are included in the result
			assert.Greater(t, len(validationResult.Policies), 0, "Should include policy information")

			// If there are violations, verify they contain required fields
			for _, violation := range validationResult.Violations {
				assert.NotEmpty(t, violation.ViolationType, "Violation should have a type")
				assert.NotEmpty(t, violation.Severity, "Violation should have a severity")
				assert.NotEmpty(t, violation.Description, "Violation should have a description")
				assert.NotEmpty(t, violation.Deployment, "Violation should specify deployment")
			}

			// If there are compliant entries, verify they contain required fields
			for _, compliant := range validationResult.Compliant {
				assert.NotEmpty(t, compliant.Deployment, "Compliant entry should specify deployment")
				assert.NotEmpty(t, compliant.PolicyName, "Compliant entry should specify policy")
			}
		})
	}
}

func TestComplianceTools_ValidatePolicyComplianceErrorHandling(t *testing.T) {
	// Create scheme and add types
	testScheme := runtime.NewScheme()
	err := v1alpha1.AddToScheme(testScheme)
	require.NoError(t, err)
	err = clientgoscheme.AddToScheme(testScheme)
	require.NoError(t, err)

	fakeClient := clientfake.NewClientBuilder().WithScheme(testScheme).Build()
	fakeKubeClient := fake.NewSimpleClientset()

	logger := zap.New(zap.UseDevMode(true))
	complianceTools := NewComplianceTools(fakeClient, fakeKubeClient, logger)

	t.Run("invalid JSON parameters", func(t *testing.T) {
		invalidJSON := json.RawMessage(`{"invalid": json}`)

		result, err := complianceTools.ValidatePolicyCompliance(context.Background(), invalidJSON)
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "invalid parameters")
	})

	t.Run("empty namespace returns all namespaces", func(t *testing.T) {
		params := ValidatePolicyComplianceParams{
			Namespace: "", // Empty namespace should work
		}
		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := complianceTools.ValidatePolicyCompliance(context.Background(), paramsJSON)
		require.NoError(t, err)
		require.NotNil(t, result)

		// Should return a valid result even with no data
		var validationResult ValidatePolicyComplianceResult
		resultJSON, err := json.Marshal(result.Content)
		require.NoError(t, err)
		err = json.Unmarshal(resultJSON, &validationResult)
		require.NoError(t, err)

		// Should have empty but valid arrays (can be nil or empty slice)
		assert.Equal(t, 0, len(validationResult.Violations), "Should have no violations")
		assert.Equal(t, 0, len(validationResult.Compliant), "Should have no compliant entries")
		assert.Equal(t, 0, len(validationResult.Policies), "Should have no policies")
		// Recommendations may be generated even with no data, so just check it's not nil
		assert.GreaterOrEqual(t, len(validationResult.Recommendations), 0, "Recommendations should be a valid array")
	})
}

func TestComplianceTools_PolicySelection(t *testing.T) {
	// Test that only policies matching the specified criteria are used
	deployment := appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-app",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "high-availability",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: ptr.To(int32(3)),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test-app"},
			},
		},
	}

	targetPolicy := v1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "target-policy",
			Namespace: "default",
		},
		Spec: v1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: v1alpha1.HighAvailability,
			Enforcement:       v1alpha1.EnforcementStrict,
			Priority:          100,
			ComponentSelector: v1alpha1.ComponentSelector{
				MatchLabels: map[string]string{},
			},
		},
	}

	otherPolicy := v1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "other-policy",
			Namespace: "default",
		},
		Spec: v1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: v1alpha1.MissionCritical,
			Enforcement:       v1alpha1.EnforcementStrict,
			Priority:          200,
			ComponentSelector: v1alpha1.ComponentSelector{
				MatchLabels: map[string]string{},
			},
		},
	}

	// Create scheme and add types
	testScheme := runtime.NewScheme()
	err := v1alpha1.AddToScheme(testScheme)
	require.NoError(t, err)
	err = clientgoscheme.AddToScheme(testScheme)
	require.NoError(t, err)

	fakeClient := clientfake.NewClientBuilder().
		WithScheme(testScheme).
		WithRuntimeObjects(&deployment, &targetPolicy, &otherPolicy).
		Build()

	fakeKubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))
	complianceTools := NewComplianceTools(fakeClient, fakeKubeClient, logger)

	// Test filtering by policy name
	params := ValidatePolicyComplianceParams{
		Namespace:  "default",
		PolicyName: "target-policy",
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := complianceTools.ValidatePolicyCompliance(context.Background(), paramsJSON)
	require.NoError(t, err)
	require.NotNil(t, result)

	var validationResult ValidatePolicyComplianceResult
	resultJSON, err := json.Marshal(result.Content)
	require.NoError(t, err)
	err = json.Unmarshal(resultJSON, &validationResult)
	require.NoError(t, err)

	// Should only consider the target policy
	assert.Len(t, validationResult.Policies, 1)
	assert.Equal(t, "target-policy", validationResult.Policies[0].Name)
}
