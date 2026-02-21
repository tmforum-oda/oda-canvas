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
	"time"

	"github.com/go-logr/logr"
	"go.opentelemetry.io/otel/trace"
)

// LogEntry defines the structure for operator log entries - NO DUPLICATES
type LogEntry struct {
	Level             string         `json:"level"`
	Timestamp         time.Time      `json:"ts"`
	Message           string         `json:"msg"`
	Controller        ControllerInfo `json:"controller"`
	Resource          ResourceInfo   `json:"resource"`
	ReconcileID       string         `json:"reconcileID"`
	ParentReconcileID string         `json:"parentReconcileID,omitempty"`
	CorrelationID     string         `json:"correlationID,omitempty"`
	Trace             *TraceInfo     `json:"trace,omitempty"`
	Details           map[string]any `json:"details,omitempty"`
}

// ControllerInfo represents controller information
type ControllerInfo struct {
	Type  string `json:"type"`
	Name  string `json:"name"`
	Group string `json:"group,omitempty"`
	Kind  string `json:"kind,omitempty"`
}

// ResourceInfo represents resource information
type ResourceInfo struct {
	Type      string            `json:"type"`
	Name      string            `json:"name"`
	Namespace string            `json:"namespace"`
	UID       string            `json:"uid,omitempty"`
	Version   string            `json:"version,omitempty"`
	Labels    map[string]string `json:"labels,omitempty"`
}

// TraceInfo represents trace information
type TraceInfo struct {
	TraceID string `json:"trace_id"`
	SpanID  string `json:"span_id"`
}

// StructuredLogger provides structured logging with proper JSON format
type StructuredLogger struct {
	logr.Logger
	ctx context.Context
}

// NewStructuredLogger creates a new structured logger
func NewStructuredLogger(ctx context.Context) *StructuredLogger {
	return &StructuredLogger{
		Logger: logr.FromContextOrDiscard(ctx),
		ctx:    ctx,
	}
}

// LogOperatorEvent logs an operator event with proper JSON structure - NO DUPLICATES
func (l *StructuredLogger) LogOperatorEvent(entry LogEntry) {
	// Build structured fields - NO DUPLICATES
	fields := []interface{}{
		"level", entry.Level,
		"ts", entry.Timestamp.Format(time.RFC3339),
		"msg", entry.Message,
		"controller", entry.Controller,
		"resource", entry.Resource,
		"reconcileID", entry.ReconcileID,
	}

	// Add optional fields only if they have values
	if entry.ParentReconcileID != "" {
		fields = append(fields, "parentReconcileID", entry.ParentReconcileID)
	}
	if entry.CorrelationID != "" {
		fields = append(fields, "correlationID", entry.CorrelationID)
	}
	if entry.Trace != nil {
		fields = append(fields, "trace", entry.Trace)
	}
	if len(entry.Details) > 0 {
		fields = append(fields, "details", entry.Details)
	}

	// Log with structured fields
	l.Logger.WithValues(fields...).Info(entry.Message)
}

// CreateLogEntry creates a log entry with current context
func (l *StructuredLogger) CreateLogEntry(level, message string, details map[string]any) LogEntry {
	entry := LogEntry{
		Level:     level,
		Timestamp: time.Now().UTC(),
		Message:   message,
		Details:   details,
	}

	// Get trace info from context
	span := trace.SpanFromContext(l.ctx)
	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()
		entry.Trace = &TraceInfo{
			TraceID: spanContext.TraceID().String(),
			SpanID:  spanContext.SpanID().String(),
		}
	}

	// Get correlation ID from context
	entry.CorrelationID = GetCorrelationID(l.ctx)

	return entry
}

// Info logs an info message with structured format
func (l *StructuredLogger) Info(msg string, details map[string]any) {
	entry := l.CreateLogEntry("info", msg, details)
	l.LogOperatorEvent(entry)
}

// Error logs an error message with structured format
func (l *StructuredLogger) Error(err error, msg string, details map[string]any) {
	entry := l.CreateLogEntry("error", msg, details)
	if err != nil {
		if entry.Details == nil {
			entry.Details = make(map[string]any)
		}
		entry.Details["error"] = err.Error()
	}
	l.LogOperatorEvent(entry)
}

// Debug logs a debug message with structured format
func (l *StructuredLogger) Debug(msg string, details map[string]any) {
	entry := l.CreateLogEntry("debug", msg, details)
	l.LogOperatorEvent(entry)
}

