package ai

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/go-logr/logr"
)

// Provider represents different AI providers
type Provider string

const (
	ProviderClaude      Provider = "claude"
	ProviderOpenAI      Provider = "openai"
	ProviderAzureOpenAI Provider = "azure-openai"
	ProviderGemini      Provider = "gemini"
)

// Config holds AI provider configuration
type Config struct {
	Provider    Provider `json:"provider"`
	APIKey      string   `json:"apiKey"`
	BaseURL     string   `json:"baseURL,omitempty"`
	Model       string   `json:"model,omitempty"`
	MaxTokens   int      `json:"maxTokens,omitempty"`
	Temperature float64  `json:"temperature,omitempty"`
}

// Message represents a chat message
type Message struct {
	ID        string     `json:"id"`
	Role      string     `json:"role"`
	Content   string     `json:"content"`
	Timestamp time.Time  `json:"timestamp"`
	ToolCalls []ToolCall `json:"toolCalls,omitempty"`
}

// ToolCall represents a tool call from the AI
type ToolCall struct {
	ID         string                 `json:"id"`
	Name       string                 `json:"name"`
	Parameters map[string]interface{} `json:"parameters"`
}

// ChatRequest represents a chat request
type ChatRequest struct {
	Messages    []Message `json:"messages"`
	Tools       []Tool    `json:"tools,omitempty"`
	ToolChoice  string    `json:"toolChoice,omitempty"`
	Stream      bool      `json:"stream,omitempty"`
	MaxTokens   int       `json:"maxTokens,omitempty"`
	Temperature float64   `json:"temperature,omitempty"`
}

// Tool represents an available tool
type Tool struct {
	Type     string       `json:"type"`
	Function ToolFunction `json:"function"`
}

// ToolFunction represents a tool function definition
type ToolFunction struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters"`
}

// ChatResponse represents a chat response
type ChatResponse struct {
	Message Message `json:"message"`
	Usage   *Usage  `json:"usage,omitempty"`
}

// Usage represents token usage information
type Usage struct {
	PromptTokens     int `json:"promptTokens"`
	CompletionTokens int `json:"completionTokens"`
	TotalTokens      int `json:"totalTokens"`
}

// Client handles AI provider requests
type Client struct {
	httpClient *http.Client
	logger     logr.Logger
}

// NewClient creates a new AI client
func NewClient(logger logr.Logger) *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // 2 minutes for AI responses
		},
		logger: logger,
	}
}

