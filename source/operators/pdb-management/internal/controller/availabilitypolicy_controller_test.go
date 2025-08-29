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
	assert.Equal(t, 5*time.Minute, result.RequeueAfter)

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

	// Verify events were recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PolicyValidated")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PolicyValidated event but none was recorded")
	}

	// Check for additional events
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PolicyApplied")
	case <-time.After(100 * time.Millisecond):
		// It's ok if there's no additional event
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
	assert.NotNil(t, retrievedPolicy.Status.LastAppliedTime, "Should have last applied time")
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
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

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

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PolicyInvalid")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PolicyInvalid event but none was recorded")
	}
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
	assert.Equal(t, metav1.ConditionFalse, readyCondition.Status, "Ready condition should be False")
	assert.Equal(t, "NoComponentsMatched", readyCondition.Reason, "Should have correct reason")
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

// Helper functions

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
