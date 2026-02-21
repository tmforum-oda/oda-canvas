package tools

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// OptimizationTools handles resource optimization analysis and recommendations
type OptimizationTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewOptimizationTools creates a new OptimizationTools instance
func NewOptimizationTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *OptimizationTools {
	return &OptimizationTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// OptimizeResourcesParams defines parameters for resource optimization
type OptimizeResourcesParams struct {
	Namespaces          []string            `json:"namespaces,omitempty"`
	IncludeMetrics      bool                `json:"includeMetrics,omitempty"`
	OptimizationTargets []string            `json:"optimizationTargets,omitempty"` // "availability", "cost", "performance"
	AnalysisPeriod      string              `json:"analysisPeriod,omitempty"`      // "1h", "24h", "7d"
	MinimumReplicas     int32               `json:"minimumReplicas,omitempty"`
	MaximumReplicas     int32               `json:"maximumReplicas,omitempty"`
	ResourceThresholds  *ResourceThresholds `json:"resourceThresholds,omitempty"`
}

// ResourceThresholds defines thresholds for resource optimization
type ResourceThresholds struct {
	CPUUtilizationLow     float64 `json:"cpuUtilizationLow,omitempty"`     // Default: 20%
	CPUUtilizationHigh    float64 `json:"cpuUtilizationHigh,omitempty"`    // Default: 80%
	MemoryUtilizationLow  float64 `json:"memoryUtilizationLow,omitempty"`  // Default: 30%
	MemoryUtilizationHigh float64 `json:"memoryUtilizationHigh,omitempty"` // Default: 85%
}

// OptimizationResult represents the result of resource optimization analysis
type OptimizationResult struct {
	Summary                OptimizationSummary      `json:"summary"`
	DeploymentAnalysis     []DeploymentOptimization `json:"deploymentAnalysis"`
	PDBOptimizations       []PDBOptimization        `json:"pdbOptimizations"`
	ClusterRecommendations []ClusterRecommendation  `json:"clusterRecommendations"`
	CostImpact             *CostImpactAnalysis      `json:"costImpact,omitempty"`
	ImplementationPlan     ImplementationPlan       `json:"implementationPlan"`
}

// OptimizationSummary provides a summary of optimization opportunities
type OptimizationSummary struct {
	TotalDeployments       int     `json:"totalDeployments"`
	OptimizableDeployments int     `json:"optimizableDeployments"`
	PotentialCostSavings   float64 `json:"potentialCostSavings"`
	AvailabilityImpact     string  `json:"availabilityImpact"`
	RiskLevel              string  `json:"riskLevel"`
	ConfidenceScore        float64 `json:"confidenceScore"`
}

// DeploymentOptimization contains optimization recommendations for a deployment
type DeploymentOptimization struct {
	Name                string                       `json:"name"`
	Namespace           string                       `json:"namespace"`
	CurrentConfig       DeploymentConfig             `json:"currentConfig"`
	RecommendedConfig   DeploymentConfig             `json:"recommendedConfig"`
	Optimizations       []OptimizationRecommendation `json:"optimizations"`
	ResourceUtilization *ResourceUtilization         `json:"resourceUtilization,omitempty"`
	AvailabilityImpact  AvailabilityImpactAnalysis   `json:"availabilityImpact"`
	ImplementationRisk  string                       `json:"implementationRisk"`
	PotentialSavings    float64                      `json:"potentialSavings"`
}

// DeploymentConfig represents deployment configuration
type DeploymentConfig struct {
	Replicas          int32                       `json:"replicas"`
	ResourceRequests  corev1.ResourceRequirements `json:"resourceRequests"`
	ResourceLimits    corev1.ResourceRequirements `json:"resourceLimits"`
	AvailabilityClass string                      `json:"availabilityClass,omitempty"`
	PDBConfig         *PDBConfiguration           `json:"pdbConfig,omitempty"`
}

// PDBConfiguration represents PDB configuration
type PDBConfiguration struct {
	MinAvailable   *intstr.IntOrString `json:"minAvailable,omitempty"`
	MaxUnavailable *intstr.IntOrString `json:"maxUnavailable,omitempty"`
	Strategy       string              `json:"strategy,omitempty"`
}

// OptimizationRecommendation represents a specific optimization recommendation
type OptimizationRecommendation struct {
	Type            string   `json:"type"`     // "scaling", "resources", "pdb", "availability"
	Priority        string   `json:"priority"` // "high", "medium", "low"
	Title           string   `json:"title"`
	Description     string   `json:"description"`
	Actions         []string `json:"actions"`
	ExpectedBenefit string   `json:"expectedBenefit"`
	Risks           []string `json:"risks"`
	Prerequisites   []string `json:"prerequisites,omitempty"`
}

// ResourceUtilization represents resource utilization metrics
type ResourceUtilization struct {
	CPU    UtilizationMetrics `json:"cpu"`
	Memory UtilizationMetrics `json:"memory"`
	Period string             `json:"period"`
}

// UtilizationMetrics represents utilization metrics for a resource
type UtilizationMetrics struct {
	Average    float64 `json:"average"`
	Peak       float64 `json:"peak"`
	P95        float64 `json:"p95"`
	Trend      string  `json:"trend"`      // "increasing", "stable", "decreasing"
	Efficiency string  `json:"efficiency"` // "underutilized", "optimal", "overutilized"
}

// AvailabilityImpactAnalysis analyzes the impact of changes on availability
type AvailabilityImpactAnalysis struct {
	CurrentAvailability   string   `json:"currentAvailability"`
	ProjectedAvailability string   `json:"projectedAvailability"`
	RiskAssessment        string   `json:"riskAssessment"`
	PDBEffectiveness      float64  `json:"pdbEffectiveness"`
	RecommendedActions    []string `json:"recommendedActions"`
}

// PDBOptimization contains PDB-specific optimization recommendations
type PDBOptimization struct {
	Name              string                     `json:"name"`
	Namespace         string                     `json:"namespace"`
	CurrentPDB        *PDBConfiguration          `json:"currentPDB,omitempty"`
	RecommendedPDB    *PDBConfiguration          `json:"recommendedPDB"`
	Rationale         string                     `json:"rationale"`
	RelatedDeployment string                     `json:"relatedDeployment"`
	ImpactAssessment  AvailabilityImpactAnalysis `json:"impactAssessment"`
}

// ClusterRecommendation represents cluster-wide optimization recommendations
type ClusterRecommendation struct {
	Category          string   `json:"category"` // "scaling", "policies", "resources"
	Priority          string   `json:"priority"`
	Title             string   `json:"title"`
	Description       string   `json:"description"`
	Actions           []string `json:"actions"`
	Benefits          []string `json:"benefits"`
	AffectedResources int      `json:"affectedResources"`
}

// CostImpactAnalysis provides cost impact analysis
type CostImpactAnalysis struct {
	CurrentMonthlyCost   float64            `json:"currentMonthlyCost"`
	OptimizedMonthlyCost float64            `json:"optimizedMonthlyCost"`
	MonthlySavings       float64            `json:"monthlySavings"`
	AnnualSavings        float64            `json:"annualSavings"`
	PaybackPeriod        string             `json:"paybackPeriod"`
	CostBreakdown        map[string]float64 `json:"costBreakdown"`
}

// ImplementationPlan provides a plan for implementing optimizations
type ImplementationPlan struct {
	Phases              []ImplementationPhase `json:"phases"`
	TotalEstimatedTime  string                `json:"totalEstimatedTime"`
	RequiredPermissions []string              `json:"requiredPermissions"`
	RollbackStrategy    string                `json:"rollbackStrategy"`
}

// ImplementationPhase represents a phase of implementation
type ImplementationPhase struct {
	Name         string   `json:"name"`
	Description  string   `json:"description"`
	Duration     string   `json:"duration"`
	Dependencies []string `json:"dependencies"`
	Actions      []string `json:"actions"`
	RiskLevel    string   `json:"riskLevel"`
}

// OptimizeResources analyzes and provides resource optimization recommendations
func (o *OptimizationTools) OptimizeResources(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var optimizeParams OptimizeResourcesParams
	if err := json.Unmarshal(params, &optimizeParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Set defaults
	o.setOptimizationDefaults(&optimizeParams)

	o.logger.Info("Starting resource optimization analysis",
		"namespaces", optimizeParams.Namespaces,
		"targets", optimizeParams.OptimizationTargets,
		"period", optimizeParams.AnalysisPeriod)

	// Get deployments for analysis
	deployments, err := o.getDeploymentsForOptimization(ctx, optimizeParams.Namespaces)
	if err != nil {
		return nil, fmt.Errorf("failed to get deployments: %w", err)
	}

	// Get existing PDBs
	pdbs, err := o.getExistingPDBs(ctx, optimizeParams.Namespaces)
	if err != nil {
		return nil, fmt.Errorf("failed to get PDBs: %w", err)
	}

	// Get availability policies
	policies, err := o.getAvailabilityPolicies(ctx, optimizeParams.Namespaces)
	if err != nil {
		return nil, fmt.Errorf("failed to get policies: %w", err)
	}

	// Analyze each deployment
	var deploymentAnalysis []DeploymentOptimization
	for _, deployment := range deployments {
		analysis := o.analyzeDeployment(ctx, deployment, pdbs, policies, optimizeParams)
		deploymentAnalysis = append(deploymentAnalysis, analysis)
	}

	// Generate PDB optimizations
	pdbOptimizations := o.generatePDBOptimizations(deployments, pdbs, policies)

	// Generate cluster-wide recommendations
	clusterRecommendations := o.generateClusterRecommendations(deploymentAnalysis)

	// Calculate cost impact if requested
	var costImpact *CostImpactAnalysis
	if o.containsString(optimizeParams.OptimizationTargets, "cost") {
		costImpact = o.calculateCostImpact(deploymentAnalysis)
	}

	// Generate implementation plan
	implementationPlan := o.generateImplementationPlan(deploymentAnalysis, pdbOptimizations)

	// Create summary
	summary := o.generateOptimizationSummary(deploymentAnalysis, costImpact)

	result := OptimizationResult{
		Summary:                summary,
		DeploymentAnalysis:     deploymentAnalysis,
		PDBOptimizations:       pdbOptimizations,
		ClusterRecommendations: clusterRecommendations,
		CostImpact:             costImpact,
		ImplementationPlan:     implementationPlan,
	}

	o.logger.Info("Resource optimization analysis completed",
		"deployments", len(deploymentAnalysis),
		"optimizableDeployments", summary.OptimizableDeployments,
		"pdbOptimizations", len(pdbOptimizations),
		"clusterRecommendations", len(clusterRecommendations))

	return &types.ToolResult{
		IsError: false,
		Content: result,
	}, nil
}

func (o *OptimizationTools) setOptimizationDefaults(params *OptimizeResourcesParams) {
	if len(params.OptimizationTargets) == 0 {
		params.OptimizationTargets = []string{"availability", "performance"}
	}
	if params.AnalysisPeriod == "" {
		params.AnalysisPeriod = "24h"
	}
	if params.MinimumReplicas == 0 {
		params.MinimumReplicas = 1
	}
	if params.MaximumReplicas == 0 {
		params.MaximumReplicas = 20
	}
	if params.ResourceThresholds == nil {
		params.ResourceThresholds = &ResourceThresholds{
			CPUUtilizationLow:     20.0,
			CPUUtilizationHigh:    80.0,
			MemoryUtilizationLow:  30.0,
			MemoryUtilizationHigh: 85.0,
		}
	}
}

func (o *OptimizationTools) getDeploymentsForOptimization(ctx context.Context, namespaces []string) ([]appsv1.Deployment, error) {
	var deployments []appsv1.Deployment

	targetNamespaces := namespaces
	if len(targetNamespaces) == 0 {
		nsList, err := o.kubeClient.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, err
		}
		for _, ns := range nsList.Items {
			targetNamespaces = append(targetNamespaces, ns.Name)
		}
	}

	for _, ns := range targetNamespaces {
		depList, err := o.kubeClient.AppsV1().Deployments(ns).List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to list deployments in namespace %s: %w", ns, err)
		}
		deployments = append(deployments, depList.Items...)
	}

	return deployments, nil
}

