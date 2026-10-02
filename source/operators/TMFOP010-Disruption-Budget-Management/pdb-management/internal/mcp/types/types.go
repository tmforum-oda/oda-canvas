package types

import (
	"context"
	"encoding/json"
	"time"
)

// Tool represents an MCP tool that can be invoked
type Tool struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"inputSchema"`
	Handler     ToolHandler     `json:"-"`
}

// ToolHandler is a function that handles tool invocations
type ToolHandler func(ctx context.Context, params json.RawMessage) (*ToolResult, error)

// ToolResult represents the result of a tool invocation
type ToolResult struct {
	Content     interface{} `json:"content"`
	IsError     bool        `json:"isError,omitempty"`
	ErrorDetail string      `json:"errorDetail,omitempty"`
}

// Request represents an MCP request
type Request struct {
	ID      string          `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
	Created time.Time       `json:"created"`
}

// Response represents an MCP response
type Response struct {
	ID      string          `json:"id"`
	Result  json.RawMessage `json:"result,omitempty"`
	Error   *Error          `json:"error,omitempty"`
	Created time.Time       `json:"created"`
}

// Error represents an MCP error
type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    any    `json:"data,omitempty"`
}

// Notification represents an MCP notification
type Notification struct {
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
	Created time.Time       `json:"created"`
}

// ServerInfo contains information about the MCP server
type ServerInfo struct {
	Name         string   `json:"name"`
	Version      string   `json:"version"`
	Capabilities []string `json:"capabilities"`
}

// InitializeParams contains parameters for server initialization
type InitializeParams struct {
	ClientInfo ClientInfo `json:"clientInfo"`
}

// ClientInfo contains information about the MCP client
type ClientInfo struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

// ListToolsResult contains the list of available tools
type ListToolsResult struct {
	Tools []ToolInfo `json:"tools"`
}

// ToolInfo contains basic information about a tool
type ToolInfo struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	InputSchema json.RawMessage `json:"inputSchema"`
}

// CallToolParams contains parameters for calling a tool
type CallToolParams struct {
	Name      string          `json:"name"`
	Arguments json.RawMessage `json:"arguments"`
}

// CallToolResult contains the result of a tool call
type CallToolResult struct {
	Content []ContentItem `json:"content"`
	IsError bool          `json:"isError,omitempty"`
}

// ContentItem represents a piece of content in the result
type ContentItem struct {
	Type string `json:"type"`
	Text string `json:"text"`
	Data any    `json:"data,omitempty"`
}

// Prompt represents a prompt that can be used by the client
type Prompt struct {
	Name        string           `json:"name"`
	Description string           `json:"description"`
	Arguments   []PromptArgument `json:"arguments,omitempty"`
}

// PromptArgument represents an argument for a prompt
type PromptArgument struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Required    bool   `json:"required"`
}

// ListPromptsResult contains the list of available prompts
type ListPromptsResult struct {
	Prompts []Prompt `json:"prompts"`
}

// GetPromptParams contains parameters for getting a prompt
type GetPromptParams struct {
	Name      string            `json:"name"`
	Arguments map[string]string `json:"arguments,omitempty"`
}

// GetPromptResult contains the result of getting a prompt
type GetPromptResult struct {
	Messages []PromptMessage `json:"messages"`
}

// PromptMessage represents a message in a prompt
type PromptMessage struct {
	Role    string        `json:"role"`
	Content []ContentItem `json:"content"`
}

// Resource represents a resource that can be accessed
type Resource struct {
	URI         string `json:"uri"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	MimeType    string `json:"mimeType,omitempty"`
}

// ListResourcesResult contains the list of available resources
type ListResourcesResult struct {
	Resources []Resource `json:"resources"`
}

// ReadResourceParams contains parameters for reading a resource
type ReadResourceParams struct {
	URI string `json:"uri"`
}

// ReadResourceResult contains the result of reading a resource
type ReadResourceResult struct {
	Content []ContentItem `json:"content"`
}
