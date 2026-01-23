package tools

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/go-logr/logr"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	k8stypes "k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes/fake"
	"sigs.k8s.io/controller-runtime/pkg/client"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestBackupTools_BackupPolicies(t *testing.T) {
	tests := []struct {
		name         string
		params       BackupPoliciesParams
		setupObjects func() []client.Object
		setupK8sObjs func() []runtime.Object
		wantSuccess  bool
		wantError    string
		checkResult  func(t *testing.T, result *types.ToolResult)
	}{
		{
			name: "successful backup with all namespaces",
			params: BackupPoliciesParams{
				Format:             "json",
				IncludeDeployments: true,
				IncludePDBs:        true,
				CompressionEnabled: false,
			},
			setupObjects: func() []client.Object {
				return []client.Object{
					&v1alpha1.AvailabilityPolicy{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "test-policy",
							Namespace: "default",
						},
						Spec: v1alpha1.AvailabilityPolicySpec{
							AvailabilityClass: v1alpha1.HighAvailability,
							ComponentSelector: v1alpha1.ComponentSelector{
								Namespaces: []string{"default"},
							},
						},
					},
					&v1alpha1.AvailabilityPolicy{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "prod-policy",
							Namespace: "production",
						},
						Spec: v1alpha1.AvailabilityPolicySpec{
							AvailabilityClass: v1alpha1.HighAvailability,
							ComponentSelector: v1alpha1.ComponentSelector{
								Namespaces: []string{"production"},
							},
						},
					},
				}
			},
			setupK8sObjs: func() []runtime.Object {
				return []runtime.Object{
					&appsv1.Deployment{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "test-app",
							Namespace: "default",
						},
						Spec: appsv1.DeploymentSpec{
							Replicas: int32Ptr(3),
						},
					},
					&policyv1.PodDisruptionBudget{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "test-pdb",
							Namespace: "default",
						},
						Spec: policyv1.PodDisruptionBudgetSpec{
							MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "50%"},
						},
					},
				}
			},
			wantSuccess: true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				assert.False(t, result.IsError)
				assert.NotEmpty(t, result.Content)

				backup, ok := result.Content.(PolicyBackup)
				require.True(t, ok)

				assert.Equal(t, 2, len(backup.AvailabilityPolicies))
				assert.Equal(t, 1, len(backup.Deployments))
				assert.Equal(t, 1, len(backup.PodDisruptionBudgets))
				assert.Equal(t, "v1alpha1", backup.Metadata.Version)
				assert.Equal(t, 2, backup.Metadata.BackupStats.PoliciesCount)
				assert.Equal(t, 1, backup.Metadata.BackupStats.DeploymentsCount)
				assert.Equal(t, 1, backup.Metadata.BackupStats.PDBsCount)
			},
		},
		{
			name: "backup with specific namespaces only",
			params: BackupPoliciesParams{
				Namespaces:         []string{"default"},
				Format:             "json",
				IncludeDeployments: false,
				IncludePDBs:        false,
			},
			setupObjects: func() []client.Object {
				return []client.Object{
					&v1alpha1.AvailabilityPolicy{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "test-policy",
							Namespace: "default",
						},
						Spec: v1alpha1.AvailabilityPolicySpec{
							AvailabilityClass: v1alpha1.Standard,
						},
					},
					&v1alpha1.AvailabilityPolicy{
						ObjectMeta: metav1.ObjectMeta{
							Name:      "prod-policy",
							Namespace: "production",
						},
						Spec: v1alpha1.AvailabilityPolicySpec{
							AvailabilityClass: v1alpha1.HighAvailability,
						},
					},
				}
			},
			setupK8sObjs: func() []runtime.Object {
				return []runtime.Object{}
			},
			wantSuccess: true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				backup, ok := result.Content.(PolicyBackup)
				require.True(t, ok)

				assert.Equal(t, 1, len(backup.AvailabilityPolicies))
				assert.Equal(t, "test-policy", backup.AvailabilityPolicies[0].Name)
				assert.Equal(t, 0, len(backup.Deployments))
				assert.Equal(t, 0, len(backup.PodDisruptionBudgets))
			},
		},
		{
			name: "backup with no policies found",
			params: BackupPoliciesParams{
				Namespaces: []string{"nonexistent"},
				Format:     "json",
			},
			setupObjects: func() []client.Object {
				return []client.Object{}
			},
			setupK8sObjs: func() []runtime.Object {
				return []runtime.Object{}
			},
			wantSuccess: true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				backup, ok := result.Content.(PolicyBackup)
				require.True(t, ok)

				assert.Equal(t, 0, len(backup.AvailabilityPolicies))
				assert.Equal(t, 0, backup.Metadata.BackupStats.PoliciesCount)
			},
		},
		{
			name: "invalid parameters",
			params: BackupPoliciesParams{
				Format: "invalid",
			},
			setupObjects: func() []client.Object {
				return []client.Object{}
			},
			setupK8sObjs: func() []runtime.Object {
				return []runtime.Object{}
			},
			wantSuccess: false,
			wantError:   "unsupported format",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			scheme := runtime.NewScheme()
			_ = v1alpha1.AddToScheme(scheme)
			_ = appsv1.AddToScheme(scheme)
			_ = corev1.AddToScheme(scheme)

			fakeClient := clientfake.NewClientBuilder().
				WithScheme(scheme).
				WithObjects(tt.setupObjects()...).
				Build()

			fakeKubeClient := fake.NewSimpleClientset(tt.setupK8sObjs()...)

			backupTools := NewBackupTools(fakeClient, fakeKubeClient, logr.Discard())

			paramsData, err := json.Marshal(tt.params)
			require.NoError(t, err)

			result, err := backupTools.BackupPolicies(context.TODO(), paramsData)

			if tt.wantSuccess {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				if tt.checkResult != nil {
					tt.checkResult(t, result)
				}
			} else {
				if tt.wantError != "" {
					assert.Error(t, err)
					assert.Contains(t, err.Error(), tt.wantError)
				} else {
					assert.NoError(t, err)
					assert.NotNil(t, result)
					assert.True(t, result.IsError)
				}
			}
		})
	}
}

