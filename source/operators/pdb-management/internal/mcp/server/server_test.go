package server

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	kfake "k8s.io/client-go/kubernetes/fake"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewMCPServer(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	server := NewMCPServer(Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	assert.NotNil(t, server)
	assert.Equal(t, "test-server", server.serverInfo.Name)
	assert.Equal(t, "v1.0.0", server.serverInfo.Version)
	assert.Contains(t, server.serverInfo.Capabilities, "tools")
	assert.Contains(t, server.serverInfo.Capabilities, "prompts")
	assert.False(t, server.IsInitialized())
}

func TestHandleInitialize(t *testing.T) {
	server := createTestServer(t)

	initParams := types.InitializeParams{
		ClientInfo: types.ClientInfo{
			Name:    "test-client",
			Version: "v1.0.0",
		},
	}

	paramsJSON, err := json.Marshal(initParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-1",
		Method:  "initialize",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Equal(t, "test-1", resp.ID)
	assert.Nil(t, resp.Error)
	assert.True(t, server.IsInitialized())

	// Verify response content
	var result map[string]interface{}
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)

	serverInfo, exists := result["serverInfo"]
	assert.True(t, exists)
	assert.NotNil(t, serverInfo)
}

func TestHandleListToolsEmpty(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-2",
		Method:  "tools/list",
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Equal(t, "test-2", resp.ID)
	assert.Nil(t, resp.Error)

	var result types.ListToolsResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)
	assert.Empty(t, result.Tools)
}

func TestRegisterTool(t *testing.T) {
	server := createTestServer(t)

	tool := &types.Tool{
		Name:        "test-tool",
		Description: "A test tool",
		InputSchema: json.RawMessage(`{"type": "object"}`),
		Handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
			return &types.ToolResult{
				Content: "test result",
			}, nil
		},
	}

	err := server.RegisterTool(tool)
	require.NoError(t, err)

	// Test duplicate registration
	err = server.RegisterTool(tool)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "already registered")

	// Test invalid tool
	err = server.RegisterTool(&types.Tool{})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "name is required")
}

func TestHandleListToolsWithRegistered(t *testing.T) {
	server := createTestServer(t)

	tool := &types.Tool{
		Name:        "test-tool",
		Description: "A test tool",
		InputSchema: json.RawMessage(`{"type": "object"}`),
		Handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
			return &types.ToolResult{
				Content: "test result",
			}, nil
		},
	}

	err := server.RegisterTool(tool)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-3",
		Method:  "tools/list",
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)

	var result types.ListToolsResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)

	assert.Len(t, result.Tools, 1)
	assert.Equal(t, "test-tool", result.Tools[0].Name)
	assert.Equal(t, "A test tool", result.Tools[0].Description)
}

func TestHandleCallTool(t *testing.T) {
	server := createTestServer(t)

	// Register a test tool
	tool := &types.Tool{
		Name:        "echo-tool",
		Description: "Echoes input",
		InputSchema: json.RawMessage(`{"type": "object"}`),
		Handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
			var input map[string]interface{}
			if err := json.Unmarshal(params, &input); err != nil {
				return &types.ToolResult{
					Content:     "Invalid input",
					IsError:     true,
					ErrorDetail: err.Error(),
				}, nil
			}
			return &types.ToolResult{
				Content: input,
			}, nil
		},
	}

	err := server.RegisterTool(tool)
	require.NoError(t, err)

	// Test successful tool call
	callParams := types.CallToolParams{
		Name:      "echo-tool",
		Arguments: json.RawMessage(`{"message": "hello world"}`),
	}

	paramsJSON, err := json.Marshal(callParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-4",
		Method:  "tools/call",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Nil(t, resp.Error)

	var result types.CallToolResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)
	assert.False(t, result.IsError)
	assert.NotEmpty(t, result.Content)
}

func TestHandleCallToolNotFound(t *testing.T) {
	server := createTestServer(t)

	callParams := types.CallToolParams{
		Name:      "nonexistent-tool",
		Arguments: json.RawMessage(`{}`),
	}

	paramsJSON, err := json.Marshal(callParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-5",
		Method:  "tools/call",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "tool not found")
}

func TestHandleInvalidMethod(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-6",
		Method:  "invalid/method",
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Equal(t, -32601, resp.Error.Code)
	assert.Contains(t, resp.Error.Message, "Method not found")
}

func TestRegisterPrompt(t *testing.T) {
	server := createTestServer(t)

	prompt := &types.Prompt{
		Name:        "test-prompt",
		Description: "A test prompt",
		Arguments: []types.PromptArgument{
			{
				Name:        "input",
				Description: "Test input",
				Required:    true,
			},
		},
	}

	err := server.RegisterPrompt(prompt)
	require.NoError(t, err)

	// Test duplicate registration
	err = server.RegisterPrompt(prompt)
	assert.Error(t, err)

	// Test invalid prompt
	err = server.RegisterPrompt(&types.Prompt{})
	assert.Error(t, err)
}

