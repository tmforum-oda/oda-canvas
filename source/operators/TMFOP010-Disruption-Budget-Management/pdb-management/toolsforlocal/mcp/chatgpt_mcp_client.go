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

// MCPClient handles communication with MCP server (reused from Claude client)
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

// ChatGPTClient handles communication with OpenAI API
type ChatGPTClient struct {
	apiKey     string
	httpClient *http.Client
}

// ChatGPTMessage represents a message in ChatGPT API
type ChatGPTMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatGPTTool represents a tool definition for ChatGPT
type ChatGPTTool struct {
	Type     string                 `json:"type"`
	Function ChatGPTFunctionTool    `json:"function"`
}

// ChatGPTFunctionTool represents a function tool
type ChatGPTFunctionTool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
}

// ChatGPTRequest represents a request to ChatGPT API
type ChatGPTRequest struct {
	Model       string           `json:"model"`
	Messages    []ChatGPTMessage `json:"messages"`
	Tools       []ChatGPTTool    `json:"tools,omitempty"`
	ToolChoice  string           `json:"tool_choice,omitempty"`
	MaxTokens   int              `json:"max_tokens,omitempty"`
}

// ChatGPTResponse represents ChatGPT's response
type ChatGPTResponse struct {
	ID      string               `json:"id"`
	Object  string               `json:"object"`
	Choices []ChatGPTChoice      `json:"choices"`
	Usage   ChatGPTUsage         `json:"usage"`
}

// ChatGPTChoice represents a choice in the response
type ChatGPTChoice struct {
	Index   int                `json:"index"`
	Message ChatGPTResponseMsg `json:"message"`
	Reason  string             `json:"finish_reason"`
}

// ChatGPTResponseMsg represents a response message
type ChatGPTResponseMsg struct {
	Role      string              `json:"role"`
	Content   string              `json:"content,omitempty"`
	ToolCalls []ChatGPTToolCall   `json:"tool_calls,omitempty"`
}

// ChatGPTToolCall represents a tool call
type ChatGPTToolCall struct {
	ID       string                    `json:"id"`
	Type     string                    `json:"type"`
	Function ChatGPTFunctionCall      `json:"function"`
}

// ChatGPTFunctionCall represents a function call
type ChatGPTFunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

// ChatGPTUsage represents token usage
type ChatGPTUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// ChatGPTMCPIntegration integrates ChatGPT API with MCP
type ChatGPTMCPIntegration struct {
	chatgpt *ChatGPTClient
	mcp     *MCPClient
	tools   []MCPTool
}

// NewChatGPTClient creates a new ChatGPT API client
func NewChatGPTClient(apiKey string) *ChatGPTClient {
	return &ChatGPTClient{
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
			"name":    "chatgpt-go-client",
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

// SendMessage sends a message to ChatGPT
func (c *ChatGPTClient) SendMessage(ctx context.Context, request ChatGPTRequest) (*ChatGPTResponse, error) {
	reqBody, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", "https://api.openai.com/v1/chat/completions", bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))

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
		return nil, fmt.Errorf("OpenAI API error (status %d): %s", resp.StatusCode, string(body))
	}

	var response ChatGPTResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to parse ChatGPT response: %w", err)
	}

	return &response, nil
}

// NewChatGPTMCPIntegration creates a new ChatGPT + MCP integration
func NewChatGPTMCPIntegration(apiKey, mcpURL string) (*ChatGPTMCPIntegration, error) {
	if apiKey == "" {
		apiKey = os.Getenv("OPENAI_API_KEY")
	}
	if apiKey == "" {
		return nil, fmt.Errorf("OpenAI API key required. Set OPENAI_API_KEY environment variable")
	}

	if mcpURL == "" {
		mcpURL = "http://localhost:8090/mcp"
	}

	chatgpt := NewChatGPTClient(apiKey)
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

	return &ChatGPTMCPIntegration{
		chatgpt: chatgpt,
		mcp:     mcp,
		tools:   tools,
	}, nil
}

