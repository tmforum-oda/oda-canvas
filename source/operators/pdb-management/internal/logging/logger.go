/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package logging

import (
	"context"
	"fmt"
	"time"

	"github.com/go-logr/logr"
	"go.opentelemetry.io/otel/trace"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// Logger wraps the standard logger with enhanced trace context
type Logger struct {
	logr.Logger
	ctx context.Context
}

// NewLogger creates a new logger with trace context
func NewLogger(ctx context.Context) *Logger {
	// Get the base logger from context
	baseLogger := log.FromContext(ctx)

	// Create enhanced logger with trace fields
	enhancedLogger := baseLogger

	// Add trace fields if available
	span := trace.SpanFromContext(ctx)
	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()
		enhancedLogger = enhancedLogger.WithValues(
			"trace_id", spanContext.TraceID().String(),
			"span_id", spanContext.SpanID().String(),
		)

		// Add trace flags if sampled
		if spanContext.IsSampled() {
			enhancedLogger = enhancedLogger.WithValues("trace_flags", "01")
		}
	}

	// Add correlation ID if present
	if correlationID := GetCorrelationID(ctx); correlationID != "" {
		enhancedLogger = enhancedLogger.WithValues("correlationID", correlationID)
	}

	return &Logger{
		Logger: enhancedLogger,
		ctx:    ctx,
	}
}

// WithValues adds key-value pairs to the logger
func (l *Logger) WithValues(keysAndValues ...interface{}) *Logger {
	return &Logger{
		Logger: l.Logger.WithValues(keysAndValues...),
		ctx:    l.ctx,
	}
}

// WithName adds a name to the logger
func (l *Logger) WithName(name string) *Logger {
	return &Logger{
		Logger: l.Logger.WithName(name),
		ctx:    l.ctx,
	}
}

// WithReconcileID adds reconcile ID to the logger
func (l *Logger) WithReconcileID(reconcileID string) *Logger {
	return l.WithValues("reconcileID", reconcileID)
}

// WithDeployment adds deployment context to the logger
func (l *Logger) WithDeployment(namespace, name string) *Logger {
	return l.WithValues(
		"deployment.name", name,
		"deployment.namespace", namespace,
		"resource.type", "deployment",
	)
}

// WithPolicy adds policy context to the logger
func (l *Logger) WithPolicy(namespace, name string) *Logger {
	return l.WithValues(
		"policy.name", name,
		"policy.namespace", namespace,
		"resource.type", "availabilitypolicy",
	)
}

// WithPDB adds PDB context to the logger
func (l *Logger) WithPDB(namespace, name string) *Logger {
	return l.WithValues(
		"pdb.name", name,
		"pdb.namespace", namespace,
		"resource.type", "poddisruptionbudget",
	)
}

// WithComponent adds component context to the logger
func (l *Logger) WithComponent(name, function string) *Logger {
	return l.WithValues(
		"component.name", name,
		"component.function", function,
	)
}

// WithAvailabilityClass adds availability class to the logger
func (l *Logger) WithAvailabilityClass(class string) *Logger {
	return l.WithValues("availabilityClass", class)
}

// WithOperation adds operation context to the logger
func (l *Logger) WithOperation(operation string) *Logger {
	return l.WithValues("operation", operation)
}

// WithMCPRequest adds MCP request context to the logger
func (l *Logger) WithMCPRequest(method, id string) *Logger {
	return l.WithValues(
		"mcp.method", method,
		"mcp.requestId", id,
		"mcp.protocol", "json-rpc",
	)
}

// WithMCPTool adds MCP tool context to the logger
func (l *Logger) WithMCPTool(toolName string) *Logger {
	return l.WithValues(
		"mcp.tool", toolName,
		"mcp.type", "tool_call",
	)
}

// WithError adds error context to the logger
func (l *Logger) WithError(err error) *Logger {
	if err == nil {
		return l
	}
	return l.WithValues(
		"error", err.Error(),
		"errorType", fmt.Sprintf("%T", err),
	)
}

// ToLogr converts Logger to logr.Logger for compatibility
func (l *Logger) ToLogr() logr.Logger {
	return l.Logger
}