func (o *OptimizationTools) getExistingPDBs(ctx context.Context, namespaces []string) (map[string]*policyv1.PodDisruptionBudget, error) {
	pdbMap := make(map[string]*policyv1.PodDisruptionBudget)

	targetNamespaces := namespaces
	if len(targetNamespaces) == 0 {
		nsList, err := o.kubeClient.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			return pdbMap, err
		}
		for _, ns := range nsList.Items {
			targetNamespaces = append(targetNamespaces, ns.Name)
		}
	}

	for _, ns := range targetNamespaces {
		pdbList, err := o.kubeClient.PolicyV1().PodDisruptionBudgets(ns).List(ctx, metav1.ListOptions{})
		if err != nil {
			continue // Skip on error
		}
		for i := range pdbList.Items {
			pdb := &pdbList.Items[i]
			key := fmt.Sprintf("%s/%s", pdb.Namespace, pdb.Name)
			pdbMap[key] = pdb
		}
	}

	return pdbMap, nil
}

func (o *OptimizationTools) getAvailabilityPolicies(ctx context.Context, namespaces []string) ([]v1alpha1.AvailabilityPolicy, error) {
	var policies v1alpha1.AvailabilityPolicyList

	if len(namespaces) > 0 {
		for _, ns := range namespaces {
			var nsPolicies v1alpha1.AvailabilityPolicyList
			if err := o.client.List(ctx, &nsPolicies, client.InNamespace(ns)); err != nil {
				continue // Skip on error
			}
			policies.Items = append(policies.Items, nsPolicies.Items...)
		}
	} else {
		if err := o.client.List(ctx, &policies); err != nil {
			return nil, err
		}
	}

	return policies.Items, nil
}

