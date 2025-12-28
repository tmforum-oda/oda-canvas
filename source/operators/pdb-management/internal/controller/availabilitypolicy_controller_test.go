package controller_test

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/controller"
)

const (
	AnnotationComponentName = "oda.tmforum.org/componentName"
)

func TestAvailabilityPolicyReconciler(t *testing.T) {
	ctx := context.Background()

	// Create a deployment
	deploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app": "test",
			},
			Annotations: map[string]string{
				AnnotationComponentName: "test-component",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
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
							Name:  "test-container",
							Image: "nginx",
							Resources: corev1.ResourceRequirements{
								Limits: corev1.ResourceList{
									corev1.ResourceCPU: resource.MustParse("500m"),
								},
							},
						},
					},
				},
			},
		},
	}

	// Create availability policy
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
	}

	// Create test reconcilers
	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	// Test reconciliation
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-policy",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	// Controller returns empty result on success (no explicit requeue needed)
	assert.Equal(t, time.Duration(0), result.RequeueAfter)

	// Verify the policy can be retrieved
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "test-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)
	assert.Equal(t, availabilityv1alpha1.HighAvailability, retrievedPolicy.Spec.AvailabilityClass)

	// Verify that the policy status was updated
	assert.NotEmpty(t, retrievedPolicy.Status.AppliedToComponents, "Policy should have applied components")
	assert.Contains(t, retrievedPolicy.Status.AppliedToComponents[0], "test-component", "Should contain the test component")

	// Verify events were recorded - controller emits PolicyApplied
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PolicyApplied")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PolicyApplied event but none was recorded")
	}
}

func TestAvailabilityPolicyReconciler_MultipleComponents(t *testing.T) {
	ctx := context.Background()

	// Create multiple deployments
	deployments := []*appsv1.Deployment{
		createTestDeployment("test-deploy-1", "default", map[string]string{"tier": "frontend"}, "frontend-component"),
		createTestDeployment("test-deploy-2", "default", map[string]string{"tier": "frontend"}, "api-component"),
		createTestDeployment("test-deploy-3", "default", map[string]string{"tier": "backend"}, "database-component"),
	}

	// Create policy that matches frontend tier
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

	objects := []client.Object{policy}
	for _, deploy := range deployments {
		objects = append(objects, deploy)
	}

	tr := controller.CreateTestReconcilers(objects...)
	reconciler := tr.AvailabilityPolicyReconciler

	// Reconcile the policy
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "frontend-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify policy status
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "frontend-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	// Should match 2 components (frontend tier)
	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 2, "Should match 2 frontend components")

	// Check conditions
	assert.NotEmpty(t, retrievedPolicy.Status.Conditions, "Should have conditions")

	var readyCondition *metav1.Condition
	for _, condition := range retrievedPolicy.Status.Conditions {
		if condition.Type == "Ready" {
			readyCondition = &condition
			break
		}
	}
	require.NotNil(t, readyCondition, "Should have Ready condition")
	assert.Equal(t, metav1.ConditionTrue, readyCondition.Status, "Ready condition should be True")
}

func TestAvailabilityPolicyReconciler_CustomPDBConfig(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deploy := createTestDeployment("test-deploy", "default", map[string]string{"app": "test"}, "test-component")

	// Create policy with custom PDB config
	customMinAvailable := intstr.FromString("80%")
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "custom-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Custom,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			CustomPDBConfig: &availabilityv1alpha1.PodDisruptionBudgetConfig{
				MinAvailable: &customMinAvailable,
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	// Reconcile
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "custom-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify policy was applied
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "custom-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1, "Should apply to 1 component")
	// Note: LastAppliedTime is set by updateStatus function which isn't called in main reconcile path
	// The test verifies the core functionality without requiring LastAppliedTime
}