// AuditStructured logs an audit entry with structured format - NO DUPLICATES
func (l *StructuredLogger) AuditStructured(action, resource, resourceType, namespace, name string, result AuditResult, metadata map[string]interface{}) {
	// Build audit details
	auditDetails := map[string]any{
		"timestamp":     time.Now().UTC().Format(time.RFC3339),
		"action":        action,
		"resource":      resource,
		"resourceType":  resourceType,
		"namespace":     namespace,
		"name":          name,
		"result":        string(result),
		"correlationId": GetCorrelationID(l.ctx),
	}

	// Add metadata fields
	for k, v := range metadata {
		auditDetails[k] = v
	}

	// Log based on result
	switch result {
	case AuditResultFailure:
		l.Error(nil, "Audit log", auditDetails)
	default:
		l.Info("Audit log", auditDetails)
	}
}

// CreateStructuredLogger creates a fully configured structured logger
func CreateStructuredLogger(ctx context.Context, controllerType, controllerName, group, kind, resourceType, name, namespace, reconcileID, correlationID string) *StructuredLogger {
	logger := NewStructuredLogger(ctx)

	// Create a log entry with all the context
	entry := LogEntry{
		Level:         "info",
		Timestamp:     time.Now().UTC(),
		Message:       "Starting reconciliation",
		ReconcileID:   reconcileID,
		CorrelationID: correlationID,
		Controller: ControllerInfo{
			Type:  controllerType,
			Name:  controllerName,
			Group: group,
			Kind:  kind,
		},
		Resource: ResourceInfo{
			Type:      resourceType,
			Name:      name,
			Namespace: namespace,
		},
	}

	// Get trace info from context
	span := trace.SpanFromContext(ctx)
	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()
		entry.Trace = &TraceInfo{
			TraceID: spanContext.TraceID().String(),
			SpanID:  spanContext.SpanID().String(),
		}
	}

	// Log the entry
	logger.LogOperatorEvent(entry)

	return logger
}

// GetStructuredLoggerFromContext creates a structured logger from context
func GetStructuredLoggerFromContext(ctx context.Context) *StructuredLogger {
	return NewStructuredLogger(ctx)
}

// ToLogr converts StructuredLogger to logr.Logger for compatibility
func (l *StructuredLogger) ToLogr() logr.Logger {
	return l.Logger
}

// WithController adds controller information to the logger
func (l *StructuredLogger) WithController(controllerType, controllerName, group, kind string) *StructuredLogger {
	controllerInfo := ControllerInfo{
		Type:  controllerType,
		Name:  controllerName,
		Group: group,
		Kind:  kind,
	}

	return &StructuredLogger{
		Logger: l.WithValues("controller", controllerInfo),
		ctx:    l.ctx,
	}
}

// WithResource adds resource information to the logger
func (l *StructuredLogger) WithResource(resourceType, name, namespace string) *StructuredLogger {
	resourceInfo := ResourceInfo{
		Type:      resourceType,
		Name:      name,
		Namespace: namespace,
	}

	return &StructuredLogger{
		Logger: l.WithValues("resource", resourceInfo),
		ctx:    l.ctx,
	}
}

// WithTrace adds trace information to the logger
func (l *StructuredLogger) WithTrace() *StructuredLogger {
	span := trace.SpanFromContext(l.ctx)
	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()
		traceInfo := TraceInfo{
			TraceID: spanContext.TraceID().String(),
			SpanID:  spanContext.SpanID().String(),
		}

		return &StructuredLogger{
			Logger: l.WithValues("trace", traceInfo),
			ctx:    l.ctx,
		}
	}

	return l
}

// WithReconcileID adds reconcile ID to the logger
func (l *StructuredLogger) WithReconcileID(reconcileID string) *StructuredLogger {
	return &StructuredLogger{
		Logger: l.WithValues("reconcileID", reconcileID),
		ctx:    l.ctx,
	}
}

// WithCorrelationID adds correlation ID to the logger
func (l *StructuredLogger) WithCorrelationID(correlationID string) *StructuredLogger {
	return &StructuredLogger{
		Logger: l.WithValues("correlationID", correlationID),
		ctx:    l.ctx,
	}
}

// WithDetails adds additional contextual details
func (l *StructuredLogger) WithDetails(details map[string]any) *StructuredLogger {
	return &StructuredLogger{
		Logger: l.WithValues("details", details),
		ctx:    l.ctx,
	}
}

// WithDetail adds a single detail field
func (l *StructuredLogger) WithDetail(key string, value interface{}) *StructuredLogger {
	details := map[string]any{key: value}
	return l.WithDetails(details)
}

// Details type for compatibility
type Details map[string]any
