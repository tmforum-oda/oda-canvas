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
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-logr/logr"
	"go.opentelemetry.io/otel/trace"
)

// UnifiedLogEntry defines the clean, structured log format - NO DUPLICATES
type UnifiedLogEntry struct {
	Level         string         `json:"level"`
	Timestamp     time.Time      `json:"ts"`
	Message       string         `json:"msg"`
	Controller    ControllerInfo `json:"controller"`
	Resource      ResourceInfo   `json:"resource"`
	ReconcileID   string         `json:"reconcileID"`
	CorrelationID string         `json:"correlationID,omitempty"`
	Trace         *TraceInfo     `json:"trace,omitempty"`
	Details       map[string]any `json:"details,omitempty"`
}

// UnifiedLogger provides clean, structured logging without field duplication
type UnifiedLogger struct {
	baseLogger logr.Logger
	ctx        context.Context
	entry      UnifiedLogEntry
}

// NewUnifiedLogger creates a new unified logger with complete context
func NewUnifiedLogger(ctx context.Context, controllerType, controllerName, group, kind, resourceType, name, namespace, reconcileID, correlationID string) *UnifiedLogger {
	// Get base logger from context
	baseLogger := logr.FromContextOrDiscard(ctx)

	// Create unified entry with all context
	entry := UnifiedLogEntry{
		Level:       "info",
		Timestamp:   time.Now().UTC(),
		Message:     "",
		ReconcileID: reconcileID,
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

	// Add correlation ID if provided
	if correlationID != "" {
		entry.CorrelationID = correlationID
	}

	// Always get trace info from context - even if span is not valid, create a default trace
	span := trace.SpanFromContext(ctx)
	if span != nil && span.SpanContext().IsValid() {
		spanContext := span.SpanContext()
		entry.Trace = &TraceInfo{
			TraceID: spanContext.TraceID().String(),
			SpanID:  spanContext.SpanID().String(),
		}
	} else {
		// Create a default trace if none exists
		entry.Trace = &TraceInfo{
			TraceID: "no-trace",
			SpanID:  "no-span",
		}
	}

	return &UnifiedLogger{
		baseLogger: baseLogger,
		ctx:        ctx,
		entry:      entry,
	}
}

// Info logs an info message with unified structure
func (l *UnifiedLogger) Info(msg string, details map[string]any) {
	entry := l.entry
	entry.Level = "info"
	entry.Timestamp = time.Now().UTC()
	entry.Message = msg
	entry.Details = details

	// Ensure trace context is always included
	if entry.Trace == nil {
		span := trace.SpanFromContext(l.ctx)
		if span != nil && span.SpanContext().IsValid() {
			spanContext := span.SpanContext()
			entry.Trace = &TraceInfo{
				TraceID: spanContext.TraceID().String(),
				SpanID:  spanContext.SpanID().String(),
			}
		} else {
			entry.Trace = &TraceInfo{
				TraceID: "no-trace",
				SpanID:  "no-span",
			}
		}
	}

	l.logEntry(entry)
}

// Error logs an error message with unified structure
func (l *UnifiedLogger) Error(err error, msg string, details map[string]any) {
	entry := l.entry
	entry.Level = "error"
	entry.Timestamp = time.Now().UTC()
	entry.Message = msg

	if entry.Details == nil {
		entry.Details = make(map[string]any)
	}
	for k, v := range details {
		entry.Details[k] = v
	}
	if err != nil {
		entry.Details["error"] = err.Error()
	}

	// Ensure trace context is always included
	if entry.Trace == nil {
		span := trace.SpanFromContext(l.ctx)
		if span != nil && span.SpanContext().IsValid() {
			spanContext := span.SpanContext()
			entry.Trace = &TraceInfo{
				TraceID: spanContext.TraceID().String(),
				SpanID:  spanContext.SpanID().String(),
			}
		} else {
			entry.Trace = &TraceInfo{
				TraceID: "no-trace",
				SpanID:  "no-span",
			}
		}
	}

	l.logEntry(entry)
}

// Debug logs a debug message with unified structure
func (l *UnifiedLogger) Debug(msg string, details map[string]any) {
	entry := l.entry
	entry.Level = "debug"
	entry.Timestamp = time.Now().UTC()
	entry.Message = msg
	entry.Details = details

	l.logEntry(entry)
}

// Audit logs an audit event with unified structure
func (l *UnifiedLogger) Audit(action, resource, resourceType, namespace, name string, result AuditResult, metadata map[string]interface{}) {
	entry := l.entry
	entry.Level = "info"
	entry.Timestamp = time.Now().UTC()
	entry.Message = "Audit log"

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

	entry.Details = auditDetails

	// Log based on result
	if result == AuditResultFailure {
		entry.Level = "error"
	}

	l.logEntry(entry)
}

// logEntry logs the unified entry as a single JSON object
func (l *UnifiedLogger) logEntry(entry UnifiedLogEntry) {
	// Marshal the entire entry to JSON
	jsonData, err := json.Marshal(entry)
	if err != nil {
		// Fallback to basic logging if JSON marshaling fails
		l.baseLogger.Info(entry.Message, "error", "failed to marshal log entry")
		return
	}

	// Log the JSON string directly to avoid controller-runtime field pollution
	// Use a raw logger that doesn't add extra fields
	rawLogger := logr.New(&rawLogSink{})
	rawLogger.Info(string(jsonData))
}

// rawLogSink provides a simple log sink that doesn't add extra fields
type rawLogSink struct{}

func (s *rawLogSink) Init(info logr.RuntimeInfo) {}
func (s *rawLogSink) Enabled(level int) bool     { return true }
func (s *rawLogSink) Info(level int, msg string, keysAndValues ...interface{}) {
	// Print the message directly to stdout to avoid field pollution
	fmt.Println(msg)
}
func (s *rawLogSink) Error(err error, msg string, keysAndValues ...interface{}) {
	fmt.Printf("ERROR: %s - %v\n", msg, err)
}
func (s *rawLogSink) WithValues(keysAndValues ...interface{}) logr.LogSink { return s }
func (s *rawLogSink) WithName(name string) logr.LogSink                    { return s }

// WithDetails creates a new logger with additional details
func (l *UnifiedLogger) WithDetails(details map[string]any) *UnifiedLogger {
	newLogger := *l
	if newLogger.entry.Details == nil {
		newLogger.entry.Details = make(map[string]any)
	}
	for k, v := range details {
		newLogger.entry.Details[k] = v
	}
	return &newLogger
}

// WithDetail adds a single detail field
func (l *UnifiedLogger) WithDetail(key string, value interface{}) *UnifiedLogger {
	details := map[string]any{key: value}
	return l.WithDetails(details)
}

// ToLogr converts UnifiedLogger to logr.Logger for compatibility
func (l *UnifiedLogger) ToLogr() logr.Logger {
	return l.baseLogger
}

// V returns a logger with the specified verbosity level
func (l *UnifiedLogger) V(level int) logr.Logger {
	return l.baseLogger.V(level)
}

// CreateUnifiedLogger creates a fully configured unified logger
func CreateUnifiedLogger(ctx context.Context, controllerType, controllerName, group, kind, resourceType, name, namespace, reconcileID, correlationID string) *UnifiedLogger {
	logger := NewUnifiedLogger(ctx, controllerType, controllerName, group, kind, resourceType, name, namespace, reconcileID, correlationID)

	// Log the initial reconciliation start
	logger.Info("Starting reconciliation", map[string]any{})

	return logger
}