func TestAvailabilityPolicyReconciler_InvalidPolicy(t *testing.T) {
	ctx := context.Background()

	// Create policy with invalid configuration (custom class without custom config)
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "invalid-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Custom,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			// Missing CustomPDBConfig for Custom class
		},
	}

	tr := controller.CreateTestReconcilers(policy)
	reconciler := tr.AvailabilityPolicyReconciler

	// Reconcile
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "invalid-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.Error(t, err) // Should return error for invalid policy

	// Verify policy status shows validation error
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err2 := tr.Client.Get(ctx, types.NamespacedName{
		Name:      "invalid-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err2)

	// Check that we have a Validated condition with False status
	var validatedCondition *metav1.Condition
	for _, condition := range retrievedPolicy.Status.Conditions {
		if condition.Type == "Validated" {
			validatedCondition = &condition
			break
		}
	}
	require.NotNil(t, validatedCondition, "Should have Validated condition")
	assert.Equal(t, metav1.ConditionFalse, validatedCondition.Status, "Validated condition should be False")
	assert.Contains(t, validatedCondition.Message, "custom availability class requires customPDBConfig", "Should contain validation error message")
	assert.Equal(t, "PolicyInvalid", validatedCondition.Reason, "Should have PolicyInvalid reason")

	// Note: Controller sets condition but doesn't emit a Kubernetes event for validation failures
	// The validation failure is reflected in the status condition above
}

func TestAvailabilityPolicyReconciler_NoMatchingComponents(t *testing.T) {
	ctx := context.Background()

	// Create deployment that won't match the policy
	deploy := createTestDeployment("test-deploy", "default", map[string]string{"app": "nomatch"}, "nomatch-component")

	// Create policy that won't match any components
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "nomatch-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "nonexistent"},
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	// Reconcile
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "nomatch-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify policy status
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "nomatch-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Empty(t, retrievedPolicy.Status.AppliedToComponents, "Should not match any components")

	// Check Ready condition
	var readyCondition *metav1.Condition
	for _, condition := range retrievedPolicy.Status.Conditions {
		if condition.Type == "Ready" {
			readyCondition = &condition
			break
		}
	}
	require.NotNil(t, readyCondition, "Should have Ready condition")
	// Policy is considered active (Ready=True) even if no components match yet
	// The policy is valid and waiting for matching deployments
	assert.Equal(t, metav1.ConditionTrue, readyCondition.Status, "Ready condition should be True (policy is active)")
	assert.Equal(t, "PolicyActive", readyCondition.Reason, "Should have PolicyActive reason")
}

func TestAvailabilityPolicyReconciler_PolicyDeletion(t *testing.T) {
	ctx := context.Background()

	// Create a deployment
	deploy := createTestDeployment("test-deploy", "default", map[string]string{"app": "test"}, "test-component")

	// Create policy that is being deleted - must have finalizer for fake client
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "delete-policy",
			Namespace:         "default",
			DeletionTimestamp: &metav1.Time{Time: time.Now()},
			Finalizers:        []string{"test-finalizer"}, // Required by fake client
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
		Status: availabilityv1alpha1.AvailabilityPolicyStatus{
			AppliedToComponents: []string{"default/test-component"},
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	// Reconcile
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "delete-policy",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PolicyRemoved")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PolicyRemoved event but none was recorded")
	}
}

func TestAvailabilityPolicyReconciler_PolicyNotFound(t *testing.T) {
	ctx := context.Background()

	tr := controller.CreateTestReconcilers() // No policy
	reconciler := tr.AvailabilityPolicyReconciler

	// Reconcile a non-existent policy
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "nonexistent-policy",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err, "Should not error for non-existent policy")
	assert.Equal(t, reconcile.Result{}, result)
}

func TestAvailabilityPolicyReconciler_NamespaceSelector(t *testing.T) {
	ctx := context.Background()

	// Create deployments in different namespaces
	deploy1 := createTestDeploymentInNamespace("deploy-1", "production", map[string]string{"app": "web"}, "web-prod")
	deploy2 := createTestDeploymentInNamespace("deploy-2", "staging", map[string]string{"app": "web"}, "web-staging")
	deploy3 := createTestDeploymentInNamespace("deploy-3", "development", map[string]string{"app": "web"}, "web-dev")

	// Create policy that only applies to production namespace
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "prod-only-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "web"},
				Namespaces:  []string{"production"},
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy1, deploy2, deploy3, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "prod-only-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify only production deployment matched
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "prod-only-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1, "Should only match production namespace")
	assert.Contains(t, retrievedPolicy.Status.AppliedToComponents[0], "web-prod")
}

