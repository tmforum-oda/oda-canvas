package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// ManagementTools provides management tools for MCP
type ManagementTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewManagementTools creates new management tools
func NewManagementTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *ManagementTools {
	return &ManagementTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// CreateAvailabilityPolicyParams represents parameters for creating an availability policy
type CreateAvailabilityPolicyParams struct {
	Name                   string                    `json:"name,omitempty"` // Auto-generated if not provided
	Namespace              string                    `json:"namespace"`
	AvailabilityClass      string                    `json:"availabilityClass,omitempty"` // Auto-detected if not provided
	Enforcement            string                    `json:"enforcement,omitempty"`
	Priority               int32                     `json:"priority,omitempty"`
	ComponentSelector      ComponentSelectorConfig   `json:"componentSelector,omitempty"` // Made optional for auto-mode
	CustomPDBConfig        *CustomPDBConfig          `json:"customPDBConfig,omitempty"`
	MaintenanceWindows     []MaintenanceWindowConfig `json:"maintenanceWindows,omitempty"`
	MinimumClass           string                    `json:"minimumClass,omitempty"`
	AllowOverride          *bool                     `json:"allowOverride,omitempty"`
	OverrideRequiresReason *bool                     `json:"overrideRequiresReason,omitempty"`

	// New intelligent parameters
	AutoDetect         bool     `json:"autoDetect,omitempty"`         // Enable auto-detection mode
	TargetDeployments  []string `json:"targetDeployments,omitempty"`  // Specific deployments to target
	ExcludeDeployments []string `json:"excludeDeployments,omitempty"` // Deployments to exclude
	GroupBy            string   `json:"groupBy,omitempty"`            // Group by: "class", "tier", "component", "auto"
	CreateMultiple     bool     `json:"createMultiple,omitempty"`     // Create multiple policies for groups
}

// ComponentSelectorConfig represents component selector configuration
type ComponentSelectorConfig struct {
	MatchLabels        map[string]string          `json:"matchLabels,omitempty"`
	MatchExpressions   []LabelSelectorRequirement `json:"matchExpressions,omitempty"`
	ComponentNames     []string                   `json:"componentNames,omitempty"`
	ComponentFunctions []string                   `json:"componentFunctions,omitempty"`
	Namespaces         []string                   `json:"namespaces,omitempty"`
}

// LabelSelectorRequirement represents a label selector requirement
type LabelSelectorRequirement struct {
	Key      string   `json:"key"`
	Operator string   `json:"operator"`
	Values   []string `json:"values,omitempty"`
}

// CustomPDBConfig represents custom PDB configuration
type CustomPDBConfig struct {
	MinAvailable               *string `json:"minAvailable,omitempty"`
	MaxUnavailable             *string `json:"maxUnavailable,omitempty"`
	UnhealthyPodEvictionPolicy string  `json:"unhealthyPodEvictionPolicy,omitempty"`
}

// MaintenanceWindowConfig represents maintenance window configuration
type MaintenanceWindowConfig struct {
	Start      string `json:"start"`
	End        string `json:"end"`
	Timezone   string `json:"timezone,omitempty"`
	DaysOfWeek []int  `json:"daysOfWeek,omitempty"`
}

// CreateAvailabilityPolicyResult represents the result of creating a policy
type CreateAvailabilityPolicyResult struct {
	Name      string `json:"name"`
	Namespace string `json:"namespace"`
	Created   bool   `json:"created"`
	Message   string `json:"message"`
}

// CreateAvailabilityPolicy creates a new AvailabilityPolicy resource with intelligent defaults
func (m *ManagementTools) CreateAvailabilityPolicy(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var createParams CreateAvailabilityPolicyParams
	if err := json.Unmarshal(params, &createParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Default namespace
	if createParams.Namespace == "" {
		createParams.Namespace = "canvas"
	}

	// Handle intelligent auto-detection mode
	if createParams.AutoDetect || createParams.GroupBy != "" {
		return m.createIntelligentPolicies(ctx, createParams)
	}

	// Handle simple mode with auto-generated name if needed
	if createParams.Name == "" {
		// Auto-generate policy name based on parameters
		if len(createParams.TargetDeployments) > 0 {
			createParams.Name = fmt.Sprintf("%s-policy-%s", createParams.TargetDeployments[0], time.Now().Format("20060102"))
		} else if createParams.AvailabilityClass != "" {
			createParams.Name = fmt.Sprintf("%s-%s-policy", createParams.Namespace, createParams.AvailabilityClass)
		} else {
			createParams.Name = fmt.Sprintf("%s-auto-policy-%d", createParams.Namespace, time.Now().Unix())
		}
	}

	// Convert string availability class to typed version
	availClass, err := m.parseAvailabilityClass(createParams.AvailabilityClass)
	if err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error: Invalid availability class: %s", createParams.AvailabilityClass),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	// Create the AvailabilityPolicy
	policy := &v1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      createParams.Name,
			Namespace: createParams.Namespace,
		},
		Spec: v1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availClass,
			Priority:          createParams.Priority,
		},
	}

	// Set enforcement mode
	if createParams.Enforcement != "" {
		enforcement, err := m.parseEnforcementMode(createParams.Enforcement)
		if err != nil {
			return &types.ToolResult{
				Content:     fmt.Sprintf("Error: Invalid enforcement mode: %s", createParams.Enforcement),
				IsError:     true,
				ErrorDetail: err.Error(),
			}, nil
		}
		policy.Spec.Enforcement = enforcement
	}

	// Set minimum class for flexible enforcement
	if createParams.MinimumClass != "" {
		minClass, err := m.parseAvailabilityClass(createParams.MinimumClass)
		if err != nil {
			return &types.ToolResult{
				Content:     fmt.Sprintf("Error: Invalid minimum class: %s", createParams.MinimumClass),
				IsError:     true,
				ErrorDetail: err.Error(),
			}, nil
		}
		policy.Spec.MinimumClass = minClass
	}

	// Set component selector
	if err := m.setComponentSelector(&policy.Spec.ComponentSelector, createParams.ComponentSelector); err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error: Invalid component selector: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	// Set custom PDB config if provided
	if createParams.CustomPDBConfig != nil && availClass == v1alpha1.Custom {
		if err := m.setCustomPDBConfig(&policy.Spec, createParams.CustomPDBConfig); err != nil {
			return &types.ToolResult{
				Content:     fmt.Sprintf("Error: Invalid custom PDB config: %v", err),
				IsError:     true,
				ErrorDetail: err.Error(),
			}, nil
		}
	}

	// Set maintenance windows
	if len(createParams.MaintenanceWindows) > 0 {
		policy.Spec.MaintenanceWindows = m.convertMaintenanceWindows(createParams.MaintenanceWindows)
	}

	// Set override options
	if createParams.AllowOverride != nil {
		policy.Spec.AllowOverride = createParams.AllowOverride
	}
	if createParams.OverrideRequiresReason != nil {
		policy.Spec.OverrideRequiresReason = createParams.OverrideRequiresReason
	}

	// Check if policy already exists
	existing := &v1alpha1.AvailabilityPolicy{}
	err = m.client.Get(ctx, client.ObjectKey{Name: createParams.Name, Namespace: createParams.Namespace}, existing)
	if err == nil {
		return &types.ToolResult{
			Content: CreateAvailabilityPolicyResult{
				Name:      createParams.Name,
				Namespace: createParams.Namespace,
				Created:   false,
				Message:   "Policy already exists",
			},
		}, nil
	}

	// Create the policy
	if err := m.client.Create(ctx, policy); err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error creating policy: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	m.logger.Info("Created AvailabilityPolicy via MCP", "name", createParams.Name, "namespace", createParams.Namespace)

	return &types.ToolResult{
		Content: CreateAvailabilityPolicyResult{
			Name:      createParams.Name,
			Namespace: createParams.Namespace,
			Created:   true,
			Message:   "Policy created successfully",
		},
	}, nil
}

