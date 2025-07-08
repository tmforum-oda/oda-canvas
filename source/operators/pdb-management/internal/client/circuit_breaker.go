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
	"fmt"
	"math"
	"sync"
	"sync/atomic"
	"time"

	"github.com/sony/gobreaker"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
)

// AdaptiveCircuitBreakerClient wraps the Kubernetes client with an adaptive circuit breaker
type AdaptiveCircuitBreakerClient struct {
	client.Client
	breakers  map[string]*adaptiveBreaker
	mu        sync.RWMutex
	metrics   *clusterMetrics
	config    *adaptiveConfig
	startTime time.Time
}

// adaptiveBreaker wraps a circuit breaker with adaptive settings
type adaptiveBreaker struct {
	breaker      *gobreaker.CircuitBreaker
	settings     *adaptiveSettings
	lastAdjusted time.Time
	mu           sync.RWMutex
}

// adaptiveSettings holds dynamic circuit breaker settings
type adaptiveSettings struct {
	maxRequests           uint32
	timeout               time.Duration
	failureRatioThreshold float64
	consecutiveFailures   uint32
	interval              time.Duration
}

// clusterMetrics tracks cluster performance metrics
type clusterMetrics struct {
	responseTimeP50 atomic.Value // time.Duration
	responseTimeP95 atomic.Value // time.Duration
	responseTimeP99 atomic.Value // time.Duration
	errorRate       atomic.Value // float64
	throughput      atomic.Value // float64
	samples         []metricSample
	sampleMu        sync.RWMutex
	lastCalculation time.Time
}

// metricSample represents a single operation metric
type metricSample struct {
	timestamp time.Time
	duration  time.Duration
	operation string
	success   bool
	errorType string
}

// adaptiveConfig holds configuration for adaptive behavior
type adaptiveConfig struct {
	// Base settings (conservative defaults)
	baseMaxRequests         uint32
	baseTimeout             time.Duration
	baseFailureRatio        float64
	baseConsecutiveFailures uint32

	// Adaptation parameters
	learningPeriod        time.Duration
	adjustmentInterval    time.Duration
	maxTimeoutMultiplier  float64
	minTimeoutMultiplier  float64
	sampleRetentionPeriod time.Duration
}

// NewAdaptiveCircuitBreakerClient creates a new adaptive circuit breaker client
func NewAdaptiveCircuitBreakerClient(c client.Client) *AdaptiveCircuitBreakerClient {
	acb := &AdaptiveCircuitBreakerClient{
		Client:    c,
		breakers:  make(map[string]*adaptiveBreaker),
		metrics:   newClusterMetrics(),
		config:    getDefaultAdaptiveConfig(),
		startTime: time.Now(),
	}

	// Start metrics calculator
	go acb.metricsCalculator()

	// Start settings adjuster
	go acb.settingsAdjuster()

	// Perform initial cluster probe
	go acb.probeClusterPerformance()

	return acb
}

func getDefaultAdaptiveConfig() *adaptiveConfig {
	return &adaptiveConfig{
		baseMaxRequests:         5,
		baseTimeout:             30 * time.Second,
		baseFailureRatio:        0.6,
		baseConsecutiveFailures: 5,
		learningPeriod:          2 * time.Minute,
		adjustmentInterval:      30 * time.Second,
		maxTimeoutMultiplier:    3.0,
		minTimeoutMultiplier:    0.5,
		sampleRetentionPeriod:   5 * time.Minute,
	}
}

func newClusterMetrics() *clusterMetrics {
	cm := &clusterMetrics{
		samples: make([]metricSample, 0, 1000),
	}
	// Initialize with conservative defaults
	cm.responseTimeP50.Store(100 * time.Millisecond)
	cm.responseTimeP95.Store(500 * time.Millisecond)
	cm.responseTimeP99.Store(1 * time.Second)
	cm.errorRate.Store(0.0)
	cm.throughput.Store(10.0)
	return cm
}

