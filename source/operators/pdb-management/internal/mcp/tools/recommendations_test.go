package tools

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewRecommendationTools(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)
	assert.NotNil(t, tools)
	assert.Equal(t, client, tools.client)
	assert.Equal(t, kubeClient, tools.kubeClient)
	assert.Equal(t, logger, tools.logger)
}

func TestRecommendationTools_RecommendAvailabilityClasses(t *testing.T) {
	// Create test deployments with various characteristics
	deployments := []*appsv1.Deployment{
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "auth-service",
				Namespace: "production",
				Annotations: map[string]string{
					"oda.tmforum.org/component-function": "security",
				},
				Labels: map[string]string{
					"tier": "critical",
				},
			},
			Spec: appsv1.DeploymentSpec{
				Replicas: int32Ptr(5),
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "api-gateway",
				Namespace: "production",
			},
			Spec: appsv1.DeploymentSpec{
				Replicas: int32Ptr(3),
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "postgres-db",
				Namespace: "production",
				Annotations: map[string]string{
					"oda.tmforum.org/component-function": "database",
				},
			},
			Spec: appsv1.DeploymentSpec{
				Replicas: int32Ptr(2),
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-app",
				Namespace: "development",
			},
			Spec: appsv1.DeploymentSpec{
				Replicas: int32Ptr(1),
			},
		},
	}

	clientBuilder := clientfake.NewClientBuilder()
	for _, dep := range deployments {
		clientBuilder = clientBuilder.WithObjects(dep)
	}
	client := clientBuilder.Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test basic recommendation
	params := RecommendAvailabilityClassesParams{}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.RecommendAvailabilityClasses(context.Background(), paramsJSON)
	require.NoError(t, err)
	assert.False(t, result.IsError)

	content, ok := result.Content.(RecommendAvailabilityClassesResult)
	require.True(t, ok)

	// Verify we got recommendations for all deployments
	assert.Equal(t, 4, content.Summary.Total)
	assert.Len(t, content.Recommendations, 4)

	// Verify recommendations are sorted by confidence
	for i := 1; i < len(content.Recommendations); i++ {
		assert.GreaterOrEqual(t, content.Recommendations[i-1].Confidence, content.Recommendations[i].Confidence)
	}

	// Verify specific recommendations
	authRec := findRecommendation(content.Recommendations, "auth-service")
	require.NotNil(t, authRec)
	assert.Equal(t, "mission-critical", authRec.RecommendedClass)
	assert.GreaterOrEqual(t, authRec.Confidence, 0.5)
	assert.Contains(t, authRec.Reasoning[0], "Security component")

	apiRec := findRecommendation(content.Recommendations, "api-gateway")
	require.NotNil(t, apiRec)
	assert.Equal(t, "standard", apiRec.RecommendedClass) // API gateway without production context gets standard

	testRec := findRecommendation(content.Recommendations, "test-app")
	require.NotNil(t, testRec)
	assert.Equal(t, "non-critical", testRec.RecommendedClass)

	// Verify summary counts
	assert.Greater(t, content.Summary.ByClass["mission-critical"], 0)
	assert.Greater(t, content.Summary.ByClass["standard"], 0)
	assert.Greater(t, content.Summary.ByClass["non-critical"], 0)
}

func TestRecommendationTools_RecommendAvailabilityClassesFiltered(t *testing.T) {
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "target-service",
			Namespace: "target-ns",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
		},
	}

	client := clientfake.NewClientBuilder().
		WithObjects(deployment).
		Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test namespace filtering
	params := RecommendAvailabilityClassesParams{
		Namespace: "target-ns",
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.RecommendAvailabilityClasses(context.Background(), paramsJSON)
	require.NoError(t, err)

	content := result.Content.(RecommendAvailabilityClassesResult)
	assert.Equal(t, 1, content.Summary.Total)
	assert.Len(t, content.Recommendations, 1)

	// Test deployment filtering
	params = RecommendAvailabilityClassesParams{
		Deployments: []string{"target-service"},
	}
	paramsJSON, err = json.Marshal(params)
	require.NoError(t, err)

	result, err = tools.RecommendAvailabilityClasses(context.Background(), paramsJSON)
	require.NoError(t, err)

	content = result.Content.(RecommendAvailabilityClassesResult)
	assert.Equal(t, 1, content.Summary.Total)
	assert.Equal(t, "target-service", content.Recommendations[0].Deployment)
}