// convertMCPToChatGPTTools converts MCP tools to ChatGPT format
func (c *ChatGPTMCPIntegration) convertMCPToChatGPTTools() []ChatGPTTool {
	var chatgptTools []ChatGPTTool
	for _, tool := range c.tools {
		// Parse the input schema
		var schema map[string]interface{}
		if err := json.Unmarshal(tool.InputSchema, &schema); err != nil {
			continue
		}

		chatgptTool := ChatGPTTool{
			Type: "function",
			Function: ChatGPTFunctionTool{
				Name:        tool.Name,
				Description: tool.Description,
				Parameters:  schema,
			},
		}
		chatgptTools = append(chatgptTools, chatgptTool)
	}
	return chatgptTools
}

// ChatWithTools sends a message to ChatGPT with MCP tools
func (c *ChatGPTMCPIntegration) ChatWithTools(ctx context.Context, userMessage string) (string, error) {
	// Convert MCP tools to ChatGPT format
	chatgptTools := c.convertMCPToChatGPTTools()

	// Create request
	request := ChatGPTRequest{
		Model:      "gpt-4-turbo-preview",
		MaxTokens:  1024,
		ToolChoice: "auto",
		Messages: []ChatGPTMessage{
			{
				Role:    "system",
				Content: "You are an AI assistant with access to Kubernetes PDB management tools. Use the available tools to help the user manage their Kubernetes cluster effectively.",
			},
			{
				Role:    "user",
				Content: userMessage,
			},
		},
		Tools: chatgptTools,
	}

	// Send to ChatGPT
	response, err := c.chatgpt.SendMessage(ctx, request)
	if err != nil {
		return "", fmt.Errorf("failed to send message to ChatGPT: %w", err)
	}

	if len(response.Choices) == 0 {
		return "No response from ChatGPT", nil
	}

	choice := response.Choices[0]
	var result strings.Builder

	// Handle text response
	if choice.Message.Content != "" {
		result.WriteString(choice.Message.Content)
	}

	// Handle tool calls
	for _, toolCall := range choice.Message.ToolCalls {
		if toolCall.Type == "function" {
			fmt.Printf("\nChatGPT is calling tool: %s\n", toolCall.Function.Name)

			// Parse arguments
			var arguments map[string]interface{}
			if err := json.Unmarshal([]byte(toolCall.Function.Arguments), &arguments); err != nil {
				fmt.Printf("Error parsing tool arguments: %v\n", err)
				continue
			}

			// Call MCP tool
			toolResult, err := c.mcp.CallTool(toolCall.Function.Name, arguments)
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

// AnalyzeNamespace asks ChatGPT to analyze a namespace
func (c *ChatGPTMCPIntegration) AnalyzeNamespace(ctx context.Context, namespace string) (string, error) {
	prompt := fmt.Sprintf("Analyze the availability status of the %s namespace and provide recommendations.", namespace)
	return c.ChatWithTools(ctx, prompt)
}

// RecommendPolicies asks ChatGPT to recommend policies
func (c *ChatGPTMCPIntegration) RecommendPolicies(ctx context.Context, namespace string) (string, error) {
	prompt := fmt.Sprintf("What availability policies do you recommend for the %s namespace? "+
		"Analyze the current deployments and suggest optimal configurations.", namespace)
	return c.ChatWithTools(ctx, prompt)
}

func main() {
	// Check for API key
	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" {
		fmt.Println("Error: Please set OPENAI_API_KEY environment variable")
		fmt.Println("Export it with: export OPENAI_API_KEY='your-api-key'")
		os.Exit(1)
	}

	// Create integration
	fmt.Println("Initializing ChatGPT + MCP integration...")
	fmt.Println("Make sure port-forward is running:")
	fmt.Println("kubectl port-forward -n canvas svc/pdb-management-mcp-service 8090:8090")
	fmt.Println(strings.Repeat("-", 50))

	integration, err := NewChatGPTMCPIntegration(apiKey, "")
	if err != nil {
		fmt.Printf("Failed to initialize: %v\n", err)
		fmt.Println("\nTroubleshooting:")
		fmt.Println("1. Check port-forward is running")
		fmt.Println("2. Check MCP server is healthy: curl http://localhost:8090/health")
		fmt.Println("3. Verify OPENAI_API_KEY is set correctly")
		os.Exit(1)
	}

	// Interactive mode
	fmt.Println("\nChatGPT + MCP Integration Ready!")
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
			fmt.Printf("\nChatGPT: %s\n", response)
		}
	}
}