// probeClusterPerformance performs initial cluster performance assessment
func (acb *AdaptiveCircuitBreakerClient) probeClusterPerformance() {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	logger := log.Log.WithName("adaptive-circuit-breaker")
	logger.Info("Probing cluster performance...")

	// Perform a series of lightweight operations to gauge cluster performance
	operations := []struct {
		name string
		fn   func() error
	}{
		{
			name: "list-namespaces",
			fn: func() error {
				// List namespaces is a lightweight operation
				namespaceList := &corev1.NamespaceList{}
				return acb.Client.List(ctx, namespaceList, client.Limit(1))
			},
		},
		{
			name: "list-deployments",
			fn: func() error {
				// List deployments in default namespace
				deployList := &appsv1.DeploymentList{}
				return acb.Client.List(ctx, deployList, client.InNamespace("default"), client.Limit(1))
			},
		},
		{
			name: "list-policies",
			fn: func() error {
				// List our own CRDs - we should have permission for this
				policyList := &availabilityv1alpha1.AvailabilityPolicyList{}
				return acb.Client.List(ctx, policyList, client.Limit(1))
			},
		},
	}

	// Run each operation multiple times to get a baseline
	for _, op := range operations {
		for i := 0; i < 5; i++ {
			start := time.Now()
			err := op.fn()
			duration := time.Since(start)

			acb.recordMetric(op.name, duration, err)

			// Small delay between probes
			time.Sleep(100 * time.Millisecond)
		}
	}

	logger.Info("Cluster performance probe completed")
}

// recordMetric records an operation metric
func (acb *AdaptiveCircuitBreakerClient) recordMetric(operation string, duration time.Duration, err error) {
	sample := metricSample{
		timestamp: time.Now(),
		duration:  duration,
		operation: operation,
		success:   err == nil,
	}

	if err != nil {
		sample.errorType = fmt.Sprintf("%T", err)
	}

	acb.metrics.sampleMu.Lock()
	acb.metrics.samples = append(acb.metrics.samples, sample)

	// Limit sample size
	if len(acb.metrics.samples) > 10000 {
		// Remove oldest samples
		acb.metrics.samples = acb.metrics.samples[5000:]
	}
	acb.metrics.sampleMu.Unlock()
}

// metricsCalculator periodically calculates performance metrics
func (acb *AdaptiveCircuitBreakerClient) metricsCalculator() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		acb.calculateMetrics()
	}
}

// calculateMetrics calculates current performance metrics
func (acb *AdaptiveCircuitBreakerClient) calculateMetrics() {
	acb.metrics.sampleMu.RLock()
	samples := make([]metricSample, len(acb.metrics.samples))
	copy(samples, acb.metrics.samples)
	acb.metrics.sampleMu.RUnlock()

	if len(samples) < 10 {
		return // Not enough samples
	}

	// Calculate metrics for recent samples (last minute)
	cutoff := time.Now().Add(-1 * time.Minute)
	recentSamples := make([]metricSample, 0)

	for _, s := range samples {
		if s.timestamp.After(cutoff) {
			recentSamples = append(recentSamples, s)
		}
	}

	if len(recentSamples) == 0 {
		return
	}

	// Calculate response time percentiles
	durations := make([]time.Duration, 0, len(recentSamples))
	successCount := 0

	for _, s := range recentSamples {
		if s.success {
			durations = append(durations, s.duration)
			successCount++
		}
	}

	if len(durations) > 0 {
		// Sort durations
		sortDurations(durations)

		// Calculate percentiles
		p50 := durations[len(durations)*50/100]
		p95 := durations[len(durations)*95/100]
		p99 := durations[min(len(durations)*99/100, len(durations)-1)]

		acb.metrics.responseTimeP50.Store(p50)
		acb.metrics.responseTimeP95.Store(p95)
		acb.metrics.responseTimeP99.Store(p99)
	}

	// Calculate error rate
	errorRate := float64(len(recentSamples)-successCount) / float64(len(recentSamples))
	acb.metrics.errorRate.Store(errorRate)

	// Calculate throughput (requests per second)
	if len(recentSamples) > 1 {
		timeSpan := recentSamples[len(recentSamples)-1].timestamp.Sub(recentSamples[0].timestamp)
		if timeSpan > 0 {
			throughput := float64(len(recentSamples)) / timeSpan.Seconds()
			acb.metrics.throughput.Store(throughput)
		}
	}

	acb.metrics.lastCalculation = time.Now()
}

