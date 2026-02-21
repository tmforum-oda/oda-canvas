package transport

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/ai"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/server"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	kfake "k8s.io/client-go/kubernetes/fake"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

// testCORSConfig returns a config with wildcard CORS for testing
func testCORSConfig() HTTPTransportConfig {
	return HTTPTransportConfig{
		AllowedOrigins: []string{"*"},
	}
}

func TestNewHTTPTransport(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)
	assert.NotNil(t, transport)
	assert.NotNil(t, transport.server)
	assert.NotNil(t, transport.logger)
	assert.NotNil(t, transport.mux)
}

func TestHandleHealth(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test health endpoint
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	transport.handleHealth(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "application/json", resp.Header.Get("Content-Type"))

	var health map[string]interface{}
	err := json.NewDecoder(resp.Body).Decode(&health)
	require.NoError(t, err)

	assert.Equal(t, "healthy", health["status"])
	assert.Equal(t, false, health["initialized"]) // Server not initialized yet
	assert.NotNil(t, health["timestamp"])
}

func TestHandleMCPRequest_Success(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Create a valid MCP request
	mcpReq := types.Request{
		ID:      "test-123",
		Method:  "initialize",
		Params:  json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		Created: time.Now(),
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "application/json", resp.Header.Get("Content-Type"))

	var mcpResp types.Response
	err = json.NewDecoder(resp.Body).Decode(&mcpResp)
	require.NoError(t, err)

	assert.Equal(t, "test-123", mcpResp.ID)
	assert.Nil(t, mcpResp.Error)
	assert.NotNil(t, mcpResp.Result)
}

func TestHandleMCPRequest_InvalidMethod(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test with GET method (should be POST)
	req := httptest.NewRequest(http.MethodGet, "/mcp", nil)
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)
}

func TestHandleMCPRequest_InvalidJSON(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Send invalid JSON
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleMCPRequest_UnknownMethod(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Create request with unknown method
	mcpReq := types.Request{
		ID:      "test-456",
		Method:  "unknown/method",
		Created: time.Now(),
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode) // Still returns 200 with error in response

	var mcpResp types.Response
	err = json.NewDecoder(resp.Body).Decode(&mcpResp)
	require.NoError(t, err)

	assert.Equal(t, "test-456", mcpResp.ID)
	assert.NotNil(t, mcpResp.Error)
	assert.Equal(t, -32601, mcpResp.Error.Code) // Method not found
}

func TestServeHTTP(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test that ServeHTTP properly routes requests
	tests := []struct {
		path           string
		expectedStatus int
	}{
		{"/health", http.StatusOK},
		{"/mcp", http.StatusMethodNotAllowed}, // GET not allowed
		{"/unknown", http.StatusNotFound},
	}

	for _, tc := range tests {
		t.Run(tc.path, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, tc.path, nil)
			w := httptest.NewRecorder()

			transport.ServeHTTP(w, req)

			resp := w.Result()
			assert.Equal(t, tc.expectedStatus, resp.StatusCode)
		})
	}
}

func TestStartHTTPServer(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Start server in a goroutine with a test port
	// Note: This is a basic test to ensure the function can be called
	// In a real scenario, we would need proper lifecycle management

	done := make(chan bool, 1)
	go func() {
		// Use a random port for testing - will immediately fail to bind
		err := StartHTTPServer(":99999", transport, logger) // Invalid port
		if err != nil {
			t.Logf("Server error (expected in test): %v", err)
		}
		done <- true
	}()

	select {
	case <-done:
		// Server exited (expected due to invalid port)
	case <-time.After(1 * time.Second):
		// Test passes if server doesn't hang
	}
}

