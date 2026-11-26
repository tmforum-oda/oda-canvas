package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// AIProvider represents different AI service providers
type AIProvider string

const (
	ProviderClaude     AIProvider = "claude"
	ProviderOpenAI     AIProvider = "openai"
	ProviderAzureOpenAI AIProvider = "azure-openai"
	ProviderGemini     AIProvider = "gemini"
)

// Config holds the client configuration
type Config struct {
	Provider    AIProvider
	Model       string
	APIKey      string
	BaseURL     string // For Azure OpenAI and custom endpoints
	MCPServerURL string
	Timeout     time.Duration
}

// MCPClient handles MCP server communication (reused)
type MCPClient struct {
	url        string
	httpClient *http.Client
	initialized bool
}

// MCPRequest, MCPResponse, MCPTool - reuse from previous implementations
type MCPRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      string          `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type MCPResponse struct {
	ID     string          `json:"id"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  *MCPError       `json:"error,omitempty"`
}

type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type MCPTool struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"inputSchema"`
}

// AIClient interface for different AI providers
type AIClient interface {
	SendMessage(ctx context.Context, message string, tools []MCPTool) (*AIResponse, error)
	GetProviderName() string
}

// Generic AI response structure
type AIResponse struct {
	Content   string
	ToolCalls []ToolCall
}

type ToolCall struct {
	Name      string
	Arguments map[string]interface{}
}

// ClaudeClient implements AIClient for Anthropic Claude
type ClaudeClient struct {
	apiKey     string
	model      string
	httpClient *http.Client
}

// OpenAIClient implements AIClient for OpenAI and Azure OpenAI
type OpenAIClient struct {
	apiKey     string
	model      string
	baseURL    string
	httpClient *http.Client
	isAzure    bool
}

// GeminiClient implements AIClient for Google Gemini
type GeminiClient struct {
	apiKey     string
	model      string
	httpClient *http.Client
}

// Claude-specific types
type ClaudeRequest struct {
	Model     string                 `json:"model"`
	MaxTokens int                    `json:"max_tokens"`
	System    string                 `json:"system,omitempty"`
	Messages  []ClaudeMessage        `json:"messages"`
	Tools     []ClaudeToolDefinition `json:"tools,omitempty"`
}

type ClaudeMessage struct {
	Role    string          `json:"role"`
	Content json.RawMessage `json:"content"`
}

type ClaudeToolDefinition struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"input_schema"`
}

type ClaudeResponse struct {
	Content []ClaudeContentBlock `json:"content"`
}

type ClaudeContentBlock struct {
	Type  string          `json:"type"`
	Text  string          `json:"text,omitempty"`
	Name  string          `json:"name,omitempty"`
	Input json.RawMessage `json:"input,omitempty"`
}

// OpenAI-specific types
type OpenAIRequest struct {
	Model      string              `json:"model"`
	Messages   []OpenAIMessage     `json:"messages"`
	Tools      []OpenAITool        `json:"tools,omitempty"`
	ToolChoice string              `json:"tool_choice,omitempty"`
	MaxTokens  int                 `json:"max_tokens,omitempty"`
}

type OpenAIMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type OpenAITool struct {
	Type     string           `json:"type"`
	Function OpenAIFunction   `json:"function"`
}

type OpenAIFunction struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
}

type OpenAIResponse struct {
	Choices []OpenAIChoice `json:"choices"`
}

type OpenAIChoice struct {
	Message OpenAIResponseMessage `json:"message"`
}

type OpenAIResponseMessage struct {
	Content   string             `json:"content,omitempty"`
	ToolCalls []OpenAIToolCall   `json:"tool_calls,omitempty"`
}

type OpenAIToolCall struct {
	Function OpenAIFunctionCall `json:"function"`
}

type OpenAIFunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

// Gemini-specific types
type GeminiRequest struct {
	Contents []GeminiContent `json:"contents"`
	Tools    []GeminiTool    `json:"tools,omitempty"`
}

type GeminiContent struct {
	Role  string        `json:"role"`
	Parts []GeminiPart  `json:"parts"`
}

