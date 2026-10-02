package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// MCPClient handles communication with MCP server
type MCPClient struct {
	url        string
	httpClient *http.Client
	initialized bool
}

// MCPRequest represents a JSON-RPC request to MCP
type MCPRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      string          `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

// MCPResponse represents a JSON-RPC response from MCP
type MCPResponse struct {
	ID     string          `json:"id"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  *MCPError       `json:"error,omitempty"`
}

// MCPError represents an MCP error
type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// MCPTool represents an MCP tool definition
type MCPTool struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"inputSchema"`
}

// ClaudeClient handles communication with Claude API
type ClaudeClient struct {
	apiKey     string
	httpClient *http.Client
}

// ClaudeMessage represents a message in Claude API
type ClaudeMessage struct {
	Role    string          `json:"role"`
	Content json.RawMessage `json:"content"`
}

// ClaudeRequest represents a request to Claude API
type ClaudeRequest struct {
	Model     string           `json:"model"`
	MaxTokens int              `json:"max_tokens"`
	System    string           `json:"system,omitempty"`
	Messages  []ClaudeMessage  `json:"messages"`
	Tools     []ClaudeTool     `json:"tools,omitempty"`
}

// ClaudeTool represents a tool definition for Claude
type ClaudeTool struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"input_schema"`
}

// ClaudeResponse represents Claude's response
type ClaudeResponse struct {
	ID      string          `json:"id"`
	Type    string          `json:"type"`
	Role    string          `json:"role"`
	Content []ContentBlock  `json:"content"`
}

// ContentBlock represents a content block in Claude's response
type ContentBlock struct {
	Type  string          `json:"type"`
	Text  string          `json:"text,omitempty"`
	ID    string          `json:"id,omitempty"`
	Name  string          `json:"name,omitempty"`
	Input json.RawMessage `json:"input,omitempty"`
}

// ClaudeMCPIntegration integrates Claude API with MCP
type ClaudeMCPIntegration struct {
	claude *ClaudeClient
	mcp    *MCPClient
	tools  []MCPTool
}

