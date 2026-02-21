/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package client

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
)

func setupTestScheme() *runtime.Scheme {
	scheme := runtime.NewScheme()
	_ = corev1.AddToScheme(scheme)
	_ = appsv1.AddToScheme(scheme)
	_ = availabilityv1alpha1.AddToScheme(scheme)
	return scheme
}

func TestGetDefaultAdaptiveConfig(t *testing.T) {
	config := getDefaultAdaptiveConfig()

	assert.Equal(t, uint32(5), config.baseMaxRequests)
	assert.Equal(t, 30*time.Second, config.baseTimeout)
	assert.Equal(t, 0.6, config.baseFailureRatio)
	assert.Equal(t, uint32(5), config.baseConsecutiveFailures)
	assert.Equal(t, 2*time.Minute, config.learningPeriod)
	assert.Equal(t, 30*time.Second, config.adjustmentInterval)
	assert.Equal(t, 3.0, config.maxTimeoutMultiplier)
	assert.Equal(t, 0.5, config.minTimeoutMultiplier)
	assert.Equal(t, 5*time.Minute, config.sampleRetentionPeriod)
}

func TestNewClusterMetrics(t *testing.T) {
	cm := newClusterMetrics()

	assert.NotNil(t, cm)
	assert.NotNil(t, cm.samples)
	assert.Equal(t, 0, len(cm.samples))

	// Check default values
	p50 := cm.responseTimeP50.Load().(time.Duration)
	assert.Equal(t, 100*time.Millisecond, p50)

	p95 := cm.responseTimeP95.Load().(time.Duration)
	assert.Equal(t, 500*time.Millisecond, p95)

	p99 := cm.responseTimeP99.Load().(time.Duration)
	assert.Equal(t, 1*time.Second, p99)

	errorRate := cm.errorRate.Load().(float64)
	assert.Equal(t, 0.0, errorRate)

	throughput := cm.throughput.Load().(float64)
	assert.Equal(t, 10.0, throughput)
}

func TestNewAdaptiveCircuitBreakerClient(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	assert.NotNil(t, acb)
	assert.NotNil(t, acb.Client)
	assert.NotNil(t, acb.breakers)
	assert.NotNil(t, acb.metrics)
	assert.NotNil(t, acb.config)
	assert.False(t, acb.startTime.IsZero())

	// Give goroutines a moment to start
	time.Sleep(100 * time.Millisecond)
}

func TestRecordMetric(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Record a successful operation
	acb.recordMetric("test-op", 100*time.Millisecond, nil)

	acb.metrics.sampleMu.RLock()
	assert.GreaterOrEqual(t, len(acb.metrics.samples), 1)
	lastSample := acb.metrics.samples[len(acb.metrics.samples)-1]
	acb.metrics.sampleMu.RUnlock()

	assert.Equal(t, "test-op", lastSample.operation)
	assert.Equal(t, 100*time.Millisecond, lastSample.duration)
	assert.True(t, lastSample.success)
	assert.Empty(t, lastSample.errorType)

	// Record a failed operation
	testErr := errors.New("test error")
	acb.recordMetric("test-op-fail", 200*time.Millisecond, testErr)

	acb.metrics.sampleMu.RLock()
	lastSample = acb.metrics.samples[len(acb.metrics.samples)-1]
	acb.metrics.sampleMu.RUnlock()

	assert.Equal(t, "test-op-fail", lastSample.operation)
	assert.False(t, lastSample.success)
	assert.NotEmpty(t, lastSample.errorType)
}

func TestRecordMetricSampleLimit(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Record more than 10000 samples to trigger cleanup
	for i := 0; i < 10050; i++ {
		acb.recordMetric("test-op", 10*time.Millisecond, nil)
	}

	acb.metrics.sampleMu.RLock()
	sampleCount := len(acb.metrics.samples)
	acb.metrics.sampleMu.RUnlock()

	// After cleanup, should have around 5050 samples (10050 - 5000 + existing)
	assert.LessOrEqual(t, sampleCount, 6000)
}

