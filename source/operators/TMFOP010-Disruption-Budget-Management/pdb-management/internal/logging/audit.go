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

	"sigs.k8s.io/controller-runtime/pkg/log"
)

// AuditAction represents the type of action being audited
type AuditAction string

const (
	AuditActionCreate      AuditAction = "CREATE"
	AuditActionUpdate      AuditAction = "UPDATE"
	AuditActionDelete      AuditAction = "DELETE"
	AuditActionReconcile   AuditAction = "RECONCILE"
	AuditActionPolicyApply AuditAction = "POLICY_APPLY"
)

// AuditResult represents the result of an audited action
type AuditResult string

const (
	AuditResultSuccess AuditResult = "SUCCESS"
	AuditResultFailure AuditResult = "FAILURE"
	AuditResultSkipped AuditResult = "SKIPPED"
)

// AuditEntry represents a single audit log entry
type AuditEntry struct {
	Timestamp     time.Time              `json:"timestamp"`
	Action        AuditAction            `json:"action"`
	Resource      string                 `json:"resource"`
	ResourceType  string                 `json:"resourceType"`
	Namespace     string                 `json:"namespace"`
	Name          string                 `json:"name"`
	Result        AuditResult            `json:"result"`
	CorrelationID string                 `json:"correlationId"`
	User          string                 `json:"user,omitempty"`
	Reason        string                 `json:"reason,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// Audit logs important operations using structured audit entry
func Audit(ctx context.Context, entry AuditEntry) {
	// Get logger from context and ensure it has trace fields
	logger := log.FromContext(ctx)
	logger = EnsureTraceFields(ctx, logger)

	// Ensure timestamp is set
	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now().UTC()
	}

	// Get correlation ID from context if not set
	if entry.CorrelationID == "" {
		entry.CorrelationID = GetCorrelationID(ctx)
	}

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
		"audit.correlationId", entry.CorrelationID,
	}

	// Add optional fields
	if entry.User != "" {
		fields = append(fields, "audit.user", entry.User)
	}
	if entry.Reason != "" {
		fields = append(fields, "audit.reason", entry.Reason)
	}

	// Add metadata fields
	for k, v := range entry.Metadata {
		fields = append(fields, fmt.Sprintf("audit.metadata.%s", k), v)
	}

	// Log based on result
	switch entry.Result {
	case AuditResultFailure:
		logger.Error(nil, "Audit log", fields...)
	default:
		logger.Info("Audit log", fields...)
	}
}

// AuditPDBCreation logs PDB creation audit entry
func AuditPDBCreation(ctx context.Context, namespace, deployment, pdbName string, result AuditResult, metadata map[string]interface{}) {
	// Use existing logger from context and ensure it has trace fields
	logger := log.FromContext(ctx)
	logger = EnsureTraceFields(ctx, logger)

	entry := AuditEntry{
		Timestamp:    time.Now().UTC(),
		Action:       AuditActionCreate,
		Resource:     pdbName,
		ResourceType: "PodDisruptionBudget",
		Namespace:    namespace,
		Name:         deployment,
		Result:       result,
		Metadata:     metadata,
	}

	// Get correlation ID from context if not set
	if entry.CorrelationID == "" {
		entry.CorrelationID = GetCorrelationID(ctx)
	}

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
		"audit.correlationId", entry.CorrelationID,
	}

	// Add metadata fields
	for k, v := range entry.Metadata {
		fields = append(fields, fmt.Sprintf("audit.metadata.%s", k), v)
	}

	// Log based on result
	switch entry.Result {
	case AuditResultFailure:
		logger.Error(nil, "Audit log", fields...)
	default:
		logger.Info("Audit log", fields...)
	}
}

// AuditPolicyApplication logs policy application audit entry
func AuditPolicyApplication(ctx context.Context, policyNamespace, policyName string, affectedComponents []string, result AuditResult) {
	// Use existing logger from context and ensure it has trace fields
	logger := log.FromContext(ctx)
	logger = EnsureTraceFields(ctx, logger)

	metadata := map[string]interface{}{
		"affectedComponents": affectedComponents,
		"componentCount":     len(affectedComponents),
	}

	entry := AuditEntry{
		Timestamp:    time.Now().UTC(),
		Action:       AuditActionPolicyApply,
		Resource:     fmt.Sprintf("%s/%s", policyNamespace, policyName),
		ResourceType: "AvailabilityPolicy",
		Namespace:    policyNamespace,
		Name:         policyName,
		Result:       result,
		Metadata:     metadata,
	}

	// Get correlation ID from context if not set
	if entry.CorrelationID == "" {
		entry.CorrelationID = GetCorrelationID(ctx)
	}

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
		"audit.correlationId", entry.CorrelationID,
	}

	// Add metadata fields
	for k, v := range entry.Metadata {
		fields = append(fields, fmt.Sprintf("audit.metadata.%s", k), v)
	}

	// Log based on result
	switch entry.Result {
	case AuditResultFailure:
		logger.Error(nil, "Audit log", fields...)
	default:
		logger.Info("Audit log", fields...)
	}
}

// AuditReconciliation logs reconciliation audit entry
func AuditReconciliation(ctx context.Context, controller, namespace, name string, duration time.Duration, result AuditResult, err error) {
	// Use existing logger from context and ensure it has trace fields
	logger := log.FromContext(ctx)
	logger = EnsureTraceFields(ctx, logger)

	metadata := map[string]interface{}{
		"controller": controller,
		"duration":   duration.String(),
		"durationMs": duration.Milliseconds(),
	}

	if err != nil {
		metadata["error"] = err.Error()
	}

	entry := AuditEntry{
		Timestamp:    time.Now().UTC(),
		Action:       AuditActionReconcile,
		Resource:     fmt.Sprintf("%s/%s", namespace, name),
		ResourceType: controller,
		Namespace:    namespace,
		Name:         name,
		Result:       result,
		Metadata:     metadata,
	}

	// Get correlation ID from context if not set
	if entry.CorrelationID == "" {
		entry.CorrelationID = GetCorrelationID(ctx)
	}

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
		"audit.correlationId", entry.CorrelationID,
	}

	// Add metadata fields
	for k, v := range entry.Metadata {
		fields = append(fields, fmt.Sprintf("audit.metadata.%s", k), v)
	}

	// Log based on result
	switch entry.Result {
	case AuditResultFailure:
		logger.Error(nil, "Audit log", fields...)
	default:
		logger.Info("Audit log", fields...)
	}
}
