package transport

import (
	"context"
	"encoding/json"
	"time"

	"github.com/go-logr/logr"
)

// AuditEventType represents the type of audit event
type AuditEventType string

const (
	AuditEventMCPRequest   AuditEventType = "mcp_request"
	AuditEventToolCall     AuditEventType = "tool_call"
	AuditEventAIProxy      AuditEventType = "ai_proxy"
	AuditEventRateLimit    AuditEventType = "rate_limit"
	AuditEventAuthFailure  AuditEventType = "auth_failure"
	AuditEventCORSRejected AuditEventType = "cors_rejected"
)

// AuditResult represents the result of an operation
type AuditResult string

const (
	AuditResultSuccess AuditResult = "success"
	AuditResultFailure AuditResult = "failure"
	AuditResultDenied  AuditResult = "denied"
)

// AuditEvent represents an audit log event
type AuditEvent struct {
	Timestamp   time.Time              `json:"timestamp"`
	EventType   AuditEventType         `json:"eventType"`
	Result      AuditResult            `json:"result"`
	ClientIP    string                 `json:"clientIP"`
	Method      string                 `json:"method,omitempty"`
	RequestID   string                 `json:"requestID,omitempty"`
	ToolName    string                 `json:"toolName,omitempty"`
	Provider    string                 `json:"provider,omitempty"`
	Duration    time.Duration          `json:"duration,omitempty"`
	DurationMs  int64                  `json:"durationMs,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Details     map[string]interface{} `json:"details,omitempty"`
	UserAgent   string                 `json:"userAgent,omitempty"`
	Origin      string                 `json:"origin,omitempty"`
	ContentSize int64                  `json:"contentSize,omitempty"`
}

// AuditLogger handles audit logging for MCP operations
type AuditLogger struct {
	logger  logr.Logger
	enabled bool
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger(logger logr.Logger, enabled bool) *AuditLogger {
	return &AuditLogger{
		logger:  logger.WithName("mcp-audit"),
		enabled: enabled,
	}
}

// Log logs an audit event
func (a *AuditLogger) Log(ctx context.Context, event AuditEvent) {
	if !a.enabled {
		return
	}

	// Set timestamp if not set
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}

	// Calculate duration in ms if duration is set
	if event.Duration > 0 {
		event.DurationMs = event.Duration.Milliseconds()
	}

	// Log as structured JSON
	a.logger.Info("Audit log",
		"event", event.EventType,
		"result", event.Result,
		"clientIP", event.ClientIP,
		"method", event.Method,
		"requestID", event.RequestID,
		"toolName", event.ToolName,
		"provider", event.Provider,
		"durationMs", event.DurationMs,
		"error", event.Error,
		"userAgent", event.UserAgent,
		"origin", event.Origin,
		"contentSize", event.ContentSize,
	)
}

// LogMCPRequest logs an MCP request
func (a *AuditLogger) LogMCPRequest(ctx context.Context, method, requestID, clientIP, userAgent string, duration time.Duration, err error) {
	result := AuditResultSuccess
	errMsg := ""
	if err != nil {
		result = AuditResultFailure
		errMsg = err.Error()
	}

	a.Log(ctx, AuditEvent{
		EventType: AuditEventMCPRequest,
		Result:    result,
		ClientIP:  clientIP,
		Method:    method,
		RequestID: requestID,
		Duration:  duration,
		Error:     errMsg,
		UserAgent: userAgent,
	})
}

// LogToolCall logs a tool invocation
func (a *AuditLogger) LogToolCall(ctx context.Context, toolName, requestID, clientIP string, params interface{}, duration time.Duration, err error) {
	result := AuditResultSuccess
	errMsg := ""
	if err != nil {
		result = AuditResultFailure
		errMsg = err.Error()
	}

	details := make(map[string]interface{})
	if params != nil {
		// Sanitize params - don't log sensitive data
		if paramsBytes, err := json.Marshal(params); err == nil {
			if len(paramsBytes) < 1000 { // Only log small params
				details["params_size"] = len(paramsBytes)
			} else {
				details["params_size"] = len(paramsBytes)
				details["params_truncated"] = true
			}
		}
	}

	a.Log(ctx, AuditEvent{
		EventType: AuditEventToolCall,
		Result:    result,
		ClientIP:  clientIP,
		RequestID: requestID,
		ToolName:  toolName,
		Duration:  duration,
		Error:     errMsg,
		Details:   details,
	})
}

// LogAIProxy logs an AI proxy request
func (a *AuditLogger) LogAIProxy(ctx context.Context, provider, clientIP, userAgent, origin string, messageCount int, duration time.Duration, err error) {
	result := AuditResultSuccess
	errMsg := ""
	if err != nil {
		result = AuditResultFailure
		errMsg = err.Error()
	}

	a.Log(ctx, AuditEvent{
		EventType: AuditEventAIProxy,
		Result:    result,
		ClientIP:  clientIP,
		Provider:  provider,
		Duration:  duration,
		Error:     errMsg,
		UserAgent: userAgent,
		Origin:    origin,
		Details: map[string]interface{}{
			"messageCount": messageCount,
		},
	})
}

// LogRateLimitExceeded logs a rate limit exceeded event
func (a *AuditLogger) LogRateLimitExceeded(ctx context.Context, clientIP, path, method string) {
	a.Log(ctx, AuditEvent{
		EventType: AuditEventRateLimit,
		Result:    AuditResultDenied,
		ClientIP:  clientIP,
		Method:    method,
		Details: map[string]interface{}{
			"path": path,
		},
	})
}

// LogCORSRejected logs a CORS rejection
func (a *AuditLogger) LogCORSRejected(ctx context.Context, clientIP, origin, path string) {
	a.Log(ctx, AuditEvent{
		EventType: AuditEventCORSRejected,
		Result:    AuditResultDenied,
		ClientIP:  clientIP,
		Origin:    origin,
		Details: map[string]interface{}{
			"path": path,
		},
	})
}

// LogAuthFailure logs an authentication failure
func (a *AuditLogger) LogAuthFailure(ctx context.Context, clientIP, path, reason string) {
	a.Log(ctx, AuditEvent{
		EventType: AuditEventAuthFailure,
		Result:    AuditResultDenied,
		ClientIP:  clientIP,
		Details: map[string]interface{}{
			"path":   path,
			"reason": reason,
		},
	})
}