// settingsAdjuster periodically adjusts circuit breaker settings based on metrics
func (acb *AdaptiveCircuitBreakerClient) settingsAdjuster() {
	ticker := time.NewTicker(acb.config.adjustmentInterval)
	defer ticker.Stop()

	// Wait for learning period
	time.Sleep(acb.config.learningPeriod)

	for range ticker.C {
		acb.adjustSettings()
	}
}

// adjustSettings adjusts circuit breaker settings based on current metrics
func (acb *AdaptiveCircuitBreakerClient) adjustSettings() {
	// Don't adjust during the learning period
	if time.Since(acb.startTime) < acb.config.learningPeriod {
		return
	}

	logger := log.Log.WithName("adaptive-circuit-breaker")

	// Get current metrics
	p50 := acb.metrics.responseTimeP50.Load().(time.Duration)
	p95 := acb.metrics.responseTimeP95.Load().(time.Duration)
	p99 := acb.metrics.responseTimeP99.Load().(time.Duration)
	errorRate := acb.metrics.errorRate.Load().(float64)
	throughput := acb.metrics.throughput.Load().(float64)

	logger.V(1).Info("Current cluster metrics",
		"p50", p50,
		"p95", p95,
		"p99", p99,
		"errorRate", fmt.Sprintf("%.2f%%", errorRate*100),
		"throughput", fmt.Sprintf("%.2f req/s", throughput))

	// Calculate new settings
	newSettings := acb.calculateNewSettings(p50, p95, p99, errorRate, throughput)

	// Apply new settings to all breakers
	acb.mu.RLock()
	defer acb.mu.RUnlock()

	for operation, ab := range acb.breakers {
		ab.updateSettings(newSettings, operation)
	}
}

// calculateNewSettings calculates new circuit breaker settings based on metrics
func (acb *AdaptiveCircuitBreakerClient) calculateNewSettings(p50, p95, p99 time.Duration, errorRate, throughput float64) *adaptiveSettings {
	settings := &adaptiveSettings{
		maxRequests:           acb.config.baseMaxRequests,
		timeout:               acb.config.baseTimeout,
		failureRatioThreshold: acb.config.baseFailureRatio,
		consecutiveFailures:   acb.config.baseConsecutiveFailures,
		interval:              2 * time.Minute,
	}

	// Adjust timeout based on P99 latency
	// Timeout should be at least 2x P99 to avoid false positives
	timeoutMultiplier := 2.5
	if errorRate > 0.1 {
		// If error rate is high, be more conservative
		timeoutMultiplier = 3.0
	}

	calculatedTimeout := time.Duration(float64(p99) * timeoutMultiplier)

	// Apply bounds
	minTimeout := time.Duration(float64(acb.config.baseTimeout) * acb.config.minTimeoutMultiplier)
	maxTimeout := time.Duration(float64(acb.config.baseTimeout) * acb.config.maxTimeoutMultiplier)

	if calculatedTimeout < minTimeout {
		settings.timeout = minTimeout
	} else if calculatedTimeout > maxTimeout {
		settings.timeout = maxTimeout
	} else {
		settings.timeout = calculatedTimeout
	}

	// Adjust failure ratio threshold based on current error rate
	if errorRate < 0.05 {
		// Low error rate, can be stricter
		settings.failureRatioThreshold = 0.5
	} else if errorRate < 0.1 {
		// Moderate error rate
		settings.failureRatioThreshold = 0.6
	} else {
		// High error rate, be more tolerant
		settings.failureRatioThreshold = 0.7
	}

	// Adjust max requests based on throughput
	if throughput > 50 {
		// High throughput cluster
		settings.maxRequests = 20
	} else if throughput > 20 {
		// Medium throughput
		settings.maxRequests = 10
	} else {
		// Low throughput, keep conservative
		settings.maxRequests = 5
	}

	// Adjust consecutive failures based on cluster stability
	if errorRate < 0.02 && p95 < 200*time.Millisecond {
		// Very stable cluster
		settings.consecutiveFailures = 3
	} else if errorRate < 0.05 {
		// Stable cluster
		settings.consecutiveFailures = 5
	} else {
		// Less stable, be more tolerant
		settings.consecutiveFailures = 10
	}

	return settings
}

