package tools

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes/fake"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestAnalysisTools_AnalyzeClusterAvailability(t *testing.T) {
	// Create test deployments
	deployment1 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "app1",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "high-availability",
				"oda.tmforum.org/component-function": "core",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
		},
	}

	deployment2 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "app2",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(1),
		},
	}

	deployment3 := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "security-service",
			Namespace: "production",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "mission-critical",
				"oda.tmforum.org/component-function": "security",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(5),
		},
	}

	// Create corresponding PDB
	pdb1 := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "app1-pdb",
			Namespace: "default",
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{
				Type:   intstr.String,
				StrVal: "75%",
			},
		},
	}

	client := clientfake.NewClientBuilder().
		WithObjects(deployment1, deployment2, deployment3, pdb1).
		Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewAnalysisTools(client, kubeClient, logger)

	// Test basic analysis
	params := AnalyzeClusterAvailabilityParams{}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.AnalyzeClusterAvailability(context.Background(), paramsJSON)
	require.NoError(t, err)
	assert.False(t, result.IsError)

	content, ok := result.Content.(AnalyzeClusterAvailabilityResult)
	require.True(t, ok)

	// Verify summary
	assert.Equal(t, 3, content.Summary.TotalDeployments)
	assert.Equal(t, 1, content.Summary.DeploymentsWithPDB)
	assert.Equal(t, 2, content.Summary.DeploymentsWithoutPDB)
	assert.InDelta(t, 33.33, content.Summary.CoveragePercentage, 0.1)

	// Verify availability classes
	assert.Equal(t, 1, content.Summary.AvailabilityClasses["high-availability"])
	assert.Equal(t, 1, content.Summary.AvailabilityClasses["mission-critical"])

	// Verify coverage by namespace
	assert.Contains(t, content.Coverage.ByNamespace, "default")
	assert.Contains(t, content.Coverage.ByNamespace, "production")
	assert.Equal(t, 1, content.Coverage.ByNamespace["default"].Covered)
	assert.Equal(t, 1, content.Coverage.ByNamespace["default"].Uncovered)
	assert.Equal(t, 0, content.Coverage.ByNamespace["production"].Covered)
	assert.Equal(t, 1, content.Coverage.ByNamespace["production"].Uncovered)

	// Verify issues are detected
	assert.NotEmpty(t, content.Issues)
}

func TestAnalysisTools_AnalyzeClusterAvailabilityDetailed(t *testing.T) {
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-app",
			Namespace: "default",
			Annotations: map[string]string{
				"oda.tmforum.org/availability-class": "standard",
			},
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

	tools := NewAnalysisTools(client, kubeClient, logger)

	// Test detailed analysis
	params := AnalyzeClusterAvailabilityParams{
		Detailed: true,
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.AnalyzeClusterAvailability(context.Background(), paramsJSON)
	require.NoError(t, err)

	content := result.Content.(AnalyzeClusterAvailabilityResult)

	// Verify detailed namespace analysis is included
	assert.NotEmpty(t, content.Namespaces)
	assert.Len(t, content.Namespaces, 1)

	nsAnalysis := content.Namespaces[0]
	assert.Equal(t, "default", nsAnalysis.Name)
	assert.Len(t, nsAnalysis.Deployments, 1)

	depAnalysis := nsAnalysis.Deployments[0]
	assert.Equal(t, "test-app", depAnalysis.Name)
	assert.Equal(t, "standard", depAnalysis.AvailabilityClass)
	assert.False(t, depAnalysis.HasPDB)
	assert.Equal(t, int32(2), depAnalysis.Replicas)
}

func TestAnalysisTools_AnalyzeWorkloadPatterns(t *testing.T) {
	// Create deployments with different patterns
	deployments := []*appsv1.Deployment{
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "api-gateway",
				Namespace: "production",
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(3)},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "frontend-ui",
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
				Name:      "auth-service",
				Namespace: "production",
				Annotations: map[string]string{
					"oda.tmforum.org/component-function": "security",
				},
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(4)},
		},
		{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "batch-processor",
				Namespace: "production",
			},
			Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(1)},
		},
	}

	clientBuilder := clientfake.NewClientBuilder()
	for _, dep := range deployments {
		clientBuilder = clientBuilder.WithObjects(dep)
	}
	client := clientBuilder.Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewAnalysisTools(client, kubeClient, logger)

	params := AnalyzeWorkloadPatternsParams{}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.AnalyzeWorkloadPatterns(context.Background(), paramsJSON)
	require.NoError(t, err)

	content := result.Content.(AnalyzeWorkloadPatternsResult)

	// Verify component functions are detected
	assert.Equal(t, 1, content.ComponentFunctions["security"]) // auth-service
	assert.Equal(t, 1, content.ComponentFunctions["database"]) // postgres-db
	assert.Equal(t, 3, content.ComponentFunctions["core"])     // api-gateway, frontend-ui, batch-processor

	// Verify replica distribution
	assert.Equal(t, 2, content.ReplicaDistribution["single"])       // postgres, batch (both have 1 replica)
	assert.Equal(t, 2, content.ReplicaDistribution["low (2-3)"])    // api (3), frontend (2)
	assert.Equal(t, 1, content.ReplicaDistribution["medium (4-6)"]) // auth (4)

	// Verify patterns are detected
	patternNames := make([]string, len(content.Patterns))
	for i, pattern := range content.Patterns {
		patternNames[i] = pattern.Name
	}

	assert.Contains(t, patternNames, "api-gateway")
	assert.Contains(t, patternNames, "frontend")
	assert.Contains(t, patternNames, "stateful-database")
	assert.Contains(t, patternNames, "batch-processor")

	// Verify recommendations are generated
	assert.NotEmpty(t, content.Recommendations)
}

