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

package events

import (
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/record"
)

const (
	// Event reasons for PDB lifecycle
	ReasonPDBCreated        = "PDBCreated"
	ReasonPDBUpdated        = "PDBUpdated"
	ReasonPDBDeleted        = "PDBDeleted"
	ReasonPDBCreationFailed = "PDBCreationFailed"
	ReasonPDBUpdateFailed   = "PDBUpdateFailed"
	ReasonPDBDeletionFailed = "PDBDeletionFailed"

	// Event reasons for configuration
	ReasonInvalidConfig      = "InvalidConfiguration"
	ReasonConfigurationError = "ConfigurationError"
	ReasonMaintenanceWindow  = "MaintenanceWindowActive"

	// Event reasons for policies
	ReasonPolicyApplied   = "PolicyApplied"
	ReasonPolicyRemoved   = "PolicyRemoved"
	ReasonPolicyUpdated   = "PolicyUpdated"
	ReasonPolicyValidated = "PolicyValidated"
	ReasonPolicyInvalid   = "PolicyInvalid"

	// Event reasons for deployments
	ReasonDeploymentManaged   = "DeploymentManaged"
	ReasonDeploymentUnmanaged = "DeploymentUnmanaged"
	ReasonDeploymentSkipped   = "DeploymentSkipped"

	// Event reasons for compliance
	ReasonComplianceAchieved = "ComplianceAchieved"
	ReasonComplianceLost     = "ComplianceLost"
)

// EventRecorder wraps the Kubernetes event recorder with domain-specific methods
type EventRecorder struct {
	recorder record.EventRecorder
}

// NewEventRecorder creates a new event recorder
func NewEventRecorder(recorder record.EventRecorder) *EventRecorder {
	return &EventRecorder{recorder: recorder}
}

// PDB Lifecycle Events

// PDBCreated records a PDB creation event
func (e *EventRecorder) PDBCreated(obj runtime.Object, deployment, pdbName, availabilityClass string, minAvailable string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPDBCreated,
		"Created PodDisruptionBudget %s for deployment %s (class: %s, minAvailable: %s)",
		pdbName, deployment, availabilityClass, minAvailable)
}

// PDBUpdated records a PDB update event
func (e *EventRecorder) PDBUpdated(obj runtime.Object, deployment, pdbName, oldMinAvailable, newMinAvailable string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPDBUpdated,
		"Updated PodDisruptionBudget %s for deployment %s (minAvailable: %s -> %s)",
		pdbName, deployment, oldMinAvailable, newMinAvailable)
}

// PDBDeleted records a PDB deletion event
func (e *EventRecorder) PDBDeleted(obj runtime.Object, deployment, pdbName, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPDBDeleted,
		"Deleted PodDisruptionBudget %s for deployment %s (reason: %s)",
		pdbName, deployment, reason)
}

// PDBCreationFailed records a PDB creation failure
func (e *EventRecorder) PDBCreationFailed(obj runtime.Object, deployment string, err error) {
	// Check if the object still exists before creating event
	if obj != nil {
		e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonPDBCreationFailed,
			"Failed to create PodDisruptionBudget for deployment %s: %v", deployment, err)
	}
}

// PDBUpdateFailed records a PDB update failure
func (e *EventRecorder) PDBUpdateFailed(obj runtime.Object, deployment string, err error) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonPDBUpdateFailed,
		"Failed to update PodDisruptionBudget for deployment %s: %v", deployment, err)
}

// PDBDeletionFailed records a PDB deletion failure
func (e *EventRecorder) PDBDeletionFailed(obj runtime.Object, deployment string, err error) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonPDBDeletionFailed,
		"Failed to delete PodDisruptionBudget for deployment %s: %v", deployment, err)
}

// Configuration Events

// InvalidConfiguration records an invalid configuration event
func (e *EventRecorder) InvalidConfiguration(obj runtime.Object, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonInvalidConfig,
		"Invalid configuration: %s", reason)
}

// ConfigurationError records a configuration error
func (e *EventRecorder) ConfigurationError(obj runtime.Object, configType string, err error) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonConfigurationError,
		"Configuration error for %s: %v", configType, err)
}

// MaintenanceWindowActive records maintenance window activation
func (e *EventRecorder) MaintenanceWindowActive(obj runtime.Object, deployment, window string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonMaintenanceWindow,
		"Deployment %s is in maintenance window (%s), PDB enforcement suspended",
		deployment, window)
}