func (o *OptimizationTools) analyzeDeployment(ctx context.Context, deployment appsv1.Deployment, pdbs map[string]*policyv1.PodDisruptionBudget, policies []v1alpha1.AvailabilityPolicy, params OptimizeResourcesParams) DeploymentOptimization {
	analysis := DeploymentOptimization{
		Name:      deployment.Name,
		Namespace: deployment.Namespace,
		CurrentConfig: DeploymentConfig{
			Replicas: *deployment.Spec.Replicas,
		},
		Optimizations: []OptimizationRecommendation{},
	}

	// Get current resource configuration
	if len(deployment.Spec.Template.Spec.Containers) > 0 {
		container := deployment.Spec.Template.Spec.Containers[0]
		analysis.CurrentConfig.ResourceRequests = corev1.ResourceRequirements{
			Requests: container.Resources.Requests,
		}
		analysis.CurrentConfig.ResourceLimits = corev1.ResourceRequirements{
			Limits: container.Resources.Limits,
		}
	}

	// Find applicable policy
	for _, policy := range policies {
		if o.deploymentMatchesPolicy(deployment, policy) {
			analysis.CurrentConfig.AvailabilityClass = string(policy.Spec.AvailabilityClass)
			break
		}
	}

	// Find existing PDB
	pdbKey := fmt.Sprintf("%s/%s-pdb", deployment.Namespace, deployment.Name)
	if pdb, exists := pdbs[pdbKey]; exists {
		analysis.CurrentConfig.PDBConfig = &PDBConfiguration{
			MinAvailable:   pdb.Spec.MinAvailable,
			MaxUnavailable: pdb.Spec.MaxUnavailable,
		}
	}

	// Generate scaling recommendations
	scalingRecs := o.analyzeScaling(deployment, params)
	analysis.Optimizations = append(analysis.Optimizations, scalingRecs...)

	// Generate resource recommendations
	resourceRecs := o.analyzeResources(deployment, params)
	analysis.Optimizations = append(analysis.Optimizations, resourceRecs...)

	// Generate PDB recommendations
	pdbRecs := o.analyzePDBConfiguration(deployment, analysis.CurrentConfig.PDBConfig, params)
	analysis.Optimizations = append(analysis.Optimizations, pdbRecs...)

	// Generate recommended configuration
	analysis.RecommendedConfig = o.generateRecommendedConfig(analysis.CurrentConfig, analysis.Optimizations)

	// Assess availability impact
	analysis.AvailabilityImpact = o.assessAvailabilityImpact(analysis.CurrentConfig, analysis.RecommendedConfig)

	// Assess implementation risk
	analysis.ImplementationRisk = o.assessImplementationRisk(analysis.Optimizations)

	// Calculate potential savings
	analysis.PotentialSavings = o.calculateDeploymentSavings(analysis.CurrentConfig, analysis.RecommendedConfig)

	return analysis
}

