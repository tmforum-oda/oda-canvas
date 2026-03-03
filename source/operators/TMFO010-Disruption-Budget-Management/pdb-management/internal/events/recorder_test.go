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
	"testing"

	"github.com/stretchr/testify/assert"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/tools/record"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
)

func TestEventRecorder_PDBLifecycleEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
		expectedType  string
	}{
		{
			name: "PDB created",
			eventFunc: func() {
				eventRecorder.PDBCreated(deployment, "test-deployment", "test-pdb", "high-availability", "75%")
			},
			expectedEvent: "Created PodDisruptionBudget test-pdb for deployment test-deployment",
			expectedType:  corev1.EventTypeNormal,
		},
		{
			name: "PDB updated",
			eventFunc: func() {
				eventRecorder.PDBUpdated(deployment, "test-deployment", "test-pdb", "50%", "75%")
			},
			expectedEvent: "Updated PodDisruptionBudget test-pdb for deployment test-deployment",
			expectedType:  corev1.EventTypeNormal,
		},
		{
			name: "PDB deleted",
			eventFunc: func() {
				eventRecorder.PDBDeleted(deployment, "test-deployment", "test-pdb", "deployment deleted")
			},
			expectedEvent: "Deleted PodDisruptionBudget test-pdb for deployment test-deployment",
			expectedType:  corev1.EventTypeNormal,
		},
		{
			name: "PDB creation failed",
			eventFunc: func() {
				eventRecorder.PDBCreationFailed(deployment, "test-deployment", assert.AnError)
			},
			expectedEvent: "Failed to create PodDisruptionBudget for deployment test-deployment",
			expectedType:  corev1.EventTypeWarning,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
				if tt.expectedType == corev1.EventTypeWarning {
					assert.Contains(t, event, "Warning")
				} else {
					assert.Contains(t, event, "Normal")
				}
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}

func TestEventRecorder_PolicyEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test policy
	policy := &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-policy",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
	}{
		{
			name: "Policy applied",
			eventFunc: func() {
				eventRecorder.PolicyApplied(policy, "test-policy", 5)
			},
			expectedEvent: "AvailabilityPolicy test-policy applied to 5 components",
		},
		{
			name: "Policy removed",
			eventFunc: func() {
				eventRecorder.PolicyRemoved(policy, "test-policy", 3)
			},
			expectedEvent: "AvailabilityPolicy test-policy removed from 3 components",
		},
		{
			name: "Policy validated",
			eventFunc: func() {
				eventRecorder.PolicyValidated(policy, "test-policy")
			},
			expectedEvent: "AvailabilityPolicy test-policy validated successfully",
		},
		{
			name: "Policy invalid",
			eventFunc: func() {
				eventRecorder.PolicyInvalid(policy, "test-policy", "missing required field")
			},
			expectedEvent: "AvailabilityPolicy test-policy validation failed: missing required field",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}

func TestEventRecorder_DeploymentEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
	}{
		{
			name: "Deployment managed",
			eventFunc: func() {
				eventRecorder.DeploymentManaged(deployment, "test-deployment", "annotation")
			},
			expectedEvent: "Deployment test-deployment is now managed for PDB (source: annotation)",
		},
		{
			name: "Deployment unmanaged",
			eventFunc: func() {
				eventRecorder.DeploymentUnmanaged(deployment, "test-deployment", "annotations removed")
			},
			expectedEvent: "Deployment test-deployment is no longer managed for PDB: annotations removed",
		},
		{
			name: "Deployment skipped",
			eventFunc: func() {
				eventRecorder.DeploymentSkipped(deployment, "test-deployment", "single replica")
			},
			expectedEvent: "Deployment test-deployment skipped for PDB management: single replica",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}

func TestEventRecorder_ConfigurationEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
		isWarning     bool
	}{
		{
			name: "Invalid configuration",
			eventFunc: func() {
				eventRecorder.InvalidConfiguration(deployment, "invalid availability class")
			},
			expectedEvent: "Invalid configuration: invalid availability class",
			isWarning:     true,
		},
		{
			name: "Configuration error",
			eventFunc: func() {
				eventRecorder.ConfigurationError(deployment, "availability", assert.AnError)
			},
			expectedEvent: "Configuration error for availability",
			isWarning:     true,
		},
		{
			name: "Maintenance window active",
			eventFunc: func() {
				eventRecorder.MaintenanceWindowActive(deployment, "test-deployment", "02:00-04:00 UTC")
			},
			expectedEvent: "Deployment test-deployment is in maintenance window (02:00-04:00 UTC)",
			isWarning:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
				if tt.isWarning {
					assert.Contains(t, event, "Warning")
				} else {
					assert.Contains(t, event, "Normal")
				}
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}

func TestEventRecorder_ComplianceEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test deployment
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
		isWarning     bool
	}{
		{
			name: "Compliance achieved",
			eventFunc: func() {
				eventRecorder.ComplianceAchieved(deployment, "test-deployment", "PDB created with 75% availability")
			},
			expectedEvent: "Deployment test-deployment achieved PDB compliance: PDB created with 75% availability",
			isWarning:     false,
		},
		{
			name: "Compliance lost",
			eventFunc: func() {
				eventRecorder.ComplianceLost(deployment, "test-deployment", "replicas reduced below minimum")
			},
			expectedEvent: "Deployment test-deployment lost PDB compliance: replicas reduced below minimum",
			isWarning:     true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
				if tt.isWarning {
					assert.Contains(t, event, "Warning")
				} else {
					assert.Contains(t, event, "Normal")
				}
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}

func TestEventRecorder_GenericEvents(t *testing.T) {
	// Create fake recorder
	fakeRecorder := record.NewFakeRecorder(10)
	eventRecorder := NewEventRecorder(fakeRecorder)

	// Create test object
	obj := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deployment",
			Namespace: "default",
		},
	}

	tests := []struct {
		name          string
		eventFunc     func()
		expectedEvent string
		eventType     string
	}{
		{
			name: "Info event",
			eventFunc: func() {
				eventRecorder.Info(obj, "TestReason", "This is an info message")
			},
			expectedEvent: "This is an info message",
			eventType:     "Normal",
		},
		{
			name: "Warning event",
			eventFunc: func() {
				eventRecorder.Warn(obj, "TestReason", "This is a warning message")
			},
			expectedEvent: "This is a warning message",
			eventType:     "Warning",
		},
		{
			name: "Error event",
			eventFunc: func() {
				eventRecorder.Error(obj, "TestReason", assert.AnError)
			},
			expectedEvent: "Error:",
			eventType:     "Warning",
		},
		{
			name: "Formatted info event",
			eventFunc: func() {
				eventRecorder.Infof(obj, "TestReason", "Deployment %s is ready", "test-app")
			},
			expectedEvent: "Deployment test-app is ready",
			eventType:     "Normal",
		},
		{
			name: "Formatted warning event",
			eventFunc: func() {
				eventRecorder.Warnf(obj, "TestReason", "Deployment %s has %d replicas", "test-app", 1)
			},
			expectedEvent: "Deployment test-app has 1 replicas",
			eventType:     "Warning",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Execute the event function
			tt.eventFunc()

			// Check the recorded event
			select {
			case event := <-fakeRecorder.Events:
				assert.Contains(t, event, tt.expectedEvent)
				assert.Contains(t, event, tt.eventType)
			default:
				t.Error("Expected event but none was recorded")
			}
		})
	}
}
