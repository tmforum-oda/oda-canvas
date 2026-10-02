package ai

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/go-logr/logr/testr"
	"github.com/stretchr/testify/assert"
)

func TestNewClient(t *testing.T) {
	logger := testr.New(t)
	client := NewClient(logger)

	assert.NotNil(t, client)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, 120*time.Second, client.httpClient.Timeout)
	assert.Equal(t, logger, client.logger)
}

func TestProvider(t *testing.T) {
	assert.Equal(t, Provider("claude"), ProviderClaude)
	assert.Equal(t, Provider("openai"), ProviderOpenAI)
	assert.Equal(t, Provider("azure-openai"), ProviderAzureOpenAI)
	assert.Equal(t, Provider("gemini"), ProviderGemini)
}

func TestGetDefaultBaseURL(t *testing.T) {
	client := &Client{}

	tests := []struct {
		provider    Provider
		customURL   string
		expectedURL string
	}{
		{ProviderClaude, "", "https://api.anthropic.com"},
		{ProviderOpenAI, "", "https://api.openai.com"},
		{ProviderAzureOpenAI, "", "https://your-resource.openai.azure.com"},
		{ProviderGemini, "", "https://generativelanguage.googleapis.com"},
		{ProviderClaude, "https://custom.api.com", "https://custom.api.com"},
		{Provider("unknown"), "", ""},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("%s_%s", tt.provider, tt.customURL), func(t *testing.T) {
			result := client.getDefaultBaseURL(tt.provider, tt.customURL)
			assert.Equal(t, tt.expectedURL, result)
		})
	}
}