func TestRecommendationTools_RecommendAvailabilityClassesInvalidParams(t *testing.T) {
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test with invalid JSON
	result, err := tools.RecommendAvailabilityClasses(context.Background(), []byte("invalid json"))
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "invalid parameters")
}

func TestAnalyzeDeploymentAvailability(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)

	tests := []struct {
		name     string
		dep      *appsv1.Deployment
		expected string
		minConf  float64
	}{
		{
			name: "security component with high replicas",
			dep: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "auth-service",
					Namespace: "production",
					Annotations: map[string]string{
						"oda.tmforum.org/component-function": "security",
					},
					Labels: map[string]string{
						"tier": "critical",
					},
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(5),
				},
			},
			expected: "mission-critical",
			minConf:  0.5,
		},
		{
			name: "api gateway in production",
			dep: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "api-gateway-prod",
					Namespace: "production",
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(3),
				},
			},
			expected: "standard",
			minConf:  0.4,
		},
		{
			name: "database with medium replicas",
			dep: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "postgres-primary",
					Namespace: "default",
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(2),
				},
			},
			expected: "high-availability",
			minConf:  0.4,
		},
		{
			name: "development single replica",
			dep: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-service-dev",
					Namespace: "development",
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(1),
				},
			},
			expected: "non-critical",
			minConf:  0.3,
		},
		{
			name: "standard service",
			dep: &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "business-service",
					Namespace: "default",
					Labels: map[string]string{
						"tier": "silver",
					},
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(2),
				},
			},
			expected: "standard",
			minConf:  0.4,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec := tools.analyzeDeploymentAvailability(tt.dep)
			assert.Equal(t, tt.expected, rec.RecommendedClass)
			assert.GreaterOrEqual(t, rec.Confidence, tt.minConf)
			assert.Equal(t, tt.dep.Name, rec.Deployment)
			assert.Equal(t, tt.dep.Namespace, rec.Namespace)
			assert.NotEmpty(t, rec.Reasoning)
			assert.NotEmpty(t, rec.Impact.MinAvailable)
		})
	}
}

func TestRecommendationTools_RecommendPolicies(t *testing.T) {
	// Create test deployments representing different patterns
	deployments := []*appsv1.Deployment{
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "auth-service",
				Namespace: "production",
				Annotations: map[string]string{
					"oda.tmforum.org/component-function": "security",
				},
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(3)},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "prod-api-gateway",
				Namespace: "production",
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(2)},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "postgres-db",
				Namespace: "production",
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(1)},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "api-service",
				Namespace: "staging",
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(2)},
		},
	}

	clientBuilder := clientfake.NewClientBuilder()
	for _, dep := range deployments {
		clientBuilder = clientBuilder.WithObjects(dep)
	}
	client := clientBuilder.Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test cluster-wide policy recommendations
	params := RecommendPoliciesParams{
		Scope: "cluster",
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.RecommendPolicies(context.Background(), paramsJSON)
	require.NoError(t, err)
	assert.False(t, result.IsError)

	content, ok := result.Content.(RecommendPoliciesResult)
	require.True(t, ok)

	// Verify we got policy recommendations
	assert.Greater(t, content.Summary.TotalPolicies, 0)
	assert.NotEmpty(t, content.Policies)

	// Verify specific patterns are detected
	policyNames := make([]string, len(content.Policies))
	for i, policy := range content.Policies {
		policyNames[i] = policy.Name
	}

	assert.Contains(t, policyNames, "security-components-policy")
	assert.Contains(t, policyNames, "production-workloads-policy")
	assert.Contains(t, policyNames, "stateful-database-policy")
	assert.Contains(t, policyNames, "api-gateway-policy")
	assert.Contains(t, policyNames, "default-availability-policy")

	// Verify summary counts
	assert.Greater(t, content.Summary.ByScope["cluster"], 0)
	assert.Greater(t, content.Summary.ByScope["namespace"], 0)
	assert.Greater(t, content.Summary.ByScope["component"], 0)
	assert.Greater(t, content.Summary.DeploymentsCovered, 0)
}

