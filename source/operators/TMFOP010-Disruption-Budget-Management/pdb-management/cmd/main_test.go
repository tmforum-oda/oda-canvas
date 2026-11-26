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

package main

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGetEnvOrDefault(t *testing.T) {
	tests := []struct {
		name         string
		key          string
		defaultValue string
		envValue     string
		expected     string
	}{
		{
			name:         "returns default when env not set",
			key:          "TEST_ENV_VAR_NOT_SET",
			defaultValue: "default",
			envValue:     "",
			expected:     "default",
		},
		{
			name:         "returns env value when set",
			key:          "TEST_ENV_VAR_SET",
			defaultValue: "default",
			envValue:     "custom",
			expected:     "custom",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue != "" {
				t.Setenv(tt.key, tt.envValue)
			}
			result := getEnvOrDefault(tt.key, tt.defaultValue)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGetBuildVersion(t *testing.T) {
	// Save original value
	originalVersion := getBuildVersion()

	tests := []struct {
		name     string
		envValue string
		expected string
	}{
		{
			name:     "returns dev when not set",
			envValue: "",
			expected: "dev",
		},
		{
			name:     "returns version when set",
			envValue: "v1.0.0",
			expected: "v1.0.0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue != "" {
				t.Setenv("BUILD_VERSION", tt.envValue)
			} else {
				t.Setenv("BUILD_VERSION", "")
			}
			result := getBuildVersion()
			assert.Equal(t, tt.expected, result)
		})
	}

	// Restore if needed
	if originalVersion != "dev" {
		t.Setenv("BUILD_VERSION", originalVersion)
	}
}

func TestGetWatchNamespaceDisplay(t *testing.T) {
	tests := []struct {
		name      string
		namespace string
		expected  string
	}{
		{
			name:      "returns all for empty namespace",
			namespace: "",
			expected:  "all",
		},
		{
			name:      "returns namespace when set",
			namespace: "kube-system",
			expected:  "kube-system",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := getWatchNamespaceDisplay(tt.namespace)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestValidateConfiguration(t *testing.T) {
	// Test with default values
	t.Run("default configuration", func(t *testing.T) {
		config := validateConfiguration()
		assert.Equal(t, "default", config.DefaultNamespace)
		assert.Equal(t, "canvas", config.MetricsNamespace)
		assert.Equal(t, "canvas", config.LeaderElectionNamespace)
	})

	// Test with custom values
	t.Run("custom configuration", func(t *testing.T) {
		t.Setenv("DEFAULT_NAMESPACE", "custom")
		t.Setenv("METRICS_NAMESPACE", "monitoring")
		t.Setenv("LEADER_ELECTION_NAMESPACE", "operators")

		config := validateConfiguration()
		assert.Equal(t, "custom", config.DefaultNamespace)
		assert.Equal(t, "monitoring", config.MetricsNamespace)
		assert.Equal(t, "operators", config.LeaderElectionNamespace)
	})
}

func TestNewGracefulShutdownManager(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	assert.NotNil(t, gsm)
	assert.Equal(t, 30*time.Second, gsm.shutdownTimeout)
	assert.Nil(t, gsm.preShutdownHooks)
	assert.False(t, gsm.isShuttingDown)
}

func TestGracefulShutdownManagerAddPreShutdownHook(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	// Add first hook
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		return nil
	})

	assert.Len(t, gsm.preShutdownHooks, 1)

	// Add second hook
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		return nil
	})

	assert.Len(t, gsm.preShutdownHooks, 2)
}

func TestGracefulShutdownManagerRunPreShutdownHooks(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	// Track hook execution order
	var executionOrder []int
	var mu sync.Mutex

	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		executionOrder = append(executionOrder, 1)
		mu.Unlock()
		return nil
	})

	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		executionOrder = append(executionOrder, 2)
		mu.Unlock()
		return nil
	})

	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		executionOrder = append(executionOrder, 3)
		mu.Unlock()
		return nil
	})

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	gsm.runPreShutdownHooks(ctx)

	assert.Equal(t, []int{1, 2, 3}, executionOrder)
}

func TestGracefulShutdownManagerRunPreShutdownHooksWithError(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	hooksCalled := 0
	var mu sync.Mutex

	// Hook that succeeds
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		hooksCalled++
		mu.Unlock()
		return nil
	})

	// Hook that fails
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		hooksCalled++
		mu.Unlock()
		return errors.New("hook failed")
	})

	// Hook that succeeds (should still be called after error)
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		mu.Lock()
		hooksCalled++
		mu.Unlock()
		return nil
	})

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Should not panic even with errors
	gsm.runPreShutdownHooks(ctx)

	// All hooks should be called even if one fails
	assert.Equal(t, 3, hooksCalled)
}

func TestGracefulShutdownManagerRunPreShutdownHooksEmpty(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Should not panic with no hooks
	gsm.runPreShutdownHooks(ctx)
}

func TestGracefulShutdownManagerConcurrentAddHooks(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	var wg sync.WaitGroup
	hookCount := 100

	// Add hooks concurrently
	for i := 0; i < hookCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			gsm.AddPreShutdownHook(func(ctx context.Context) error {
				return nil
			})
		}()
	}

	wg.Wait()

	// All hooks should be added
	assert.Len(t, gsm.preShutdownHooks, hookCount)
}

func TestConfigurationStructure(t *testing.T) {
	config := Configuration{
		DefaultNamespace:        "test-default",
		MetricsNamespace:        "test-metrics",
		LeaderElectionNamespace: "test-leader",
	}

	assert.Equal(t, "test-default", config.DefaultNamespace)
	assert.Equal(t, "test-metrics", config.MetricsNamespace)
	assert.Equal(t, "test-leader", config.LeaderElectionNamespace)
}

func TestGracefulShutdownManagerIsShuttingDown(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	// Initially not shutting down
	gsm.mu.RLock()
	assert.False(t, gsm.isShuttingDown)
	gsm.mu.RUnlock()

	// Simulate setting shutdown state
	gsm.mu.Lock()
	gsm.isShuttingDown = true
	gsm.mu.Unlock()

	gsm.mu.RLock()
	assert.True(t, gsm.isShuttingDown)
	gsm.mu.RUnlock()
}

func TestGracefulShutdownManagerHookTimeout(t *testing.T) {
	gsm := NewGracefulShutdownManager(nil, 30*time.Second)

	hookStarted := make(chan struct{})
	hookFinished := make(chan struct{})

	// Add a hook that checks context cancellation
	gsm.AddPreShutdownHook(func(ctx context.Context) error {
		close(hookStarted)
		select {
		case <-ctx.Done():
			close(hookFinished)
			return ctx.Err()
		case <-time.After(5 * time.Second):
			close(hookFinished)
			return nil
		}
	})

	// Use a very short timeout
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	go gsm.runPreShutdownHooks(ctx)

	// Wait for hook to start
	select {
	case <-hookStarted:
		// Hook started
	case <-time.After(1 * time.Second):
		t.Fatal("Hook did not start in time")
	}

	// Wait for hook to finish (due to context timeout)
	select {
	case <-hookFinished:
		// Hook finished
	case <-time.After(2 * time.Second):
		t.Fatal("Hook did not finish in time")
	}
}

func TestSchemeRegistration(t *testing.T) {
	// Verify scheme is not nil
	require.NotNil(t, scheme)

	// The scheme should have been initialized with clientgoscheme and our custom types
	// This is tested implicitly by the init() function running without panic
}

func TestPrintStartupBanner(t *testing.T) {
	// Should not panic
	printStartupBanner()
}