// Chat sends a chat request to the AI provider
func (c *Client) Chat(ctx context.Context, config Config, request ChatRequest) (*ChatResponse, error) {
	baseURL := c.getDefaultBaseURL(config.Provider, config.BaseURL)
	endpoint := c.getProviderEndpoint(config.Provider, config.Model)
	headers := c.getProviderHeaders(config)

	payload, err := c.buildProviderPayload(config, request)
	if err != nil {
		return nil, fmt.Errorf("failed to build payload: %w", err)
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	c.logger.V(1).Info("Making AI provider request",
		"provider", config.Provider,
		"endpoint", endpoint,
		"messageCount", len(request.Messages))

	req, err := http.NewRequestWithContext(ctx, "POST", baseURL+endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	for key, value := range headers {
		req.Header.Set(key, value)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed: %d %s - %s",
			resp.StatusCode, resp.Status, string(body))
	}

	var responseData map[string]interface{}
	if err := json.Unmarshal(body, &responseData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return c.parseProviderResponse(config.Provider, responseData)
}

func (c *Client) getDefaultBaseURL(provider Provider, customBaseURL string) string {
	if customBaseURL != "" {
		return customBaseURL
	}

	switch provider {
	case ProviderClaude:
		return "https://api.anthropic.com"
	case ProviderOpenAI:
		return "https://api.openai.com"
	case ProviderAzureOpenAI:
		return "https://your-resource.openai.azure.com" // This should be configured per deployment
	case ProviderGemini:
		return "https://generativelanguage.googleapis.com"
	default:
		return ""
	}
}

func (c *Client) getProviderEndpoint(provider Provider, model string) string {
	switch provider {
	case ProviderClaude:
		return "/v1/messages"
	case ProviderOpenAI:
		return "/v1/chat/completions"
	case ProviderAzureOpenAI:
		if model == "" {
			model = "gpt-4"
		}
		return fmt.Sprintf("/openai/deployments/%s/chat/completions?api-version=2024-02-15-preview", model)
	case ProviderGemini:
		if model == "" {
			model = "gemini-pro"
		}
		return fmt.Sprintf("/v1beta/models/%s:generateContent", model)
	default:
		return ""
	}
}

func (c *Client) getProviderHeaders(config Config) map[string]string {
	headers := map[string]string{
		"Content-Type": "application/json",
	}

	switch config.Provider {
	case ProviderClaude:
		headers["x-api-key"] = config.APIKey
		headers["anthropic-version"] = "2023-06-01"
	case ProviderOpenAI:
		headers["Authorization"] = fmt.Sprintf("Bearer %s", config.APIKey)
	case ProviderAzureOpenAI:
		headers["api-key"] = config.APIKey
	case ProviderGemini:
		// Use x-goog-api-key header for Gemini (more secure than query parameter)
		headers["x-goog-api-key"] = config.APIKey
	}

	return headers
}

func (c *Client) buildProviderPayload(config Config, request ChatRequest) (map[string]interface{}, error) {
	maxTokens := config.MaxTokens
	if maxTokens == 0 {
		maxTokens = 4000
	}
	if request.MaxTokens > 0 {
		maxTokens = request.MaxTokens
	}

	temperature := config.Temperature
	if temperature == 0 {
		temperature = 0.7
	}
	if request.Temperature > 0 {
		temperature = request.Temperature
	}

	model := config.Model
	if model == "" {
		switch config.Provider {
		case ProviderClaude:
			model = "claude-3-sonnet-20240229"
		case ProviderOpenAI:
			model = "gpt-4"
		case ProviderAzureOpenAI:
			model = "gpt-4"
		case ProviderGemini:
			model = "gemini-pro"
		}
	}

	switch config.Provider {
	case ProviderClaude:
		payload := map[string]interface{}{
			"model":       model,
			"max_tokens":  maxTokens,
			"temperature": temperature,
			"messages":    c.formatMessagesForClaude(request.Messages),
		}

		// Handle system message separately for Claude
		systemMessage := c.findSystemMessage(request.Messages)
		if systemMessage != "" {
			payload["system"] = systemMessage
		}

		if len(request.Tools) > 0 {
			// Convert tools from OpenAI format to Claude format
			claudeTools := c.convertToolsForClaude(request.Tools)
			if len(claudeTools) > 0 {
				payload["tools"] = claudeTools
			}
		}

		return payload, nil

	case ProviderOpenAI, ProviderAzureOpenAI:
		payload := map[string]interface{}{
			"model":       model,
			"max_tokens":  maxTokens,
			"temperature": temperature,
			"messages":    c.formatMessagesForOpenAI(request.Messages),
		}

		if len(request.Tools) > 0 {
			payload["tools"] = request.Tools
			payload["tool_choice"] = "auto"
		}

		return payload, nil

	case ProviderGemini:
		payload := map[string]interface{}{
			"contents": c.formatMessagesForGemini(request.Messages),
			"generationConfig": map[string]interface{}{
				"temperature":     temperature,
				"maxOutputTokens": maxTokens,
			},
		}

		return payload, nil

	default:
		return nil, fmt.Errorf("unsupported provider: %s", config.Provider)
	}
}

func (c *Client) formatMessagesForClaude(messages []Message) []map[string]interface{} {
	var formatted []map[string]interface{}
	for _, msg := range messages {
		if msg.Role == "system" {
			continue // System messages are handled separately in Claude
		}
		role := msg.Role
		if role == "assistant" {
			role = "assistant"
		} else {
			role = "user"
		}
		formatted = append(formatted, map[string]interface{}{
			"role":    role,
			"content": msg.Content,
		})
	}
	return formatted
}

func (c *Client) formatMessagesForOpenAI(messages []Message) []map[string]interface{} {
	var formatted []map[string]interface{}
	for _, msg := range messages {
		formatted = append(formatted, map[string]interface{}{
			"role":    msg.Role,
			"content": msg.Content,
		})
	}
	return formatted
}

func (c *Client) formatMessagesForGemini(messages []Message) []map[string]interface{} {
	var formatted []map[string]interface{}
	for _, msg := range messages {
		if msg.Role == "system" {
			continue // Gemini doesn't support system messages
		}
		role := msg.Role
		if role == "assistant" {
			role = "model"
		} else {
			role = "user"
		}
		formatted = append(formatted, map[string]interface{}{
			"role": role,
			"parts": []map[string]string{
				{"text": msg.Content},
			},
		})
	}
	return formatted
}

func (c *Client) findSystemMessage(messages []Message) string {
	for _, msg := range messages {
		if msg.Role == "system" {
			return msg.Content
		}
	}
	return ""
}

// convertToolsForClaude converts tools from OpenAI format to Claude format
// OpenAI format: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
// Claude format: {"name": "...", "description": "...", "input_schema": {...}}
func (c *Client) convertToolsForClaude(tools []Tool) []map[string]interface{} {
	var claudeTools []map[string]interface{}

	for _, tool := range tools {
		// Handle both OpenAI format (with function wrapper) and direct format
		name := tool.Function.Name
		description := tool.Function.Description
		parameters := tool.Function.Parameters

		// Skip tools without a name
		if name == "" {
			continue
		}

		claudeTool := map[string]interface{}{
			"name":        name,
			"description": description,
		}

		// Convert parameters to input_schema for Claude
		if parameters != nil {
			claudeTool["input_schema"] = parameters
		} else {
			// Default empty schema
			claudeTool["input_schema"] = map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			}
		}

		claudeTools = append(claudeTools, claudeTool)
	}

	return claudeTools
}

func (c *Client) parseProviderResponse(provider Provider, data map[string]interface{}) (*ChatResponse, error) {
	switch provider {
	case ProviderClaude:
		return c.parseClaudeResponse(data)
	case ProviderOpenAI, ProviderAzureOpenAI:
		return c.parseOpenAIResponse(data)
	case ProviderGemini:
		return c.parseGeminiResponse(data)
	default:
		return nil, fmt.Errorf("unsupported provider: %s", provider)
	}
}

func (c *Client) parseClaudeResponse(data map[string]interface{}) (*ChatResponse, error) {
	content, ok := data["content"].([]interface{})
	if !ok || len(content) == 0 {
		return nil, fmt.Errorf("invalid Claude response format")
	}

	var messageContent string
	var toolCalls []ToolCall

	for _, item := range content {
		itemMap, ok := item.(map[string]interface{})
		if !ok {
			continue
		}

		if itemType, exists := itemMap["type"].(string); exists {
			switch itemType {
			case "text":
				if text, ok := itemMap["text"].(string); ok {
					messageContent = text
				}
			case "tool_use":
				if toolID, ok := itemMap["id"].(string); ok {
					if toolName, ok := itemMap["name"].(string); ok {
						if toolInput, ok := itemMap["input"].(map[string]interface{}); ok {
							toolCalls = append(toolCalls, ToolCall{
								ID:         toolID,
								Name:       toolName,
								Parameters: toolInput,
							})
						}
					}
				}
			}
		}
	}

	return &ChatResponse{
		Message: Message{
			Role:      "assistant",
			Content:   messageContent,
			Timestamp: time.Now(),
			ToolCalls: toolCalls,
		},
	}, nil
}

func (c *Client) parseOpenAIResponse(data map[string]interface{}) (response *ChatResponse, err error) {
	// Recover from panics caused by unexpected response format
	defer func() {
		if r := recover(); r != nil {
			c.logger.Error(nil, "Panic in parseOpenAIResponse", "panic", r)
			err = fmt.Errorf("failed to parse OpenAI response: %v", r)
			response = nil
		}
	}()

	choices, ok := data["choices"].([]interface{})
	if !ok || len(choices) == 0 {
		return nil, fmt.Errorf("invalid OpenAI response format: missing choices")
	}

	choice, ok := choices[0].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid OpenAI response format: invalid choice structure")
	}

	message, ok := choice["message"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid OpenAI response format: invalid message structure")
	}

	content := ""
	if msgContent, ok := message["content"].(string); ok {
		content = msgContent
	}

	var toolCalls []ToolCall
	if toolCallsData, exists := message["tool_calls"].([]interface{}); exists {
		for _, tc := range toolCallsData {
			toolCallMap, ok := tc.(map[string]interface{})
			if !ok {
				continue
			}
			function, ok := toolCallMap["function"].(map[string]interface{})
			if !ok {
				continue
			}

			var parameters map[string]interface{}
			if args, ok := function["arguments"].(string); ok {
				if err := json.Unmarshal([]byte(args), &parameters); err != nil {
					c.logger.V(1).Info("Failed to parse tool call arguments", "error", err)
				}
			}

			id, _ := toolCallMap["id"].(string)
			name, _ := function["name"].(string)
			if name != "" {
				toolCalls = append(toolCalls, ToolCall{
					ID:         id,
					Name:       name,
					Parameters: parameters,
				})
			}
		}
	}

	return &ChatResponse{
		Message: Message{
			Role:      "assistant",
			Content:   content,
			Timestamp: time.Now(),
			ToolCalls: toolCalls,
		},
	}, nil
}

func (c *Client) parseGeminiResponse(data map[string]interface{}) (response *ChatResponse, err error) {
	// Recover from panics caused by unexpected response format
	defer func() {
		if r := recover(); r != nil {
			c.logger.Error(nil, "Panic in parseGeminiResponse", "panic", r)
			err = fmt.Errorf("failed to parse Gemini response: %v", r)
			response = nil
		}
	}()

	candidates, ok := data["candidates"].([]interface{})
	if !ok || len(candidates) == 0 {
		return nil, fmt.Errorf("invalid Gemini response format: missing candidates")
	}

	candidate, ok := candidates[0].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid Gemini response format: invalid candidate structure")
	}

	content, ok := candidate["content"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid Gemini response format: missing content")
	}

	parts, ok := content["parts"].([]interface{})
	if !ok || len(parts) == 0 {
		return nil, fmt.Errorf("invalid Gemini response format: missing parts")
	}

	part, ok := parts[0].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid Gemini response format: invalid part structure")
	}

	text, _ := part["text"].(string)

	return &ChatResponse{
		Message: Message{
			Role:      "assistant",
			Content:   text,
			Timestamp: time.Now(),
			ToolCalls: []ToolCall{},
		},
	}, nil
}