func (o *OptimizationTools) analyzeScaling(deployment appsv1.Deployment, params OptimizeResourcesParams) []OptimizationRecommendation {
	var recommendations []OptimizationRecommendation
	currentReplicas := *deployment.Spec.Replicas

	// Check for under-replication (availability risk)
	if currentReplicas < 2 && o.containsString(params.OptimizationTargets, "availability") {
		recommendations = append(recommendations, OptimizationRecommendation{
			Type:        "scaling",
			Priority:    "high",
			Title:       "Increase Replicas for High Availability",
			Description: fmt.Sprintf("Deployment has only %d replica(s), which creates a single point of failure", currentReplicas),
			Actions: []string{
				"Increase replicas to at least 2 for basic availability",
				"Consider 3+ replicas for critical workloads",
				"Implement appropriate PodDisruptionBudget",
			},
			ExpectedBenefit: "Improved availability and resilience to node failures",
			Risks:           []string{"Increased resource usage and costs"},
		})
	}

	// Check for over-replication (cost optimization)
	if currentReplicas > 10 && o.containsString(params.OptimizationTargets, "cost") {
		recommendations = append(recommendations, OptimizationRecommendation{
			Type:        "scaling",
			Priority:    "medium",
			Title:       "Consider Replica Count Optimization",
			Description: fmt.Sprintf("Deployment has %d replicas, which may be excessive", currentReplicas),
			Actions: []string{
				"Analyze actual load patterns and requirements",
				"Consider implementing Horizontal Pod Autoscaler",
				"Review if current replica count is necessary",
			},
			ExpectedBenefit: "Potential cost savings while maintaining performance",
			Risks:           []string{"Reduced capacity during traffic spikes"},
			Prerequisites:   []string{"Load analysis", "Performance testing"},
		})
	}

	return recommendations
}