func TestAvailabilityPolicyReconciler_MaintenanceWindowValidation(t *testing.T) {
	ctx := context.Background()

	// Create policy with valid maintenance windows
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "maintenance-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			MaintenanceWindows: []availabilityv1alpha1.MaintenanceWindow{
				{
					Start:      "02:00",
					End:        "04:00",
					Timezone:   "UTC",
					DaysOfWeek: []int{0, 6}, // Sunday and Saturday
				},
				{
					Start:      "22:00",
					End:        "23:00",
					Timezone:   "America/New_York",
					DaysOfWeek: []int{1, 2, 3, 4, 5}, // Weekdays
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "maintenance-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify policy is valid
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "maintenance-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	// Check for Ready condition (main reconcile path sets Ready when validation passes)
	var readyCondition *metav1.Condition
	for _, condition := range retrievedPolicy.Status.Conditions {
		if condition.Type == "Ready" {
			readyCondition = &condition
			break
		}
	}
	require.NotNil(t, readyCondition, "Should have Ready condition")
	assert.Equal(t, metav1.ConditionTrue, readyCondition.Status, "Should be ready")
}

func TestAvailabilityPolicyReconciler_InvalidMaintenanceWindow(t *testing.T) {
	ctx := context.Background()

	// Create policy with invalid maintenance window
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "invalid-maint-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			MaintenanceWindows: []availabilityv1alpha1.MaintenanceWindow{
				{
					Start:    "25:00", // Invalid hour
					End:      "04:00",
					Timezone: "UTC",
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "invalid-maint-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	assert.Error(t, err, "Should error for invalid maintenance window")
}

func TestAvailabilityPolicyReconciler_FlexibleEnforcementWithMinimum(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deploy := createTestDeployment("flex-deploy", "default", map[string]string{"app": "flex"}, "flex-component")

	// Create policy with flexible enforcement and minimum class
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "flexible-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "flex"},
			},
			Enforcement:  availabilityv1alpha1.EnforcementFlexible,
			MinimumClass: availabilityv1alpha1.Standard,
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "flexible-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify policy was applied
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "flexible-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1)
}

func TestAvailabilityPolicyReconciler_MatchExpressionDoesNotExist(t *testing.T) {
	ctx := context.Background()

	// Create deployment without the label
	deploy := createTestDeployment("no-label-deploy", "default", map[string]string{"app": "test"}, "test-component")

	// Create policy with DoesNotExist operator
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "doesnotexist-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "deprecated",
						Operator: metav1.LabelSelectorOpDoesNotExist,
					},
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "doesnotexist-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify deployment without "deprecated" label matches
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "doesnotexist-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1, "Should match deployment without deprecated label")
}

func TestAvailabilityPolicyReconciler_ComponentFunctionSelector(t *testing.T) {
	ctx := context.Background()

	// Create deployments with different component functions
	securityDeploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "auth-service",
			Namespace: "default",
			Labels:    map[string]string{"app": "auth"},
			Annotations: map[string]string{
				AnnotationComponentName:              "auth-component",
				"oda.tmforum.org/component-function": "security",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{MatchLabels: map[string]string{"app": "auth"}},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": "auth"}},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "auth", Image: "nginx"}},
				},
			},
		},
	}

	coreDeploy := createTestDeployment("core-service", "default", map[string]string{"app": "core"}, "core-component")

	// Create policy matching security functions
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "security-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				ComponentFunctions: []availabilityv1alpha1.ComponentFunction{
					availabilityv1alpha1.SecurityFunction,
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(securityDeploy, coreDeploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "security-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	// Verify only security deployment matched
	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "security-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1, "Should only match security function")
	assert.Contains(t, retrievedPolicy.Status.AppliedToComponents[0], "auth-component")
}