func TestHandleMCPRequest_ZeroTimestamp(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Create an MCP request with zero timestamp
	mcpReq := types.Request{
		ID:     "test-zero-timestamp",
		Method: "initialize",
		Params: json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		// Created is zero value
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var mcpResp types.Response
	err = json.NewDecoder(resp.Body).Decode(&mcpResp)
	require.NoError(t, err)

	assert.Equal(t, "test-zero-timestamp", mcpResp.ID)
	assert.Nil(t, mcpResp.Error)
}

func TestHandleMCPRequest_ContextTimeout(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test that context timeout is properly set
	mcpReq := types.Request{
		ID:      "test-context",
		Method:  "initialize",
		Params:  json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		Created: time.Now(),
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestHandleHealth_InitializedServer(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	// Initialize the server first
	initParams := types.InitializeParams{
		ClientInfo: types.ClientInfo{
			Name:    "test-client",
			Version: "v1.0.0",
		},
	}
	paramsJSON, _ := json.Marshal(initParams)
	initReq := &types.Request{
		ID:      "init",
		Method:  "initialize",
		Params:  paramsJSON,
		Created: time.Now(),
	}
	_, _ = mcpServer.HandleRequest(context.Background(), initReq)

	transport := NewHTTPTransport(mcpServer, logger)

	// Test health endpoint with initialized server
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	transport.handleHealth(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "application/json", resp.Header.Get("Content-Type"))

	var health map[string]interface{}
	err := json.NewDecoder(resp.Body).Decode(&health)
	require.NoError(t, err)

	assert.Equal(t, "healthy", health["status"])
	assert.Equal(t, true, health["initialized"])
	assert.NotNil(t, health["timestamp"])
}

func TestHandleMCPRequest_RequestWithExistingTimestamp(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	specificTime := time.Date(2023, 1, 1, 12, 0, 0, 0, time.UTC)
	mcpReq := types.Request{
		ID:      "test-existing-timestamp",
		Method:  "initialize",
		Params:  json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		Created: specificTime,
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	var mcpResp types.Response
	err = json.NewDecoder(resp.Body).Decode(&mcpResp)
	require.NoError(t, err)

	assert.Equal(t, "test-existing-timestamp", mcpResp.ID)
	assert.Nil(t, mcpResp.Error)
}

func TestStartHTTPServer_ValidPort(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test that the server can be started on a valid port
	// We'll start it and immediately close it
	done := make(chan error, 1)
	go func() {
		err := StartHTTPServer(":0", transport, logger) // :0 means any available port
		done <- err
	}()

	// Give the server a moment to start, then we expect it to be running
	select {
	case err := <-done:
		// If it exits immediately, it might be an error binding
		if err != nil {
			t.Logf("Server start error: %v", err)
		}
	case <-time.After(100 * time.Millisecond):
		// Server is likely running, which is what we expect
		// We can't easily stop it in this test, so this is sufficient
	}
}

func TestHandleAIProxy_Success(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransportWithConfig(mcpServer, logger, testCORSConfig())

	// Mock AI API server
	mockAIServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"content": []interface{}{
				map[string]interface{}{
					"type": "text",
					"text": "Hello! How can I help you?",
				},
			},
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(response)
	}))
	defer mockAIServer.Close()

	// Create AI proxy request
	proxyReq := struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}{
		Config: ai.Config{
			Provider: ai.ProviderClaude,
			APIKey:   "test-key",
			BaseURL:  mockAIServer.URL,
		},
		Request: ai.ChatRequest{
			Messages: []ai.Message{
				{Role: "user", Content: "Hello"},
			},
		},
	}

	reqBody, err := json.Marshal(proxyReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "application/json", resp.Header.Get("Content-Type"))
	assert.Equal(t, "http://localhost:3000", resp.Header.Get("Access-Control-Allow-Origin"))

	var response map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	assert.Equal(t, true, response["success"])
	assert.NotNil(t, response["data"])
}

func TestHandleAIProxy_MethodNotAllowed(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Test with GET method (should be POST)
	req := httptest.NewRequest(http.MethodGet, "/ai/proxy", nil)
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)
}

func TestHandleAIProxy_OptionsRequest(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransportWithConfig(mcpServer, logger, testCORSConfig())

	// Test OPTIONS request for CORS
	req := httptest.NewRequest(http.MethodOptions, "/ai/proxy", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "http://localhost:3000", resp.Header.Get("Access-Control-Allow-Origin"))
	assert.Equal(t, "POST, OPTIONS", resp.Header.Get("Access-Control-Allow-Methods"))
	assert.Equal(t, "Content-Type", resp.Header.Get("Access-Control-Allow-Headers"))
}