func (o *OptimizationTools) analyzeResources(deployment appsv1.Deployment, params OptimizeResourcesParams) []OptimizationRecommendation {
	var recommendations []OptimizationRecommendation

	if len(deployment.Spec.Template.Spec.Containers) == 0 {
		return recommendations
	}

	container := deployment.Spec.Template.Spec.Containers[0]
	requests := container.Resources.Requests
	limits := container.Resources.Limits

	// Check if resources are defined
	if len(requests) == 0 {
		recommendations = append(recommendations, OptimizationRecommendation{
			Type:        "resources",
			Priority:    "high",
			Title:       "Define Resource Requests",
			Description: "Container has no resource requests defined",
			Actions: []string{
				"Define CPU and memory requests based on actual usage",
				"Start with conservative estimates and tune over time",
				"Use metrics to guide resource allocation",
			},
			ExpectedBenefit: "Better scheduling, resource planning, and cluster stability",
			Risks:           []string{"Potential resource contention if estimates are too low"},
		})
	}

	// Check for missing limits
	if len(limits) == 0 {
		recommendations = append(recommendations, OptimizationRecommendation{
			Type:        "resources",
			Priority:    "medium",
			Title:       "Define Resource Limits",
			Description: "Container has no resource limits defined",
			Actions: []string{
				"Define CPU and memory limits to prevent resource starvation",
				"Set limits 20-50% above requests for buffer",
				"Monitor for limit-related throttling or OOM kills",
			},
			ExpectedBenefit: "Prevent resource starvation and improve cluster stability",
			Risks:           []string{"Application performance issues if limits are too low"},
		})
	}

	return recommendations
}

func (o *OptimizationTools) analyzePDBConfiguration(deployment appsv1.Deployment, currentPDB *PDBConfiguration, params OptimizeResourcesParams) []OptimizationRecommendation {
	var recommendations []OptimizationRecommendation
	replicas := *deployment.Spec.Replicas

	if currentPDB == nil && replicas > 1 {
		minAvailable := "50%"
		if replicas == 2 {
			minAvailable = "1"
		}

		recommendations = append(recommendations, OptimizationRecommendation{
			Type:        "pdb",
			Priority:    "high",
			Title:       "Create Pod Disruption Budget",
			Description: "Deployment lacks PDB protection for rolling updates and node maintenance",
			Actions: []string{
				fmt.Sprintf("Create PDB with minAvailable: %s", minAvailable),
				"Test PDB effectiveness during simulated disruptions",
				"Monitor PDB events for constraint violations",
			},
			ExpectedBenefit: "Protection against simultaneous pod evictions during maintenance",
			Risks:           []string{"May slow down cluster operations if configured too restrictively"},
		})
	} else if currentPDB != nil {
		// Analyze existing PDB configuration
		if replicas >= 3 && currentPDB.MinAvailable != nil && currentPDB.MinAvailable.String() == "1" {
			recommendations = append(recommendations, OptimizationRecommendation{
				Type:        "pdb",
				Priority:    "medium",
				Title:       "Optimize PDB Configuration",
				Description: "PDB configuration could be more effective for current replica count",
				Actions: []string{
					"Consider using percentage-based minAvailable (e.g., 50%)",
					"Evaluate if maxUnavailable might be more appropriate",
					"Test disruption scenarios with current configuration",
				},
				ExpectedBenefit: "Better balance between availability and operational flexibility",
				Risks:           []string{"Changes in disruption behavior during maintenance windows"},
			})
		}
	}

	return recommendations
}