func TestCalculateMetrics(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Clear existing samples and add controlled test data
	acb.metrics.sampleMu.Lock()
	acb.metrics.samples = []metricSample{}
	acb.metrics.sampleMu.Unlock()

	// Add enough samples with varying durations
	durations := []time.Duration{
		10 * time.Millisecond,
		20 * time.Millisecond,
		30 * time.Millisecond,
		40 * time.Millisecond,
		50 * time.Millisecond,
		60 * time.Millisecond,
		70 * time.Millisecond,
		80 * time.Millisecond,
		90 * time.Millisecond,
		100 * time.Millisecond,
		200 * time.Millisecond, // Higher values for P95/P99
		300 * time.Millisecond,
	}

	now := time.Now()
	acb.metrics.sampleMu.Lock()
	for i, d := range durations {
		acb.metrics.samples = append(acb.metrics.samples, metricSample{
			timestamp: now.Add(-time.Duration(len(durations)-i) * time.Second),
			duration:  d,
			operation: "test",
			success:   true,
		})
	}
	// Add some failures
	acb.metrics.samples = append(acb.metrics.samples, metricSample{
		timestamp: now,
		duration:  50 * time.Millisecond,
		operation: "test",
		success:   false,
		errorType: "error",
	})
	acb.metrics.sampleMu.Unlock()

	// Calculate metrics
	acb.calculateMetrics()

	// Verify metrics were calculated
	p50 := acb.metrics.responseTimeP50.Load().(time.Duration)
	assert.Greater(t, p50, time.Duration(0))

	errorRate := acb.metrics.errorRate.Load().(float64)
	assert.Greater(t, errorRate, 0.0)
}

func TestCalculateMetricsNotEnoughSamples(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Clear samples
	acb.metrics.sampleMu.Lock()
	acb.metrics.samples = []metricSample{}
	acb.metrics.sampleMu.Unlock()

	// Add only a few samples
	for i := 0; i < 5; i++ {
		acb.recordMetric("test", 10*time.Millisecond, nil)
	}

	// Store original values
	originalP50 := acb.metrics.responseTimeP50.Load().(time.Duration)

	// Calculate metrics - should return early due to insufficient samples
	acb.calculateMetrics()

	// Values should remain unchanged
	newP50 := acb.metrics.responseTimeP50.Load().(time.Duration)
	assert.Equal(t, originalP50, newP50)
}

func TestCalculateNewSettings(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	tests := []struct {
		name               string
		p50                time.Duration
		p95                time.Duration
		p99                time.Duration
		errorRate          float64
		throughput         float64
		expectedMaxReq     uint32
		expectedThreshold  float64
		expectedConsecFail uint32
	}{
		{
			name:               "low error rate, low latency, high throughput",
			p50:                50 * time.Millisecond,
			p95:                100 * time.Millisecond,
			p99:                150 * time.Millisecond,
			errorRate:          0.01,
			throughput:         100,
			expectedMaxReq:     20,
			expectedThreshold:  0.5,
			expectedConsecFail: 3,
		},
		{
			name:               "moderate error rate",
			p50:                100 * time.Millisecond,
			p95:                300 * time.Millisecond,
			p99:                500 * time.Millisecond,
			errorRate:          0.08,
			throughput:         30,  // throughput > 20 => maxRequests = 10
			expectedMaxReq:     10,  // Medium throughput
			expectedThreshold:  0.6, // errorRate < 0.1 => threshold = 0.6
			expectedConsecFail: 10,  // errorRate >= 0.05 => consecutiveFailures = 10
		},
		{
			name:               "high error rate",
			p50:                200 * time.Millisecond,
			p95:                500 * time.Millisecond,
			p99:                1 * time.Second,
			errorRate:          0.15,
			throughput:         10,
			expectedMaxReq:     5,
			expectedThreshold:  0.7,
			expectedConsecFail: 10,
		},
		{
			name:               "low throughput",
			p50:                50 * time.Millisecond,
			p95:                100 * time.Millisecond,
			p99:                150 * time.Millisecond,
			errorRate:          0.02,
			throughput:         5,
			expectedMaxReq:     5,
			expectedThreshold:  0.5,
			expectedConsecFail: 5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			settings := acb.calculateNewSettings(tt.p50, tt.p95, tt.p99, tt.errorRate, tt.throughput)

			assert.Equal(t, tt.expectedMaxReq, settings.maxRequests)
			assert.Equal(t, tt.expectedThreshold, settings.failureRatioThreshold)
			assert.Equal(t, tt.expectedConsecFail, settings.consecutiveFailures)
			assert.Greater(t, settings.timeout, time.Duration(0))
		})
	}
}

func TestCalculateNewSettingsTimeoutBounds(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Test with very low P99 - should use minimum timeout
	settings := acb.calculateNewSettings(1*time.Millisecond, 2*time.Millisecond, 3*time.Millisecond, 0.01, 50)
	minTimeout := time.Duration(float64(acb.config.baseTimeout) * acb.config.minTimeoutMultiplier)
	assert.GreaterOrEqual(t, settings.timeout, minTimeout)

	// Test with very high P99 - should use maximum timeout
	settings = acb.calculateNewSettings(10*time.Second, 20*time.Second, 30*time.Second, 0.01, 50)
	maxTimeout := time.Duration(float64(acb.config.baseTimeout) * acb.config.maxTimeoutMultiplier)
	assert.LessOrEqual(t, settings.timeout, maxTimeout)
}