func TestBackupTools_RestorePolicies(t *testing.T) {
	// Create test backup data
	testBackup := PolicyBackup{
		Metadata: BackupMetadata{
			CreatedAt: time.Date(2023, 12, 1, 12, 0, 0, 0, time.UTC),
			Version:   "v1.0.0",
			ClusterInfo: ClusterInfo{
				ServerVersion: "v1.25.0",
				Namespaces:    []string{"default", "production"},
			},
			BackupStats: BackupStats{
				PoliciesCount: 2,
			},
		},
		AvailabilityPolicies: []v1alpha1.AvailabilityPolicy{
			{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-policy",
					Namespace: "default",
				},
				Spec: v1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: v1alpha1.Standard,
				},
			},
			{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "prod-policy",
					Namespace: "production",
				},
				Spec: v1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: v1alpha1.HighAvailability,
				},
			},
		},
	}

	backupData, err := json.Marshal(testBackup)
	require.NoError(t, err)

	tests := []struct {
		name         string
		params       RestorePoliciesParams
		existingObjs []client.Object
		wantSuccess  bool
		wantError    string
		checkResult  func(t *testing.T, result *types.ToolResult)
		checkCreated func(t *testing.T, client client.Client)
	}{
		{
			name: "successful restore with dry run",
			params: RestorePoliciesParams{
				BackupData:    json.RawMessage(backupData),
				DryRun:        true,
				OverwriteMode: "skip",
			},
			existingObjs: []client.Object{},
			wantSuccess:  true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				restoreResult, ok := result.Content.(RestoreResult)
				require.True(t, ok)

				assert.True(t, restoreResult.DryRun)
				assert.Equal(t, 2, restoreResult.Summary.TotalPolicies)
				assert.Equal(t, 2, restoreResult.Summary.CreatedCount)
				assert.Equal(t, 0, restoreResult.Summary.ErrorCount)
			},
		},
		{
			name: "successful restore with actual creation",
			params: RestorePoliciesParams{
				BackupData:    json.RawMessage(backupData),
				DryRun:        false,
				OverwriteMode: "skip",
			},
			existingObjs: []client.Object{},
			wantSuccess:  true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				restoreResult, ok := result.Content.(RestoreResult)
				require.True(t, ok)

				assert.False(t, restoreResult.DryRun)
				assert.Equal(t, 2, restoreResult.Summary.CreatedCount)
				assert.Equal(t, 2, len(restoreResult.CreatedPolicies))
			},
			checkCreated: func(t *testing.T, client client.Client) {
				var policy v1alpha1.AvailabilityPolicy
				err := client.Get(context.TODO(),
					k8stypes.NamespacedName{Name: "test-policy", Namespace: "default"},
					&policy)
				assert.NoError(t, err)
				assert.Equal(t, v1alpha1.Standard, policy.Spec.AvailabilityClass)
			},
		},
		{
			name: "restore with skip existing policies",
			params: RestorePoliciesParams{
				BackupData:    json.RawMessage(backupData),
				DryRun:        false,
				OverwriteMode: "skip",
			},
			existingObjs: []client.Object{
				&v1alpha1.AvailabilityPolicy{
					ObjectMeta: metav1.ObjectMeta{
						Name:      "test-policy",
						Namespace: "default",
					},
					Spec: v1alpha1.AvailabilityPolicySpec{
						AvailabilityClass: v1alpha1.HighAvailability,
					},
				},
			},
			wantSuccess: true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				restoreResult, ok := result.Content.(RestoreResult)
				require.True(t, ok)

				assert.Equal(t, 1, restoreResult.Summary.CreatedCount)
				assert.Equal(t, 1, restoreResult.Summary.SkippedCount)
				assert.Equal(t, 1, len(restoreResult.SkippedPolicies))
			},
		},
		{
			name: "restore with namespace filtering",
			params: RestorePoliciesParams{
				BackupData:    json.RawMessage(backupData),
				DryRun:        false,
				OverwriteMode: "skip",
				Namespaces:    []string{"default"},
			},
			existingObjs: []client.Object{},
			wantSuccess:  true,
			checkResult: func(t *testing.T, result *types.ToolResult) {
				restoreResult, ok := result.Content.(RestoreResult)
				require.True(t, ok)

				assert.Equal(t, 1, restoreResult.Summary.CreatedCount)
				assert.Equal(t, 1, len(restoreResult.CreatedPolicies))
				assert.Equal(t, "test-policy", restoreResult.CreatedPolicies[0].Name)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			scheme := runtime.NewScheme()
			_ = v1alpha1.AddToScheme(scheme)

			fakeClient := clientfake.NewClientBuilder().
				WithScheme(scheme).
				WithObjects(tt.existingObjs...).
				Build()

			fakeKubeClient := fake.NewSimpleClientset()

			backupTools := NewBackupTools(fakeClient, fakeKubeClient, logr.Discard())

			paramsData, err := json.Marshal(tt.params)
			require.NoError(t, err)

			result, err := backupTools.RestorePolicies(context.TODO(), paramsData)

			if tt.wantSuccess {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.False(t, result.IsError)
				if tt.checkResult != nil {
					tt.checkResult(t, result)
				}
				if tt.checkCreated != nil {
					tt.checkCreated(t, fakeClient)
				}
			} else {
				if tt.wantError != "" {
					assert.Error(t, err)
					assert.Contains(t, err.Error(), tt.wantError)
				} else {
					assert.NoError(t, err)
					assert.NotNil(t, result)
					assert.True(t, result.IsError)
				}
			}
		})
	}
}

func TestRegisterBackupTools(t *testing.T) {
	mockServer := &MockToolServer{}
	tools := NewBackupTools(nil, nil, logr.Discard())

	err := RegisterBackupTools(mockServer, tools)
	assert.NoError(t, err)
	assert.Equal(t, 2, len(mockServer.registeredTools))

	toolNames := make(map[string]bool)
	for _, tool := range mockServer.registeredTools {
		toolNames[tool.Name] = true
	}

	assert.True(t, toolNames["backup_policies"])
	assert.True(t, toolNames["restore_policies"])
}

// MockToolServer for testing tool registration
type MockToolServer struct {
	registeredTools []*types.Tool
}

func (m *MockToolServer) RegisterTool(tool *types.Tool) error {
	m.registeredTools = append(m.registeredTools, tool)
	return nil
}