func TestAvailabilityPolicyReconciler_HighPriorityPolicy(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deploy := createTestDeployment("priority-deploy", "default", map[string]string{"app": "priority"}, "priority-component")

	// Create high priority policy
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "high-priority-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "priority"},
			},
			Priority: 1000, // Very high priority
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "high-priority-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "high-priority-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1)
}

func TestAvailabilityPolicyReconciler_StrictEnforcement(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deploy := createTestDeployment("strict-deploy", "default", map[string]string{"env": "production"}, "prod-component")

	// Create policy with strict enforcement
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "strict-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"env": "production"},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
		},
	}

	tr := controller.CreateTestReconcilers(deploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "strict-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "strict-policy",
		Namespace: "default",
	}, retrievedPolicy)
	require.NoError(t, err)

	// Verify enforcement mode is preserved
	assert.Equal(t, availabilityv1alpha1.EnforcementStrict, retrievedPolicy.Spec.Enforcement)
	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1)
}

// Helper functions

func TestAvailabilityPolicyReconciler_InvalidCustomPDBConfigNoPDBConfig(t *testing.T) {
	ctx := context.Background()

	// Custom class without custom PDB config should fail validation
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "invalid-custom-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Custom,
			// Missing CustomPDBConfig
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
	}

	tr := controller.CreateTestReconcilers(policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "invalid-custom-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "custom availability class requires customPDBConfig")
}

func TestAvailabilityPolicyReconciler_AllAvailabilityClasses(t *testing.T) {
	testCases := []struct {
		name              string
		availabilityClass availabilityv1alpha1.AvailabilityClass
	}{
		{"NonCritical", availabilityv1alpha1.NonCritical},
		{"Standard", availabilityv1alpha1.Standard},
		{"HighAvailability", availabilityv1alpha1.HighAvailability},
		{"MissionCritical", availabilityv1alpha1.MissionCritical},
	}

	for _, tc := range testCases {
		t.Run(string(tc.availabilityClass), func(t *testing.T) {
			ctx := context.Background()

			policy := &availabilityv1alpha1.AvailabilityPolicy{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "class-test-policy",
					Namespace: "default",
				},
				Spec: availabilityv1alpha1.AvailabilityPolicySpec{
					AvailabilityClass: tc.availabilityClass,
					ComponentSelector: availabilityv1alpha1.ComponentSelector{
						MatchLabels: map[string]string{"test": "true"},
					},
				},
			}

			deployment := createTestDeployment("test-deploy", "default", map[string]string{"test": "true"}, "test-component")

			tr := controller.CreateTestReconcilers(policy, deployment)
			reconciler := tr.AvailabilityPolicyReconciler

			req := reconcile.Request{
				NamespacedName: types.NamespacedName{
					Name:      "class-test-policy",
					Namespace: "default",
				},
			}

			_, err := reconciler.Reconcile(ctx, req)
			require.NoError(t, err)

			retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
			err = tr.Client.Get(ctx, req.NamespacedName, retrievedPolicy)
			require.NoError(t, err)
			assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1)
		})
	}
}

func TestAvailabilityPolicyReconciler_MatchExpressionIn(t *testing.T) {
	ctx := context.Background()

	// Create deployments with different environments
	devDeploy := createTestDeployment("dev-service", "default", map[string]string{"env": "dev"}, "dev-comp")
	stagingDeploy := createTestDeployment("staging-service", "default", map[string]string{"env": "staging"}, "staging-comp")
	prodDeploy := createTestDeployment("prod-service", "default", map[string]string{"env": "prod"}, "prod-comp")

	// Policy that matches dev and staging but not prod
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "nonprod-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "env",
						Operator: metav1.LabelSelectorOpIn,
						Values:   []string{"dev", "staging"},
					},
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(devDeploy, stagingDeploy, prodDeploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "nonprod-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, req.NamespacedName, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 2, "Should match dev and staging only")
}