// Policy Events

// PolicyApplied records policy application
func (e *EventRecorder) PolicyApplied(obj runtime.Object, policyName string, componentsCount int) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPolicyApplied,
		"AvailabilityPolicy %s applied to %d components", policyName, componentsCount)
}

// PolicyRemoved records policy removal
func (e *EventRecorder) PolicyRemoved(obj runtime.Object, policyName string, componentsCount int) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPolicyRemoved,
		"AvailabilityPolicy %s removed from %d components", policyName, componentsCount)
}

// PolicyUpdated records policy update
func (e *EventRecorder) PolicyUpdated(obj runtime.Object, policyName string, changes string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPolicyUpdated,
		"AvailabilityPolicy %s updated: %s", policyName, changes)
}

// PolicyValidated records successful policy validation
func (e *EventRecorder) PolicyValidated(obj runtime.Object, policyName string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonPolicyValidated,
		"AvailabilityPolicy %s validated successfully", policyName)
}

// PolicyInvalid records policy validation failure
func (e *EventRecorder) PolicyInvalid(obj runtime.Object, policyName string, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonPolicyInvalid,
		"AvailabilityPolicy %s validation failed: %s", policyName, reason)
}

// Deployment Events

// DeploymentManaged records when a deployment becomes managed
func (e *EventRecorder) DeploymentManaged(obj runtime.Object, deployment string, source string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonDeploymentManaged,
		"Deployment %s is now managed for PDB (source: %s)", deployment, source)
}

// DeploymentUnmanaged records when a deployment becomes unmanaged
func (e *EventRecorder) DeploymentUnmanaged(obj runtime.Object, deployment string, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonDeploymentUnmanaged,
		"Deployment %s is no longer managed for PDB: %s", deployment, reason)
}

// DeploymentSkipped records when a deployment is skipped
func (e *EventRecorder) DeploymentSkipped(obj runtime.Object, deployment string, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonDeploymentSkipped,
		"Deployment %s skipped for PDB management: %s", deployment, reason)
}

// Compliance Events

// ComplianceAchieved records when compliance is achieved
func (e *EventRecorder) ComplianceAchieved(obj runtime.Object, deployment string, details string) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, ReasonComplianceAchieved,
		"Deployment %s achieved PDB compliance: %s", deployment, details)
}

// ComplianceLost records when compliance is lost
func (e *EventRecorder) ComplianceLost(obj runtime.Object, deployment string, reason string) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, ReasonComplianceLost,
		"Deployment %s lost PDB compliance: %s", deployment, reason)
}

// Generic event helpers

// Info records a generic informational event
func (e *EventRecorder) Info(obj runtime.Object, reason, message string) {
	e.recorder.Event(obj, corev1.EventTypeNormal, reason, message)
}

// Warn records a generic warning event
func (e *EventRecorder) Warn(obj runtime.Object, reason, message string) {
	e.recorder.Event(obj, corev1.EventTypeWarning, reason, message)
}

// Error records a generic error event
func (e *EventRecorder) Error(obj runtime.Object, reason string, err error) {
	// Skip event creation if object is nil or namespace not found
	if obj == nil {
		return
	}
	e.recorder.Eventf(obj, corev1.EventTypeWarning, reason, "Error: %v", err)
}

// SafeEventf creates an event safely, handling namespace not found errors
func (e *EventRecorder) SafeEventf(obj runtime.Object, eventType string, reason, format string, args ...interface{}) {
	if obj == nil {
		return
	}

	// Try to create the event, but don't fail if namespace is gone
	defer func() {
		if r := recover(); r != nil {
			// Log the panic but don't crash
			// This can happen when namespace is deleted during event creation
		}
	}()

	e.recorder.Eventf(obj, eventType, reason, format, args...)
}

// Infof records a formatted informational event
func (e *EventRecorder) Infof(obj runtime.Object, reason, format string, args ...interface{}) {
	e.recorder.Eventf(obj, corev1.EventTypeNormal, reason, format, args...)
}

// Warnf records a formatted warning event
func (e *EventRecorder) Warnf(obj runtime.Object, reason, format string, args ...interface{}) {
	e.recorder.Eventf(obj, corev1.EventTypeWarning, reason, format, args...)
}
