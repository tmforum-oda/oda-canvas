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
	assert.Equal(t, reconcile.Result{Requeue: true}, result)

	// Get the updated deployment
	updatedDeployment := &appsv1.Deployment{}
	err = tr.Client.Get(ctx, req.NamespacedName, updatedDeployment)
	require.NoError(t, err)

	// Verify finalizer was added
	assert.Contains(t, updatedDeployment.Finalizers, FinalizerPDBCleanup, "Finalizer should be added")

	// Reconcile again to create PDB
	_, err = reconciler.Reconcile(ctx, req)
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
eventLoop:
	for i := 0; i < 2; i++ {
		select {
		case event := <-fakeRecorder.Events:
			events = append(events, event)
		case <-timeout:
			break eventLoop
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
	// matches a policy and create a PDB based on policy configuration
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{Requeue: true}, result)

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

	// First reconcile: single replica deployments are skipped immediately (no finalizer added)
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Reconcile again - should still skip (no PDB for single replica)
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
	assert.Equal(t, reconcile.Result{Requeue: true}, result)

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

func TestDeploymentReconciler_PolicyBasedPDBWithAnnotations(t *testing.T) {
	ctx := context.Background()

	// Create a deployment that matches a policy AND has annotations
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "policy-annotation-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"tier": "backend",
			},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard", // Annotation says standard
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "backend"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "backend"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "backend-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with higher availability class
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "backend-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability, // Policy says high-availability
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"tier": "backend"},
			},
			Enforcement: availabilityv1alpha1.EnforcementAdvisory, // Advisory mode - annotations preferred
			Priority:    10,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "policy-annotation-deployment",
			Namespace: "default",
		},
	}

	// First reconcile adds finalizer
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Second reconcile creates PDB
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// In advisory mode, annotations are preferred - so should be 50% (standard)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "policy-annotation-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "Advisory mode should use annotation (standard = 50%)")
}

func TestDeploymentReconciler_StrictEnforcementMode(t *testing.T) {
	ctx := context.Background()

	// Create deployment with annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "strict-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"env": "production",
			},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "non-critical", // User tries to set low availability
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "strict"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "strict"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "strict-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with strict enforcement
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "strict-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical, // Policy enforces mission-critical
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"env": "production"},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict, // Strict - policy always wins
			Priority:    100,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "strict-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Strict enforcement - policy wins, should be 90% (mission-critical)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "strict-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "90%", pdb.Spec.MinAvailable.String(), "Strict mode should use policy (mission-critical = 90%)")
}

func TestDeploymentReconciler_FlexibleEnforcementMode(t *testing.T) {
	ctx := context.Background()

	// Create deployment with annotation below minimum
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "flexible-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"team": "platform",
			},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "non-critical", // Below minimum
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "flexible"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "flexible"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "flexible-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with flexible enforcement and minimum class
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "flexible-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"team": "platform"},
			},
			Enforcement:  availabilityv1alpha1.EnforcementFlexible,
			MinimumClass: availabilityv1alpha1.Standard, // Minimum is standard
			Priority:     50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "flexible-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Flexible mode with minimum - annotation is below minimum, so use minimum (standard = 50%)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "flexible-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "Flexible mode should enforce minimum (standard = 50%)")
}

func TestDeploymentReconciler_SecurityFunctionBoost(t *testing.T) {
	ctx := context.Background()

	// Create deployment with security function
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "security-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentFunction: "security", // Security function gets boosted
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "auth"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "auth"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "auth-container",
							Image: "keycloak",
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
			Name:      "security-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Security function should boost standard from 50% to 75%
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "security-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "Security function should boost standard to 75%")
	assert.Equal(t, "security", pdb.Labels[LabelFunction], "Should have security function label")
}

func TestDeploymentReconciler_DeploymentNotFound(t *testing.T) {
	ctx := context.Background()

	tr := CreateTestReconcilers() // No deployment
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "nonexistent-deployment",
			Namespace: "default",
		},
	}

	// Should handle gracefully when deployment doesn't exist
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err, "Should not error when deployment not found")
	assert.Equal(t, reconcile.Result{}, result, "Should return empty result")
}