func (o *OptimizationTools) generateRecommendedConfig(current DeploymentConfig, optimizations []OptimizationRecommendation) DeploymentConfig {
	recommended := current // Copy current config

	for _, opt := range optimizations {
		switch opt.Type {
		case "scaling":
			if opt.Title == "Increase Replicas for High Availability" && recommended.Replicas == 1 {
				recommended.Replicas = 2
			}
		case "pdb":
			if opt.Title == "Create Pod Disruption Budget" && recommended.PDBConfig == nil {
				minAvail := intstr.FromString("50%")
				if recommended.Replicas == 2 {
					minAvail = intstr.FromInt(1)
				}
				recommended.PDBConfig = &PDBConfiguration{
					MinAvailable: &minAvail,
					Strategy:     "balanced",
				}
			}
		}
	}

	return recommended
}

func (o *OptimizationTools) assessAvailabilityImpact(current, recommended DeploymentConfig) AvailabilityImpactAnalysis {
	impact := AvailabilityImpactAnalysis{
		CurrentAvailability:   "Unknown",
		ProjectedAvailability: "Unknown",
		RiskAssessment:        "Low",
		PDBEffectiveness:      0.0,
	}

	// Simple availability assessment based on replicas
	switch current.Replicas {
	case 1:
		impact.CurrentAvailability = "Low (Single Point of Failure)"
		impact.RiskAssessment = "High"
	case 2:
		impact.CurrentAvailability = "Moderate"
		impact.RiskAssessment = "Medium"
	default:
		impact.CurrentAvailability = "Good"
		impact.RiskAssessment = "Low"
	}

	if recommended.Replicas > current.Replicas {
		impact.ProjectedAvailability = "Improved"
		impact.RecommendedActions = []string{"Implement gradual scaling", "Monitor performance"}
	} else {
		impact.ProjectedAvailability = impact.CurrentAvailability
	}

	// PDB effectiveness assessment
	if recommended.PDBConfig != nil && current.PDBConfig == nil {
		impact.PDBEffectiveness = 0.8 // Estimated improvement
		impact.RecommendedActions = append(impact.RecommendedActions, "Create and test PDB configuration")
	}

	return impact
}

func (o *OptimizationTools) assessImplementationRisk(optimizations []OptimizationRecommendation) string {
	highRiskCount := 0
	mediumRiskCount := 0

	for _, opt := range optimizations {
		switch opt.Priority {
		case "high":
			highRiskCount++
		case "medium":
			mediumRiskCount++
		}
	}

	if highRiskCount > 2 {
		return "High"
	} else if highRiskCount > 0 || mediumRiskCount > 2 {
		return "Medium"
	}
	return "Low"
}

func (o *OptimizationTools) calculateDeploymentSavings(current, recommended DeploymentConfig) float64 {
	// Simple cost calculation based on replica changes
	// This would be more sophisticated in a real implementation
	replicaDiff := float64(current.Replicas - recommended.Replicas)
	if replicaDiff > 0 {
		// Estimate savings per replica per month (example values)
		return replicaDiff * 50.0 // $50 per replica per month
	}
	return 0.0
}

func (o *OptimizationTools) generatePDBOptimizations(deployments []appsv1.Deployment, pdbs map[string]*policyv1.PodDisruptionBudget, policies []v1alpha1.AvailabilityPolicy) []PDBOptimization {
	var optimizations []PDBOptimization

	for _, deployment := range deployments {
		if *deployment.Spec.Replicas <= 1 {
			continue // Skip single-replica deployments
		}

		pdbKey := fmt.Sprintf("%s/%s-pdb", deployment.Namespace, deployment.Name)
		existingPDB := pdbs[pdbKey]

		if existingPDB == nil {
			// Recommend creating PDB
			minAvail := intstr.FromString("50%")
			if *deployment.Spec.Replicas == 2 {
				minAvail = intstr.FromInt(1)
			}

			optimizations = append(optimizations, PDBOptimization{
				Name:       deployment.Name + "-pdb",
				Namespace:  deployment.Namespace,
				CurrentPDB: nil,
				RecommendedPDB: &PDBConfiguration{
					MinAvailable: &minAvail,
					Strategy:     "balanced",
				},
				Rationale:         "Deployment lacks PDB protection for graceful handling of disruptions",
				RelatedDeployment: deployment.Name,
				ImpactAssessment: AvailabilityImpactAnalysis{
					CurrentAvailability:   "Unprotected",
					ProjectedAvailability: "Protected",
					RiskAssessment:        "Low",
					PDBEffectiveness:      0.8,
				},
			})
		}
	}

	return optimizations
}