func TestHandleAIProxy_InvalidJSON(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Send invalid JSON
	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", strings.NewReader("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleAIProxy_MissingProvider(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Request without provider
	proxyReq := struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}{
		Config: ai.Config{
			APIKey: "test-key",
		},
		Request: ai.ChatRequest{
			Messages: []ai.Message{
				{Role: "user", Content: "Hello"},
			},
		},
	}

	reqBody, err := json.Marshal(proxyReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleAIProxy_MissingAPIKey(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Request without API key
	proxyReq := struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}{
		Config: ai.Config{
			Provider: ai.ProviderClaude,
		},
		Request: ai.ChatRequest{
			Messages: []ai.Message{
				{Role: "user", Content: "Hello"},
			},
		},
	}

	reqBody, err := json.Marshal(proxyReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleAIProxy_AIProviderError(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Mock AI API server that returns error
	mockAIServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = fmt.Fprint(w, `{"error": {"message": "Invalid API key"}}`)
	}))
	defer mockAIServer.Close()

	proxyReq := struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}{
		Config: ai.Config{
			Provider: ai.ProviderClaude,
			APIKey:   "invalid-key",
			BaseURL:  mockAIServer.URL,
		},
		Request: ai.ChatRequest{
			Messages: []ai.Message{
				{Role: "user", Content: "Hello"},
			},
		},
	}

	reqBody, err := json.Marshal(proxyReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusInternalServerError, resp.StatusCode)
	assert.Equal(t, "application/json", resp.Header.Get("Content-Type"))

	var response map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&response)
	require.NoError(t, err)

	assert.Equal(t, false, response["success"])
	assert.NotNil(t, response["error"])
}

func TestHandleAIProxy_ReadBodyError(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Create request with a body that will cause read error
	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", &errorReader{})
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleMCPRequest_ReadBodyError(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Create request with a body that will cause read error
	req := httptest.NewRequest(http.MethodPost, "/mcp", &errorReader{})
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
}

func TestHandleAIProxy_ResponseEncodingError(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	// Mock AI API server
	mockAIServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := map[string]interface{}{
			"content": []interface{}{
				map[string]interface{}{
					"type": "text",
					"text": "Hello! How can I help you?",
				},
			},
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(response)
	}))
	defer mockAIServer.Close()

	proxyReq := struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}{
		Config: ai.Config{
			Provider: ai.ProviderClaude,
			APIKey:   "test-key",
			BaseURL:  mockAIServer.URL,
		},
		Request: ai.ChatRequest{
			Messages: []ai.Message{
				{Role: "user", Content: "Hello"},
			},
		},
	}

	reqBody, err := json.Marshal(proxyReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/ai/proxy", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")

	// Use a response writer that will fail on encoding
	w := &errorWriter{ResponseRecorder: httptest.NewRecorder()}

	transport.handleAIProxy(w, req)

	// The test passes if we don't panic - error is logged but handled gracefully
}