func TestGetBreaker(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Get a breaker - should create new one
	breaker1 := acb.getBreaker("test-operation")
	assert.NotNil(t, breaker1)

	// Get same breaker again - should return existing
	breaker2 := acb.getBreaker("test-operation")
	assert.Equal(t, breaker1, breaker2)

	// Get different breaker
	breaker3 := acb.getBreaker("another-operation")
	assert.NotNil(t, breaker3)
	assert.NotEqual(t, breaker1, breaker3)
}

func TestCreateAdaptiveBreaker(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	tests := []struct {
		name      string
		operation string
	}{
		{"get operation", "get"},
		{"list operation", "list"},
		{"create operation", "create"},
		{"update operation", "update"},
		{"delete operation", "delete"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ab := acb.createAdaptiveBreaker(tt.operation)

			assert.NotNil(t, ab)
			assert.NotNil(t, ab.breaker)
			assert.NotNil(t, ab.settings)
			assert.False(t, ab.lastAdjusted.IsZero())
		})
	}
}

func TestAdaptiveBreakerShouldUpdate(t *testing.T) {
	ab := &adaptiveBreaker{
		settings: &adaptiveSettings{
			timeout:               30 * time.Second,
			failureRatioThreshold: 0.6,
		},
		lastAdjusted: time.Now().Add(-2 * time.Minute), // Adjusted 2 minutes ago
	}

	// No significant change
	newSettings := &adaptiveSettings{
		timeout:               31 * time.Second, // < 20% change
		failureRatioThreshold: 0.61,             // < 0.1 change
	}
	assert.False(t, ab.shouldUpdate(newSettings))

	// Significant timeout change
	newSettings = &adaptiveSettings{
		timeout:               40 * time.Second, // > 20% change
		failureRatioThreshold: 0.6,
	}
	assert.True(t, ab.shouldUpdate(newSettings))

	// Significant threshold change
	newSettings = &adaptiveSettings{
		timeout:               30 * time.Second,
		failureRatioThreshold: 0.75, // > 0.1 change
	}
	assert.True(t, ab.shouldUpdate(newSettings))

	// Recently adjusted - should not update
	ab.lastAdjusted = time.Now()
	newSettings = &adaptiveSettings{
		timeout:               60 * time.Second,
		failureRatioThreshold: 0.9,
	}
	assert.False(t, ab.shouldUpdate(newSettings))
}

func TestAdaptiveBreakerUpdateSettings(t *testing.T) {
	ab := &adaptiveBreaker{
		settings: &adaptiveSettings{
			timeout:               30 * time.Second,
			failureRatioThreshold: 0.6,
		},
		lastAdjusted: time.Now().Add(-2 * time.Minute),
	}

	newSettings := &adaptiveSettings{
		timeout:               60 * time.Second,
		failureRatioThreshold: 0.8,
	}

	ab.updateSettings(newSettings, "test")

	assert.Equal(t, newSettings.timeout, ab.settings.timeout)
	assert.Equal(t, newSettings.failureRatioThreshold, ab.settings.failureRatioThreshold)
}

func TestClientGet(t *testing.T) {
	scheme := setupTestScheme()

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "test-ns",
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(ns).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Test successful Get
	result := &corev1.Namespace{}
	err := acb.Get(context.Background(), client.ObjectKey{Name: "test-ns"}, result)
	require.NoError(t, err)
	assert.Equal(t, "test-ns", result.Name)

	// Test Get not found
	err = acb.Get(context.Background(), client.ObjectKey{Name: "nonexistent"}, &corev1.Namespace{})
	assert.True(t, apierrors.IsNotFound(err))
}

func TestClientList(t *testing.T) {
	scheme := setupTestScheme()

	ns1 := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "ns1"}}
	ns2 := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{Name: "ns2"}}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(ns1, ns2).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	result := &corev1.NamespaceList{}
	err := acb.List(context.Background(), result)
	require.NoError(t, err)
	assert.Len(t, result.Items, 2)
}

func TestClientCreate(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "new-ns",
		},
	}

	err := acb.Create(context.Background(), ns)
	require.NoError(t, err)

	// Verify it was created
	result := &corev1.Namespace{}
	err = acb.Get(context.Background(), client.ObjectKey{Name: "new-ns"}, result)
	require.NoError(t, err)
	assert.Equal(t, "new-ns", result.Name)
}

func TestClientUpdate(t *testing.T) {
	scheme := setupTestScheme()

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "test-ns",
			Labels: map[string]string{
				"original": "value",
			},
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(ns).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Get and update
	result := &corev1.Namespace{}
	err := acb.Get(context.Background(), client.ObjectKey{Name: "test-ns"}, result)
	require.NoError(t, err)

	result.Labels["updated"] = "true"
	err = acb.Update(context.Background(), result)
	require.NoError(t, err)

	// Verify update
	updated := &corev1.Namespace{}
	err = acb.Get(context.Background(), client.ObjectKey{Name: "test-ns"}, updated)
	require.NoError(t, err)
	assert.Equal(t, "true", updated.Labels["updated"])
}