func TestAvailabilityPolicyReconciler_MatchExpressionNotIn(t *testing.T) {
	ctx := context.Background()

	// Create deployments with different tiers
	webDeploy := createTestDeployment("web-service", "default", map[string]string{"tier": "web"}, "web-comp")
	apiDeploy := createTestDeployment("api-service", "default", map[string]string{"tier": "api"}, "api-comp")
	dbDeploy := createTestDeployment("db-service", "default", map[string]string{"tier": "database"}, "db-comp")

	// Policy that excludes database tier
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "non-db-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "tier",
						Operator: metav1.LabelSelectorOpNotIn,
						Values:   []string{"database"},
					},
				},
			},
		},
	}

	tr := controller.CreateTestReconcilers(webDeploy, apiDeploy, dbDeploy, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "non-db-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, req.NamespacedName, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 2, "Should exclude database tier")
}

func TestAvailabilityPolicyReconciler_ComponentNameSelector(t *testing.T) {
	ctx := context.Background()

	// Create deployments with specific component names
	deploy1 := createTestDeployment("service-a", "default", map[string]string{"app": "a"}, "component-alpha")
	deploy2 := createTestDeployment("service-b", "default", map[string]string{"app": "b"}, "component-beta")
	deploy3 := createTestDeployment("service-c", "default", map[string]string{"app": "c"}, "component-gamma")

	// Policy targeting specific component names
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "component-name-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				ComponentNames: []string{"component-alpha", "component-gamma"},
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy1, deploy2, deploy3, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "component-name-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, req.NamespacedName, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 2, "Should match alpha and gamma components")
}

func TestAvailabilityPolicyReconciler_CombinedSelectors(t *testing.T) {
	ctx := context.Background()

	// Create deployments with various characteristics
	deploy1 := createTestDeploymentInNamespace("web-prod", "production", map[string]string{"app": "web", "tier": "frontend"}, "web-prod-comp")
	deploy2 := createTestDeploymentInNamespace("api-prod", "production", map[string]string{"app": "api", "tier": "backend"}, "api-prod-comp")
	deploy3 := createTestDeploymentInNamespace("web-dev", "development", map[string]string{"app": "web", "tier": "frontend"}, "web-dev-comp")

	// Policy with multiple selector criteria (namespace + labels)
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "combined-selector-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				Namespaces:  []string{"production"},
				MatchLabels: map[string]string{"tier": "frontend"},
			},
		},
	}

	tr := controller.CreateTestReconcilers(deploy1, deploy2, deploy3, policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "combined-selector-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.NoError(t, err)

	retrievedPolicy := &availabilityv1alpha1.AvailabilityPolicy{}
	err = tr.Client.Get(ctx, req.NamespacedName, retrievedPolicy)
	require.NoError(t, err)

	assert.Len(t, retrievedPolicy.Status.AppliedToComponents, 1, "Should only match production frontend")
}

func TestAvailabilityPolicyReconciler_EmptySelectorRejected(t *testing.T) {
	ctx := context.Background()

	// Policy with empty selector should be rejected
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "empty-selector-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				// Empty selector - should fail validation
			},
		},
	}

	tr := controller.CreateTestReconcilers(policy)
	reconciler := tr.AvailabilityPolicyReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "empty-selector-policy",
			Namespace: "default",
		},
	}

	_, err := reconciler.Reconcile(ctx, req)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "must specify at least one selection criteria")
}

func createTestDeploymentInNamespace(name, namespace string, labels map[string]string, componentName string) *appsv1.Deployment {
	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels:    labels,
			Annotations: map[string]string{
				AnnotationComponentName: componentName,
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "test-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}
}

func createTestDeployment(name, namespace string, labels map[string]string, componentName string) *appsv1.Deployment {
	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels:    labels,
			Annotations: map[string]string{
				AnnotationComponentName: componentName,
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "test-container",
							Image: "nginx",
							Resources: corev1.ResourceRequirements{
								Limits: corev1.ResourceList{
									corev1.ResourceCPU: resource.MustParse("500m"),
								},
							},
						},
					},
				},
			},
		},
	}
}

func int32Ptr(i int32) *int32 {
	return &i
}
