package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// MonitoringTools handles monitoring and event tracking for PDB-related resources
type MonitoringTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewMonitoringTools creates a new MonitoringTools instance
func NewMonitoringTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *MonitoringTools {
	return &MonitoringTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// MonitorPDBEventsParams defines parameters for monitoring PDB events
type MonitorPDBEventsParams struct {
	Namespaces     []string   `json:"namespaces,omitempty"`
	EventTypes     []string   `json:"eventTypes,omitempty"` // Warning, Normal
	Since          *time.Time `json:"since,omitempty"`
	MaxEvents      int        `json:"maxEvents,omitempty"`
	IncludeRelated bool       `json:"includeRelated,omitempty"` // Include deployment/pod events
	FollowMode     bool       `json:"followMode,omitempty"`     // For future streaming support
}

// PDBEventsResult represents the result of PDB event monitoring
type PDBEventsResult struct {
	Summary          EventSummary          `json:"summary"`
	Events           []PDBEvent            `json:"events"`
	RelatedResources RelatedResourcesInfo  `json:"relatedResources,omitempty"`
	Recommendations  []EventRecommendation `json:"recommendations"`
}

// EventSummary provides a summary of events found
type EventSummary struct {
	TotalEvents    int            `json:"totalEvents"`
	EventsByType   map[string]int `json:"eventsByType"`
	EventsByReason map[string]int `json:"eventsByReason"`
	NamespaceStats map[string]int `json:"namespaceStats"`
	TimeRange      TimeRange      `json:"timeRange"`
	CriticalIssues int            `json:"criticalIssues"`
}

// PDBEvent represents a PDB-related event with enhanced context
type PDBEvent struct {
	Type           string          `json:"type"`
	Reason         string          `json:"reason"`
	Message        string          `json:"message"`
	Namespace      string          `json:"namespace"`
	InvolvedObject ObjectReference `json:"involvedObject"`
	Source         EventSource     `json:"source"`
	FirstTime      time.Time       `json:"firstTime"`
	LastTime       time.Time       `json:"lastTime"`
	Count          int32           `json:"count"`
	Severity       string          `json:"severity"`
	Impact         string          `json:"impact"`
	Context        EventContext    `json:"context,omitempty"`
}

// ObjectReference represents a reference to a Kubernetes object
type ObjectReference struct {
	Kind       string `json:"kind"`
	Name       string `json:"name"`
	Namespace  string `json:"namespace"`
	APIVersion string `json:"apiVersion"`
}

// EventSource represents the source of an event
type EventSource struct {
	Component string `json:"component"`
	Host      string `json:"host,omitempty"`
}

// EventContext provides additional context about the event
type EventContext struct {
	RelatedDeployments []string          `json:"relatedDeployments,omitempty"`
	PodStatus          []PodStatusInfo   `json:"podStatus,omitempty"`
	PDBStatus          *PDBStatusInfo    `json:"pdbStatus,omitempty"`
	Annotations        map[string]string `json:"annotations,omitempty"`
}

// PodStatusInfo contains information about pod status
type PodStatusInfo struct {
	Name   string `json:"name"`
	Phase  string `json:"phase"`
	Ready  bool   `json:"ready"`
	Reason string `json:"reason,omitempty"`
}

// PDBStatusInfo contains information about PDB status
type PDBStatusInfo struct {
	CurrentHealthy     int32 `json:"currentHealthy"`
	DesiredHealthy     int32 `json:"desiredHealthy"`
	DisruptionsAllowed int32 `json:"disruptionsAllowed"`
	ExpectedPods       int32 `json:"expectedPods"`
}

// RelatedResourcesInfo contains information about related resources
type RelatedResourcesInfo struct {
	DeploymentStats map[string]DeploymentStat `json:"deploymentStats"`
	PDBStats        map[string]PDBStat        `json:"pdbStats"`
	NodeEvents      []NodeEventInfo           `json:"nodeEvents,omitempty"`
}

// DeploymentStat contains deployment statistics
type DeploymentStat struct {
	Replicas            int32 `json:"replicas"`
	ReadyReplicas       int32 `json:"readyReplicas"`
	AvailableReplicas   int32 `json:"availableReplicas"`
	UnavailableReplicas int32 `json:"unavailableReplicas"`
}

// PDBStat contains PDB statistics
type PDBStat struct {
	CurrentHealthy     int32  `json:"currentHealthy"`
	DisruptionsAllowed int32  `json:"disruptionsAllowed"`
	ExpectedPods       int32  `json:"expectedPods"`
	MinAvailable       string `json:"minAvailable,omitempty"`
	MaxUnavailable     string `json:"maxUnavailable,omitempty"`
}

// NodeEventInfo contains information about node events affecting PDBs
type NodeEventInfo struct {
	NodeName  string    `json:"nodeName"`
	Type      string    `json:"type"`
	Reason    string    `json:"reason"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

// TimeRange represents a time range
type TimeRange struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
}

// EventRecommendation provides recommendations based on events
type EventRecommendation struct {
	Type        string   `json:"type"`     // "action", "warning", "info"
	Priority    string   `json:"priority"` // "high", "medium", "low"
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Actions     []string `json:"actions"`
}

// MonitorPDBEvents monitors and analyzes PDB-related events
func (m *MonitoringTools) MonitorPDBEvents(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var monitorParams MonitorPDBEventsParams
	if err := json.Unmarshal(params, &monitorParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Set defaults
	if monitorParams.MaxEvents == 0 {
		monitorParams.MaxEvents = 100
	}
	if monitorParams.Since == nil {
		since := time.Now().Add(-24 * time.Hour) // Last 24 hours
		monitorParams.Since = &since
	}
	if len(monitorParams.EventTypes) == 0 {
		monitorParams.EventTypes = []string{"Warning", "Normal"}
	}

	m.logger.Info("Starting PDB event monitoring",
		"namespaces", monitorParams.Namespaces,
		"since", monitorParams.Since,
		"maxEvents", monitorParams.MaxEvents)

	// Get PDB-related events
	events, err := m.getPDBEvents(ctx, monitorParams)
	if err != nil {
		return nil, fmt.Errorf("failed to get PDB events: %w", err)
	}

	// Get related resources information if requested
	var relatedResources RelatedResourcesInfo
	if monitorParams.IncludeRelated {
		relatedResources, err = m.getRelatedResourcesInfo(ctx, monitorParams.Namespaces)
		if err != nil {
			m.logger.Error(err, "Failed to get related resources info")
		}
	}

	// Generate summary
	summary := m.generateEventSummary(events, *monitorParams.Since)

	// Generate recommendations
	recommendations := m.generateEventRecommendations(events, summary)

	result := PDBEventsResult{
		Summary:          summary,
		Events:           events,
		RelatedResources: relatedResources,
		Recommendations:  recommendations,
	}

	m.logger.Info("PDB event monitoring completed",
		"totalEvents", len(events),
		"criticalIssues", summary.CriticalIssues,
		"recommendations", len(recommendations))

	return &types.ToolResult{
		IsError: false,
		Content: result,
	}, nil
}

func (m *MonitoringTools) getPDBEvents(ctx context.Context, params MonitorPDBEventsParams) ([]PDBEvent, error) {
	var allEvents []PDBEvent

	namespaces := params.Namespaces
	if len(namespaces) == 0 {
		// Get all namespaces
		nsList, err := m.kubeClient.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to list namespaces: %w", err)
		}
		for _, ns := range nsList.Items {
			namespaces = append(namespaces, ns.Name)
		}
	}

	for _, namespace := range namespaces {
		nsEvents, err := m.getNamespaceEvents(ctx, namespace, params)
		if err != nil {
			m.logger.Error(err, "Failed to get events for namespace", "namespace", namespace)
			continue
		}
		allEvents = append(allEvents, nsEvents...)
	}

	// Sort events by time (most recent first)
	sort.Slice(allEvents, func(i, j int) bool {
		return allEvents[i].LastTime.After(allEvents[j].LastTime)
	})

	// Limit results
	if len(allEvents) > params.MaxEvents {
		allEvents = allEvents[:params.MaxEvents]
	}

	return allEvents, nil
}

func (m *MonitoringTools) getNamespaceEvents(ctx context.Context, namespace string, params MonitorPDBEventsParams) ([]PDBEvent, error) {
	// Get all events in the namespace
	events, err := m.kubeClient.CoreV1().Events(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list events in namespace %s: %w", namespace, err)
	}

	var pdbEvents []PDBEvent
	for _, event := range events.Items {
		// Filter events that are PDB-related or deployment-related
		if !m.isPDBRelatedEvent(event) {
			continue
		}

		// Filter by event type
		if !m.containsString(params.EventTypes, event.Type) {
			continue
		}

		// Filter by time
		if event.LastTimestamp.Time.Before(*params.Since) {
			continue
		}

		// Convert to PDBEvent with enhanced context
		pdbEvent := m.convertToPDBEvent(ctx, event)
		pdbEvents = append(pdbEvents, pdbEvent)
	}

	return pdbEvents, nil
}

func (m *MonitoringTools) isPDBRelatedEvent(event corev1.Event) bool {
	// Check if the event is directly related to PDB
	if event.InvolvedObject.Kind == "PodDisruptionBudget" {
		return true
	}

	// Check if the event is related to deployments that might have PDBs
	if event.InvolvedObject.Kind == "Deployment" {
		// Look for eviction-related events
		evictionReasons := []string{"EvictionExecutor", "PodDisruptionBudget", "Evicted", "Evicting"}
		for _, reason := range evictionReasons {
			if strings.Contains(event.Reason, reason) || strings.Contains(event.Message, reason) {
				return true
			}
		}
	}

	// Check for pod events that might be related to PDB constraints
	if event.InvolvedObject.Kind == "Pod" {
		pdbReasons := []string{"Evicted", "EvictionThresholdMet", "DisruptionTarget"}
		for _, reason := range pdbReasons {
			if strings.Contains(event.Reason, reason) || strings.Contains(event.Message, reason) {
				return true
			}
		}
	}

	return false
}

func (m *MonitoringTools) convertToPDBEvent(ctx context.Context, event corev1.Event) PDBEvent {
	pdbEvent := PDBEvent{
		Type:      event.Type,
		Reason:    event.Reason,
		Message:   event.Message,
		Namespace: event.Namespace,
		InvolvedObject: ObjectReference{
			Kind:       event.InvolvedObject.Kind,
			Name:       event.InvolvedObject.Name,
			Namespace:  event.InvolvedObject.Namespace,
			APIVersion: event.InvolvedObject.APIVersion,
		},
		Source: EventSource{
			Component: event.Source.Component,
			Host:      event.Source.Host,
		},
		FirstTime: event.FirstTimestamp.Time,
		LastTime:  event.LastTimestamp.Time,
		Count:     event.Count,
		Severity:  m.determineSeverity(event),
		Impact:    m.determineImpact(event),
	}

	// Add context information
	pdbEvent.Context = m.getEventContext(ctx, event)

	return pdbEvent
}

func (m *MonitoringTools) getEventContext(ctx context.Context, event corev1.Event) EventContext {
	context := EventContext{
		Annotations: make(map[string]string),
	}

	// Get related deployments if this is a pod or PDB event
	if event.InvolvedObject.Kind == "Pod" || event.InvolvedObject.Kind == "PodDisruptionBudget" {
		deployments, err := m.kubeClient.AppsV1().Deployments(event.Namespace).List(ctx, metav1.ListOptions{})
		if err == nil {
			for _, dep := range deployments.Items {
				if m.isRelatedToEvent(dep, event) {
					context.RelatedDeployments = append(context.RelatedDeployments, dep.Name)
				}
			}
		}
	}

	// Get PDB status if this is a PDB event
	if event.InvolvedObject.Kind == "PodDisruptionBudget" {
		pdb, err := m.kubeClient.PolicyV1().PodDisruptionBudgets(event.Namespace).Get(ctx, event.InvolvedObject.Name, metav1.GetOptions{})
		if err == nil {
			context.PDBStatus = &PDBStatusInfo{
				CurrentHealthy:     pdb.Status.CurrentHealthy,
				DesiredHealthy:     pdb.Status.DesiredHealthy,
				DisruptionsAllowed: pdb.Status.DisruptionsAllowed,
				ExpectedPods:       pdb.Status.ExpectedPods,
			}
		}
	}

	// Get pod status if this is related to pods
	if len(context.RelatedDeployments) > 0 {
		for _, depName := range context.RelatedDeployments {
			pods, err := m.kubeClient.CoreV1().Pods(event.Namespace).List(ctx, metav1.ListOptions{
				LabelSelector: fmt.Sprintf("app=%s", depName),
			})
			if err == nil {
				for _, pod := range pods.Items {
					ready := false
					for _, condition := range pod.Status.Conditions {
						if condition.Type == corev1.PodReady && condition.Status == corev1.ConditionTrue {
							ready = true
							break
						}
					}

					reason := string(pod.Status.Phase)
					if pod.Status.Reason != "" {
						reason = pod.Status.Reason
					}

					context.PodStatus = append(context.PodStatus, PodStatusInfo{
						Name:   pod.Name,
						Phase:  string(pod.Status.Phase),
						Ready:  ready,
						Reason: reason,
					})
				}
			}
		}
	}

	return context
}

func (m *MonitoringTools) isRelatedToEvent(deployment appsv1.Deployment, event corev1.Event) bool {
	// Simple heuristic: check if deployment name or labels match event
	if strings.Contains(event.Message, deployment.Name) {
		return true
	}

	// Check if event involves pods that belong to this deployment
	if event.InvolvedObject.Kind == "Pod" {
		// Extract deployment name from pod name (common pattern: deployment-name-xxx)
		podName := event.InvolvedObject.Name
		if strings.HasPrefix(podName, deployment.Name+"-") {
			return true
		}
	}

	return false
}

func (m *MonitoringTools) determineSeverity(event corev1.Event) string {
	if event.Type == "Warning" {
		criticalReasons := []string{"Failed", "Error", "Evicted", "OutOfMemory", "DiskPressure"}
		for _, reason := range criticalReasons {
			if strings.Contains(event.Reason, reason) || strings.Contains(event.Message, reason) {
				return "critical"
			}
		}
		return "warning"
	}
	return "info"
}

func (m *MonitoringTools) determineImpact(event corev1.Event) string {
	if event.InvolvedObject.Kind == "PodDisruptionBudget" {
		if strings.Contains(event.Message, "disruption") || strings.Contains(event.Message, "evict") {
			return "high"
		}
	}

	if strings.Contains(event.Message, "Failed") || strings.Contains(event.Message, "Error") {
		return "high"
	}

	if event.Type == "Warning" {
		return "medium"
	}

	return "low"
}

func (m *MonitoringTools) getRelatedResourcesInfo(ctx context.Context, namespaces []string) (RelatedResourcesInfo, error) {
	info := RelatedResourcesInfo{
		DeploymentStats: make(map[string]DeploymentStat),
		PDBStats:        make(map[string]PDBStat),
	}

	targetNamespaces := namespaces
	if len(targetNamespaces) == 0 {
		nsList, err := m.kubeClient.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			return info, err
		}
		for _, ns := range nsList.Items {
			targetNamespaces = append(targetNamespaces, ns.Name)
		}
	}

	for _, ns := range targetNamespaces {
		// Get deployment stats
		deployments, err := m.kubeClient.AppsV1().Deployments(ns).List(ctx, metav1.ListOptions{})
		if err == nil {
			for _, dep := range deployments.Items {
				key := fmt.Sprintf("%s/%s", ns, dep.Name)
				info.DeploymentStats[key] = DeploymentStat{
					Replicas:            dep.Status.Replicas,
					ReadyReplicas:       dep.Status.ReadyReplicas,
					AvailableReplicas:   dep.Status.AvailableReplicas,
					UnavailableReplicas: dep.Status.UnavailableReplicas,
				}
			}
		}

		// Get PDB stats
		pdbs, err := m.kubeClient.PolicyV1().PodDisruptionBudgets(ns).List(ctx, metav1.ListOptions{})
		if err == nil {
			for _, pdb := range pdbs.Items {
				key := fmt.Sprintf("%s/%s", ns, pdb.Name)
				pdbStat := PDBStat{
					CurrentHealthy:     pdb.Status.CurrentHealthy,
					DisruptionsAllowed: pdb.Status.DisruptionsAllowed,
					ExpectedPods:       pdb.Status.ExpectedPods,
				}

				if pdb.Spec.MinAvailable != nil {
					pdbStat.MinAvailable = pdb.Spec.MinAvailable.String()
				}
				if pdb.Spec.MaxUnavailable != nil {
					pdbStat.MaxUnavailable = pdb.Spec.MaxUnavailable.String()
				}

				info.PDBStats[key] = pdbStat
			}
		}
	}

	return info, nil
}

func (m *MonitoringTools) generateEventSummary(events []PDBEvent, since time.Time) EventSummary {
	summary := EventSummary{
		TotalEvents:    len(events),
		EventsByType:   make(map[string]int),
		EventsByReason: make(map[string]int),
		NamespaceStats: make(map[string]int),
		TimeRange: TimeRange{
			Start: since,
			End:   time.Now(),
		},
	}

	if len(events) > 0 {
		summary.TimeRange.Start = events[len(events)-1].FirstTime
		summary.TimeRange.End = events[0].LastTime
	}

	for _, event := range events {
		summary.EventsByType[event.Type]++
		summary.EventsByReason[event.Reason]++
		summary.NamespaceStats[event.Namespace]++

		if event.Severity == "critical" || event.Impact == "high" {
			summary.CriticalIssues++
		}
	}

	return summary
}

func (m *MonitoringTools) generateEventRecommendations(events []PDBEvent, summary EventSummary) []EventRecommendation {
	var recommendations []EventRecommendation

	// High number of critical events
	if summary.CriticalIssues > 5 {
		recommendations = append(recommendations, EventRecommendation{
			Type:        "warning",
			Priority:    "high",
			Title:       "High Number of Critical Events",
			Description: fmt.Sprintf("Found %d critical events that may indicate stability issues", summary.CriticalIssues),
			Actions: []string{
				"Review PDB configurations for affected deployments",
				"Check cluster resource availability",
				"Examine node health and capacity",
			},
		})
	}

	// Frequent evictions
	evictionCount := summary.EventsByReason["Evicted"] + summary.EventsByReason["EvictionExecutor"]
	if evictionCount > 3 {
		recommendations = append(recommendations, EventRecommendation{
			Type:        "action",
			Priority:    "high",
			Title:       "Frequent Pod Evictions",
			Description: fmt.Sprintf("Found %d eviction events, which may indicate resource pressure", evictionCount),
			Actions: []string{
				"Review resource requests and limits",
				"Consider adjusting PDB minAvailable values",
				"Scale up deployments if necessary",
			},
		})
	}

	// PDB constraint violations
	for _, event := range events {
		if event.InvolvedObject.Kind == "PodDisruptionBudget" && event.Type == "Warning" {
			recommendations = append(recommendations, EventRecommendation{
				Type:        "action",
				Priority:    "medium",
				Title:       "PDB Constraint Violations",
				Description: "PodDisruptionBudget constraints are preventing necessary operations",
				Actions: []string{
					"Review PDB configuration for " + event.InvolvedObject.Name,
					"Consider adjusting minAvailable or maxUnavailable values",
					"Ensure sufficient replicas for PDB to be effective",
				},
			})
			break
		}
	}

	// No recent events (good sign)
	if len(events) == 0 {
		recommendations = append(recommendations, EventRecommendation{
			Type:        "info",
			Priority:    "low",
			Title:       "No Recent PDB Events",
			Description: "No PDB-related events found in the specified time period",
			Actions: []string{
				"Continue monitoring for any emerging issues",
				"Consider running compliance validation",
			},
		})
	}

	return recommendations
}

func (m *MonitoringTools) containsString(slice []string, str string) bool {
	for _, s := range slice {
		if s == str {
			return true
		}
	}
	return false
}

// RegisterMonitoringTools registers monitoring tools with the MCP server
func RegisterMonitoringTools(server interface{ RegisterTool(*types.Tool) error }, tools *MonitoringTools) error {
	monitorTool := &types.Tool{
		Name:        "monitor_pdb_events",
		Description: "Monitor and analyze PDB-related events in the cluster",
		InputSchema: func() json.RawMessage {
			schema := map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"namespaces": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string"},
						"description": "List of namespaces to monitor (empty for all)",
					},
					"eventTypes": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string", "enum": []string{"Warning", "Normal"}},
						"description": "Types of events to include",
						"default":     []string{"Warning", "Normal"},
					},
					"since": map[string]interface{}{
						"type":        "string",
						"format":      "date-time",
						"description": "Include events since this time (default: 24 hours ago)",
					},
					"maxEvents": map[string]interface{}{
						"type":        "integer",
						"description": "Maximum number of events to return",
						"default":     100,
					},
					"includeRelated": map[string]interface{}{
						"type":        "boolean",
						"description": "Include information about related resources",
						"default":     false,
					},
				},
			}
			data, _ := json.Marshal(schema)
			return data
		}(),
		Handler: tools.MonitorPDBEvents,
	}

	return server.RegisterTool(monitorTool)
}