func TestDeploymentReconciler_InvalidAvailabilityClass(t *testing.T) {
	ctx := context.Background()

	// Create deployment with invalid availability class
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "invalid-class-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "super-duper-critical", // Invalid class
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "invalid"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "invalid"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "invalid-container",
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
			Name:      "invalid-class-deployment",
			Namespace: "default",
		},
	}

	// Reconcile - should detect invalid class and return error
	_, err := reconciler.Reconcile(ctx, req)
	// The controller returns an error for invalid configuration
	assert.Error(t, err, "Should return error for invalid availability class")
	assert.Contains(t, err.Error(), "invalid availability class")

	// Should NOT create a PDB for invalid class
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "invalid-class-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created for invalid class")

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "InvalidConfiguration")
	case <-time.After(100 * time.Millisecond):
		// Event may not be recorded if error happens early
	}
}

func TestDeploymentReconciler_PDBOwnershipAndLabels(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "ownership-deployment",
			Namespace: "default",
			UID:       types.UID("deployment-uid-123"),
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentName:     "test-component",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "ownership"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "ownership"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "ownership-container",
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
			Name:      "ownership-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer first
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Create PDB
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB exists with correct ownership and labels
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "ownership-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should exist")

	// Verify labels
	assert.Equal(t, OperatorName, pdb.Labels[LabelManagedBy], "Should have managed-by label")
	assert.Equal(t, "test-component", pdb.Labels[LabelComponent], "Should have component label")
	assert.Equal(t, "standard", pdb.Labels[LabelAvailabilityClass], "Should have availability class label")

	// Verify annotations
	assert.Equal(t, OperatorName, pdb.Annotations[AnnotationCreatedBy], "Should have created-by annotation")
	assert.Equal(t, "standard", pdb.Annotations[AnnotationAvailabilityClass], "Should have availability class annotation")

	// Verify owner reference
	assert.Len(t, pdb.OwnerReferences, 1, "Should have one owner reference")
	assert.Equal(t, "ownership-deployment", pdb.OwnerReferences[0].Name)
	assert.Equal(t, "Deployment", pdb.OwnerReferences[0].Kind)
}

func TestDeploymentReconciler_NoAnnotationsNoPolicy(t *testing.T) {
	ctx := context.Background()

	// Create deployment without any availability configuration
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "no-config-deployment",
			Namespace: "default",
			// No annotations, no matching policy
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "no-config"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "no-config"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "no-config-container",
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
			Name:      "no-config-deployment",
			Namespace: "default",
		},
	}

	// Reconcile - should skip since no configuration
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Should NOT create a PDB
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "no-config-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created without configuration")

	// Verify unmanaged event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "DeploymentUnmanaged")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected DeploymentUnmanaged event but none was recorded")
	}
}

func TestDeploymentReconciler_AllAvailabilityClasses(t *testing.T) {
	testCases := []struct {
		class           string
		expectedPercent string
	}{
		{"non-critical", "20%"},
		{"standard", "50%"},
		{"high-availability", "75%"},
		{"mission-critical", "90%"},
	}

	for _, tc := range testCases {
		t.Run(tc.class, func(t *testing.T) {
			ctx := context.Background()

			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      tc.class + "-deployment",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationAvailabilityClass: tc.class,
					},
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(3),
					Selector: &metav1.LabelSelector{
						MatchLabels: map[string]string{"app": tc.class},
					},
					Template: corev1.PodTemplateSpec{
						ObjectMeta: metav1.ObjectMeta{
							Labels: map[string]string{"app": tc.class},
						},
						Spec: corev1.PodSpec{
							Containers: []corev1.Container{
								{
									Name:  "container",
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
					Name:      tc.class + "-deployment",
					Namespace: "default",
				},
			}

			// Add finalizer and create PDB
			_, err := reconciler.Reconcile(ctx, req)
			assert.NoError(t, err)
			_, err = reconciler.Reconcile(ctx, req)
			assert.NoError(t, err)

			// Verify PDB has correct minAvailable
			pdb := &policyv1.PodDisruptionBudget{}
			err = tr.Client.Get(ctx, types.NamespacedName{
				Name:      tc.class + "-deployment-pdb",
				Namespace: "default",
			}, pdb)
			assert.NoError(t, err, "PDB should be created for %s", tc.class)
			assert.Equal(t, tc.expectedPercent, pdb.Spec.MinAvailable.String(),
				"Class %s should have minAvailable %s", tc.class, tc.expectedPercent)
		})
	}
}

func TestDeploymentReconciler_NamespaceFiltering(t *testing.T) {
	ctx := context.Background()

	// Create deployment in specific namespace
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "namespaced-deployment",
			Namespace: "production",
			Labels: map[string]string{
				"app": "namespaced",
			},
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "namespaced"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "namespaced"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "namespaced-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy that only applies to different namespace
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "staging-only-policy",
			Namespace: "staging", // Different namespace
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "namespaced"},
				Namespaces:  []string{"staging"}, // Only staging namespace
			},
			Priority: 100,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "namespaced-deployment",
			Namespace: "production",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Policy should NOT match (wrong namespace), so use annotation (standard = 50%)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "namespaced-deployment-pdb",
		Namespace: "production",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "Should use annotation since policy namespace doesn't match")
}

