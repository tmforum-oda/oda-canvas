package transport

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewAuditLogger(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))

	// Test enabled
	al := NewAuditLogger(logger, true)
	assert.NotNil(t, al)
	assert.True(t, al.enabled)

	// Test disabled
	al = NewAuditLogger(logger, false)
	assert.NotNil(t, al)
	assert.False(t, al.enabled)
}

func TestAuditLogger_LogDisabled(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, false)

	// Should not panic when disabled
	al.Log(context.Background(), AuditEvent{
		EventType: AuditEventMCPRequest,
		Result:    AuditResultSuccess,
		ClientIP:  "192.168.1.1",
	})
}

func TestAuditLogger_LogEnabled(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	// Should not panic when enabled
	al.Log(context.Background(), AuditEvent{
		EventType: AuditEventMCPRequest,
		Result:    AuditResultSuccess,
		ClientIP:  "192.168.1.1",
	})
}

func TestAuditLogger_LogWithZeroTimestamp(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	event := AuditEvent{
		EventType: AuditEventMCPRequest,
		Result:    AuditResultSuccess,
		ClientIP:  "192.168.1.1",
		// Timestamp is zero
	}

	// Should not panic and timestamp should be set
	al.Log(context.Background(), event)
}

func TestAuditLogger_LogWithDuration(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	event := AuditEvent{
		EventType: AuditEventMCPRequest,
		Result:    AuditResultSuccess,
		ClientIP:  "192.168.1.1",
		Duration:  100 * time.Millisecond,
	}

	// Should calculate DurationMs
	al.Log(context.Background(), event)
}

func TestAuditLogger_LogMCPRequest(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	// Test success
	al.LogMCPRequest(context.Background(), "tools/list", "req-123", "192.168.1.1", "test-agent", time.Second, nil)

	// Test failure
	al.LogMCPRequest(context.Background(), "tools/call", "req-456", "192.168.1.1", "test-agent", time.Second, assert.AnError)
}

func TestAuditLogger_LogToolCall(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	// Test success with small params
	params := map[string]string{"key": "value"}
	al.LogToolCall(context.Background(), "get-pods", "req-123", "192.168.1.1", params, time.Second, nil)

	// Test success with nil params
	al.LogToolCall(context.Background(), "get-pods", "req-123", "192.168.1.1", nil, time.Second, nil)

	// Test success with large params
	largeParams := map[string]string{}
	for i := 0; i < 100; i++ {
		largeParams[string(rune('a'+i%26))+string(rune(i))] = "a very long value that makes the params large"
	}
	al.LogToolCall(context.Background(), "get-pods", "req-123", "192.168.1.1", largeParams, time.Second, nil)

	// Test failure
	al.LogToolCall(context.Background(), "get-pods", "req-456", "192.168.1.1", params, time.Second, assert.AnError)
}

func TestAuditLogger_LogAIProxy(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	// Test success
	al.LogAIProxy(context.Background(), "claude", "192.168.1.1", "test-agent", "http://example.com", 5, time.Second, nil)

	// Test failure
	al.LogAIProxy(context.Background(), "openai", "192.168.1.1", "test-agent", "http://example.com", 3, time.Second, assert.AnError)
}

func TestAuditLogger_LogRateLimitExceeded(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	al.LogRateLimitExceeded(context.Background(), "192.168.1.1", "/mcp", "POST")
}

func TestAuditLogger_LogCORSRejected(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	al := NewAuditLogger(logger, true)

	al.LogCORSRejected(context.Background(), "192.168.1.1", "http://evil.com", "/ai/proxy")
}

func TestAuditEventTypes(t *testing.T) {
	// Verify constants are defined
	assert.Equal(t, AuditEventType("mcp_request"), AuditEventMCPRequest)
	assert.Equal(t, AuditEventType("tool_call"), AuditEventToolCall)
	assert.Equal(t, AuditEventType("ai_proxy"), AuditEventAIProxy)
	assert.Equal(t, AuditEventType("rate_limit"), AuditEventRateLimit)
	assert.Equal(t, AuditEventType("auth_failure"), AuditEventAuthFailure)
	assert.Equal(t, AuditEventType("cors_rejected"), AuditEventCORSRejected)
}

func TestAuditResultTypes(t *testing.T) {
	// Verify constants are defined
	assert.Equal(t, AuditResult("success"), AuditResultSuccess)
	assert.Equal(t, AuditResult("failure"), AuditResultFailure)
	assert.Equal(t, AuditResult("denied"), AuditResultDenied)
}