// getBreaker gets or creates a circuit breaker for the operation
func (acb *AdaptiveCircuitBreakerClient) getBreaker(operation string) *gobreaker.CircuitBreaker {
	acb.mu.RLock()
	ab, exists := acb.breakers[operation]
	acb.mu.RUnlock()

	if exists {
		return ab.breaker
	}

	acb.mu.Lock()
	defer acb.mu.Unlock()

	// Double-check
	if ab, exists := acb.breakers[operation]; exists {
		return ab.breaker
	}

	// Create new adaptive breaker
	ab = acb.createAdaptiveBreaker(operation)
	acb.breakers[operation] = ab

	return ab.breaker
}

// createAdaptiveBreaker creates a new adaptive circuit breaker
func (acb *AdaptiveCircuitBreakerClient) createAdaptiveBreaker(operation string) *adaptiveBreaker {
	// Get current metrics to inform initial settings
	var initialSettings *adaptiveSettings

	if time.Since(acb.startTime) > acb.config.learningPeriod {
		// We have metrics, use them
		p50 := acb.metrics.responseTimeP50.Load().(time.Duration)
		p95 := acb.metrics.responseTimeP95.Load().(time.Duration)
		p99 := acb.metrics.responseTimeP99.Load().(time.Duration)
		errorRate := acb.metrics.errorRate.Load().(float64)
		throughput := acb.metrics.throughput.Load().(float64)

		initialSettings = acb.calculateNewSettings(p50, p95, p99, errorRate, throughput)
	} else {
		// Use conservative defaults during learning period
		initialSettings = &adaptiveSettings{
			maxRequests:           acb.config.baseMaxRequests,
			timeout:               acb.config.baseTimeout,
			failureRatioThreshold: acb.config.baseFailureRatio,
			consecutiveFailures:   acb.config.baseConsecutiveFailures,
			interval:              2 * time.Minute,
		}
	}

	// Customize based on operation type
	switch operation {
	case "list":
		initialSettings.timeout = time.Duration(float64(initialSettings.timeout) * 1.5)
	case "create", "update":
		initialSettings.timeout = time.Duration(float64(initialSettings.timeout) * 1.2)
	}

	logger := log.Log.WithName("adaptive-circuit-breaker")

	settings := gobreaker.Settings{
		Name:        operation,
		MaxRequests: initialSettings.maxRequests,
		Interval:    initialSettings.interval,
		Timeout:     initialSettings.timeout,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			if counts.Requests < 3 {
				return false
			}

			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return failureRatio >= initialSettings.failureRatioThreshold ||
				counts.ConsecutiveFailures >= initialSettings.consecutiveFailures
		},
		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			switch to {
			case gobreaker.StateOpen:
				logger.Error(nil, "Circuit breaker opened",
					"operation", name,
					"timeout", initialSettings.timeout,
					"threshold", initialSettings.failureRatioThreshold)
			case gobreaker.StateClosed:
				logger.Info("Circuit breaker closed",
					"operation", name)
			}
		},
		IsSuccessful: func(err error) bool {
			if err == nil {
				return true
			}

			// Don't count certain errors as failures
			if client.IgnoreNotFound(err) == nil {
				return true
			}

			errStr := err.Error()
			if errStr == "conflict" || errStr == "the object has been modified" {
				return true
			}

			return false
		},
	}

	return &adaptiveBreaker{
		breaker:      gobreaker.NewCircuitBreaker(settings),
		settings:     initialSettings,
		lastAdjusted: time.Now(),
	}
}

// updateSettings updates the settings for an adaptive breaker
func (ab *adaptiveBreaker) updateSettings(newSettings *adaptiveSettings, operation string) {
	ab.mu.Lock()
	defer ab.mu.Unlock()

	// Only update if settings have changed significantly
	if ab.shouldUpdate(newSettings) {
		// Circuit breaker doesn't support dynamic updates, so we log for monitoring
		log.Log.WithName("adaptive-circuit-breaker").V(1).Info("Settings adjusted",
			"operation", operation,
			"oldTimeout", ab.settings.timeout,
			"newTimeout", newSettings.timeout,
			"oldThreshold", ab.settings.failureRatioThreshold,
			"newThreshold", newSettings.failureRatioThreshold)

		ab.settings = newSettings
		ab.lastAdjusted = time.Now()
	}
}

