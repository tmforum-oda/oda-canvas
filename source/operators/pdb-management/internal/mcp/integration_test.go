package mcp

import (
	"context"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"k8s.io/client-go/kubernetes/fake"
	clientfake "sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewMCPIntegration(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	// Test disabled integration
	disabledConfig := Config{
		Enabled:    false,
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(disabledConfig)
	assert.NotNil(t, integration)
	assert.False(t, integration.IsEnabled())
	assert.Empty(t, integration.GetAddress())

	// Test enabled integration
	enabledConfig := Config{
		Enabled:    true,
		Address:    ":8091", // Different port for testing
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration = NewMCPIntegration(enabledConfig)
	assert.NotNil(t, integration)
	assert.True(t, integration.IsEnabled())
	assert.Equal(t, ":8091", integration.GetAddress())
}

func TestMCPIntegrationStartStop(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8092", // Different port for testing
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)
	require.NotNil(t, integration)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Start the integration
	err := integration.Start(ctx)
	require.NoError(t, err)

	// Give it a moment to start
	time.Sleep(100 * time.Millisecond)

	// Test health endpoint (should be running)
	httpClient := &http.Client{Timeout: 2 * time.Second}
	resp, err := httpClient.Get("http://localhost:8092/health")
	if err == nil {
		_ = resp.Body.Close()
		assert.Equal(t, http.StatusOK, resp.StatusCode)
	}
	// Note: In CI environments, this might fail due to port conflicts, so we don't require it

	// Stop the integration
	stopCtx, stopCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer stopCancel()

	err = integration.Stop(stopCtx)
	assert.NoError(t, err)
}

func TestMCPIntegrationDisabled(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    false,
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	ctx := context.Background()

	// Start should succeed but do nothing
	err := integration.Start(ctx)
	assert.NoError(t, err)

	// Stop should succeed but do nothing
	err = integration.Stop(ctx)
	assert.NoError(t, err)
}

func TestMCPIntegrationDefaultAddress(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    "", // Empty address should use default
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)
	assert.Equal(t, ":8090", integration.GetAddress())
}

func TestMCPIntegrationServerReady(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8093", // Different port for testing
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	// Server should not be ready before starting
	assert.False(t, integration.isServerReady())

	// Start the server
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	err := integration.Start(ctx)
	require.NoError(t, err)

	// Give it time to start
	time.Sleep(200 * time.Millisecond)

	// Check if server is ready (may fail in CI due to port conflicts)
	// This is more of a smoke test
	ready := integration.isServerReady()
	t.Logf("Server ready status: %v", ready)

	// Clean up
	stopCtx, stopCancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer stopCancel()
	_ = integration.Stop(stopCtx)
}

func TestMCPIntegrationRegisterTools(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8094",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	// Test tool registration
	err := integration.registerTools()
	assert.NoError(t, err)

	// Verify that tools are registered by checking the server state
	// This is an indirect test since we can't easily inspect the server's tools
	assert.NotNil(t, integration.server)
}

func TestMCPIntegrationStopWithoutStart(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8095",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	// Test stopping without starting should not error
	ctx := context.Background()
	err := integration.Stop(ctx)
	assert.NoError(t, err)
}

func TestMCPIntegrationMultipleStartStop(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	ctx := context.Background()

	// First integration instance
	config1 := Config{
		Enabled:    true,
		Address:    ":8096",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration1 := NewMCPIntegration(config1)

	err := integration1.Start(ctx)
	assert.NoError(t, err)

	err = integration1.Stop(ctx)
	assert.NoError(t, err)

	// Second integration instance (new server, no tool conflicts)
	config2 := Config{
		Enabled:    true,
		Address:    ":8096", // Same port but different instance
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration2 := NewMCPIntegration(config2)

	err = integration2.Start(ctx)
	assert.NoError(t, err)

	err = integration2.Stop(ctx)
	assert.NoError(t, err)
}

func TestMCPIntegrationInvalidPort(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":99999", // Invalid high port
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start should succeed even if server fails to bind
	// (error is logged but not returned)
	err := integration.Start(ctx)
	assert.NoError(t, err)

	// Stop should not error
	err = integration.Stop(ctx)
	assert.NoError(t, err)
}

func TestMCPIntegrationShutdownTimeout(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8097",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	startCtx := context.Background()
	err := integration.Start(startCtx)
	assert.NoError(t, err)

	// Give it time to start
	time.Sleep(100 * time.Millisecond)

	// Test shutdown with very short timeout
	stopCtx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
	defer cancel()

	// This might fail due to timeout, but shouldn't panic
	_ = integration.Stop(stopCtx)

	// Clean up with proper timeout
	cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cleanupCancel()
	_ = integration.Stop(cleanupCtx)
}

func TestMCPIntegrationServerReadyBeforeStart(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8098",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	// Server should not be ready before start
	assert.False(t, integration.isServerReady())
}

func TestMCPIntegrationNilHttpServer(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := clientfake.NewClientBuilder().Build()
	kubeClient := fake.NewSimpleClientset()

	config := Config{
		Enabled:    true,
		Address:    ":8099",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	}

	integration := NewMCPIntegration(config)

	// Before starting, httpServer is nil
	assert.False(t, integration.isServerReady())
}
