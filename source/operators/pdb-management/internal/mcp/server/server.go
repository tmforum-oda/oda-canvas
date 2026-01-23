package server

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/go-logr/logr"
	"github.com/google/uuid"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// MCPServer represents the MCP server for PDB management
type MCPServer struct {
	logger      logr.Logger
	client      client.Client
	kubeClient  kubernetes.Interface
	tools       map[string]*types.Tool
	prompts     map[string]*types.Prompt
	resources   map[string]*types.Resource
	mu          sync.RWMutex
	initialized bool
	serverInfo  types.ServerInfo
	handlers    map[string]HandlerFunc
}

// HandlerFunc is a function that handles MCP requests
type HandlerFunc func(ctx context.Context, params json.RawMessage) (interface{}, error)

// Config contains configuration for the MCP server
type Config struct {
	Name       string
	Version    string
	Logger     logr.Logger
	Client     client.Client
	KubeClient kubernetes.Interface
}

// NewMCPServer creates a new MCP server instance
func NewMCPServer(cfg Config) *MCPServer {
	s := &MCPServer{
		logger:     cfg.Logger,
		client:     cfg.Client,
		kubeClient: cfg.KubeClient,
		tools:      make(map[string]*types.Tool),
		prompts:    make(map[string]*types.Prompt),
		resources:  make(map[string]*types.Resource),
		handlers:   make(map[string]HandlerFunc),
		serverInfo: types.ServerInfo{
			Name:    cfg.Name,
			Version: cfg.Version,
			Capabilities: []string{
				"tools",
				"prompts",
				"resources",
				"notifications",
			},
		},
	}

	// Register standard MCP handlers
	s.registerHandlers()

	return s
}

// registerHandlers registers the standard MCP protocol handlers
func (s *MCPServer) registerHandlers() {
	s.handlers["initialize"] = s.handleInitialize
	s.handlers["tools/list"] = s.handleListTools
	s.handlers["tools/call"] = s.handleCallTool
	s.handlers["prompts/list"] = s.handleListPrompts
	s.handlers["prompts/get"] = s.handleGetPrompt
	s.handlers["resources/list"] = s.handleListResources
	s.handlers["resources/read"] = s.handleReadResource
}

// HandleRequest processes an MCP request and returns a response
func (s *MCPServer) HandleRequest(ctx context.Context, req *types.Request) (*types.Response, error) {
	s.logger.V(2).Info("Handling MCP request", "method", req.Method, "id", req.ID)

	handler, exists := s.handlers[req.Method]
	if !exists {
		return &types.Response{
			ID: req.ID,
			Error: &types.Error{
				Code:    -32601,
				Message: fmt.Sprintf("Method not found: %s", req.Method),
			},
			Created: time.Now(),
		}, nil
	}

	result, err := handler(ctx, req.Params)
	if err != nil {
		s.logger.Error(err, "Handler error", "method", req.Method)
		return &types.Response{
			ID: req.ID,
			Error: &types.Error{
				Code:    -32603,
				Message: err.Error(),
			},
			Created: time.Now(),
		}, nil
	}

	resultJSON, err := json.Marshal(result)
	if err != nil {
		return &types.Response{
			ID: req.ID,
			Error: &types.Error{
				Code:    -32603,
				Message: fmt.Sprintf("Failed to marshal result: %v", err),
			},
			Created: time.Now(),
		}, nil
	}

	return &types.Response{
		ID:      req.ID,
		Result:  resultJSON,
		Created: time.Now(),
	}, nil
}

// handleInitialize handles the initialize request
func (s *MCPServer) handleInitialize(ctx context.Context, params json.RawMessage) (interface{}, error) {
	var initParams types.InitializeParams
	if err := json.Unmarshal(params, &initParams); err != nil {
		return nil, fmt.Errorf("invalid initialize params: %w", err)
	}

	s.mu.Lock()
	s.initialized = true
	s.mu.Unlock()

	s.logger.Info("MCP server initialized",
		"client", initParams.ClientInfo.Name,
		"version", initParams.ClientInfo.Version)

	return map[string]interface{}{
		"serverInfo": s.serverInfo,
	}, nil
}

// handleListTools handles the tools/list request
func (s *MCPServer) handleListTools(ctx context.Context, params json.RawMessage) (interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var tools []types.ToolInfo
	for _, tool := range s.tools {
		tools = append(tools, types.ToolInfo{
			Name:        tool.Name,
			Description: tool.Description,
			InputSchema: tool.InputSchema,
		})
	}

	return &types.ListToolsResult{
		Tools: tools,
	}, nil
}

// handleCallTool handles the tools/call request
func (s *MCPServer) handleCallTool(ctx context.Context, params json.RawMessage) (interface{}, error) {
	var callParams types.CallToolParams
	if err := json.Unmarshal(params, &callParams); err != nil {
		return nil, fmt.Errorf("invalid call tool params: %w", err)
	}

	s.mu.RLock()
	tool, exists := s.tools[callParams.Name]
	s.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("tool not found: %s", callParams.Name)
	}

	// Call the tool handler
	result, err := tool.Handler(ctx, callParams.Arguments)
	if err != nil {
		return &types.CallToolResult{
			Content: []types.ContentItem{
				{
					Type: "text",
					Text: fmt.Sprintf("Error calling tool %s: %v", callParams.Name, err),
				},
			},
			IsError: true,
		}, nil
	}

	// Convert result to content items
	var content []types.ContentItem
	switch v := result.Content.(type) {
	case string:
		content = append(content, types.ContentItem{
			Type: "text",
			Text: v,
		})
	case map[string]interface{}:
		jsonData, _ := json.MarshalIndent(v, "", "  ")
		content = append(content, types.ContentItem{
			Type: "text",
			Text: string(jsonData),
		})
	default:
		// Marshal any struct to pretty JSON
		jsonData, err := json.MarshalIndent(v, "", "  ")
		if err != nil {
			content = append(content, types.ContentItem{
				Type: "text",
				Text: fmt.Sprintf("Error formatting result: %v", err),
			})
		} else {
			content = append(content, types.ContentItem{
				Type: "text",
				Text: string(jsonData),
			})
		}
	}

	return &types.CallToolResult{
		Content: content,
		IsError: result.IsError,
	}, nil
}