func TestHandleMCPRequest_ResponseEncodingError(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransport(mcpServer, logger)

	mcpReq := types.Request{
		ID:      "test-encoding-error",
		Method:  "initialize",
		Params:  json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		Created: time.Now(),
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")

	// Use a response writer that will fail on encoding
	w := &errorWriter{ResponseRecorder: httptest.NewRecorder()}

	transport.handleMCPRequest(w, req)

	// The test passes if we don't panic - error is logged but handled gracefully
}

func TestServeHTTP_AIProxyRoute(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransportWithConfig(mcpServer, logger, testCORSConfig())

	// Test OPTIONS request to AI proxy endpoint
	req := httptest.NewRequest(http.MethodOptions, "/ai/proxy", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()

	transport.ServeHTTP(w, req)

	resp := w.Result()
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "http://localhost:3000", resp.Header.Get("Access-Control-Allow-Origin"))
}

// Helper types for error testing
type errorReader struct{}

func (e *errorReader) Read(p []byte) (n int, err error) {
	return 0, fmt.Errorf("simulated read error")
}

type errorWriter struct {
	*httptest.ResponseRecorder
}

func (w *errorWriter) Write(b []byte) (int, error) {
	return 0, fmt.Errorf("simulated write error")
}

// testRateLimitConfig returns a config with rate limiting enabled for testing
func testRateLimitConfig() HTTPTransportConfig {
	return HTTPTransportConfig{
		AllowedOrigins: []string{"*"},
		RateLimit: RateLimitConfig{
			Enabled:           true,
			RequestsPerSecond: 2.0,
			BurstSize:         2,
			PerClientLimit:    true,
			CleanupInterval:   5 * time.Minute,
		},
		EnableAuditLog: true,
	}
}

func TestHandleMCPRequest_RateLimited(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransportWithConfig(mcpServer, logger, testRateLimitConfig())
	defer transport.Stop()

	mcpReq := types.Request{
		ID:      "test-rate-limit",
		Method:  "initialize",
		Params:  json.RawMessage(`{"clientInfo":{"name":"test-client","version":"1.0.0"}}`),
		Created: time.Now(),
	}

	reqBody, err := json.Marshal(mcpReq)
	require.NoError(t, err)

	// First requests should succeed (burst size = 2)
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
		req.Header.Set("Content-Type", "application/json")
		req.RemoteAddr = "192.168.1.1:8080"
		w := httptest.NewRecorder()

		transport.handleMCPRequest(w, req)
		assert.Equal(t, http.StatusOK, w.Code, "Request %d should succeed", i+1)
	}

	// Next request should be rate limited
	req := httptest.NewRequest(http.MethodPost, "/mcp", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	req.RemoteAddr = "192.168.1.1:8080"
	w := httptest.NewRecorder()

	transport.handleMCPRequest(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	assert.Equal(t, "1", w.Header().Get("Retry-After"))
}

func TestHandleAIProxy_RateLimited(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	// Use very strict rate limiting (0.01 rps = 1 request per 100 seconds)
	config := HTTPTransportConfig{
		AllowedOrigins: []string{"*"},
		RateLimit: RateLimitConfig{
			Enabled:           true,
			RequestsPerSecond: 0.01, // Very slow replenishment
			BurstSize:         2,
			PerClientLimit:    true,
			CleanupInterval:   5 * time.Minute,
		},
		EnableAuditLog: true,
	}
	transport := NewHTTPTransportWithConfig(mcpServer, logger, config)
	defer transport.Stop()

	// Test that rate limiting returns 429 status
	// Use OPTIONS request which doesn't make external API calls
	// First exhaust the burst
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodOptions, "/ai/proxy", nil)
		req.Header.Set("Origin", "http://localhost:3000")
		req.RemoteAddr = "192.168.1.10:8080"
		w := httptest.NewRecorder()

		transport.handleAIProxy(w, req)
		assert.Equal(t, http.StatusOK, w.Code, "Request %d should succeed", i+1)
	}

	// Next request should be rate limited
	req := httptest.NewRequest(http.MethodOptions, "/ai/proxy", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	req.RemoteAddr = "192.168.1.10:8080"
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	assert.Equal(t, "1", w.Header().Get("Retry-After"))
}

func TestHTTPTransport_Stop(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	transport := NewHTTPTransportWithConfig(mcpServer, logger, testRateLimitConfig())

	// Should not panic
	transport.Stop()
}

func TestHandleAIProxy_CORSRejected(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	mcpServer := server.NewMCPServer(server.Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	// Use config with specific allowed origin
	config := HTTPTransportConfig{
		AllowedOrigins: []string{"http://allowed.com"},
		EnableAuditLog: true,
	}
	transport := NewHTTPTransportWithConfig(mcpServer, logger, config)
	defer transport.Stop()

	// Test OPTIONS request with disallowed origin
	req := httptest.NewRequest(http.MethodOptions, "/ai/proxy", nil)
	req.Header.Set("Origin", "http://not-allowed.com")
	w := httptest.NewRecorder()

	transport.handleAIProxy(w, req)

	assert.Equal(t, http.StatusForbidden, w.Code)
	assert.Empty(t, w.Header().Get("Access-Control-Allow-Origin"))
}