func TestRecommendationTools_RecommendPoliciesNamespaceFilter(t *testing.T) {
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-service",
			Namespace: "test-namespace",
		},
		Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(1)},
	}

	client := clientfake.NewClientBuilder().
		WithObjects(deployment).
		Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test namespace filtering
	params := RecommendPoliciesParams{
		Namespace: "test-namespace",
		Scope:     "namespace",
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.RecommendPolicies(context.Background(), paramsJSON)
	require.NoError(t, err)

	content := result.Content.(RecommendPoliciesResult)
	assert.GreaterOrEqual(t, content.Summary.TotalPolicies, 0)
}

func TestRecommendationTools_RecommendPoliciesInvalidParams(t *testing.T) {
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Test with invalid JSON
	result, err := tools.RecommendPolicies(context.Background(), []byte("invalid json"))
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "invalid parameters")
}

func TestAnalyzeDeploymentPatterns(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)

	deployments := []appsv1.Deployment{
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "auth-service",
				Namespace: "security",
				Annotations: map[string]string{
					"oda.tmforum.org/component-function": "security",
				},
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "security-vault",
				Namespace: "security",
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "prod-api",
				Namespace: "production",
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "postgres-db",
				Namespace: "database",
			},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "api-gateway",
				Namespace: "gateway",
			},
		},
	}

	patterns := tools.analyzeDeploymentPatterns(deployments)

	// Verify security pattern
	securityPattern, exists := patterns["security"]
	require.True(t, exists)
	assert.Equal(t, 2, securityPattern.Count)
	assert.True(t, securityPattern.Namespaces["security"])
	assert.Contains(t, securityPattern.Deployments, "auth-service")
	assert.Contains(t, securityPattern.Deployments, "security-vault")

	// Verify production pattern
	prodPattern, exists := patterns["production"]
	require.True(t, exists)
	assert.Equal(t, 1, prodPattern.Count)
	assert.True(t, prodPattern.Namespaces["production"])
	assert.Contains(t, prodPattern.Deployments, "prod-api")

	// Verify database pattern
	dbPattern, exists := patterns["database"]
	require.True(t, exists)
	assert.Equal(t, 1, dbPattern.Count)
	assert.True(t, dbPattern.Namespaces["database"])
	assert.Contains(t, dbPattern.Deployments, "postgres-db")

	// Verify API pattern
	apiPattern, exists := patterns["api"]
	require.True(t, exists)
	assert.Equal(t, 2, apiPattern.Count) // Both prod-api and api-gateway contain "api"
	assert.True(t, apiPattern.Namespaces["gateway"])
	assert.True(t, apiPattern.Namespaces["production"])
	assert.Contains(t, apiPattern.Deployments, "api-gateway")
	assert.Contains(t, apiPattern.Deployments, "prod-api")
}