func (o *OptimizationTools) generateClusterRecommendations(deploymentAnalysis []DeploymentOptimization) []ClusterRecommendation {
	var recommendations []ClusterRecommendation

	// Count deployments needing PDBs
	pdbNeeded := 0
	resourcesNeeded := 0
	scalingNeeded := 0

	for _, analysis := range deploymentAnalysis {
		for _, opt := range analysis.Optimizations {
			switch opt.Type {
			case "pdb":
				pdbNeeded++
			case "resources":
				resourcesNeeded++
			case "scaling":
				scalingNeeded++
			}
		}
	}

	if pdbNeeded > 3 {
		recommendations = append(recommendations, ClusterRecommendation{
			Category:    "policies",
			Priority:    "high",
			Title:       "Implement Cluster-Wide PDB Strategy",
			Description: fmt.Sprintf("%d deployments need PDB configuration", pdbNeeded),
			Actions: []string{
				"Create AvailabilityPolicy resources for systematic PDB management",
				"Implement automated PDB creation based on deployment patterns",
				"Establish PDB governance and best practices",
			},
			Benefits:          []string{"Consistent availability protection", "Reduced operational overhead", "Better disruption management"},
			AffectedResources: pdbNeeded,
		})
	}

	if resourcesNeeded > 5 {
		recommendations = append(recommendations, ClusterRecommendation{
			Category:    "resources",
			Priority:    "high",
			Title:       "Establish Resource Management Standards",
			Description: fmt.Sprintf("%d deployments need resource configuration", resourcesNeeded),
			Actions: []string{
				"Define resource request and limit policies",
				"Implement ResourceQuota and LimitRange objects",
				"Create resource sizing guidelines based on workload types",
			},
			Benefits:          []string{"Better resource utilization", "Improved scheduling", "Cost optimization"},
			AffectedResources: resourcesNeeded,
		})
	}

	return recommendations
}

func (o *OptimizationTools) calculateCostImpact(deploymentAnalysis []DeploymentOptimization) *CostImpactAnalysis {
	totalCurrentCost := 0.0
	totalSavings := 0.0

	for _, analysis := range deploymentAnalysis {
		// Simplified cost calculation
		currentCost := float64(analysis.CurrentConfig.Replicas) * 100.0 // $100 per replica per month
		totalCurrentCost += currentCost
		totalSavings += analysis.PotentialSavings
	}

	return &CostImpactAnalysis{
		CurrentMonthlyCost:   totalCurrentCost,
		OptimizedMonthlyCost: totalCurrentCost - totalSavings,
		MonthlySavings:       totalSavings,
		AnnualSavings:        totalSavings * 12,
		PaybackPeriod:        "Immediate",
		CostBreakdown: map[string]float64{
			"compute": totalCurrentCost * 0.8,
			"storage": totalCurrentCost * 0.2,
		},
	}
}

func (o *OptimizationTools) generateImplementationPlan(deploymentAnalysis []DeploymentOptimization, pdbOptimizations []PDBOptimization) ImplementationPlan {
	phases := []ImplementationPhase{
		{
			Name:        "Assessment and Planning",
			Description: "Validate recommendations and plan implementation",
			Duration:    "1-2 days",
			Actions: []string{
				"Review all optimization recommendations",
				"Validate with stakeholders",
				"Create detailed implementation timeline",
			},
			RiskLevel: "Low",
		},
		{
			Name:         "Low-Risk Optimizations",
			Description:  "Implement low-risk optimizations first",
			Duration:     "1 week",
			Dependencies: []string{"Assessment and Planning"},
			Actions: []string{
				"Create missing PDBs for non-critical workloads",
				"Add resource requests where missing",
				"Implement monitoring for optimization impact",
			},
			RiskLevel: "Low",
		},
		{
			Name:         "Medium-Risk Optimizations",
			Description:  "Implement scaling and configuration changes",
			Duration:     "2 weeks",
			Dependencies: []string{"Low-Risk Optimizations"},
			Actions: []string{
				"Scale deployments as recommended",
				"Update resource limits and requests",
				"Implement PDB optimizations for critical workloads",
			},
			RiskLevel: "Medium",
		},
	}

	return ImplementationPlan{
		Phases:              phases,
		TotalEstimatedTime:  "3-4 weeks",
		RequiredPermissions: []string{"cluster-admin", "deployment management", "PDB creation"},
		RollbackStrategy:    "Maintain configuration backups and implement changes gradually with monitoring",
	}
}

