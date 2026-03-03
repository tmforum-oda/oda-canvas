package controller

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
)

func TestDeploymentReconciler_AnnotationBasedPDB(t *testing.T) {
	ctx := context.Background()

	// Create a deployment with availability annotations
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "annotation-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
				AnnotationComponentFunction: "core",
				AnnotationComponentName:     "my-component",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "my-app"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "my-app"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "app-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.DeploymentReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	// Test reconciliation
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "annotation-deployment",
			Namespace: "default",
		},
	}

	// First reconciliation adds finalizer
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{RequeueAfter: 5 * time.Second}, result)

	// Get the updated deployment
	updatedDeployment := &appsv1.Deployment{}
	err = tr.Client.Get(ctx, req.NamespacedName, updatedDeployment)
	require.NoError(t, err)

	// Verify finalizer was added
	assert.Contains(t, updatedDeployment.Finalizers, FinalizerPDBCleanup, "Finalizer should be added")

	// Reconcile again to create PDB
	result, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB was created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "annotation-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "High availability should be 75%")
	assert.Equal(t, map[string]string{"app": "my-app"}, pdb.Spec.Selector.MatchLabels)

	// Verify labels and annotations on PDB
	assert.Equal(t, OperatorName, pdb.Labels[LabelManagedBy], "Should have managed-by label")
	assert.Equal(t, "my-component", pdb.Labels[LabelComponent], "Should have component label")
	assert.Equal(t, "core", pdb.Labels[LabelFunction], "Should have function label")
	assert.Equal(t, OperatorName, pdb.Annotations[AnnotationCreatedBy], "Should have created-by annotation")
	assert.Equal(t, "high-availability", pdb.Annotations[AnnotationAvailabilityClass], "Should have availability class annotation")

	// Verify events were recorded
	events := []string{}
	timeout := time.After(200 * time.Millisecond)
	for i := 0; i < 2; i++ {
		select {
		case event := <-fakeRecorder.Events:
			events = append(events, event)
		case <-timeout:
			break
		}
	}

	// Should have at least one PDB created event
	foundPDBCreated := false
	for _, event := range events {
		if contains(event, "PDBCreated") {
			foundPDBCreated = true
			break
		}
	}
	assert.True(t, foundPDBCreated, "Should have PDBCreated event")
}

func TestDeploymentReconciler_PolicyBasedPDB(t *testing.T) {
	ctx := context.Background()

	// Create a deployment with annotation that references a policy-managed deployment
	// The deployment controller checks for policies but only creates PDB if there's
	// some form of availability configuration
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "policy-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"tier": "frontend",
				"app":  "webapp",
			},
			Annotations: map[string]string{
				// Add component name so policy matching works properly
				AnnotationComponentName: "webapp-component",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "webapp"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "webapp"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "webapp-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create an AvailabilityPolicy that matches this deployment
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
			Priority: 10,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "policy-deployment",
			Namespace: "default",
		},
	}

	// The deployment controller should recognize that this deployment
	// doesn't have availability annotations and skip it
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{RequeueAfter: 5 * time.Second}, result)

	// Verify no PDB was created since deployment has no availability annotations
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "policy-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created without availability annotations")
}

func TestDeploymentReconciler_SingleReplicaDeployment(t *testing.T) {
	ctx := context.Background()

	// Create single replica deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "single-replica",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(1), // Single replica
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "single"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "single"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "single-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.DeploymentReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "single-replica",
			Namespace: "default",
		},
	}

	// Add finalizer
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{RequeueAfter: 5 * time.Second}, result)

	// Process single replica (should skip PDB creation)
	result, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify no PDB was created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "single-replica-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created for single replica")

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "DeploymentSkipped")
		assert.Contains(t, event, "insufficient replicas")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected DeploymentSkipped event but none was recorded")
	}
}