func TestGetProviderEndpoint(t *testing.T) {
	client := &Client{}

	tests := []struct {
		provider Provider
		model    string
		expected string
	}{
		{ProviderClaude, "", "/v1/messages"},
		{ProviderClaude, "claude-3", "/v1/messages"},
		{ProviderOpenAI, "", "/v1/chat/completions"},
		{ProviderOpenAI, "gpt-4", "/v1/chat/completions"},
		{ProviderAzureOpenAI, "", "/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview"},
		{ProviderAzureOpenAI, "gpt-35-turbo", "/openai/deployments/gpt-35-turbo/chat/completions?api-version=2024-02-15-preview"},
		{ProviderGemini, "", "/v1beta/models/gemini-pro:generateContent"},
		{ProviderGemini, "gemini-pro-vision", "/v1beta/models/gemini-pro-vision:generateContent"},
		{Provider("unknown"), "", ""},
	}

	for _, tt := range tests {
		t.Run(fmt.Sprintf("%s_%s", tt.provider, tt.model), func(t *testing.T) {
			result := client.getProviderEndpoint(tt.provider, tt.model)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGetProviderHeaders(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name     string
		config   Config
		expected map[string]string
	}{
		{
			name: "Claude headers",
			config: Config{
				Provider: ProviderClaude,
				APIKey:   "test-key",
			},
			expected: map[string]string{
				"Content-Type":      "application/json",
				"x-api-key":         "test-key",
				"anthropic-version": "2023-06-01",
			},
		},
		{
			name: "OpenAI headers",
			config: Config{
				Provider: ProviderOpenAI,
				APIKey:   "test-key",
			},
			expected: map[string]string{
				"Content-Type":  "application/json",
				"Authorization": "Bearer test-key",
			},
		},
		{
			name: "Azure OpenAI headers",
			config: Config{
				Provider: ProviderAzureOpenAI,
				APIKey:   "test-key",
			},
			expected: map[string]string{
				"Content-Type": "application/json",
				"api-key":      "test-key",
			},
		},
		{
			name: "Gemini headers",
			config: Config{
				Provider: ProviderGemini,
				APIKey:   "test-key",
			},
			expected: map[string]string{
				"Content-Type":   "application/json",
				"x-goog-api-key": "test-key",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := client.getProviderHeaders(tt.config)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestFormatMessagesForClaude(t *testing.T) {
	client := &Client{}

	messages := []Message{
		{Role: "system", Content: "You are a helpful assistant"},
		{Role: "user", Content: "Hello"},
		{Role: "assistant", Content: "Hi there!"},
	}

	result := client.formatMessagesForClaude(messages)

	// System messages should be filtered out
	assert.Len(t, result, 2)
	assert.Equal(t, "user", result[0]["role"])
	assert.Equal(t, "Hello", result[0]["content"])
	assert.Equal(t, "assistant", result[1]["role"])
	assert.Equal(t, "Hi there!", result[1]["content"])
}

func TestFormatMessagesForOpenAI(t *testing.T) {
	client := &Client{}

	messages := []Message{
		{Role: "system", Content: "You are a helpful assistant"},
		{Role: "user", Content: "Hello"},
		{Role: "assistant", Content: "Hi there!"},
	}

	result := client.formatMessagesForOpenAI(messages)

	// All messages should be preserved
	assert.Len(t, result, 3)
	assert.Equal(t, "system", result[0]["role"])
	assert.Equal(t, "You are a helpful assistant", result[0]["content"])
	assert.Equal(t, "user", result[1]["role"])
	assert.Equal(t, "Hello", result[1]["content"])
	assert.Equal(t, "assistant", result[2]["role"])
	assert.Equal(t, "Hi there!", result[2]["content"])
}

func TestFormatMessagesForGemini(t *testing.T) {
	client := &Client{}

	messages := []Message{
		{Role: "system", Content: "You are a helpful assistant"}, // Should be filtered
		{Role: "user", Content: "Hello"},
		{Role: "assistant", Content: "Hi there!"},
	}

	result := client.formatMessagesForGemini(messages)

	// System messages should be filtered out, assistant becomes model
	assert.Len(t, result, 2)
	assert.Equal(t, "user", result[0]["role"])
	assert.Equal(t, []map[string]string{{"text": "Hello"}}, result[0]["parts"])
	assert.Equal(t, "model", result[1]["role"])
	assert.Equal(t, []map[string]string{{"text": "Hi there!"}}, result[1]["parts"])
}

func TestFindSystemMessage(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name     string
		messages []Message
		expected string
	}{
		{
			name: "system message exists",
			messages: []Message{
				{Role: "system", Content: "You are helpful"},
				{Role: "user", Content: "Hello"},
			},
			expected: "You are helpful",
		},
		{
			name: "no system message",
			messages: []Message{
				{Role: "user", Content: "Hello"},
				{Role: "assistant", Content: "Hi"},
			},
			expected: "",
		},
		{
			name: "multiple system messages - returns first",
			messages: []Message{
				{Role: "system", Content: "First system"},
				{Role: "user", Content: "Hello"},
				{Role: "system", Content: "Second system"},
			},
			expected: "First system",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := client.findSystemMessage(tt.messages)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestBuildProviderPayload(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name        string
		config      Config
		request     ChatRequest
		expectError bool
		checkFields []string
	}{
		{
			name: "Claude payload",
			config: Config{
				Provider:    ProviderClaude,
				Model:       "claude-3-sonnet",
				MaxTokens:   1000,
				Temperature: 0.5,
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "system", Content: "You are helpful"},
					{Role: "user", Content: "Hello"},
				},
			},
			expectError: false,
			checkFields: []string{"model", "max_tokens", "temperature", "messages", "system"},
		},
		{
			name: "OpenAI payload",
			config: Config{
				Provider:    ProviderOpenAI,
				Model:       "gpt-4",
				MaxTokens:   2000,
				Temperature: 0.7,
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "user", Content: "Hello"},
				},
				Tools: []Tool{
					{
						Type: "function",
						Function: ToolFunction{
							Name:        "test_tool",
							Description: "A test tool",
							Parameters:  map[string]interface{}{"type": "object"},
						},
					},
				},
			},
			expectError: false,
			checkFields: []string{"model", "max_tokens", "temperature", "messages", "tools", "tool_choice"},
		},
		{
			name: "Gemini payload",
			config: Config{
				Provider:    ProviderGemini,
				Temperature: 0.3,
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "user", Content: "Hello"},
				},
			},
			expectError: false,
			checkFields: []string{"contents", "generationConfig"},
		},
		{
			name: "Unknown provider",
			config: Config{
				Provider: Provider("unknown"),
			},
			request:     ChatRequest{},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := client.buildProviderPayload(tt.config, tt.request)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)

				for _, field := range tt.checkFields {
					assert.Contains(t, result, field, "Missing required field: %s", field)
				}
			}
		})
	}
}