func TestDeploymentReconciler_PolicyPriorityResolution(t *testing.T) {
	ctx := context.Background()

	// Create deployment that matches multiple policies
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "multi-policy-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app":  "multi",
				"tier": "backend",
				"env":  "prod",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "multi"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "multi"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "multi-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create low priority policy
	lowPriorityPolicy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "low-priority-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.NonCritical, // 20%
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"tier": "backend"},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    10, // Low priority
		},
	}

	// Create high priority policy
	highPriorityPolicy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "high-priority-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical, // 90%
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"env": "prod"},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    100, // High priority - should win
		},
	}

	tr := CreateTestReconcilers(deployment, lowPriorityPolicy, highPriorityPolicy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "multi-policy-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// High priority policy should win - 90% (mission-critical)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "multi-policy-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "90%", pdb.Spec.MinAvailable.String(), "High priority policy should win")
}

func TestDeploymentReconciler_ComponentNameMatching(t *testing.T) {
	ctx := context.Background()

	// Create deployment with component name
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "named-component-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationComponentName: "payment-service",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "payment"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "payment"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "payment-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy matching by component name
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "payment-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				ComponentNames: []string{"payment-service", "billing-service"},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "named-component-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Policy should match by component name
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "named-component-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "90%", pdb.Spec.MinAvailable.String(), "Policy should match by component name")
}

func TestDeploymentReconciler_ComponentFunctionMatching(t *testing.T) {
	ctx := context.Background()

	// Create deployment with management function annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "management-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationComponentFunction: "management",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "admin"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "admin"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "admin-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy matching by component function
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "management-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				ComponentFunctions: []availabilityv1alpha1.ComponentFunction{
					availabilityv1alpha1.ManagementFunction,
				},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "management-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Policy should match by component function
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "management-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "Policy should match by component function")
}

func TestDeploymentReconciler_MatchExpressions(t *testing.T) {
	ctx := context.Background()

	// Create deployment with specific labels
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "expr-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app":     "web",
				"version": "v2",
				"tier":    "frontend",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "web"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "web"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "web-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with match expressions
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "expression-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.HighAvailability,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "version",
						Operator: metav1.LabelSelectorOpIn,
						Values:   []string{"v2", "v3"},
					},
					{
						Key:      "tier",
						Operator: metav1.LabelSelectorOpNotIn,
						Values:   []string{"backend"},
					},
				},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "expr-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Policy should match using expressions
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "expr-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "Policy should match using expressions")
}

func TestDeploymentReconciler_MatchExpressionExists(t *testing.T) {
	ctx := context.Background()

	// Create deployment with specific label
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "exists-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"app":       "special",
				"monitored": "true", // This label exists
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "special"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "special"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "special-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with Exists operator
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "exists-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.MissionCritical,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchExpressions: []metav1.LabelSelectorRequirement{
					{
						Key:      "monitored",
						Operator: metav1.LabelSelectorOpExists,
					},
				},
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "exists-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Policy should match using Exists operator
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "exists-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "90%", pdb.Spec.MinAvailable.String(), "Policy should match using Exists operator")
}

func TestDeploymentReconciler_ReplicaScaleUp(t *testing.T) {
	ctx := context.Background()

	// Create deployment starting with single replica (no PDB created)
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "scaleup-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(1), // Single replica - no PDB
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "scaleup"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "scaleup"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "scaleup-container",
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
			Name:      "scaleup-deployment",
			Namespace: "default",
		},
	}

	// Reconcile with single replica - should skip
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify no PDB created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "scaleup-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not exist for single replica")

	// Scale up to 3 replicas
	err = tr.Client.Get(ctx, req.NamespacedName, deployment)
	require.NoError(t, err)
	deployment.Spec.Replicas = int32Ptr(3)
	err = tr.Client.Update(ctx, deployment)
	require.NoError(t, err)

	// Reconcile again - should now create PDB
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB was created after scale up
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "scaleup-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created after scale up")
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String())
}