func (o *OptimizationTools) generateOptimizationSummary(deploymentAnalysis []DeploymentOptimization, costImpact *CostImpactAnalysis) OptimizationSummary {
	totalDeployments := len(deploymentAnalysis)
	optimizableDeployments := 0
	totalSavings := 0.0

	for _, analysis := range deploymentAnalysis {
		if len(analysis.Optimizations) > 0 {
			optimizableDeployments++
		}
		totalSavings += analysis.PotentialSavings
	}

	summary := OptimizationSummary{
		TotalDeployments:       totalDeployments,
		OptimizableDeployments: optimizableDeployments,
		PotentialCostSavings:   totalSavings,
		AvailabilityImpact:     "Improved",
		RiskLevel:              "Medium",
		ConfidenceScore:        0.85,
	}

	if optimizableDeployments == 0 {
		summary.AvailabilityImpact = "No Change"
		summary.RiskLevel = "None"
		summary.ConfidenceScore = 1.0
	}

	return summary
}

func (o *OptimizationTools) deploymentMatchesPolicy(deployment appsv1.Deployment, policy v1alpha1.AvailabilityPolicy) bool {
	// Simplified matching logic - in reality this would be more complex
	selector := policy.Spec.ComponentSelector

	if len(selector.Namespaces) > 0 {
		found := false
		for _, ns := range selector.Namespaces {
			if ns == deployment.Namespace {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	if len(selector.ComponentNames) > 0 {
		found := false
		for _, name := range selector.ComponentNames {
			if name == deployment.Name {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Check MatchLabels
	if len(selector.MatchLabels) > 0 {
		for key, value := range selector.MatchLabels {
			deploymentValue, ok := deployment.Labels[key]
			if !ok || deploymentValue != value {
				return false
			}
		}
	}

	return true
}

func (o *OptimizationTools) containsString(slice []string, str string) bool {
	for _, s := range slice {
		if s == str {
			return true
		}
	}
	return false
}

// RegisterOptimizationTools registers optimization tools with the MCP server
func RegisterOptimizationTools(server interface{ RegisterTool(*types.Tool) error }, tools *OptimizationTools) error {
	optimizeTool := &types.Tool{
		Name:        "optimize_resource_allocation",
		Description: "Analyze and provide resource optimization recommendations for deployments and PDBs",
		InputSchema: func() json.RawMessage {
			schema := map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"namespaces": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string"},
						"description": "List of namespaces to optimize (empty for all)",
					},
					"includeMetrics": map[string]interface{}{
						"type":        "boolean",
						"description": "Include metrics-based analysis (requires metrics server)",
						"default":     false,
					},
					"optimizationTargets": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string", "enum": []string{"availability", "cost", "performance"}},
						"description": "Optimization objectives",
						"default":     []string{"availability", "performance"},
					},
					"analysisPeriod": map[string]interface{}{
						"type":        "string",
						"description": "Period for historical analysis",
						"enum":        []string{"1h", "24h", "7d"},
						"default":     "24h",
					},
					"minimumReplicas": map[string]interface{}{
						"type":        "integer",
						"description": "Minimum replicas to recommend",
						"default":     1,
					},
					"maximumReplicas": map[string]interface{}{
						"type":        "integer",
						"description": "Maximum replicas to recommend",
						"default":     20,
					},
					"resourceThresholds": map[string]interface{}{
						"type": "object",
						"properties": map[string]interface{}{
							"cpuUtilizationLow": map[string]interface{}{
								"type":    "number",
								"default": 20.0,
							},
							"cpuUtilizationHigh": map[string]interface{}{
								"type":    "number",
								"default": 80.0,
							},
							"memoryUtilizationLow": map[string]interface{}{
								"type":    "number",
								"default": 30.0,
							},
							"memoryUtilizationHigh": map[string]interface{}{
								"type":    "number",
								"default": 85.0,
							},
						},
					},
				},
			}
			data, _ := json.Marshal(schema)
			return data
		}(),
		Handler: tools.OptimizeResources,
	}

	return server.RegisterTool(optimizeTool)
}