func TestParseClaudeResponse(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name        string
		data        map[string]interface{}
		expectError bool
		expected    *ChatResponse
	}{
		{
			name: "valid text response",
			data: map[string]interface{}{
				"content": []interface{}{
					map[string]interface{}{
						"type": "text",
						"text": "Hello, how can I help you?",
					},
				},
			},
			expectError: false,
			expected: &ChatResponse{
				Message: Message{
					Role:      "assistant",
					Content:   "Hello, how can I help you?",
					ToolCalls: []ToolCall{},
				},
			},
		},
		{
			name: "response with tool use",
			data: map[string]interface{}{
				"content": []interface{}{
					map[string]interface{}{
						"type": "text",
						"text": "I'll help you with that.",
					},
					map[string]interface{}{
						"type": "tool_use",
						"id":   "tool_123",
						"name": "search",
						"input": map[string]interface{}{
							"query": "test query",
						},
					},
				},
			},
			expectError: false,
			expected: &ChatResponse{
				Message: Message{
					Role:    "assistant",
					Content: "I'll help you with that.",
					ToolCalls: []ToolCall{
						{
							ID:   "tool_123",
							Name: "search",
							Parameters: map[string]interface{}{
								"query": "test query",
							},
						},
					},
				},
			},
		},
		{
			name: "invalid response format",
			data: map[string]interface{}{
				"error": "invalid format",
			},
			expectError: true,
		},
		{
			name: "empty content",
			data: map[string]interface{}{
				"content": []interface{}{},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := client.parseClaudeResponse(tt.data)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, tt.expected.Message.Role, result.Message.Role)
				assert.Equal(t, tt.expected.Message.Content, result.Message.Content)
				assert.Len(t, result.Message.ToolCalls, len(tt.expected.Message.ToolCalls))
				if len(tt.expected.Message.ToolCalls) > 0 {
					assert.Equal(t, tt.expected.Message.ToolCalls[0].Name, result.Message.ToolCalls[0].Name)
				}
			}
		})
	}
}

func TestParseOpenAIResponse(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name        string
		data        map[string]interface{}
		expectError bool
		expected    *ChatResponse
	}{
		{
			name: "valid text response",
			data: map[string]interface{}{
				"choices": []interface{}{
					map[string]interface{}{
						"message": map[string]interface{}{
							"role":    "assistant",
							"content": "Hello! How can I assist you today?",
						},
					},
				},
			},
			expectError: false,
			expected: &ChatResponse{
				Message: Message{
					Role:      "assistant",
					Content:   "Hello! How can I assist you today?",
					ToolCalls: []ToolCall{},
				},
			},
		},
		{
			name: "response with tool calls",
			data: map[string]interface{}{
				"choices": []interface{}{
					map[string]interface{}{
						"message": map[string]interface{}{
							"role":    "assistant",
							"content": nil,
							"tool_calls": []interface{}{
								map[string]interface{}{
									"id": "call_123",
									"function": map[string]interface{}{
										"name":      "search_web",
										"arguments": `{"query": "test"}`,
									},
								},
							},
						},
					},
				},
			},
			expectError: false,
			expected: &ChatResponse{
				Message: Message{
					Role:    "assistant",
					Content: "",
					ToolCalls: []ToolCall{
						{
							ID:   "call_123",
							Name: "search_web",
							Parameters: map[string]interface{}{
								"query": "test",
							},
						},
					},
				},
			},
		},
		{
			name: "invalid response format",
			data: map[string]interface{}{
				"error": "invalid format",
			},
			expectError: true,
		},
		{
			name: "empty choices",
			data: map[string]interface{}{
				"choices": []interface{}{},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := client.parseOpenAIResponse(tt.data)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, tt.expected.Message.Role, result.Message.Role)
				assert.Equal(t, tt.expected.Message.Content, result.Message.Content)
				assert.Len(t, result.Message.ToolCalls, len(tt.expected.Message.ToolCalls))
				if len(tt.expected.Message.ToolCalls) > 0 {
					assert.Equal(t, tt.expected.Message.ToolCalls[0].Name, result.Message.ToolCalls[0].Name)
				}
			}
		})
	}
}

func TestParseGeminiResponse(t *testing.T) {
	client := &Client{}

	tests := []struct {
		name        string
		data        map[string]interface{}
		expectError bool
		expected    string
	}{
		{
			name: "valid response",
			data: map[string]interface{}{
				"candidates": []interface{}{
					map[string]interface{}{
						"content": map[string]interface{}{
							"parts": []interface{}{
								map[string]interface{}{
									"text": "Hello from Gemini!",
								},
							},
						},
					},
				},
			},
			expectError: false,
			expected:    "Hello from Gemini!",
		},
		{
			name: "invalid response format",
			data: map[string]interface{}{
				"error": "invalid format",
			},
			expectError: true,
		},
		{
			name: "empty candidates",
			data: map[string]interface{}{
				"candidates": []interface{}{},
			},
			expectError: true,
		},
		{
			name: "no parts",
			data: map[string]interface{}{
				"candidates": []interface{}{
					map[string]interface{}{
						"content": map[string]interface{}{
							"parts": []interface{}{},
						},
					},
				},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := client.parseGeminiResponse(tt.data)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, "assistant", result.Message.Role)
				assert.Equal(t, tt.expected, result.Message.Content)
				assert.Empty(t, result.Message.ToolCalls)
			}
		})
	}
}