func TestDeploymentReconciler_MaintenanceWindow(t *testing.T) {
	ctx := context.Background()

	// Create deployment with maintenance window annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "maintenance-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationMaintenanceWindow: "02:00-04:00 UTC", // Not active now
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "maintenance"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "maintenance"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "maintenance-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "maintenance-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{RequeueAfter: 5 * time.Second}, result)

	// Outside maintenance window, should create PDB normally
	result, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	// Should not requeue for maintenance since we're outside the window
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "maintenance-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created outside maintenance window")
}

func TestDeploymentReconciler_DeletionWithCleanup(t *testing.T) {
	ctx := context.Background()

	// Create deployment already marked for deletion
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "delete-deployment",
			Namespace:         "default",
			Finalizers:        []string{FinalizerPDBCleanup},
			DeletionTimestamp: &metav1.Time{Time: time.Now()},
			UID:               types.UID("test-uid"),
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "delete"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "delete"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "delete-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Pre-create PDB that should be cleaned up
	pdb := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "delete-deployment-pdb",
			Namespace: "default",
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion:         "apps/v1",
					Kind:               "Deployment",
					Name:               "delete-deployment",
					UID:                deployment.UID,
					Controller:         &[]bool{true}[0],
					BlockOwnerDeletion: &[]bool{true}[0],
				},
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "50%"},
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "delete"},
			},
		},
	}

	tr := CreateTestReconcilers(deployment, pdb)
	reconciler := tr.DeploymentReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "delete-deployment",
			Namespace: "default",
		},
	}

	// Test deletion handling
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was deleted
	deletedPDB := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "delete-deployment-pdb",
		Namespace: "default",
	}, deletedPDB)
	assert.True(t, errors.IsNotFound(err), "PDB should be deleted")

	// Verify deployment finalizer was removed
	updatedDeployment := &appsv1.Deployment{}
	err = tr.Client.Get(ctx, req.NamespacedName, updatedDeployment)

	if errors.IsNotFound(err) {
		// Object was deleted after finalizer removal - this is correct behavior
		assert.True(t, true, "Deployment was correctly deleted after finalizer removal")
	} else {
		// Object still exists but finalizer should be removed
		require.NoError(t, err)
		assert.NotContains(t, updatedDeployment.Finalizers, FinalizerPDBCleanup, "Finalizer should be removed")
	}

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PDBDeleted")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PDBDeleted event but none was recorded")
	}
}

func TestDeploymentReconciler_LegacyAnnotation(t *testing.T) {
	ctx := context.Background()

	// Create deployment with legacy annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "legacy-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				LegacyAnnotationPDB: "high-availability", // Legacy annotation
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "legacy"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "legacy"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "legacy-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "legacy-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Create PDB from legacy annotation
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB was created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "legacy-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created from legacy annotation")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "High availability should be 75%")
}

func TestDeploymentReconciler_UpdatePDB(t *testing.T) {
	ctx := context.Background()

	// Create a deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "update-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "update"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "update"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "update-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create existing PDB with different minAvailable
	existingPDB := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "update-deployment-pdb",
			Namespace: "default",
			Labels: map[string]string{
				LabelManagedBy: OperatorName,
			},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "non-critical", // Different class
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "20%"}, // Different value
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "update"},
			},
		},
	}

	tr := CreateTestReconcilers(deployment, existingPDB)
	reconciler := tr.DeploymentReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	// Add finalizer first
	deployment.Finalizers = []string{FinalizerPDBCleanup}
	err := tr.Client.Update(ctx, deployment)
	require.NoError(t, err)

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "update-deployment",
			Namespace: "default",
		},
	}

	// Reconcile to update PDB
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was updated
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "update-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err)
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "MinAvailable should be updated to 50%")
	assert.Equal(t, "standard", pdb.Annotations[AnnotationAvailabilityClass], "Availability class should be updated")

	// Verify update event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PDBUpdated")
		assert.Contains(t, event, "20% -> 50%")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PDBUpdated event but none was recorded")
	}
}

// Helper functions

func int32Ptr(i int32) *int32 {
	return &i
}