func TestHandleListPrompts(t *testing.T) {
	server := createTestServer(t)

	prompt := &types.Prompt{
		Name:        "test-prompt",
		Description: "A test prompt",
	}

	err := server.RegisterPrompt(prompt)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-7",
		Method:  "prompts/list",
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)

	var result types.ListPromptsResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)

	assert.Len(t, result.Prompts, 1)
	assert.Equal(t, "test-prompt", result.Prompts[0].Name)
}

func TestRegisterResource(t *testing.T) {
	server := createTestServer(t)

	resource := &types.Resource{
		URI:         "test://resource",
		Name:        "test-resource",
		Description: "A test resource",
		MimeType:    "application/json",
	}

	err := server.RegisterResource(resource)
	require.NoError(t, err)

	// Test duplicate registration
	err = server.RegisterResource(resource)
	assert.Error(t, err)

	// Test invalid resource
	err = server.RegisterResource(&types.Resource{})
	assert.Error(t, err)
}

func TestHandleListResources(t *testing.T) {
	server := createTestServer(t)

	resource := &types.Resource{
		URI:         "test://resource",
		Name:        "test-resource",
		Description: "A test resource",
	}

	err := server.RegisterResource(resource)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-8",
		Method:  "resources/list",
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)

	var result types.ListResourcesResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)

	assert.Len(t, result.Resources, 1)
	assert.Equal(t, "test://resource", result.Resources[0].URI)
}

func TestSendNotification(t *testing.T) {
	server := createTestServer(t)

	notification, err := server.SendNotification("test/notification", map[string]string{
		"message": "test",
	})
	require.NoError(t, err)
	assert.Equal(t, "test/notification", notification.Method)
	assert.NotEmpty(t, notification.Params)
	assert.False(t, notification.Created.IsZero())
}

func TestGenerateRequestID(t *testing.T) {
	id1 := GenerateRequestID()
	id2 := GenerateRequestID()

	assert.NotEmpty(t, id1)
	assert.NotEmpty(t, id2)
	assert.NotEqual(t, id1, id2)
}

func TestGetClients(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	server := NewMCPServer(Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})

	assert.Equal(t, client, server.GetClient())
	assert.Equal(t, kubeClient, server.GetKubeClient())
}

func TestHandleGetPrompt(t *testing.T) {
	server := createTestServer(t)

	// Register a test prompt
	prompt := &types.Prompt{
		Name:        "test-prompt",
		Description: "A test prompt",
		Arguments: []types.PromptArgument{
			{
				Name:        "input",
				Description: "Test input",
				Required:    true,
			},
		},
	}

	err := server.RegisterPrompt(prompt)
	require.NoError(t, err)

	// Test successful prompt get
	getParams := types.GetPromptParams{
		Name: "test-prompt",
		Arguments: map[string]string{
			"input": "test value",
		},
	}

	paramsJSON, err := json.Marshal(getParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-get-prompt",
		Method:  "prompts/get",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Nil(t, resp.Error)

	var result types.GetPromptResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)
	assert.NotEmpty(t, result.Messages)
	assert.Equal(t, "user", result.Messages[0].Role)
}

func TestHandleGetPromptNotFound(t *testing.T) {
	server := createTestServer(t)

	getParams := types.GetPromptParams{
		Name: "nonexistent-prompt",
	}

	paramsJSON, err := json.Marshal(getParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-get-prompt-not-found",
		Method:  "prompts/get",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "prompt not found")
}

func TestHandleGetPromptInvalidParams(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-get-prompt-invalid",
		Method:  "prompts/get",
		Params:  json.RawMessage(`invalid json`),
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "invalid get prompt params")
}

func TestHandleReadResource(t *testing.T) {
	server := createTestServer(t)

	// Register a test resource
	resource := &types.Resource{
		URI:         "test://resource",
		Name:        "test-resource",
		Description: "A test resource",
		MimeType:    "application/json",
	}

	err := server.RegisterResource(resource)
	require.NoError(t, err)

	// Test successful resource read
	readParams := types.ReadResourceParams{
		URI: "test://resource",
	}

	paramsJSON, err := json.Marshal(readParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-read-resource",
		Method:  "resources/read",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Nil(t, resp.Error)

	var result types.ReadResourceResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)
	assert.NotEmpty(t, result.Content)
	assert.Equal(t, "text", result.Content[0].Type)
	assert.Contains(t, result.Content[0].Text, "test-resource")
}