// Audit creates an audit log entry
func (l *Logger) Audit(action, resource, resourceType, namespace, name string, result AuditResult, metadata map[string]interface{}) {
	entry := AuditEntry{
		Timestamp:    time.Now().UTC(),
		Action:       AuditAction(action),
		Resource:     resource,
		ResourceType: resourceType,
		Namespace:    namespace,
		Name:         name,
		Result:       result,
		Metadata:     metadata,
	}

	// Create audit logger
	auditLogger := l.WithName("audit")

	// Build structured fields
	fields := []interface{}{
		"audit", true,
		"audit.timestamp", entry.Timestamp.Format(time.RFC3339),
		"audit.action", string(entry.Action),
		"audit.resource", entry.Resource,
		"audit.resourceType", entry.ResourceType,
		"audit.namespace", entry.Namespace,
		"audit.name", entry.Name,
		"audit.result", string(entry.Result),
		"audit.correlationId", GetCorrelationID(l.ctx),
	}

	// Add metadata fields
	for k, v := range entry.Metadata {
		fields = append(fields, fmt.Sprintf("audit.metadata.%s", k), v)
	}

	// Log based on result
	switch entry.Result {
	case AuditResultFailure:
		auditLogger.Error(nil, "Audit log", fields...)
	default:
		auditLogger.Info("Audit log", fields...)
	}
}

// AuditPDBCreation logs PDB creation audit
func (l *Logger) AuditPDBCreation(namespace, deployment, pdbName string, result AuditResult, metadata map[string]interface{}) {
	l.Audit("CREATE", pdbName, "PodDisruptionBudget", namespace, deployment, result, metadata)
}

// AuditPolicyApplication logs policy application audit
func (l *Logger) AuditPolicyApplication(policyNamespace, policyName string, affectedComponents []string, result AuditResult) {
	metadata := map[string]interface{}{
		"affectedComponents": affectedComponents,
		"componentCount":     len(affectedComponents),
	}
	l.Audit("POLICY_APPLY", fmt.Sprintf("%s/%s", policyNamespace, policyName), "AvailabilityPolicy", policyNamespace, policyName, result, metadata)
}

// AuditReconciliation logs reconciliation audit
func (l *Logger) AuditReconciliation(controller, namespace, name string, duration time.Duration, result AuditResult, err error) {
	metadata := map[string]interface{}{
		"controller": controller,
		"duration":   duration.String(),
		"durationMs": duration.Milliseconds(),
	}

	if err != nil {
		metadata["error"] = err.Error()
	}

	l.Audit("RECONCILE", fmt.Sprintf("%s/%s", namespace, name), controller, namespace, name, result, metadata)
}

// AuditMCPRequest logs MCP request audit
func (l *Logger) AuditMCPRequest(method, requestID, source string, duration time.Duration, result AuditResult, err error) {
	metadata := map[string]interface{}{
		"mcp.method":    method,
		"mcp.requestId": requestID,
		"mcp.source":    source,
		"duration":      duration.String(),
		"durationMs":    duration.Milliseconds(),
	}

	if err != nil {
		metadata["error"] = err.Error()
	}

	l.Audit("MCP_REQUEST", requestID, "MCPRequest", "", method, result, metadata)
}

// AuditMCPToolCall logs MCP tool call audit
func (l *Logger) AuditMCPToolCall(toolName string, arguments map[string]interface{}, result AuditResult, metadata map[string]interface{}) {
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["tool"] = toolName
	metadata["argumentCount"] = len(arguments)

	l.Audit("MCP_TOOL_CALL", toolName, "MCPTool", "", toolName, result, metadata)
}

// GetLoggerFromContext creates a logger from context with proper trace fields
func GetLoggerFromContext(ctx context.Context) *Logger {
	return NewLogger(ctx)
}

// GetLoggerFromContextWithValues creates a logger from context with additional values
func GetLoggerFromContextWithValues(ctx context.Context, keysAndValues ...interface{}) *Logger {
	logger := NewLogger(ctx)
	return logger.WithValues(keysAndValues...)
}

// InitializeLogger sets up the logging system
func InitializeLogger(development bool, level string) (logr.Logger, error) {
	// This is a placeholder - the actual logger initialization is handled by controller-runtime
	// We just need to ensure the logging system is ready
	return logr.Discard(), nil
}