// shouldUpdate determines if settings should be updated
func (ab *adaptiveBreaker) shouldUpdate(newSettings *adaptiveSettings) bool {
	// Don't update too frequently
	if time.Since(ab.lastAdjusted) < 1*time.Minute {
		return false
	}

	// Check if there's a significant change
	timeoutChange := math.Abs(float64(newSettings.timeout-ab.settings.timeout)) / float64(ab.settings.timeout)
	thresholdChange := math.Abs(newSettings.failureRatioThreshold - ab.settings.failureRatioThreshold)

	return timeoutChange > 0.2 || thresholdChange > 0.1
}

// Client interface implementations with metrics recording

func (acb *AdaptiveCircuitBreakerClient) Get(ctx context.Context, key client.ObjectKey, obj client.Object, opts ...client.GetOption) error {
	breaker := acb.getBreaker("get")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.Get(ctx, key, obj, opts...)
	})

	acb.recordMetric("get", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) List(ctx context.Context, list client.ObjectList, opts ...client.ListOption) error {
	breaker := acb.getBreaker("list")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.List(ctx, list, opts...)
	})

	acb.recordMetric("list", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) Create(ctx context.Context, obj client.Object, opts ...client.CreateOption) error {
	breaker := acb.getBreaker("create")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.Create(ctx, obj, opts...)
	})

	acb.recordMetric("create", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) Update(ctx context.Context, obj client.Object, opts ...client.UpdateOption) error {
	breaker := acb.getBreaker("update")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.Update(ctx, obj, opts...)
	})

	acb.recordMetric("update", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) Delete(ctx context.Context, obj client.Object, opts ...client.DeleteOption) error {
	breaker := acb.getBreaker("delete")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.Delete(ctx, obj, opts...)
	})

	acb.recordMetric("delete", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) Patch(ctx context.Context, obj client.Object, patch client.Patch, opts ...client.PatchOption) error {
	breaker := acb.getBreaker("patch")

	start := time.Now()
	_, err := breaker.Execute(func() (interface{}, error) {
		return nil, acb.Client.Patch(ctx, obj, patch, opts...)
	})

	acb.recordMetric("patch", time.Since(start), err)
	return err
}

func (acb *AdaptiveCircuitBreakerClient) Status() client.StatusWriter {
	return &adaptiveStatusWriter{
		statusWriter: acb.Client.Status(),
		breaker:      acb.getBreaker("status"),
		recorder:     acb.recordMetric,
	}
}

// adaptiveStatusWriter wraps StatusWriter with adaptive circuit breaker
type adaptiveStatusWriter struct {
	statusWriter client.StatusWriter
	breaker      *gobreaker.CircuitBreaker
	recorder     func(string, time.Duration, error)
}

func (w *adaptiveStatusWriter) Create(ctx context.Context, obj client.Object, subResource client.Object, opts ...client.SubResourceCreateOption) error {
	start := time.Now()
	_, err := w.breaker.Execute(func() (interface{}, error) {
		return nil, w.statusWriter.Create(ctx, obj, subResource, opts...)
	})
	w.recorder("status-create", time.Since(start), err)
	return err
}

func (w *adaptiveStatusWriter) Update(ctx context.Context, obj client.Object, opts ...client.SubResourceUpdateOption) error {
	start := time.Now()
	_, err := w.breaker.Execute(func() (interface{}, error) {
		return nil, w.statusWriter.Update(ctx, obj, opts...)
	})
	w.recorder("status-update", time.Since(start), err)
	return err
}

func (w *adaptiveStatusWriter) Patch(ctx context.Context, obj client.Object, patch client.Patch, opts ...client.SubResourcePatchOption) error {
	start := time.Now()
	_, err := w.breaker.Execute(func() (interface{}, error) {
		return nil, w.statusWriter.Patch(ctx, obj, patch, opts...)
	})
	w.recorder("status-patch", time.Since(start), err)
	return err
}

// Helper functions

func sortDurations(durations []time.Duration) {
	// Simple insertion sort for small arrays
	for i := 1; i < len(durations); i++ {
		key := durations[i]
		j := i - 1
		for j >= 0 && durations[j] > key {
			durations[j+1] = durations[j]
			j--
		}
		durations[j+1] = key
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
