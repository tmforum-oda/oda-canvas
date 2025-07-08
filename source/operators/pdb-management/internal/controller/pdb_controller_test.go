package controller

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

func TestPDBReconciler_BasicFlow(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	// Create a deployment with availability annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "high-availability",
				AnnotationComponentFunction: "core",
				AnnotationComponentName:     "test-component",
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
						},
					},
				},
			},
		},
	}

	// Create test reconcilers
	tr := CreateTestReconcilers(deployment)
	reconciler := tr.PDBReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	// Test reconciliation
	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "test-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "High availability should be 75%")
	assert.Equal(t, map[string]string{"app": "test"}, pdb.Spec.Selector.MatchLabels)

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "PDBCreated")
		assert.Contains(t, event, "test-deployment-pdb")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected PDBCreated event but none was recorded")
	}
}

func TestPDBReconciler_SingleReplica(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	// Create a deployment with single replica
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "single-replica-deployment",
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
							Name:  "test-container",
							Image: "nginx",
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.PDBReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "single-replica-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was NOT created for single replica
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "single-replica-deployment-pdb",
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

func TestPDBReconciler_NoAvailabilityAnnotation(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	// Create a deployment without availability annotation
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "no-annotation-deployment",
			Namespace: "default",
			// No availability annotation
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(3),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "no-annotation"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "no-annotation"},
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

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.PDBReconciler
	fakeRecorder := reconciler.Recorder.(*record.FakeRecorder)

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "no-annotation-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was NOT created
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "no-annotation-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created without availability annotation")

	// Verify event was recorded
	select {
	case event := <-fakeRecorder.Events:
		assert.Contains(t, event, "DeploymentUnmanaged")
		assert.Contains(t, event, "no availability annotation")
	case <-time.After(100 * time.Millisecond):
		t.Error("Expected DeploymentUnmanaged event but none was recorded")
	}
}

func TestPDBReconciler_SecurityFunction(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	// Create a deployment with security function
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "security-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
				AnnotationComponentFunction: "security",
				AnnotationComponentName:     "auth-service",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
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
	reconciler := tr.PDBReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "security-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was created with security boost (standard -> 75%)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "security-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should be created")
	assert.Equal(t, "75%", pdb.Spec.MinAvailable.String(), "Security function should boost standard to 75%")
}

func TestPDBReconciler_PDBDisabled(t *testing.T) {
	// Disable PDB
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "false")
	defer cleanup()

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
						},
					},
				},
			},
		},
	}

	tr := CreateTestReconcilers(deployment)
	reconciler := tr.PDBReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB was NOT created when disabled
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "test-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.True(t, errors.IsNotFound(err), "PDB should not be created when disabled")
}

func TestPDBReconciler_DeploymentNotFound(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	tr := CreateTestReconcilers()
	reconciler := tr.PDBReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "nonexistent-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err, "Should handle missing deployment gracefully")
	assert.Equal(t, reconcile.Result{}, result)
}

func TestPDBReconciler_ExistingPDB(t *testing.T) {
	// Enable PDB for testing
	cleanup := SetEnvWithCleanup("ENABLE_PDB", "true")
	defer cleanup()

	ctx := context.Background()

	// Create a deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "existing-pdb-deployment",
			Namespace: "default",
			Annotations: map[string]string{
				AnnotationAvailabilityClass: "standard",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: int32Ptr(2),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "existing"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "existing"},
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

	// Pre-create PDB
	existingPDB := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "existing-pdb-deployment-pdb",
			Namespace: "default",
			Labels: map[string]string{
				LabelManagedBy: OperatorName,
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &intstr.IntOrString{Type: intstr.String, StrVal: "25%"},
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "existing"},
			},
		},
	}

	tr := CreateTestReconcilers(deployment, existingPDB)
	reconciler := tr.PDBReconciler

	req := reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      "existing-pdb-deployment",
			Namespace: "default",
		},
	}

	result, err := reconciler.Reconcile(ctx, req)
	assert.NoError(t, err)
	assert.Equal(t, reconcile.Result{}, result)

	// Verify PDB still exists (should handle AlreadyExists error gracefully)
	pdb := &policyv1.PodDisruptionBudget{}
	err = tr.Client.Get(ctx, types.NamespacedName{
		Name:      "existing-pdb-deployment-pdb",
		Namespace: "default",
	}, pdb)
	assert.NoError(t, err, "PDB should still exist")
}

func TestCalculateMinAvailable(t *testing.T) {
	tests := []struct {
		name           string
		class          string
		function       string
		expectedResult string
	}{
		{
			name:           "non-critical core",
			class:          "non-critical",
			function:       "core",
			expectedResult: "20%",
		},
		{
			name:           "standard core",
			class:          "standard",
			function:       "core",
			expectedResult: "50%",
		},
		{
			name:           "standard security (boosted)",
			class:          "standard",
			function:       "security",
			expectedResult: "75%",
		},
		{
			name:           "high-availability core",
			class:          "high-availability",
			function:       "core",
			expectedResult: "75%",
		},
		{
			name:           "mission-critical core",
			class:          "mission-critical",
			function:       "core",
			expectedResult: "90%",
		},
		{
			name:           "unknown class (default)",
			class:          "unknown",
			function:       "core",
			expectedResult: "50%",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calculateMinAvailable(tt.class, tt.function)
			assert.Equal(t, tt.expectedResult, result.String())
		})
	}
}

//func int32Ptr(i int32) *int32 {
//	return &i
//}