func TestAnalysisTools_AnalyzeWorkloadPatternsFiltered(t *testing.T) {
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-service",
			Namespace: "test-ns",
		},
		Spec: appsv1.DeploymentSpec{Replicas: int32Ptr(1)},
	}

	client := clientfake.NewClientBuilder().
		WithObjects(deployment).
		Build()

	kubeClient := fake.NewSimpleClientset()
	logger := zap.New(zap.UseDevMode(true))

	tools := NewAnalysisTools(client, kubeClient, logger)

	// Test namespace filtering
	params := AnalyzeWorkloadPatternsParams{
		Namespace: "test-ns",
	}
	paramsJSON, err := json.Marshal(params)
	require.NoError(t, err)

	result, err := tools.AnalyzeWorkloadPatterns(context.Background(), paramsJSON)
	require.NoError(t, err)

	content := result.Content.(AnalyzeWorkloadPatternsResult)
	assert.Equal(t, 1, content.ComponentFunctions["core"])
	assert.Equal(t, 1, content.ReplicaDistribution["single"])
}

func TestInferComponentFunction(t *testing.T) {
	tools := &AnalysisTools{}

	tests := []struct {
		name     string
		expected string
	}{
		{"auth-service", "security"},
		{"oauth-server", "security"},
		{"security-gateway", "security"},
		{"keycloak-service", "security"},
		{"vault-secrets", "security"},
		{"controller-manager", "management"},
		{"operator-webhook", "management"},
		{"admin-dashboard", "management"},
		{"postgres-primary", "database"},
		{"mysql-server", "database"},
		{"redis-cache", "database"},
		{"mongodb-replica", "database"},
		{"api-service", "core"},
		{"web-frontend", "core"},
		{"unknown-service", "core"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tools.inferComponentFunction(tt.name)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestContainsPattern(t *testing.T) {
	tests := []struct {
		text    string
		pattern string
		want    bool
	}{
		{"api-service", "api", true},
		{"API-SERVICE", "api", true},
		{"service-api", "api", true},
		{"web-service", "api", false},
		{"postgres", "postgres", true},
		{"POSTGRES", "postgres", true},
		{"mysql", "postgres", false},
	}

	for _, tt := range tests {
		t.Run(tt.text+"_"+tt.pattern, func(t *testing.T) {
			result := containsPattern(tt.text, tt.pattern)
			assert.Equal(t, tt.want, result)
		})
	}
}

func TestGetReplicaRange(t *testing.T) {
	tools := &AnalysisTools{}

	tests := []struct {
		replicas int32
		expected string
	}{
		{1, "single"},
		{2, "low (2-3)"},
		{3, "low (2-3)"},
		{4, "medium (4-6)"},
		{6, "medium (4-6)"},
		{7, "high (7-10)"},
		{10, "high (7-10)"},
		{15, "very high (>10)"},
	}

	for _, tt := range tests {
		t.Run(string(rune(tt.replicas)), func(t *testing.T) {
			result := tools.getReplicaRange(tt.replicas)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDetectPattern(t *testing.T) {
	tools := &AnalysisTools{}

	tests := []struct {
		name     string
		expected string
	}{
		{"api-gateway", "api-gateway"},
		{"gateway-service", "api-gateway"},
		{"frontend-ui", "frontend"},
		{"web-interface", "frontend"},
		{"backend-service", "backend-service"},
		{"business-service", "backend-service"},
		{"postgres-db", "stateful-database"},
		{"database-server", "stateful-database"},
		{"kafka-queue", "message-queue"},
		{"rabbitmq-server", "message-queue"},
		{"redis-cache", "cache"},
		{"memcached-server", "cache"},
		{"batch-job", "batch-processor"},
		{"cron-worker", "batch-processor"},
		{"unknown-app", "general-workload"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name: tt.name,
				},
			}
			result := tools.detectPattern(deployment)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// Helper function
func int32Ptr(i int32) *int32 {
	return &i
}