func TestGeneratePolicyRecommendations(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)

	patterns := map[string]*DeploymentPattern{
		"security": {
			Type:        "security",
			Count:       2,
			Namespaces:  map[string]bool{"security": true},
			Components:  map[string]bool{"security": true},
			Deployments: []string{"auth-service", "vault"},
		},
		"production": {
			Type:        "production",
			Count:       3,
			Namespaces:  map[string]bool{"production": true},
			Components:  map[string]bool{"core": true},
			Deployments: []string{"prod-api", "prod-web", "prod-worker"},
		},
		"database": {
			Type:        "database",
			Count:       1,
			Namespaces:  map[string]bool{"data": true},
			Components:  map[string]bool{"database": true},
			Deployments: []string{"postgres"},
		},
		"api": {
			Type:        "api",
			Count:       2,
			Namespaces:  map[string]bool{"gateway": true},
			Components:  map[string]bool{"core": true},
			Deployments: []string{"api-gateway", "edge-proxy"},
		},
	}

	policies := tools.generatePolicyRecommendations(patterns, "cluster")

	// Should generate policies for all patterns plus default
	assert.Len(t, policies, 5)

	// Verify security policy
	securityPolicy := findPolicy(policies, "security-components-policy")
	require.NotNil(t, securityPolicy)
	assert.Equal(t, "mission-critical", securityPolicy.AvailabilityClass)
	assert.Equal(t, "strict", securityPolicy.Enforcement)
	assert.Equal(t, 1000, securityPolicy.Priority)

	// Verify production policy
	prodPolicy := findPolicy(policies, "production-workloads-policy")
	require.NotNil(t, prodPolicy)
	assert.Equal(t, "high-availability", prodPolicy.AvailabilityClass)
	assert.Equal(t, "flexible", prodPolicy.Enforcement)
	assert.Equal(t, 500, prodPolicy.Priority)

	// Verify database policy
	dbPolicy := findPolicy(policies, "stateful-database-policy")
	require.NotNil(t, dbPolicy)
	assert.Equal(t, "custom", dbPolicy.AvailabilityClass)
	assert.Equal(t, "strict", dbPolicy.Enforcement)
	assert.Equal(t, 750, dbPolicy.Priority)

	// Verify API policy
	apiPolicy := findPolicy(policies, "api-gateway-policy")
	require.NotNil(t, apiPolicy)
	assert.Equal(t, "high-availability", apiPolicy.AvailabilityClass)
	assert.Equal(t, "advisory", apiPolicy.Enforcement)
	assert.Equal(t, 400, apiPolicy.Priority)

	// Verify default policy
	defaultPolicy := findPolicy(policies, "default-availability-policy")
	require.NotNil(t, defaultPolicy)
	assert.Equal(t, "standard", defaultPolicy.AvailabilityClass)
	assert.Equal(t, "advisory", defaultPolicy.Enforcement)
	assert.Equal(t, 1, defaultPolicy.Priority)
}

func TestRecommendationInferComponentFunction(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)

	tests := []struct {
		name     string
		expected string
	}{
		{"auth-service", "security"},
		{"oauth-server", "security"},
		{"security-vault", "security"},
		{"keycloak-auth", "security"},
		{"vault-secrets", "security"},
		{"controller-manager", "management"},
		{"operator-webhook", "management"},
		{"admin-dashboard", "management"},
		{"postgres-primary", "database"},
		{"mysql-server", "database"},
		{"mongodb-replica", "database"},
		{"redis-cache", "database"},
		{"web-service", "core"},
		{"api-gateway", "core"},
		{"unknown-app", "core"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tools.inferComponentFunction(tt.name)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestRegisterRecommendationTools(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	tools := NewRecommendationTools(client, kubeClient, logger)

	// Mock server that tracks registered tools
	mockServer := &mockToolServer{
		tools: make(map[string]*types.Tool),
	}

	err := RegisterRecommendationTools(mockServer, tools)
	require.NoError(t, err)

	// Verify both tools were registered
	assert.Len(t, mockServer.tools, 2)
	assert.Contains(t, mockServer.tools, "recommend_availability_classes")
	assert.Contains(t, mockServer.tools, "recommend_policies")

	// Verify tool details
	availTool := mockServer.tools["recommend_availability_classes"]
	assert.Equal(t, "recommend_availability_classes", availTool.Name)
	assert.Contains(t, availTool.Description, "availability classes")
	assert.NotEmpty(t, availTool.InputSchema)

	policyTool := mockServer.tools["recommend_policies"]
	assert.Equal(t, "recommend_policies", policyTool.Name)
	assert.Contains(t, policyTool.Description, "policies")
	assert.NotEmpty(t, policyTool.InputSchema)
}

// Helper functions

func findRecommendation(recommendations []AvailabilityRecommendation, name string) *AvailabilityRecommendation {
	for _, rec := range recommendations {
		if rec.Deployment == name {
			return &rec
		}
	}
	return nil
}

func findPolicy(policies []PolicyRecommendation, name string) *PolicyRecommendation {
	for _, policy := range policies {
		if policy.Name == name {
			return &policy
		}
	}
	return nil
}