func TestChat_Integration(t *testing.T) {
	// Test different providers with mock HTTP servers
	tests := []struct {
		name           string
		provider       Provider
		config         Config
		request        ChatRequest
		mockResponse   string
		mockStatusCode int
		expectError    bool
	}{
		{
			name:     "Claude successful request",
			provider: ProviderClaude,
			config: Config{
				Provider: ProviderClaude,
				APIKey:   "test-key",
				Model:    "claude-3-sonnet",
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "user", Content: "Hello"},
				},
			},
			mockResponse: `{
				"content": [
					{
						"type": "text",
						"text": "Hello! How can I help you today?"
					}
				]
			}`,
			mockStatusCode: 200,
			expectError:    false,
		},
		{
			name:     "OpenAI successful request",
			provider: ProviderOpenAI,
			config: Config{
				Provider: ProviderOpenAI,
				APIKey:   "test-key",
				Model:    "gpt-4",
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "user", Content: "Hello"},
				},
			},
			mockResponse: `{
				"choices": [
					{
						"message": {
							"role": "assistant",
							"content": "Hello! How can I assist you?"
						}
					}
				]
			}`,
			mockStatusCode: 200,
			expectError:    false,
		},
		{
			name:     "API error response",
			provider: ProviderClaude,
			config: Config{
				Provider: ProviderClaude,
				APIKey:   "invalid-key",
			},
			request: ChatRequest{
				Messages: []Message{
					{Role: "user", Content: "Hello"},
				},
			},
			mockResponse:   `{"error": {"message": "Invalid API key"}}`,
			mockStatusCode: 401,
			expectError:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock server
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.mockStatusCode)
				w.Header().Set("Content-Type", "application/json")
				_, _ = fmt.Fprint(w, tt.mockResponse)
			}))
			defer server.Close()

			// Update config to use mock server
			tt.config.BaseURL = server.URL

			logger := testr.New(t)
			client := NewClient(logger)

			ctx := context.Background()
			result, err := client.Chat(ctx, tt.config, tt.request)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, "assistant", result.Message.Role)
				assert.NotEmpty(t, result.Message.Content)
			}
		})
	}
}

func TestChat_ContextTimeout(t *testing.T) {
	// Create a server that delays response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond) // Small delay
		w.WriteHeader(200)
		_, _ = fmt.Fprint(w, `{"content": [{"type": "text", "text": "response"}]}`)
	}))
	defer server.Close()

	config := Config{
		Provider: ProviderClaude,
		APIKey:   "test-key",
		BaseURL:  server.URL,
	}

	request := ChatRequest{
		Messages: []Message{
			{Role: "user", Content: "Hello"},
		},
	}

	logger := testr.New(t)
	client := NewClient(logger)

	// Create context with very short timeout
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	result, err := client.Chat(ctx, config, request)
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "context deadline exceeded")
}

func TestParseProviderResponse_UnsupportedProvider(t *testing.T) {
	client := &Client{}

	result, err := client.parseProviderResponse(Provider("unsupported"), map[string]interface{}{})
	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "unsupported provider")
}

func TestMessage_Struct(t *testing.T) {
	timestamp := time.Now()
	msg := Message{
		ID:        "test-id",
		Role:      "user",
		Content:   "Hello",
		Timestamp: timestamp,
		ToolCalls: []ToolCall{
			{
				ID:         "tool-1",
				Name:       "search",
				Parameters: map[string]interface{}{"query": "test"},
			},
		},
	}

	assert.Equal(t, "test-id", msg.ID)
	assert.Equal(t, "user", msg.Role)
	assert.Equal(t, "Hello", msg.Content)
	assert.Equal(t, timestamp, msg.Timestamp)
	assert.Len(t, msg.ToolCalls, 1)
	assert.Equal(t, "tool-1", msg.ToolCalls[0].ID)
}

func TestConfig_Struct(t *testing.T) {
	config := Config{
		Provider:    ProviderClaude,
		APIKey:      "test-key",
		BaseURL:     "https://custom.api.com",
		Model:       "claude-3",
		MaxTokens:   1000,
		Temperature: 0.7,
	}

	assert.Equal(t, ProviderClaude, config.Provider)
	assert.Equal(t, "test-key", config.APIKey)
	assert.Equal(t, "https://custom.api.com", config.BaseURL)
	assert.Equal(t, "claude-3", config.Model)
	assert.Equal(t, 1000, config.MaxTokens)
	assert.Equal(t, 0.7, config.Temperature)
}