// UpdateDeploymentAnnotationsParams represents parameters for updating deployment annotations
type UpdateDeploymentAnnotationsParams struct {
	Name              string            `json:"name"`
	Namespace         string            `json:"namespace"`
	Annotations       map[string]string `json:"annotations"`
	RemoveAnnotations []string          `json:"removeAnnotations,omitempty"`
}

// UpdateDeploymentAnnotationsResult represents the result of updating deployment annotations
type UpdateDeploymentAnnotationsResult struct {
	Name        string            `json:"name"`
	Namespace   string            `json:"namespace"`
	Updated     bool              `json:"updated"`
	Message     string            `json:"message"`
	Annotations map[string]string `json:"annotations"`
}

// UpdateDeploymentAnnotations updates availability-related annotations on a deployment
func (m *ManagementTools) UpdateDeploymentAnnotations(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var updateParams UpdateDeploymentAnnotationsParams
	if err := json.Unmarshal(params, &updateParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Validate required parameters
	if updateParams.Name == "" || updateParams.Namespace == "" {
		return &types.ToolResult{
			Content:     "Error: Deployment name and namespace are required",
			IsError:     true,
			ErrorDetail: "Both name and namespace must be specified",
		}, nil
	}

	// Get the deployment
	deployment := &appsv1.Deployment{}
	err := m.client.Get(ctx, client.ObjectKey{
		Name:      updateParams.Name,
		Namespace: updateParams.Namespace,
	}, deployment)
	if err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error: Deployment not found: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	// Initialize annotations map if nil
	if deployment.Annotations == nil {
		deployment.Annotations = make(map[string]string)
	}

	// Track changes
	originalAnnotations := make(map[string]string)
	for k, v := range deployment.Annotations {
		originalAnnotations[k] = v
	}

	// Add/update annotations
	for key, value := range updateParams.Annotations {
		// Validate ODA-specific annotations
		if isODAAnnotation(key) {
			if err := m.validateODAAnnotation(key, value); err != nil {
				return &types.ToolResult{
					Content:     fmt.Sprintf("Error: Invalid annotation %s=%s: %v", key, value, err),
					IsError:     true,
					ErrorDetail: err.Error(),
				}, nil
			}
		}
		deployment.Annotations[key] = value
	}

	// Remove annotations
	for _, key := range updateParams.RemoveAnnotations {
		delete(deployment.Annotations, key)
	}

	// Update the deployment
	if err := m.client.Update(ctx, deployment); err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error updating deployment: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	m.logger.Info("Updated deployment annotations via MCP",
		"deployment", updateParams.Name,
		"namespace", updateParams.Namespace)

	return &types.ToolResult{
		Content: UpdateDeploymentAnnotationsResult{
			Name:        updateParams.Name,
			Namespace:   updateParams.Namespace,
			Updated:     true,
			Message:     "Deployment annotations updated successfully",
			Annotations: deployment.Annotations,
		},
	}, nil
}

// SimulatePolicyImpactParams represents parameters for simulating policy impact
type SimulatePolicyImpactParams struct {
	PolicySpec       CreateAvailabilityPolicyParams `json:"policySpec"`
	TargetNamespaces []string                       `json:"targetNamespaces,omitempty"`
}

// SimulatePolicyImpactResult represents the result of policy impact simulation
type SimulatePolicyImpactResult struct {
	AffectedDeployments []DeploymentImpact `json:"affectedDeployments"`
	Summary             SimulationSummary  `json:"summary"`
	Warnings            []string           `json:"warnings,omitempty"`
}

// DeploymentImpact represents the impact on a specific deployment
type DeploymentImpact struct {
	Name                 string `json:"name"`
	Namespace            string `json:"namespace"`
	CurrentClass         string `json:"currentClass,omitempty"`
	ProposedClass        string `json:"proposedClass"`
	CurrentMinAvailable  string `json:"currentMinAvailable,omitempty"`
	ProposedMinAvailable string `json:"proposedMinAvailable"`
	Impact               string `json:"impact"`
	Replicas             int32  `json:"replicas"`
}

// SimulationSummary provides a summary of the simulation
type SimulationSummary struct {
	TotalDeployments    int `json:"totalDeployments"`
	AffectedDeployments int `json:"affectedDeployments"`
	HighImpact          int `json:"highImpact"`
	MediumImpact        int `json:"mediumImpact"`
	LowImpact           int `json:"lowImpact"`
}

// SimulatePolicyImpact simulates the impact of applying a policy without actually creating it
func (m *ManagementTools) SimulatePolicyImpact(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var simParams SimulatePolicyImpactParams
	if err := json.Unmarshal(params, &simParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Create a temporary policy object for simulation
	availClass, err := m.parseAvailabilityClass(simParams.PolicySpec.AvailabilityClass)
	if err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error: Invalid availability class: %s", simParams.PolicySpec.AvailabilityClass),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	tempPolicy := &v1alpha1.AvailabilityPolicy{
		Spec: v1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availClass,
			Priority:          simParams.PolicySpec.Priority,
		},
	}

	// Set component selector
	if err := m.setComponentSelector(&tempPolicy.Spec.ComponentSelector, simParams.PolicySpec.ComponentSelector); err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error: Invalid component selector: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	// Get deployments to analyze
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{}
	if err := m.client.List(ctx, &deployments, listOpts); err != nil {
		return &types.ToolResult{
			Content:     fmt.Sprintf("Error listing deployments: %v", err),
			IsError:     true,
			ErrorDetail: err.Error(),
		}, nil
	}

	result := &SimulatePolicyImpactResult{
		AffectedDeployments: []DeploymentImpact{},
		Summary:             SimulationSummary{},
		Warnings:            []string{},
	}

	// Analyze impact on each deployment
	for _, deployment := range deployments.Items {
		// Check if this deployment would be affected by the policy
		if m.deploymentMatchesSelector(&deployment, &tempPolicy.Spec.ComponentSelector) {
			impact := m.calculateDeploymentImpact(&deployment, tempPolicy)
			result.AffectedDeployments = append(result.AffectedDeployments, impact)
			result.Summary.AffectedDeployments++

			// Categorize impact level
			switch impact.Impact {
			case "high":
				result.Summary.HighImpact++
			case "medium":
				result.Summary.MediumImpact++
			case "low":
				result.Summary.LowImpact++
			}
		}
		result.Summary.TotalDeployments++
	}

	// Generate warnings
	if result.Summary.HighImpact > 0 {
		result.Warnings = append(result.Warnings,
			fmt.Sprintf("%d deployments will have high impact changes", result.Summary.HighImpact))
	}

	if result.Summary.AffectedDeployments == 0 {
		result.Warnings = append(result.Warnings,
			"Policy selector does not match any deployments")
	}

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// Helper functions

func (m *ManagementTools) parseAvailabilityClass(class string) (v1alpha1.AvailabilityClass, error) {
	switch class {
	case "non-critical":
		return v1alpha1.NonCritical, nil
	case "standard":
		return v1alpha1.Standard, nil
	case "high-availability":
		return v1alpha1.HighAvailability, nil
	case "mission-critical":
		return v1alpha1.MissionCritical, nil
	case "custom":
		return v1alpha1.Custom, nil
	default:
		return "", fmt.Errorf("invalid availability class: %s", class)
	}
}

func (m *ManagementTools) parseEnforcementMode(mode string) (v1alpha1.EnforcementMode, error) {
	switch mode {
	case "strict":
		return v1alpha1.EnforcementStrict, nil
	case "flexible":
		return v1alpha1.EnforcementFlexible, nil
	case "advisory":
		return v1alpha1.EnforcementAdvisory, nil
	default:
		return "", fmt.Errorf("invalid enforcement mode: %s", mode)
	}
}

func (m *ManagementTools) setComponentSelector(selector *v1alpha1.ComponentSelector, config ComponentSelectorConfig) error {
	// Set match labels
	if len(config.MatchLabels) > 0 {
		selector.MatchLabels = config.MatchLabels
	}

	// Set match expressions
	if len(config.MatchExpressions) > 0 {
		for _, expr := range config.MatchExpressions {
			selector.MatchExpressions = append(selector.MatchExpressions, metav1.LabelSelectorRequirement{
				Key:      expr.Key,
				Operator: metav1.LabelSelectorOperator(expr.Operator),
				Values:   expr.Values,
			})
		}
	}

	// Set component names
	if len(config.ComponentNames) > 0 {
		selector.ComponentNames = config.ComponentNames
	}

	// Set component functions
	if len(config.ComponentFunctions) > 0 {
		for _, fn := range config.ComponentFunctions {
			switch fn {
			case "core":
				selector.ComponentFunctions = append(selector.ComponentFunctions, v1alpha1.CoreFunction)
			case "management":
				selector.ComponentFunctions = append(selector.ComponentFunctions, v1alpha1.ManagementFunction)
			case "security":
				selector.ComponentFunctions = append(selector.ComponentFunctions, v1alpha1.SecurityFunction)
			default:
				return fmt.Errorf("invalid component function: %s", fn)
			}
		}
	}

	// Set namespaces
	if len(config.Namespaces) > 0 {
		selector.Namespaces = config.Namespaces
	}

	return nil
}

func (m *ManagementTools) setCustomPDBConfig(spec *v1alpha1.AvailabilityPolicySpec, config *CustomPDBConfig) error {
	pdbConfig := &v1alpha1.PodDisruptionBudgetConfig{}

	if config.MinAvailable != nil {
		minAvail := intstr.FromString(*config.MinAvailable)
		pdbConfig.MinAvailable = &minAvail
	}

	if config.MaxUnavailable != nil {
		maxUnavail := intstr.FromString(*config.MaxUnavailable)
		pdbConfig.MaxUnavailable = &maxUnavail
	}

	if config.UnhealthyPodEvictionPolicy != "" {
		pdbConfig.UnhealthyPodEvictionPolicy = config.UnhealthyPodEvictionPolicy
	}

	spec.CustomPDBConfig = pdbConfig
	return nil
}

func (m *ManagementTools) convertMaintenanceWindows(windows []MaintenanceWindowConfig) []v1alpha1.MaintenanceWindow {
	var result []v1alpha1.MaintenanceWindow
	for _, w := range windows {
		window := v1alpha1.MaintenanceWindow{
			Start:      w.Start,
			End:        w.End,
			Timezone:   w.Timezone,
			DaysOfWeek: w.DaysOfWeek,
		}
		if window.Timezone == "" {
			window.Timezone = "UTC"
		}
		result = append(result, window)
	}
	return result
}

func isODAAnnotation(key string) bool {
	return len(key) > 12 && key[:12] == "oda.tmforum."
}

func (m *ManagementTools) validateODAAnnotation(key, value string) error {
	switch key {
	case "oda.tmforum.org/availability-class":
		_, err := m.parseAvailabilityClass(value)
		return err
	case "oda.tmforum.org/component-function":
		switch value {
		case "core", "management", "security":
			return nil
		default:
			return fmt.Errorf("invalid component function: %s", value)
		}
	default:
		return nil // Allow other ODA annotations
	}
}

func (m *ManagementTools) deploymentMatchesSelector(deployment *appsv1.Deployment, selector *v1alpha1.ComponentSelector) bool {
	// Check namespace filter
	if len(selector.Namespaces) > 0 {
		found := false
		for _, ns := range selector.Namespaces {
			if deployment.Namespace == ns {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check component names
	if len(selector.ComponentNames) > 0 {
		componentName := deployment.Annotations["oda.tmforum.org/componentName"]
		if componentName == "" {
			componentName = deployment.Name
		}
		found := false
		for _, name := range selector.ComponentNames {
			if componentName == name {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check component functions
	if len(selector.ComponentFunctions) > 0 {
		functionStr := deployment.Annotations["oda.tmforum.org/component-function"]
		if functionStr == "" {
			functionStr = "core" // default
		}

		found := false
		for _, fn := range selector.ComponentFunctions {
			if string(fn) == functionStr {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check match labels (simplified - would need full label selector logic in production)
	if len(selector.MatchLabels) > 0 {
		for key, value := range selector.MatchLabels {
			if deployment.Labels[key] != value {
				return false
			}
		}
	}

	return true
}

func (m *ManagementTools) calculateDeploymentImpact(deployment *appsv1.Deployment, policy *v1alpha1.AvailabilityPolicy) DeploymentImpact {
	currentClass := deployment.Annotations["oda.tmforum.org/availability-class"]
	proposedClass := string(policy.Spec.AvailabilityClass)

	replicas := int32(1)
	if deployment.Spec.Replicas != nil {
		replicas = *deployment.Spec.Replicas
	}

	// Calculate current and proposed min available
	var currentMinAvailable, proposedMinAvailable string

	if currentClass != "" {
		currentAvailClass, err := m.parseAvailabilityClass(currentClass)
		if err == nil {
			currentMinVal := v1alpha1.GetMinAvailableForClass(currentAvailClass, v1alpha1.CoreFunction)
			currentMinAvailable = currentMinVal.String()
		}
	}

	proposedMinVal := v1alpha1.GetMinAvailableForClass(policy.Spec.AvailabilityClass, v1alpha1.CoreFunction)
	proposedMinAvailable = proposedMinVal.String()

	// Determine impact level
	var impact string
	if currentClass == "" {
		impact = "medium" // New PDB will be created
	} else {
		currentOrder := getAvailabilityOrder(currentClass)
		proposedOrder := getAvailabilityOrder(proposedClass)

		diff := proposedOrder - currentOrder
		switch {
		case diff >= 2:
			impact = "high"
		case diff == 1:
			impact = "medium"
		case diff == 0:
			impact = "low"
		case diff <= -1:
			impact = "high" // Reducing availability is high impact
		default:
			impact = "low"
		}
	}

	return DeploymentImpact{
		Name:                 deployment.Name,
		Namespace:            deployment.Namespace,
		CurrentClass:         currentClass,
		ProposedClass:        proposedClass,
		CurrentMinAvailable:  currentMinAvailable,
		ProposedMinAvailable: proposedMinAvailable,
		Impact:               impact,
		Replicas:             replicas,
	}
}

func getAvailabilityOrder(class string) int {
	switch class {
	case "non-critical":
		return 1
	case "standard":
		return 2
	case "high-availability":
		return 3
	case "mission-critical":
		return 4
	case "custom":
		return 5
	default:
		return 0
	}
}

// createIntelligentPolicies creates policies with intelligent grouping and auto-detection
func (m *ManagementTools) createIntelligentPolicies(ctx context.Context, params CreateAvailabilityPolicyParams) (*types.ToolResult, error) {
	// Get all deployments in the namespace
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{Namespace: params.Namespace}
	if err := m.client.List(ctx, &deployments, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	// Filter deployments
	targetDeployments := m.filterDeployments(deployments.Items, params)

	if len(targetDeployments) == 0 {
		return &types.ToolResult{
			Content: "No deployments found matching criteria",
			IsError: true,
		}, nil
	}

	// Group deployments based on groupBy parameter
	groups := m.groupDeployments(targetDeployments, params.GroupBy)

	// Create policies for each group
	var createdPolicies []string
	for groupName, groupDeployments := range groups {
		if len(groupDeployments) == 0 {
			continue
		}

		// Auto-detect availability class for the group
		class := m.detectAvailabilityClass(groupDeployments)

		// Generate policy name
		policyName := fmt.Sprintf("%s-%s-auto", params.Namespace, strings.ToLower(groupName))

		// Build component selector
		selector := m.buildSmartSelector(groupDeployments)

		// Create the policy
		policy := &v1alpha1.AvailabilityPolicy{
			ObjectMeta: metav1.ObjectMeta{
				Name:      policyName,
				Namespace: params.Namespace,
			},
			Spec: v1alpha1.AvailabilityPolicySpec{
				AvailabilityClass: class,
				ComponentSelector: selector,
				Enforcement:       v1alpha1.EnforcementFlexible, // Default to flexible
				Priority:          m.calculatePriority(class),
			},
		}

		// Apply defaults
		if params.Enforcement != "" {
			enforcement, _ := m.parseEnforcementMode(params.Enforcement)
			policy.Spec.Enforcement = enforcement
		}

		// Create the policy
		if err := m.client.Create(ctx, policy); err != nil {
			m.logger.Error(err, "Failed to create policy", "name", policyName)
			continue
		}

		createdPolicies = append(createdPolicies, fmt.Sprintf("%s (%d deployments, %s)", policyName, len(groupDeployments), class))

		// If not creating multiple, stop after first group
		if !params.CreateMultiple {
			break
		}
	}

	if len(createdPolicies) == 0 {
		return &types.ToolResult{
			Content: "Failed to create any policies",
			IsError: true,
		}, nil
	}

	result := fmt.Sprintf("Successfully created %d policies:\n%s", len(createdPolicies), strings.Join(createdPolicies, "\n"))
	return &types.ToolResult{
		Content: result,
	}, nil
}

// filterDeployments filters deployments based on parameters
func (m *ManagementTools) filterDeployments(deployments []appsv1.Deployment, params CreateAvailabilityPolicyParams) []appsv1.Deployment {
	var filtered []appsv1.Deployment

	for _, d := range deployments {
		// Skip if in exclude list
		if contains(params.ExcludeDeployments, d.Name) {
			continue
		}

		// Include if in target list or no target list specified
		if len(params.TargetDeployments) == 0 || contains(params.TargetDeployments, d.Name) {
			// Skip single-replica deployments unless explicitly targeted
			if *d.Spec.Replicas > 1 || contains(params.TargetDeployments, d.Name) {
				filtered = append(filtered, d)
			}
		}
	}

	return filtered
}

// groupDeployments groups deployments based on the groupBy parameter
func (m *ManagementTools) groupDeployments(deployments []appsv1.Deployment, groupBy string) map[string][]appsv1.Deployment {
	groups := make(map[string][]appsv1.Deployment)

	switch groupBy {
	case "", "auto":
		// Auto-group by detected patterns
		for _, d := range deployments {
			group := m.detectDeploymentGroup(d)
			groups[group] = append(groups[group], d)
		}
	case "class":
		// Group by availability class
		for _, d := range deployments {
			class := m.detectSingleAvailabilityClass(d)
			groups[string(class)] = append(groups[string(class)], d)
		}
	case "tier":
		// Group by tier label
		for _, d := range deployments {
			tier := d.Labels["tier"]
			if tier == "" {
				tier = "default"
			}
			groups[tier] = append(groups[tier], d)
		}
	case "component":
		// Group by component type
		for _, d := range deployments {
			component := d.Labels["component"]
			if component == "" {
				component = m.detectComponentType(d.Name)
			}
			groups[component] = append(groups[component], d)
		}
	default:
		// Default: all in one group
		groups["all"] = deployments
	}

	return groups
}

// detectDeploymentGroup detects the group for a deployment based on patterns
func (m *ManagementTools) detectDeploymentGroup(d appsv1.Deployment) string {
	name := strings.ToLower(d.Name)

	// Security components
	if strings.Contains(name, "auth") || strings.Contains(name, "oauth") || strings.Contains(name, "security") {
		return "security"
	}

	// Database components
	if strings.Contains(name, "db") || strings.Contains(name, "database") || strings.Contains(name, "postgres") || strings.Contains(name, "mysql") {
		return "database"
	}

	// Frontend components
	if strings.Contains(name, "frontend") || strings.Contains(name, "ui") || strings.Contains(name, "web") {
		return "frontend"
	}

	// API/Gateway components
	if strings.Contains(name, "api") || strings.Contains(name, "gateway") {
		return "api-gateway"
	}

	// Backend components
	if strings.Contains(name, "backend") || strings.Contains(name, "service") {
		return "backend"
	}

	// Payment/Financial
	if strings.Contains(name, "payment") || strings.Contains(name, "billing") {
		return "financial"
	}

	// Batch/Worker
	if strings.Contains(name, "batch") || strings.Contains(name, "worker") || strings.Contains(name, "job") {
		return "batch"
	}

	return "general"
}

// detectComponentType detects component type from name
func (m *ManagementTools) detectComponentType(name string) string {
	lowerName := strings.ToLower(name)

	if strings.Contains(lowerName, "frontend") || strings.Contains(lowerName, "ui") {
		return "frontend"
	}
	if strings.Contains(lowerName, "backend") || strings.Contains(lowerName, "api") {
		return "backend"
	}
	if strings.Contains(lowerName, "db") || strings.Contains(lowerName, "database") {
		return "database"
	}
	if strings.Contains(lowerName, "cache") || strings.Contains(lowerName, "redis") {
		return "cache"
	}
	if strings.Contains(lowerName, "queue") || strings.Contains(lowerName, "mq") {
		return "queue"
	}

	return "service"
}

// detectAvailabilityClass auto-detects the appropriate availability class for a group
func (m *ManagementTools) detectAvailabilityClass(deployments []appsv1.Deployment) v1alpha1.AvailabilityClass {
	if len(deployments) == 0 {
		return v1alpha1.Standard
	}

	// Calculate average replicas and check patterns
	totalReplicas := int32(0)
	hasCritical := false
	hasProduction := false

	for _, d := range deployments {
		totalReplicas += *d.Spec.Replicas

		name := strings.ToLower(d.Name)
		if strings.Contains(name, "critical") || strings.Contains(name, "auth") || strings.Contains(name, "payment") {
			hasCritical = true
		}
		if strings.Contains(name, "prod") || strings.Contains(name, "production") {
			hasProduction = true
		}

		// Check labels
		if tier := d.Labels["tier"]; tier == "critical" || tier == "gold" {
			hasCritical = true
		}
	}

	avgReplicas := totalReplicas / int32(len(deployments))

	// Decision logic
	if hasCritical || avgReplicas >= 5 {
		return v1alpha1.MissionCritical
	}
	if hasProduction || avgReplicas >= 3 {
		return v1alpha1.HighAvailability
	}
	if avgReplicas >= 2 {
		return v1alpha1.Standard
	}

	return v1alpha1.NonCritical
}

// detectSingleAvailabilityClass detects class for a single deployment
func (m *ManagementTools) detectSingleAvailabilityClass(d appsv1.Deployment) v1alpha1.AvailabilityClass {
	return m.detectAvailabilityClass([]appsv1.Deployment{d})
}

// buildSmartSelector builds an intelligent component selector for a group
func (m *ManagementTools) buildSmartSelector(deployments []appsv1.Deployment) v1alpha1.ComponentSelector {
	selector := v1alpha1.ComponentSelector{}

	// Try to find common labels
	commonLabels := m.findCommonLabels(deployments)
	if len(commonLabels) > 0 {
		selector.MatchLabels = commonLabels
	} else {
		// Fall back to listing component names
		var names []string
		for _, d := range deployments {
			names = append(names, d.Name)
		}
		selector.ComponentNames = names
	}

	// Add namespace
	if len(deployments) > 0 {
		selector.Namespaces = []string{deployments[0].Namespace}
	}

	return selector
}

// findCommonLabels finds labels common to all deployments
func (m *ManagementTools) findCommonLabels(deployments []appsv1.Deployment) map[string]string {
	if len(deployments) == 0 {
		return nil
	}

	// Start with first deployment's labels
	common := make(map[string]string)
	for k, v := range deployments[0].Labels {
		// Skip kubernetes default labels
		if strings.HasPrefix(k, "app.kubernetes.io/") || k == "version" {
			continue
		}
		common[k] = v
	}

	// Check against other deployments
	for _, d := range deployments[1:] {
		for k, v := range common {
			if dv, exists := d.Labels[k]; !exists || dv != v {
				delete(common, k)
			}
		}
	}

	return common
}

// calculatePriority calculates priority based on availability class
func (m *ManagementTools) calculatePriority(class v1alpha1.AvailabilityClass) int32 {
	switch class {
	case v1alpha1.MissionCritical:
		return 1000
	case v1alpha1.HighAvailability:
		return 500
	case v1alpha1.Standard:
		return 100
	case v1alpha1.NonCritical:
		return 50
	default:
		return 10
	}
}

// contains checks if a string is in a slice
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// RegisterManagementTools registers all management tools with the MCP server
func RegisterManagementTools(server interface{ RegisterTool(*types.Tool) error }, tools *ManagementTools) error {
	// Register create availability policy tool
	createPolicyTool := &types.Tool{
		Name:        "create_availability_policy",
		Description: "Create availability policies with intelligent auto-detection and grouping. Can create a single policy or multiple policies by automatically analyzing deployments.",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string", 
					"description": "Target namespace (required)"
				},
				"autoDetect": {
					"type": "boolean",
					"description": "Enable intelligent auto-detection mode (recommended)"
				},
				"groupBy": {
					"type": "string",
					"enum": ["auto", "class", "tier", "component"],
					"description": "How to group deployments: auto=smart detection, class=by availability class, tier=by tier label, component=by component type"
				},
				"createMultiple": {
					"type": "boolean",
					"description": "Create multiple policies for different groups (default: false)"
				},
				"targetDeployments": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Specific deployments to target (optional)"
				},
				"excludeDeployments": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Deployments to exclude (optional)"
				},
				"name": {
					"type": "string", 
					"description": "Policy name (auto-generated if not provided)"
				},
				"availabilityClass": {
					"type": "string",
					"enum": ["non-critical", "standard", "high-availability", "mission-critical", "custom"],
					"description": "Availability class (auto-detected if not provided)"
				},
				"enforcement": {
					"type": "string",
					"enum": ["strict", "flexible", "advisory"],
					"description": "Enforcement mode (defaults to 'flexible')"
				},
				"priority": {
					"type": "integer", 
					"description": "Policy priority (auto-calculated if not provided)"
				},
				"componentSelector": {
					"type": "object",
					"description": "Component selector (auto-generated if not provided)",
					"properties": {
						"matchLabels": {"type": "object"},
						"componentNames": {"type": "array", "items": {"type": "string"}},
						"componentFunctions": {"type": "array", "items": {"type": "string"}},
						"namespaces": {"type": "array", "items": {"type": "string"}}
					}
				}
			},
			"required": ["namespace"]
		}`),
		Handler: tools.CreateAvailabilityPolicy,
	}
	if err := server.RegisterTool(createPolicyTool); err != nil {
		return fmt.Errorf("failed to register create policy tool: %w", err)
	}

	// Register update deployment annotations tool
	updateAnnotationsTool := &types.Tool{
		Name:        "update_deployment_annotations",
		Description: "Update availability-related annotations on a deployment",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"name": {"type": "string", "description": "Deployment name"},
				"namespace": {"type": "string", "description": "Deployment namespace"},
				"annotations": {
					"type": "object",
					"description": "Annotations to add/update"
				},
				"removeAnnotations": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Annotation keys to remove"
				}
			},
			"required": ["name", "namespace"]
		}`),
		Handler: tools.UpdateDeploymentAnnotations,
	}
	if err := server.RegisterTool(updateAnnotationsTool); err != nil {
		return fmt.Errorf("failed to register update annotations tool: %w", err)
	}

	// Register simulate policy impact tool
	simulateTool := &types.Tool{
		Name:        "simulate_policy_impact",
		Description: "Simulate the impact of applying an availability policy without actually creating it",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"policySpec": {
					"type": "object",
					"description": "Policy specification to simulate"
				},
				"targetNamespaces": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Namespaces to analyze (optional)"
				}
			},
			"required": ["policySpec"]
		}`),
		Handler: tools.SimulatePolicyImpact,
	}
	if err := server.RegisterTool(simulateTool); err != nil {
		return fmt.Errorf("failed to register simulate tool: %w", err)
	}

	return nil
}
