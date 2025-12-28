package controller

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"k8s.io/apimachinery/pkg/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/events"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
)

// Test utilities for the controller package

// SetupTestScheme creates a scheme with all required types for testing
func SetupTestScheme() *runtime.Scheme {
	scheme := runtime.NewScheme()

	// Add all required schemes
	_ = clientgoscheme.AddToScheme(scheme)
	_ = availabilityv1alpha1.AddToScheme(scheme)
	_ = appsv1.AddToScheme(scheme)
	_ = policyv1.AddToScheme(scheme)

	return scheme
}

// CreateFakeClient creates a fake Kubernetes client for testing
func CreateFakeClient(objects ...client.Object) client.Client {
	scheme := SetupTestScheme()

	return fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(objects...).
		WithStatusSubresource(&availabilityv1alpha1.AvailabilityPolicy{}).
		Build()
}

// CreateTestReconciler creates a test reconciler with fake client and event recorder
type TestReconcilers struct {
	DeploymentReconciler         *DeploymentReconciler
	AvailabilityPolicyReconciler *AvailabilityPolicyReconciler
	Client                       client.Client
	Scheme                       *runtime.Scheme
	EventRecorder                *events.EventRecorder
}

// CreateTestReconcilers creates reconcilers for testing
func CreateTestReconcilers(objects ...client.Object) *TestReconcilers {
	scheme := SetupTestScheme()
	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(objects...).
		WithStatusSubresource(&availabilityv1alpha1.AvailabilityPolicy{}).
		Build()

	// Create a fake event recorder
	fakeRecorder := record.NewFakeRecorder(100)
	eventRecorder := events.NewEventRecorder(fakeRecorder)

	return &TestReconcilers{
		Client:        fakeClient,
		Scheme:        scheme,
		EventRecorder: eventRecorder,
		DeploymentReconciler: &DeploymentReconciler{
			Client:   fakeClient,
			Scheme:   scheme,
			Recorder: fakeRecorder,
			Events:   eventRecorder,
		},
		AvailabilityPolicyReconciler: &AvailabilityPolicyReconciler{
			Client:   fakeClient,
			Scheme:   scheme,
			Recorder: fakeRecorder,
			Events:   eventRecorder,
		},
	}
}

// SetEnvWithCleanup sets an environment variable and returns a cleanup function
func SetEnvWithCleanup(key, value string) func() {
	oldValue := os.Getenv(key)
	_ = os.Setenv(key, value)
	return func() {
		if oldValue == "" {
			_ = os.Unsetenv(key)
		} else {
			_ = os.Setenv(key, oldValue)
		}
	}
}

// WaitForDeletion waits for an object to be deleted (for fake client, this is immediate)
func WaitForDeletion(ctx context.Context, c client.Client, obj client.Object, timeout time.Duration) error {
	key := client.ObjectKeyFromObject(obj)

	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	timeoutTimer := time.NewTimer(timeout)
	defer timeoutTimer.Stop()

	for {
		select {
		case <-timeoutTimer.C:
			return fmt.Errorf("timeout waiting for deletion of %s %s", obj.GetObjectKind().GroupVersionKind().Kind, key)
		case <-ticker.C:
			err := c.Get(ctx, key, obj)
			if client.IgnoreNotFound(err) == nil {
				return nil // Object not found, deletion successful
			}
			if err != nil {
				return err // Unexpected error
			}
			// Object still exists, continue waiting
		}
	}
}

// WaitForCondition waits for a specific condition to be met
func WaitForCondition(ctx context.Context, checkFunc func() (bool, error), timeout time.Duration) error {
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	timeoutTimer := time.NewTimer(timeout)
	defer timeoutTimer.Stop()

	for {
		select {
		case <-timeoutTimer.C:
			return fmt.Errorf("timeout waiting for condition")
		case <-ticker.C:
			satisfied, err := checkFunc()
			if err != nil {
				return err
			}
			if satisfied {
				return nil
			}
		}
	}
}

// CreateTestNamespace creates a unique test namespace (for unit tests, just returns default)
func CreateTestNamespace(ctx context.Context, baseName string) (string, error) {
	// For unit tests with fake clients, we just use "default"
	return "default", nil
}

// CleanupTestNamespace removes a test namespace (no-op for unit tests)
func CleanupTestNamespace(ctx context.Context, namespace string) error {
	// For unit tests with fake clients, no cleanup needed
	return nil
}

// AssertEventRecorded checks if a specific event was recorded
func AssertEventRecorded(t *testing.T, recorder *record.FakeRecorder, expectedReason string) {
	t.Helper()

	select {
	case event := <-recorder.Events:
		if !contains(event, expectedReason) {
			t.Errorf("Expected event with reason '%s', but got: %s", expectedReason, event)
		}
	case <-time.After(100 * time.Millisecond):
		t.Errorf("Expected event with reason '%s' but no event was recorded", expectedReason)
	}
}

// contains checks if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[0:len(substr)] == substr || len(s) > len(substr) && contains(s[1:], substr)
}

// TestMain can be used to set up global test state if needed
func TestMain(m *testing.M) {
	// Add any global test setup here if needed

	// Run tests
	code := m.Run()

	// Add any global test cleanup here if needed

	os.Exit(code)
}