// handleListPrompts handles the prompts/list request
func (s *MCPServer) handleListPrompts(ctx context.Context, params json.RawMessage) (interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var prompts []types.Prompt
	for _, prompt := range s.prompts {
		prompts = append(prompts, *prompt)
	}

	return &types.ListPromptsResult{
		Prompts: prompts,
	}, nil
}

// handleGetPrompt handles the prompts/get request
func (s *MCPServer) handleGetPrompt(ctx context.Context, params json.RawMessage) (interface{}, error) {
	var getParams types.GetPromptParams
	if err := json.Unmarshal(params, &getParams); err != nil {
		return nil, fmt.Errorf("invalid get prompt params: %w", err)
	}

	s.mu.RLock()
	prompt, exists := s.prompts[getParams.Name]
	s.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("prompt not found: %s", getParams.Name)
	}

	// Generate prompt messages based on the prompt template and arguments
	// This is a simplified implementation - real prompts would be more sophisticated
	messages := []types.PromptMessage{
		{
			Role: "user",
			Content: []types.ContentItem{
				{
					Type: "text",
					Text: fmt.Sprintf("Execute %s prompt with arguments: %v", prompt.Name, getParams.Arguments),
				},
			},
		},
	}

	return &types.GetPromptResult{
		Messages: messages,
	}, nil
}

// handleListResources handles the resources/list request
func (s *MCPServer) handleListResources(ctx context.Context, params json.RawMessage) (interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var resources []types.Resource
	for _, resource := range s.resources {
		resources = append(resources, *resource)
	}

	return &types.ListResourcesResult{
		Resources: resources,
	}, nil
}

// handleReadResource handles the resources/read request
func (s *MCPServer) handleReadResource(ctx context.Context, params json.RawMessage) (interface{}, error) {
	var readParams types.ReadResourceParams
	if err := json.Unmarshal(params, &readParams); err != nil {
		return nil, fmt.Errorf("invalid read resource params: %w", err)
	}

	s.mu.RLock()
	resource, exists := s.resources[readParams.URI]
	s.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("resource not found: %s", readParams.URI)
	}

	// For now, return basic resource information
	// Real implementation would fetch actual resource content
	return &types.ReadResourceResult{
		Content: []types.ContentItem{
			{
				Type: "text",
				Text: fmt.Sprintf("Resource: %s\nDescription: %s", resource.Name, resource.Description),
			},
		},
	}, nil
}

// RegisterTool registers a new tool with the MCP server
func (s *MCPServer) RegisterTool(tool *types.Tool) error {
	if tool == nil || tool.Name == "" {
		return fmt.Errorf("invalid tool: name is required")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.tools[tool.Name]; exists {
		return fmt.Errorf("tool already registered: %s", tool.Name)
	}

	s.tools[tool.Name] = tool
	s.logger.Info("Registered MCP tool", "name", tool.Name)
	return nil
}

// RegisterPrompt registers a new prompt with the MCP server
func (s *MCPServer) RegisterPrompt(prompt *types.Prompt) error {
	if prompt == nil || prompt.Name == "" {
		return fmt.Errorf("invalid prompt: name is required")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.prompts[prompt.Name]; exists {
		return fmt.Errorf("prompt already registered: %s", prompt.Name)
	}

	s.prompts[prompt.Name] = prompt
	s.logger.Info("Registered MCP prompt", "name", prompt.Name)
	return nil
}

// RegisterResource registers a new resource with the MCP server
func (s *MCPServer) RegisterResource(resource *types.Resource) error {
	if resource == nil || resource.URI == "" {
		return fmt.Errorf("invalid resource: URI is required")
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.resources[resource.URI]; exists {
		return fmt.Errorf("resource already registered: %s", resource.URI)
	}

	s.resources[resource.URI] = resource
	s.logger.Info("Registered MCP resource", "uri", resource.URI)
	return nil
}

// IsInitialized returns whether the server has been initialized
func (s *MCPServer) IsInitialized() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.initialized
}

// SendNotification sends a notification to the client
func (s *MCPServer) SendNotification(method string, params interface{}) (*types.Notification, error) {
	paramsJSON, err := json.Marshal(params)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal notification params: %w", err)
	}

	notification := &types.Notification{
		Method:  method,
		Params:  paramsJSON,
		Created: time.Now(),
	}

	s.logger.V(2).Info("Sending notification", "method", method)
	return notification, nil
}

// GetClient returns the Kubernetes client
func (s *MCPServer) GetClient() client.Client {
	return s.client
}

// GetKubeClient returns the Kubernetes clientset
func (s *MCPServer) GetKubeClient() kubernetes.Interface {
	return s.kubeClient
}

// GenerateRequestID generates a unique request ID
func GenerateRequestID() string {
	return uuid.New().String()
}