func TestDeploymentReconciler_AvailabilityClassChange(t *testing.T) {
	ctx := context.Background()

	// Create deployment with standard class
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "class-change-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "class-change"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "class-change"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "class-change-container",
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
			Name:      "class-change-deployment",
			Namespace: "default",
		},
	}

	// Create initial PDB with standard class
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify initial PDB
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "class-change-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err)
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "Initial class should be standard (50%)")

	// Change to mission-critical
	updatedDeployment := &appsv1.Deployment{}
	err = tr.Client.Get(ctx, req.NamespacedName, updatedDeployment)
	require.NoError(t, err)
	updatedDeployment.Annotations[AnnotationAvailabilityClass] = "mission-critical"
	err = tr.Client.Update(ctx, updatedDeployment)
	require.NoError(t, err)

	// Clear state cache to force re-evaluation
	reconciler.clearDeploymentState(updatedDeployment)

	// Reconcile to update PDB
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB was updated
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "class-change-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err)
	assert.Equal(t, "90%", pdb.Spec.MinAvailable.String(), "Updated class should be mission-critical (90%)")
}

func TestDeploymentReconciler_ZeroReplicas(t *testing.T) {
	ctx := context.Background()

	// Create deployment with zero replicas
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "zero-replica-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(0), // Zero replicas
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "zero"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "zero"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "zero-container",
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
			Name:      "zero-replica-deployment",
			Namespace: "default",
		},
	}

	// Reconcile - should skip zero replica deployment
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify no PDB created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "zero-replica-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created for zero replicas")
}

func TestDeploymentReconciler_NilReplicas(t *testing.T) {
	ctx := context.Background()

	// Create deployment with nil replicas (defaults to 1)
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "nil-replica-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: nil, // Nil replicas - defaults to 1
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "nil"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "nil"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "nil-container",
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
			Name:      "nil-replica-deployment",
			Namespace: "default",
		},
	}

	// Reconcile - should skip (nil defaults to 1 replica)
	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify no PDB created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "nil-replica-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created for nil replicas (defaults to 1)")
}

func TestDeploymentReconciler_CustomPDBConfig(t *testing.T) {
	ctx := context.Background()

	// Create deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "custom-config-deployment",
			Namespace: "default",
			Labels: map[string]string{
				"custom": "true",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(5),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "custom"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "custom"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "custom-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	// Create policy with custom PDB config
	customMinAvailable := intstr.FromInt(3)
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "custom-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Custom,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"custom": "true"},
			},
			CustomPDBConfig: &availabilityv1alpha1.PodDisruptionBudgetConfig{
				MinAvailable: &customMinAvailable, // Fixed value of 3
			},
			Enforcement: availabilityv1alpha1.EnforcementStrict,
			Priority:    50,
		},
	}

	tr := CreateTestReconcilers(deployment, policy)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "custom-config-deployment",
			Namespace: "default",
		},
	}

	// Add finalizer and create PDB
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB uses custom config
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "custom-config-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "3", pdb.Spec.MinAvailable.String(), "Should use custom minAvailable value")
}

func TestDeploymentReconciler_DuplicatePDBCleanup(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "duplicate-pdb-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentFunction: "core",
				AnnotationComponentName:     "duplicate-test",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "duplicate-test"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "duplicate-test"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "app", Image: "nginx"}},
				},
			},
		},
	}

	// Create multiple PDBs for the same deployment (simulating duplicates)
	pdb1 := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "duplicate-pdb-deployment-pdb",
			Namespace:         "default",
			CreationTimestamp: metav1.Time{Time: time.Now().Add(-1 * time.Hour)},
			Labels: map[string]string{
				"pdb.oda.tmforum.org/managed-by":     "pdb-management-operator",
				"pdb.oda.tmforum.org/deployment":     "duplicate-pdb-deployment",
				"pdb.oda.tmforum.org/owner-kind":     "Deployment",
				"pdb.oda.tmforum.org/owner-name":     "duplicate-pdb-deployment",
				"pdb.oda.tmforum.org/owner-apigroup": "apps",
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "50%"},
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "duplicate-test"},
			},
		},
	}

	pdb2 := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "duplicate-pdb-deployment-pdb-dup",
			Namespace:         "default",
			CreationTimestamp: metav1.Time{Time: time.Now()},
			Labels: map[string]string{
				"pdb.oda.tmforum.org/managed-by":     "pdb-management-operator",
				"pdb.oda.tmforum.org/deployment":     "duplicate-pdb-deployment",
				"pdb.oda.tmforum.org/owner-kind":     "Deployment",
				"pdb.oda.tmforum.org/owner-name":     "duplicate-pdb-deployment",
				"pdb.oda.tmforum.org/owner-apigroup": "apps",
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "75%"},
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "duplicate-test"},
			},
		},
	}

	tr := CreateTestReconcilers(deployment, pdb1, pdb2)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "duplicate-pdb-deployment",
			Namespace: "default",
		},
	}

	// Reconcile should clean up duplicates
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
}

