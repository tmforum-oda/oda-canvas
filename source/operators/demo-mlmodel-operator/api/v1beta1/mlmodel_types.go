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

package v1beta1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

type ResourceState string

const (
	StatePending         ResourceState = "Pending"
	StateCreatingStorage ResourceState = "CreatingStorage"
	StateDownloading     ResourceState = "Downloading"
	StateServing         ResourceState = "Serving"
	StateFailed          ResourceState = "Failed"
	StateReady           ResourceState = "Ready"
	StateTerminating     ResourceState = "Terminating"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// MLModelSpec defines the desired state of MLModel
type MLModelSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// Foo is an example field of MLModel. Edit mlmodel_types.go to remove/update
	ModelURL    string `json:"modelURL,omitempty"`
	StorageSize string `json:"storageSize"`
	Framework   string `json:"framework"`
	Replicas    int32  `json:"replicas"`
	Expose      bool   `json:"expose"`
}

type MLModelStatus struct {
	Phase              ResourceState `json:"phase"`
	Message            string        `json:"message,omitempty"`
	ServiceEndpoint    string        `json:"serviceEndpoint,omitempty"`
	ObservedGeneration int64         `json:"observedGeneration"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

// MLModel is the Schema for the mlmodels API
type MLModel struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MLModelSpec   `json:"spec,omitempty"`
	Status MLModelStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// MLModelList contains a list of MLModel
type MLModelList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []MLModel `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MLModel{}, &MLModelList{})
}
