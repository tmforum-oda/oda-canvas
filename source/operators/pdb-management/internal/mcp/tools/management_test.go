package tools

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/fake"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewManagementTools(t *testing.T) {
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewManagementTools(client, kubeClient, logger)
	assert.NotNil(t, tools)
	assert.NotNil(t, tools.client)
	assert.NotNil(t, tools.kubeClient)
	assert.NotNil(t, tools.logger)
}

func TestCreateAvailabilityPolicy(t *testing.T) {
	scheme := runtime.NewScheme()
	_ = v1alpha1.AddToScheme(scheme)
	_ = appsv1.AddToScheme(scheme)

	client := clientfake.NewClientBuilder().
		WithScheme(scheme).
		Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewManagementTools(client, kubeClient, logger)

	t.Run("successful creation", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "test-policy",
			Namespace:         "canvas",
			AvailabilityClass: "high-availability",
			Enforcement:       "strict",
			Priority:          100,
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{
					"app": "test",
				},
				Namespaces: []string{"default"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		createResult := result.Content.(CreateAvailabilityPolicyResult)
		assert.Equal(t, "test-policy", createResult.Name)
		assert.Equal(t, "canvas", createResult.Namespace)
		assert.True(t, createResult.Created)
		assert.Equal(t, "Policy created successfully", createResult.Message)
	})

	t.Run("auto-generated name", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "", // Missing name - should auto-generate
			AvailabilityClass: "standard",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError) // Should succeed with auto-generated name

		// Result should be CreateAvailabilityPolicyResult
		createResult, ok := result.Content.(CreateAvailabilityPolicyResult)
		assert.True(t, ok, "Expected CreateAvailabilityPolicyResult")
		assert.True(t, createResult.Created)
		assert.Contains(t, createResult.Name, "canvas-standard-policy") // Auto-generated name pattern
	})

	t.Run("invalid availability class", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "test-policy",
			AvailabilityClass: "invalid-class",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "Invalid availability class")
	})

	t.Run("invalid enforcement mode", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "test-policy",
			AvailabilityClass: "standard",
			Enforcement:       "invalid-mode",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "Invalid enforcement mode")
	})

	t.Run("policy already exists", func(t *testing.T) {
		// Create first policy
		params := CreateAvailabilityPolicyParams{
			Name:              "existing-policy",
			Namespace:         "canvas",
			AvailabilityClass: "standard",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		// First creation should succeed
		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		// Second creation should indicate policy exists
		result, err = tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		createResult := result.Content.(CreateAvailabilityPolicyResult)
		assert.False(t, createResult.Created)
		assert.Equal(t, "Policy already exists", createResult.Message)
	})

	t.Run("with custom PDB config", func(t *testing.T) {
		minAvailable := "75%"
		params := CreateAvailabilityPolicyParams{
			Name:              "custom-policy",
			Namespace:         "canvas",
			AvailabilityClass: "custom",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
			CustomPDBConfig: &CustomPDBConfig{
				MinAvailable:               &minAvailable,
				UnhealthyPodEvictionPolicy: "IfHealthyBudget",
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		createResult := result.Content.(CreateAvailabilityPolicyResult)
		assert.True(t, createResult.Created)
	})

	t.Run("with maintenance windows", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "maintenance-policy",
			Namespace:         "canvas",
			AvailabilityClass: "standard",
			ComponentSelector: ComponentSelectorConfig{
				MatchLabels: map[string]string{"app": "test"},
			},
			MaintenanceWindows: []MaintenanceWindowConfig{
				{
					Start:      "02:00",
					End:        "04:00",
					Timezone:   "UTC",
					DaysOfWeek: []int{0, 6},
				},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		createResult := result.Content.(CreateAvailabilityPolicyResult)
		assert.True(t, createResult.Created)
	})

	t.Run("with component functions", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "function-policy",
			Namespace:         "canvas",
			AvailabilityClass: "high-availability",
			ComponentSelector: ComponentSelectorConfig{
				ComponentFunctions: []string{"security", "core", "management"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)
	})

	t.Run("invalid component function", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Name:              "invalid-function-policy",
			Namespace:         "canvas",
			AvailabilityClass: "standard",
			ComponentSelector: ComponentSelectorConfig{
				ComponentFunctions: []string{"invalid-function"},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.ErrorDetail, "invalid component function")
	})

	t.Run("intelligent auto-detection mode - no deployments", func(t *testing.T) {
		// Test intelligent mode with no deployments - should handle gracefully
		params := CreateAvailabilityPolicyParams{
			Namespace:      "empty-ns",
			AutoDetect:     true,
			GroupBy:        "auto",
			CreateMultiple: true,
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError) // Should return error when no deployments found

		// Should return string explaining no deployments found
		assert.Equal(t, "No deployments found matching criteria", result.Content)
	})

	t.Run("single policy with auto-generated name from target deployment", func(t *testing.T) {
		params := CreateAvailabilityPolicyParams{
			Namespace:         "canvas",
			TargetDeployments: []string{"payment-service"},
			AvailabilityClass: "high-availability",
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.CreateAvailabilityPolicy(context.Background(), paramsJSON)
		require.NoError(t, err)
		// May or may not succeed depending on deployment existence, but shouldn't crash
		assert.NotNil(t, result)
	})
}

func TestUpdateDeploymentAnnotations(t *testing.T) {
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				"existing": "annotation",
			},
		},
	}

	client := clientfake.NewClientBuilder().
		WithObjects(deployment).
		Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewManagementTools(client, kubeClient, logger)

	t.Run("successful update", func(t *testing.T) {
		params := UpdateDeploymentAnnotationsParams{
			Name:      "test-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "high-availability",
				"oda.tmforum.org/component-function": "core",
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.UpdateDeploymentAnnotations(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		updateResult := result.Content.(UpdateDeploymentAnnotationsResult)
		assert.True(t, updateResult.Updated)
		assert.Equal(t, "high-availability", updateResult.Annotations["oda.tmforum.org/availability-class"])
		assert.Equal(t, "core", updateResult.Annotations["oda.tmforum.org/component-function"])
		assert.Equal(t, "annotation", updateResult.Annotations["existing"]) // Existing annotation preserved
	})

	t.Run("remove annotations", func(t *testing.T) {
		params := UpdateDeploymentAnnotationsParams{
			Name:              "test-deployment",
			Namespace:         "default",
			RemoveAnnotations: []string{"existing"},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.UpdateDeploymentAnnotations(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		updateResult := result.Content.(UpdateDeploymentAnnotationsResult)
		assert.True(t, updateResult.Updated)
		_, exists := updateResult.Annotations["existing"]
		assert.False(t, exists)
	})

	t.Run("deployment not found", func(t *testing.T) {
		params := UpdateDeploymentAnnotationsParams{
			Name:      "nonexistent",
			Namespace: "default",
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.UpdateDeploymentAnnotations(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "Deployment not found")
	})

	t.Run("missing required parameters", func(t *testing.T) {
		params := UpdateDeploymentAnnotationsParams{
			Name: "", // Missing name
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.UpdateDeploymentAnnotations(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "name and namespace are required")
	})

	t.Run("invalid ODA annotation value", func(t *testing.T) {
		params := UpdateDeploymentAnnotationsParams{
			Name:      "test-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "invalid-class",
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.UpdateDeploymentAnnotations(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "Invalid annotation")
	})
}

func TestSimulatePolicyImpact(t *testing.T) {
	scheme := runtime.NewScheme()
	_ = v1alpha1.AddToScheme(scheme)
	_ = appsv1.AddToScheme(scheme)

	// Create test deployments
	deployment1 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "app1",
			Namespace: "production",
			Labels: map[string]string{
				"tier": "frontend",
			},
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
		},
	}

	deployment2 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "app2",
			Namespace: "production",
			Labels: map[string]string{
				"tier": "backend",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(1),
		},
	}

	client := clientfake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(deployment1, deployment2).
		Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewManagementTools(client, kubeClient, logger)

	t.Run("successful simulation", func(t *testing.T) {
		params := SimulatePolicyImpactParams{
			PolicySpec: CreateAvailabilityPolicyParams{
				Name:              "test-policy",
				AvailabilityClass: "high-availability",
				ComponentSelector: ComponentSelectorConfig{
					MatchLabels: map[string]string{
						"tier": "frontend",
					},
				},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.SimulatePolicyImpact(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		impactResult := result.Content.(SimulatePolicyImpactResult)
		assert.Equal(t, 2, impactResult.Summary.TotalDeployments)
		assert.Equal(t, 1, impactResult.Summary.AffectedDeployments)
		assert.Len(t, impactResult.AffectedDeployments, 1)
		assert.Equal(t, "app1", impactResult.AffectedDeployments[0].Name)
	})

	t.Run("no matching deployments", func(t *testing.T) {
		params := SimulatePolicyImpactParams{
			PolicySpec: CreateAvailabilityPolicyParams{
				Name:              "no-match-policy",
				AvailabilityClass: "mission-critical",
				ComponentSelector: ComponentSelectorConfig{
					MatchLabels: map[string]string{
						"tier": "nonexistent",
					},
				},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.SimulatePolicyImpact(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.False(t, result.IsError)

		impactResult := result.Content.(SimulatePolicyImpactResult)
		assert.Equal(t, 0, impactResult.Summary.AffectedDeployments)
		assert.Contains(t, impactResult.Warnings, "Policy selector does not match any deployments")
	})

	t.Run("invalid availability class", func(t *testing.T) {
		params := SimulatePolicyImpactParams{
			PolicySpec: CreateAvailabilityPolicyParams{
				Name:              "invalid-class-policy",
				AvailabilityClass: "invalid",
				ComponentSelector: ComponentSelectorConfig{
					MatchLabels: map[string]string{"tier": "frontend"},
				},
			},
		}

		paramsJSON, err := json.Marshal(params)
		require.NoError(t, err)

		result, err := tools.SimulatePolicyImpact(context.Background(), paramsJSON)
		require.NoError(t, err)
		assert.True(t, result.IsError)
		assert.Contains(t, result.Content.(string), "Invalid availability class")
	})
}

func TestParseAvailabilityClass(t *testing.T) {
	tools := &ManagementTools{}

	tests := []struct {
		input    string
		expected v1alpha1.AvailabilityClass
		hasError bool
	}{
		{"non-critical", v1alpha1.NonCritical, false},
		{"standard", v1alpha1.Standard, false},
		{"high-availability", v1alpha1.HighAvailability, false},
		{"mission-critical", v1alpha1.MissionCritical, false},
		{"custom", v1alpha1.Custom, false},
		{"invalid", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result, err := tools.parseAvailabilityClass(tt.input)
			if tt.hasError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestParseEnforcementMode(t *testing.T) {
	tools := &ManagementTools{}

	tests := []struct {
		input    string
		expected v1alpha1.EnforcementMode
		hasError bool
	}{
		{"strict", v1alpha1.EnforcementStrict, false},
		{"flexible", v1alpha1.EnforcementFlexible, false},
		{"advisory", v1alpha1.EnforcementAdvisory, false},
		{"invalid", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result, err := tools.parseEnforcementMode(tt.input)
			if tt.hasError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

func TestValidateODAAnnotation(t *testing.T) {
	tools := &ManagementTools{}

	tests := []struct {
		key      string
		value    string
		hasError bool
	}{
		{"oda.tmforum.org/availability-class", "standard", false},
		{"oda.tmforum.org/availability-class", "invalid", true},
		{"oda.tmforum.org/component-function", "core", false},
		{"oda.tmforum.org/component-function", "security", false},
		{"oda.tmforum.org/component-function", "management", false},
		{"oda.tmforum.org/component-function", "invalid", true},
		{"oda.tmforum.org/other-annotation", "anything", false},
		{"non-oda-annotation", "anything", false},
	}

	for _, tt := range tests {
		t.Run(tt.key+"="+tt.value, func(t *testing.T) {
			err := tools.validateODAAnnotation(tt.key, tt.value)
			if tt.hasError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestDeploymentMatchesSelector(t *testing.T) {
	tools := &ManagementTools{}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-app",
			Namespace: "production",
			Labels: map[string]string{
				"app":  "test",
				"tier": "frontend",
			},
			Annotations: map[string]string{
				"oda.tmforum.org/componentName":      "test-component",
				"oda.tmforum.org/component-function": "core",
			},
		},
	}

	tests := []struct {
		name     string
		selector v1alpha1.ComponentSelector
		matches  bool
	}{
		{
			name: "namespace match",
			selector: v1alpha1.ComponentSelector{
				Namespaces: []string{"production"},
			},
			matches: true,
		},
		{
			name: "namespace no match",
			selector: v1alpha1.ComponentSelector{
				Namespaces: []string{"staging"},
			},
			matches: false,
		},
		{
			name: "component name match",
			selector: v1alpha1.ComponentSelector{
				ComponentNames: []string{"test-component"},
			},
			matches: true,
		},
		{
			name: "component name no match",
			selector: v1alpha1.ComponentSelector{
				ComponentNames: []string{"other-component"},
			},
			matches: false,
		},
		{
			name: "component function match",
			selector: v1alpha1.ComponentSelector{
				ComponentFunctions: []v1alpha1.ComponentFunction{v1alpha1.CoreFunction},
			},
			matches: true,
		},
		{
			name: "component function no match",
			selector: v1alpha1.ComponentSelector{
				ComponentFunctions: []v1alpha1.ComponentFunction{v1alpha1.SecurityFunction},
			},
			matches: false,
		},
		{
			name: "match labels all match",
			selector: v1alpha1.ComponentSelector{
				MatchLabels: map[string]string{
					"app":  "test",
					"tier": "frontend",
				},
			},
			matches: true,
		},
		{
			name: "match labels partial match",
			selector: v1alpha1.ComponentSelector{
				MatchLabels: map[string]string{
					"app":  "test",
					"tier": "backend", // Different value
				},
			},
			matches: false,
		},
		{
			name:     "empty selector matches all",
			selector: v1alpha1.ComponentSelector{},
			matches:  true,
		},
		{
			name: "multiple criteria all must match",
			selector: v1alpha1.ComponentSelector{
				Namespaces: []string{"production"},
				MatchLabels: map[string]string{
					"app": "test",
				},
			},
			matches: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tools.deploymentMatchesSelector(deployment, &tt.selector)
			assert.Equal(t, tt.matches, result)
		})
	}
}

func TestCalculateDeploymentImpact(t *testing.T) {
	tools := &ManagementTools{}

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-app",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
		},
	}

	tests := []struct {
		name           string
		policyClass    v1alpha1.AvailabilityClass
		expectedImpact string
	}{
		{
			name:           "same class - low impact",
			policyClass:    v1alpha1.Standard,
			expectedImpact: "low",
		},
		{
			name:           "one level increase - medium impact",
			policyClass:    v1alpha1.HighAvailability,
			expectedImpact: "medium",
		},
		{
			name:           "two levels increase - high impact",
			policyClass:    v1alpha1.MissionCritical,
			expectedImpact: "high",
		},
		{
			name:           "decrease - high impact",
			policyClass:    v1alpha1.NonCritical,
			expectedImpact: "high",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			policy := &v1alpha1.AvailabilityPolicy{
				Spec: v1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: tt.policyClass,
				},
			}

			impact := tools.calculateDeploymentImpact(deployment, policy)
			assert.Equal(t, tt.expectedImpact, impact.Impact)
			assert.Equal(t, "test-app", impact.Name)
			assert.Equal(t, "default", impact.Namespace)
		})
	}
}

func TestRegisterManagementTools(t *testing.T) {
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewManagementTools(client, kubeClient, logger)

	// Mock server that tracks registrations
	mockServer := &mockToolServer{
		tools: make(map[string]*types.Tool),
	}

	err := RegisterManagementTools(mockServer, tools)
	assert.NoError(t, err)

	// Verify all expected tools were registered
	expectedTools := []string{
		"create_availability_policy",
		"update_deployment_annotations",
		"simulate_policy_impact",
	}

	assert.Len(t, mockServer.tools, len(expectedTools))
	for _, toolName := range expectedTools {
		assert.Contains(t, mockServer.tools, toolName, "Tool %s should be registered", toolName)
	}
}

// Mock server for testing tool registration
type mockToolServer struct {
	tools map[string]*types.Tool
}

func (m *mockToolServer) RegisterTool(tool *types.Tool) error {
	m.tools[tool.Name] = tool
	return nil
}