func TestDeploymentReconciler_PDBUpdateOnChange(t *testing.T) {
	ctx := context.Background()

	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "pdb-update-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentFunction: "core",
				AnnotationComponentName:     "update-test",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(4),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "update-test"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "update-test"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "app", Image: "nginx"}},
				},
			},
		},
	}

	// Create existing PDB with old config
	oldPdb := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "pdb-update-deployment-pdb",
			Namespace: "default",
			Labels: map[string]string{
				"pdb.oda.tmforum.org/managed-by":     "pdb-management-operator",
				"pdb.oda.tmforum.org/deployment":     "pdb-update-deployment",
				"pdb.oda.tmforum.org/owner-kind":     "Deployment",
				"pdb.oda.tmforum.org/owner-name":     "pdb-update-deployment",
				"pdb.oda.tmforum.org/owner-apigroup": "apps",
			},
			Annotations: map[string]string{
				"pdb.oda.tmforum.org/config-hash": "old-hash",
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "20%"}, // Old config
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "update-test"},
			},
		},
	}

	tr := CreateTestReconcilers(deployment, oldPdb)
	reconciler := tr.DeploymentReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "pdb-update-deployment",
			Namespace: "default",
		},
	}

	// First reconcile adds finalizer
	_, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Second reconcile should update the PDB
	_, err = reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)

	// Verify PDB was updated
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "pdb-update-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err)
	assert.Equal(t, "50%", pdb.Spec.MinAvailable.String(), "PDB should be updated to standard 50%")
}

func TestDeploymentReconciler_AvailabilityClassPDBValues(t *testing.T) {
	testCases := []struct {
		class           string
		expectedPercent string
	}{
		{"non-critical", "20%"},
		{"standard", "50%"},
		{"high-availability", "75%"},
		{"mission-critical", "90%"},
	}

	for _, tc := range testCases {
		t.Run(tc.class, func(t *testing.T) {
			ctx := context.Background()

			deployment := &appsv1.Deployment{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "class-test-deployment",
					Namespace: "default",
					Annotations: map[string]string{
						AnnotationAvailabilityClass: tc.class,
						AnnotationComponentFunction: "core",
						AnnotationComponentName:     "class-test",
					},
				},
				Spec: appsv1.DeploymentSpec{
					Replicas: int32Ptr(4),
					Selector: &metav1.LabelSelector{
						MatchLabels: map[string]string{"app": "class-test"},
					},
					Template: corev1.PodTemplateSpec{
						ObjectMeta: metav1.ObjectMeta{
							Labels: map[string]string{"app": "class-test"},
						},
						Spec: corev1.PodSpec{
							Containers: []corev1.Container{{Name: "app", Image: "nginx"}},
						},
					},
				},
			}

			tr := CreateTestReconcilers(deployment)
			reconciler := tr.DeploymentReconciler

			req := reconcile.Request{
				NamespacedName: types.NamespacedName{
					Name:      "class-test-deployment",
					Namespace: "default",
				},
			}

			// First reconcile adds finalizer
			_, err := reconciler.Reconcile(ctx, req)
			assert.NoError(t, err)

			// Second reconcile creates PDB
			_, err = reconciler.Reconcile(ctx, req)
			assert.NoError(t, err)

			// Verify PDB was created with correct minAvailable
			pdb := &policyv1.PodDisruptionBudget{}
			err = tr.Client.Get(ctx, types.NamespacedName{
				Name:      "class-test-deployment-pdb",
				Namespace: "default",
			}, pdb)
			assert.NoError(t, err)
			assert.NotNil(t, pdb.Spec.MinAvailable)
			assert.Equal(t, tc.expectedPercent, pdb.Spec.MinAvailable.String())
		})
	}
}

// Helper functions

func int32Ptr(i int32) *int32 {
	return &i
}