type GeminiPart struct {
	Text string `json:"text"`
}

type GeminiTool struct {
	FunctionDeclarations []GeminiFunction `json:"functionDeclarations"`
}

type GeminiFunction struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
}

type GeminiResponse struct {
	Candidates []GeminiCandidate `json:"candidates"`
}

type GeminiCandidate struct {
	Content GeminiContent `json:"content"`
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

// MCP Client methods (reuse from previous implementations)
func (m *MCPClient) Initialize() error {
	params := map[string]interface{}{
		"protocolVersion": "2024-11-05",
		"clientInfo": map[string]string{
			"name":    "generic-mcp-client",
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
	return nil
}

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

// ClaudeClient implementation
func NewClaudeClient(apiKey, model string) *ClaudeClient {
	if model == "" {
		model = "claude-3-haiku-20240307"
	}
	return &ClaudeClient{
		apiKey: apiKey,
		model:  model,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

func (c *ClaudeClient) GetProviderName() string {
	return "Claude (" + c.model + ")"
}

func (c *ClaudeClient) SendMessage(ctx context.Context, message string, tools []MCPTool) (*AIResponse, error) {
	// Convert MCP tools to Claude format
	var claudeTools []ClaudeToolDefinition
	for _, tool := range tools {
		claudeTools = append(claudeTools, ClaudeToolDefinition{
			Name:        tool.Name,
			Description: tool.Description,
			InputSchema: tool.InputSchema,
		})
	}

	messageContent, _ := json.Marshal(message)
	request := ClaudeRequest{
		Model:     c.model,
		MaxTokens: 1024,
		System:    "You are an AI assistant with access to Kubernetes PDB management tools.",
		Messages: []ClaudeMessage{
			{
				Role:    "user",
				Content: messageContent,
			},
		},
		Tools: claudeTools,
	}

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

	// Convert to generic response
	aiResponse := &AIResponse{}
	for _, content := range response.Content {
		switch content.Type {
		case "text":
			aiResponse.Content += content.Text
		case "tool_use":
			var arguments map[string]interface{}
			json.Unmarshal(content.Input, &arguments)
			aiResponse.ToolCalls = append(aiResponse.ToolCalls, ToolCall{
				Name:      content.Name,
				Arguments: arguments,
			})
		}
	}

	return aiResponse, nil
}

// OpenAIClient implementation
func NewOpenAIClient(apiKey, model, baseURL string, isAzure bool) *OpenAIClient {
	if model == "" {
		if isAzure {
			model = "gpt-4"
		} else {
			model = "gpt-4-turbo-preview"
		}
	}
	if baseURL == "" {
		if isAzure {
			baseURL = "https://YOUR_RESOURCE.openai.azure.com" // User needs to set this
		} else {
			baseURL = "https://api.openai.com"
		}
	}

	return &OpenAIClient{
		apiKey:  apiKey,
		model:   model,
		baseURL: baseURL,
		isAzure: isAzure,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

func (c *OpenAIClient) GetProviderName() string {
	provider := "OpenAI"
	if c.isAzure {
		provider = "Azure OpenAI"
	}
	return fmt.Sprintf("%s (%s)", provider, c.model)
}

func (c *OpenAIClient) SendMessage(ctx context.Context, message string, tools []MCPTool) (*AIResponse, error) {
	// Convert MCP tools to OpenAI format
	var openaiTools []OpenAITool
	for _, tool := range tools {
		var schema map[string]interface{}
		json.Unmarshal(tool.InputSchema, &schema)

		openaiTools = append(openaiTools, OpenAITool{
			Type: "function",
			Function: OpenAIFunction{
				Name:        tool.Name,
				Description: tool.Description,
				Parameters:  schema,
			},
		})
	}

	request := OpenAIRequest{
		Model:      c.model,
		MaxTokens:  1024,
		ToolChoice: "auto",
		Messages: []OpenAIMessage{
			{
				Role:    "system",
				Content: "You are an AI assistant with access to Kubernetes PDB management tools.",
			},
			{
				Role:    "user",
				Content: message,
			},
		},
		Tools: openaiTools,
	}

	reqBody, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	endpoint := "/v1/chat/completions"
	if c.isAzure {
		endpoint = fmt.Sprintf("/openai/deployments/%s/chat/completions?api-version=2023-12-01-preview", c.model)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+endpoint, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	if c.isAzure {
		req.Header.Set("api-key", c.apiKey)
	} else {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))
	}

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

	var response OpenAIResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to parse OpenAI response: %w", err)
	}

	if len(response.Choices) == 0 {
		return &AIResponse{Content: "No response"}, nil
	}

	// Convert to generic response
	choice := response.Choices[0]
	aiResponse := &AIResponse{
		Content: choice.Message.Content,
	}

	for _, toolCall := range choice.Message.ToolCalls {
		var arguments map[string]interface{}
		json.Unmarshal([]byte(toolCall.Function.Arguments), &arguments)
		aiResponse.ToolCalls = append(aiResponse.ToolCalls, ToolCall{
			Name:      toolCall.Function.Name,
			Arguments: arguments,
		})
	}

	return aiResponse, nil
}

// GeminiClient implementation
func NewGeminiClient(apiKey, model string) *GeminiClient {
	if model == "" {
		model = "gemini-pro"
	}
	return &GeminiClient{
		apiKey: apiKey,
		model:  model,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

func (c *GeminiClient) GetProviderName() string {
	return "Google Gemini (" + c.model + ")"
}

func (c *GeminiClient) SendMessage(ctx context.Context, message string, tools []MCPTool) (*AIResponse, error) {
	// Convert MCP tools to Gemini format
	var geminiTools []GeminiTool
	if len(tools) > 0 {
		var functions []GeminiFunction
		for _, tool := range tools {
			var schema map[string]interface{}
			json.Unmarshal(tool.InputSchema, &schema)

			functions = append(functions, GeminiFunction{
				Name:        tool.Name,
				Description: tool.Description,
				Parameters:  schema,
			})
		}
		geminiTools = append(geminiTools, GeminiTool{
			FunctionDeclarations: functions,
		})
	}

	request := GeminiRequest{
		Contents: []GeminiContent{
			{
				Role: "user",
				Parts: []GeminiPart{
					{Text: message},
				},
			},
		},
		Tools: geminiTools,
	}

	reqBody, err := json.Marshal(request)
	if err != nil {
		return nil, err
	}

	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", c.model, c.apiKey)
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")

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
		return nil, fmt.Errorf("Gemini API error (status %d): %s", resp.StatusCode, string(body))
	}

	var response GeminiResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to parse Gemini response: %w", err)
	}

	if len(response.Candidates) == 0 {
		return &AIResponse{Content: "No response"}, nil
	}

	// Convert to generic response
	candidate := response.Candidates[0]
	aiResponse := &AIResponse{}
	for _, part := range candidate.Content.Parts {
		aiResponse.Content += part.Text
	}

	// Note: Gemini function calling implementation would need more complex parsing
	// This is a simplified version

	return aiResponse, nil
}

// GenericMCPIntegration ties everything together
type GenericMCPIntegration struct {
	aiClient AIClient
	mcp      *MCPClient
	tools    []MCPTool
}

func NewGenericMCPIntegration(config Config) (*GenericMCPIntegration, error) {
	// Create AI client based on provider
	var aiClient AIClient
	switch config.Provider {
	case ProviderClaude:
		aiClient = NewClaudeClient(config.APIKey, config.Model)
	case ProviderOpenAI:
		aiClient = NewOpenAIClient(config.APIKey, config.Model, config.BaseURL, false)
	case ProviderAzureOpenAI:
		aiClient = NewOpenAIClient(config.APIKey, config.Model, config.BaseURL, true)
	case ProviderGemini:
		aiClient = NewGeminiClient(config.APIKey, config.Model)
	default:
		return nil, fmt.Errorf("unsupported provider: %s", config.Provider)
	}

	// Create MCP client
	mcp := NewMCPClient(config.MCPServerURL)
	if err := mcp.Initialize(); err != nil {
		return nil, fmt.Errorf("failed to initialize MCP: %w", err)
	}

	// Load tools
	tools, err := mcp.ListTools()
	if err != nil {
		return nil, fmt.Errorf("failed to load MCP tools: %w", err)
	}

	return &GenericMCPIntegration{
		aiClient: aiClient,
		mcp:      mcp,
		tools:    tools,
	}, nil
}

func (g *GenericMCPIntegration) ChatWithTools(ctx context.Context, userMessage string) (string, error) {
	// Send to AI provider
	response, err := g.aiClient.SendMessage(ctx, userMessage, g.tools)
	if err != nil {
		return "", fmt.Errorf("failed to send message to AI: %w", err)
	}

	var result strings.Builder
	result.WriteString(response.Content)

	// Handle tool calls
	for _, toolCall := range response.ToolCalls {
		fmt.Printf("\n%s is calling tool: %s\n", g.aiClient.GetProviderName(), toolCall.Name)

		toolResult, err := g.mcp.CallTool(toolCall.Name, toolCall.Arguments)
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

	return result.String(), nil
}

func main() {
	// Parse command line flags
	var (
		provider = flag.String("provider", "claude", "AI provider (claude, openai, azure-openai, gemini)")
		model    = flag.String("model", "", "AI model name (provider-specific)")
		apiKey   = flag.String("api-key", "", "API key for the provider")
		baseURL  = flag.String("base-url", "", "Base URL for Azure OpenAI or custom endpoints")
		mcpURL   = flag.String("mcp-url", "http://localhost:8090/mcp", "MCP server URL")
		message  = flag.String("message", "", "Single message to send (non-interactive mode)")
	)
	flag.Parse()

	// Validate provider
	validProviders := map[string]AIProvider{
		"claude":       ProviderClaude,
		"openai":       ProviderOpenAI,
		"azure-openai": ProviderAzureOpenAI,
		"gemini":       ProviderGemini,
	}

	providerEnum, ok := validProviders[*provider]
	if !ok {
		fmt.Printf("Invalid provider: %s\n", *provider)
		fmt.Println("Valid providers: claude, openai, azure-openai, gemini")
		os.Exit(1)
	}

	// Get API key from environment if not provided
	if *apiKey == "" {
		envKeys := map[AIProvider]string{
			ProviderClaude:      "ANTHROPIC_API_KEY",
			ProviderOpenAI:      "OPENAI_API_KEY",
			ProviderAzureOpenAI: "AZURE_OPENAI_API_KEY",
			ProviderGemini:      "GEMINI_API_KEY",
		}
		*apiKey = os.Getenv(envKeys[providerEnum])
	}

	if *apiKey == "" {
		fmt.Printf("API key required for %s provider\n", *provider)
		os.Exit(1)
	}

	// Create configuration
	config := Config{
		Provider:     providerEnum,
		Model:        *model,
		APIKey:       *apiKey,
		BaseURL:      *baseURL,
		MCPServerURL: *mcpURL,
		Timeout:      60 * time.Second,
	}

	// Initialize integration
	fmt.Printf("Initializing %s + MCP integration...\n", strings.Title(*provider))
	integration, err := NewGenericMCPIntegration(config)
	if err != nil {
		fmt.Printf("Failed to initialize: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("MCP server initialized successfully\n")
	fmt.Printf("Loaded %d MCP tools\n", len(integration.tools))
	fmt.Printf("Using %s\n", integration.aiClient.GetProviderName())

	ctx := context.Background()

	// Single message mode
	if *message != "" {
		response, err := integration.ChatWithTools(ctx, *message)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
		} else {
			fmt.Printf("\n%s: %s\n", integration.aiClient.GetProviderName(), response)
		}
		return
	}

	// Interactive mode
	fmt.Println("\nGeneric MCP Integration Ready!")
	fmt.Println("Type your message or 'quit' to exit")
	fmt.Println(strings.Repeat("-", 50))

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
			fmt.Printf("\n%s: %s\n", integration.aiClient.GetProviderName(), response)
		}
	}
}