func TestHandleReadResourceNotFound(t *testing.T) {
	server := createTestServer(t)

	readParams := types.ReadResourceParams{
		URI: "test://nonexistent",
	}

	paramsJSON, err := json.Marshal(readParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-read-resource-not-found",
		Method:  "resources/read",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "resource not found")
}

func TestHandleReadResourceInvalidParams(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-read-resource-invalid",
		Method:  "resources/read",
		Params:  json.RawMessage(`invalid json`),
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "invalid read resource params")
}

func TestHandleCallToolWithDifferentContentTypes(t *testing.T) {
	server := createTestServer(t)

	tests := []struct {
		name     string
		handler  func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error)
		expected string
	}{
		{
			name: "string-content",
			handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
				return &types.ToolResult{
					Content: "simple string result",
				}, nil
			},
			expected: "simple string result",
		},
		{
			name: "map-content",
			handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
				return &types.ToolResult{
					Content: map[string]interface{}{
						"key1": "value1",
						"key2": 42,
					},
				}, nil
			},
			expected: "{\n  \"key1\": \"value1\",\n  \"key2\": 42\n}",
		},
		{
			name: "other-content",
			handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
				return &types.ToolResult{
					Content: 12345,
				}, nil
			},
			expected: "12345",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			toolName := "test-tool-" + tt.name
			tool := &types.Tool{
				Name:        toolName,
				Description: "Test tool",
				InputSchema: json.RawMessage(`{"type": "object"}`),
				Handler:     tt.handler,
			}

			err := server.RegisterTool(tool)
			require.NoError(t, err)

			callParams := types.CallToolParams{
				Name:      toolName,
				Arguments: json.RawMessage(`{}`),
			}

			paramsJSON, err := json.Marshal(callParams)
			require.NoError(t, err)

			req := &types.Request{
				ID:      "test-call-tool-content-" + tt.name,
				Method:  "tools/call",
				Params:  paramsJSON,
				Created: time.Now(),
			}

			resp, err := server.HandleRequest(context.Background(), req)
			require.NoError(t, err)
			assert.Nil(t, resp.Error)

			var result types.CallToolResult
			err = json.Unmarshal(resp.Result, &result)
			require.NoError(t, err)
			assert.False(t, result.IsError)
			assert.Len(t, result.Content, 1)
			assert.Equal(t, "text", result.Content[0].Type)
			assert.Equal(t, tt.expected, result.Content[0].Text)
		})
	}
}

func TestHandleCallToolWithError(t *testing.T) {
	server := createTestServer(t)

	// Register a tool that returns an error
	tool := &types.Tool{
		Name:        "error-tool",
		Description: "Tool that returns error",
		InputSchema: json.RawMessage(`{"type": "object"}`),
		Handler: func(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
			return nil, fmt.Errorf("simulated tool error")
		},
	}

	err := server.RegisterTool(tool)
	require.NoError(t, err)

	callParams := types.CallToolParams{
		Name:      "error-tool",
		Arguments: json.RawMessage(`{}`),
	}

	paramsJSON, err := json.Marshal(callParams)
	require.NoError(t, err)

	req := &types.Request{
		ID:      "test-call-tool-error",
		Method:  "tools/call",
		Params:  paramsJSON,
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.Nil(t, resp.Error) // Handler errors are wrapped in result, not response error

	var result types.CallToolResult
	err = json.Unmarshal(resp.Result, &result)
	require.NoError(t, err)
	assert.True(t, result.IsError)
	assert.Contains(t, result.Content[0].Text, "Error calling tool error-tool")
}

func TestHandleCallToolInvalidParams(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-call-tool-invalid",
		Method:  "tools/call",
		Params:  json.RawMessage(`invalid json`),
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "invalid call tool params")
}

func TestHandleInitializeInvalidParams(t *testing.T) {
	server := createTestServer(t)

	req := &types.Request{
		ID:      "test-init-invalid",
		Method:  "initialize",
		Params:  json.RawMessage(`invalid json`),
		Created: time.Now(),
	}

	resp, err := server.HandleRequest(context.Background(), req)
	require.NoError(t, err)
	assert.NotNil(t, resp.Error)
	assert.Contains(t, resp.Error.Message, "invalid initialize params")
}

// Helper function to create a test server
func createTestServer(t *testing.T) *MCPServer {
	logger := zap.New(zap.UseDevMode(true))
	client := fake.NewClientBuilder().Build()
	kubeClient := kfake.NewSimpleClientset()

	return NewMCPServer(Config{
		Name:       "test-server",
		Version:    "v1.0.0",
		Logger:     logger,
		Client:     client,
		KubeClient: kubeClient,
	})
}
