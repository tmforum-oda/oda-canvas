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
	"testing"

	"github.com/stretchr/testify/assert"
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

func TestGetEnvBool(t *testing.T) {
	tests := []struct {
		name         string
		key          string
		defaultValue bool
		envValue     string
		expected     bool
	}{
		{
			name:         "returns default when env not set",
			key:          "TEST_BOOL_VAR_NOT_SET",
			defaultValue: true,
			envValue:     "",
			expected:     true,
		},
		{
			name:         "returns true when env is true",
			key:          "TEST_BOOL_VAR_TRUE",
			defaultValue: false,
			envValue:     "true",
			expected:     true,
		},
		{
			name:         "returns false when env is not true",
			key:          "TEST_BOOL_VAR_FALSE",
			defaultValue: true,
			envValue:     "false",
			expected:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue != "" {
				t.Setenv(tt.key, tt.envValue)
			}
			result := getEnvBool(tt.key, tt.defaultValue)
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
	// Save original values
	originalPDB := getEnvOrDefault("ENABLE_PDB", "")

	// Test with default values
	t.Run("default configuration", func(t *testing.T) {
		t.Setenv("ENABLE_PDB", "")
		config := validateConfiguration()
		assert.True(t, config.EnablePDB)
		assert.Equal(t, "default", config.DefaultNamespace)
		assert.Equal(t, "canvas", config.MetricsNamespace)
		assert.Equal(t, "canvas", config.LeaderElectionNamespace)
	})

	// Test with custom values
	t.Run("custom configuration", func(t *testing.T) {
		t.Setenv("ENABLE_PDB", "false")
		t.Setenv("DEFAULT_NAMESPACE", "custom")
		t.Setenv("METRICS_NAMESPACE", "monitoring")
		t.Setenv("LEADER_ELECTION_NAMESPACE", "operators")

		config := validateConfiguration()
		assert.False(t, config.EnablePDB)
		assert.Equal(t, "custom", config.DefaultNamespace)
		assert.Equal(t, "monitoring", config.MetricsNamespace)
		assert.Equal(t, "operators", config.LeaderElectionNamespace)
	})

	// Restore original values
	if originalPDB != "" {
		t.Setenv("ENABLE_PDB", originalPDB)
	}
}