// NewClaudeClient creates a new Claude API client
func NewClaudeClient(apiKey string) *ClaudeClient {
	return &ClaudeClient{
		apiKey: apiKey,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// NewMCPClient creates a new MCP client
func NewMCPClient(url string) *MCPClient {
	return &MCPClient{
		url: url,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Initialize initializes the MCP connection
func (m *MCPClient) Initialize() error {
	params := map[string]interface{}{
		"protocolVersion": "2024-11-05",
		"clientInfo": map[string]string{
			"name":    "claude-go-client",
			"version": "1.0.0",
		},
	}

	paramsJSON, _ := json.Marshal(params)
	request := MCPRequest{
		JSONRPC: "2.0",
		ID:      "init",
		Method:  "initialize",
		Params:  paramsJSON,
	}

	var response MCPResponse
	if err := m.callMCP(request, &response); err != nil {
		return fmt.Errorf("failed to initialize MCP: %w", err)
	}

	m.initialized = true
	fmt.Println("MCP server initialized successfully")
	return nil
}

// ListTools lists available MCP tools
func (m *MCPClient) ListTools() ([]MCPTool, error) {
	if !m.initialized {
		if err := m.Initialize(); err != nil {
			return nil, err
		}
	}

	request := MCPRequest{
		JSONRPC: "2.0",
		ID:      "list-tools",
		Method:  "tools/list",
		Params:  json.RawMessage("{}"),
	}

	var response MCPResponse
	if err := m.callMCP(request, &response); err != nil {
		return nil, fmt.Errorf("failed to list tools: %w", err)
	}

	var result struct {
		Tools []MCPTool `json:"tools"`
	}
	if err := json.Unmarshal(response.Result, &result); err != nil {
		return nil, fmt.Errorf("failed to parse tools: %w", err)
	}

	return result.Tools, nil
}

// CallTool calls an MCP tool
func (m *MCPClient) CallTool(toolName string, arguments map[string]interface{}) (json.RawMessage, error) {
	params := map[string]interface{}{
		"name":      toolName,
		"arguments": arguments,
	}

	paramsJSON, _ := json.Marshal(params)
	request := MCPRequest{
		JSONRPC: "2.0",
		ID:      fmt.Sprintf("call-%s-%d", toolName, time.Now().Unix()),
		Method:  "tools/call",
		Params:  paramsJSON,
	}

	var response MCPResponse
	if err := m.callMCP(request, &response); err != nil {
		return nil, fmt.Errorf("failed to call tool %s: %w", toolName, err)
	}

	return response.Result, nil
}

// callMCP makes an HTTP call to the MCP server
func (m *MCPClient) callMCP(request MCPRequest, response *MCPResponse) error {
	reqBody, err := json.Marshal(request)
	if err != nil {
		return err
	}

	req, err := http.NewRequest("POST", m.url, bytes.NewBuffer(reqBody))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	if err := json.Unmarshal(body, response); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	if response.Error != nil {
		return fmt.Errorf("MCP error: %s", response.Error.Message)
	}

	return nil
}

// SendMessage sends a message to Claude
func (c *ClaudeClient) SendMessage(ctx context.Context, request ClaudeRequest) (*ClaudeResponse, error) {
	reqBody, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", "https://api.anthropic.com/v1/messages", bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", c.apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Claude API error (status %d): %s", resp.StatusCode, string(body))
	}

	var response ClaudeResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to parse Claude response: %w", err)
	}

	return &response, nil
}

// NewClaudeMCPIntegration creates a new Claude + MCP integration
func NewClaudeMCPIntegration(apiKey, mcpURL string) (*ClaudeMCPIntegration, error) {
	if apiKey == "" {
		apiKey = os.Getenv("ANTHROPIC_API_KEY")
	}
	if apiKey == "" {
		return nil, fmt.Errorf("Claude API key required. Set ANTHROPIC_API_KEY environment variable")
	}

	if mcpURL == "" {
		mcpURL = "http://localhost:8090/mcp"
	}

	claude := NewClaudeClient(apiKey)
	mcp := NewMCPClient(mcpURL)

	// Initialize MCP
	if err := mcp.Initialize(); err != nil {
		return nil, fmt.Errorf("failed to initialize MCP: %w", err)
	}

	// Load tools
	tools, err := mcp.ListTools()
	if err != nil {
		return nil, fmt.Errorf("failed to load MCP tools: %w", err)
	}

	fmt.Printf("Loaded %d MCP tools\n", len(tools))

	return &ClaudeMCPIntegration{
		claude: claude,
		mcp:    mcp,
		tools:  tools,
	}, nil
}

// ChatWithTools sends a message to Claude with MCP tools
func (c *ClaudeMCPIntegration) ChatWithTools(ctx context.Context, userMessage string) (string, error) {
	// Convert MCP tools to Claude format
	var claudeTools []ClaudeTool
	for _, tool := range c.tools {
		claudeTools = append(claudeTools, ClaudeTool{
			Name:        tool.Name,
			Description: tool.Description,
			InputSchema: tool.InputSchema,
		})
	}

	// Create message content
	messageContent, _ := json.Marshal(userMessage)

	// Create request
	request := ClaudeRequest{
		Model:     "claude-3-haiku-20240307",
		MaxTokens: 1024,
		System: "You are an AI assistant with access to Kubernetes PDB management tools. " +
			"Use the available tools to help the user manage their Kubernetes cluster effectively.",
		Messages: []ClaudeMessage{
			{
				Role:    "user",
				Content: messageContent,
			},
		},
		Tools: claudeTools,
	}

	// Send to Claude
	response, err := c.claude.SendMessage(ctx, request)
	if err != nil {
		return "", fmt.Errorf("failed to send message to Claude: %w", err)
	}

	// Process response
	var result strings.Builder
	for _, content := range response.Content {
		switch content.Type {
		case "text":
			result.WriteString(content.Text)
		case "tool_use":
			fmt.Printf("\nClaude is calling tool: %s\n", content.Name)
			
			// Parse arguments
			var arguments map[string]interface{}
			if err := json.Unmarshal(content.Input, &arguments); err != nil {
				fmt.Printf("Error parsing tool arguments: %v\n", err)
				continue
			}

			// Call MCP tool
			toolResult, err := c.mcp.CallTool(content.Name, arguments)
			if err != nil {
				fmt.Printf("Error calling tool: %v\n", err)
				result.WriteString(fmt.Sprintf("\n\nTool error: %v", err))
			} else {
				// Pretty print JSON result
				var prettyResult interface{}
				if err := json.Unmarshal(toolResult, &prettyResult); err == nil {
					if prettyJSON, err := json.MarshalIndent(prettyResult, "", "  "); err == nil {
						result.WriteString(fmt.Sprintf("\n\nTool result:\n%s", string(prettyJSON)))
					} else {
						result.WriteString(fmt.Sprintf("\n\nTool result: %s", string(toolResult)))
					}
				} else {
					result.WriteString(fmt.Sprintf("\n\nTool result: %s", string(toolResult)))
				}
			}
		}
	}

	return result.String(), nil
}

// AnalyzeNamespace asks Claude to analyze a namespace
func (c *ClaudeMCPIntegration) AnalyzeNamespace(ctx context.Context, namespace string) (string, error) {
	prompt := fmt.Sprintf("Analyze the availability status of the %s namespace and provide recommendations.", namespace)
	return c.ChatWithTools(ctx, prompt)
}

// RecommendPolicies asks Claude to recommend policies
func (c *ClaudeMCPIntegration) RecommendPolicies(ctx context.Context, namespace string) (string, error) {
	prompt := fmt.Sprintf("What availability policies do you recommend for the %s namespace? "+
		"Analyze the current deployments and suggest optimal configurations.", namespace)
	return c.ChatWithTools(ctx, prompt)
}

func main() {
	// Check for API key
	apiKey := os.Getenv("ANTHROPIC_API_KEY")
	if apiKey == "" {
		fmt.Println("Error: Please set ANTHROPIC_API_KEY environment variable")
		fmt.Println("Export it with: export ANTHROPIC_API_KEY='your-api-key'")
		os.Exit(1)
	}

	// Create integration
	fmt.Println("Initializing Claude + MCP integration...")
	fmt.Println("Make sure port-forward is running:")
	fmt.Println("kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090")
	fmt.Println(strings.Repeat("-", 50))

	integration, err := NewClaudeMCPIntegration(apiKey, "")
	if err != nil {
		fmt.Printf("Failed to initialize: %v\n", err)
		fmt.Println("\nTroubleshooting:")
		fmt.Println("1. Check port-forward is running")
		fmt.Println("2. Check MCP server is healthy: curl http://localhost:8090/health")
		fmt.Println("3. Verify ANTHROPIC_API_KEY is set correctly")
		os.Exit(1)
	}

	// Interactive mode
	fmt.Println("\nClaude + MCP Integration Ready!")
	fmt.Println("Type your message or 'quit' to exit")
	fmt.Println(strings.Repeat("-", 50))

	ctx := context.Background()
	scanner := bufio.NewScanner(os.Stdin)
	
	for {
		fmt.Print("\n> ")
		if !scanner.Scan() {
			break
		}
		
		input := scanner.Text()
		
		if input == "quit" || input == "exit" {
			fmt.Println("Goodbye!")
			return
		}

		if input == "" {
			continue
		}

		response, err := integration.ChatWithTools(ctx, input)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
		} else {
			fmt.Printf("\nClaude: %s\n", response)
		}
	}
}