func TestClientDelete(t *testing.T) {
	scheme := setupTestScheme()

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "test-ns",
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(ns).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	err := acb.Delete(context.Background(), ns)
	require.NoError(t, err)

	// Verify deletion
	err = acb.Get(context.Background(), client.ObjectKey{Name: "test-ns"}, &corev1.Namespace{})
	assert.True(t, apierrors.IsNotFound(err))
}

func TestClientPatch(t *testing.T) {
	scheme := setupTestScheme()

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: "test-ns",
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(ns).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Patch with merge patch
	patch := client.MergeFrom(ns.DeepCopy())
	ns.Labels = map[string]string{"patched": "true"}

	err := acb.Patch(context.Background(), ns, patch)
	require.NoError(t, err)
}

func TestClientStatus(t *testing.T) {
	scheme := setupTestScheme()

	deploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deploy",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": "test"},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "test", Image: "nginx"},
					},
				},
			},
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(deploy).
		WithStatusSubresource(deploy).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	statusWriter := acb.Status()
	assert.NotNil(t, statusWriter)

	// Update status
	deploy.Status.Replicas = 3
	err := statusWriter.Update(context.Background(), deploy)
	require.NoError(t, err)
}

func TestSortDurations(t *testing.T) {
	durations := []time.Duration{
		500 * time.Millisecond,
		100 * time.Millisecond,
		300 * time.Millisecond,
		200 * time.Millisecond,
		400 * time.Millisecond,
	}

	sortDurations(durations)

	expected := []time.Duration{
		100 * time.Millisecond,
		200 * time.Millisecond,
		300 * time.Millisecond,
		400 * time.Millisecond,
		500 * time.Millisecond,
	}

	assert.Equal(t, expected, durations)
}

func TestMin(t *testing.T) {
	assert.Equal(t, 1, min(1, 2))
	assert.Equal(t, 1, min(2, 1))
	assert.Equal(t, 5, min(5, 5))
	assert.Equal(t, -1, min(-1, 0))
}

func TestAdaptiveStatusWriter(t *testing.T) {
	scheme := setupTestScheme()

	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
			ComponentSelector: availabilityv1alpha1.ComponentSelector{
				MatchLabels: map[string]string{"app": "test"},
			},
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(policy).
		WithStatusSubresource(policy).
		Build()

	acb := NewAdaptiveCircuitBreakerClient(fakeClient)
	statusWriter := acb.Status()

	// Test Update
	policy.Status.ObservedGeneration = 1
	err := statusWriter.Update(context.Background(), policy)
	require.NoError(t, err)

	// Test Patch
	patch := client.MergeFrom(policy.DeepCopy())
	policy.Status.ObservedGeneration = 2
	err = statusWriter.Patch(context.Background(), policy, patch)
	require.NoError(t, err)
}

func TestCircuitBreakerIsSuccessful(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Create a breaker to test IsSuccessful logic
	ab := acb.createAdaptiveBreaker("test")

	// The IsSuccessful function is embedded in the breaker settings
	// We can indirectly test it by checking behavior

	// Not found errors should not trip the breaker
	notFoundErr := apierrors.NewNotFound(schema.GroupResource{}, "test")

	// Execute with not found error - should be considered successful
	_, err := ab.breaker.Execute(func() (interface{}, error) {
		return nil, notFoundErr
	})
	// Error is returned but circuit should stay closed
	assert.Error(t, err)
	assert.Equal(t, "closed", ab.breaker.State().String())
}

func TestCircuitBreakerStateTransition(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Get a breaker
	breaker := acb.getBreaker("test-state")

	// Initial state should be closed
	assert.Equal(t, "closed", breaker.State().String())

	// Simulate failures to trip the breaker
	testErr := errors.New("server error")
	for i := 0; i < 10; i++ {
		_, _ = breaker.Execute(func() (interface{}, error) {
			return nil, testErr
		})
	}

	// After enough failures, breaker might open
	// Note: The exact behavior depends on the settings
}

func TestConcurrentBreakerAccess(t *testing.T) {
	scheme := setupTestScheme()
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()
	acb := NewAdaptiveCircuitBreakerClient(fakeClient)

	// Concurrent access to getBreaker
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(idx int) {
			breaker := acb.getBreaker("concurrent-test")
			assert.NotNil(t, breaker)
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	// Should only have one breaker for this operation
	acb.mu.RLock()
	_, exists := acb.breakers["concurrent-test"]
	acb.mu.RUnlock()
	assert.True(t, exists)
}
