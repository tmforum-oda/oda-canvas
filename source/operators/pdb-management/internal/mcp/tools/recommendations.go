package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// RecommendationTools provides recommendation tools for MCP
type RecommendationTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewRecommendationTools creates new recommendation tools
func NewRecommendationTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *RecommendationTools {
	return &RecommendationTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// RecommendAvailabilityClassesParams represents parameters for availability class recommendations
type RecommendAvailabilityClassesParams struct {
	Namespace   string   `json:"namespace,omitempty"`
	Deployments []string `json:"deployments,omitempty"`
}

// RecommendAvailabilityClassesResult represents availability class recommendations
type RecommendAvailabilityClassesResult struct {
	Recommendations []AvailabilityRecommendation `json:"recommendations"`
	Summary         RecommendationSummary        `json:"summary"`
}

// AvailabilityRecommendation represents a single availability recommendation
type AvailabilityRecommendation struct {
	Deployment       string             `json:"deployment"`
	Namespace        string             `json:"namespace"`
	CurrentClass     string             `json:"currentClass,omitempty"`
	RecommendedClass string             `json:"recommendedClass"`
	Confidence       float64            `json:"confidence"`
	Reasoning        []string           `json:"reasoning"`
	Impact           AvailabilityImpact `json:"impact"`
}

// AvailabilityImpact describes the impact of applying the recommendation
type AvailabilityImpact struct {
	MinAvailable   string `json:"minAvailable"`
	MaxUnavailable string `json:"maxUnavailable,omitempty"`
	Description    string `json:"description"`
}

// RecommendationSummary provides a summary of recommendations
type RecommendationSummary struct {
	Total            int            `json:"total"`
	ByClass          map[string]int `json:"byClass"`
	HighConfidence   int            `json:"highConfidence"`
	MediumConfidence int            `json:"mediumConfidence"`
	LowConfidence    int            `json:"lowConfidence"`
}

// RecommendAvailabilityClasses recommends optimal availability classes for deployments
func (r *RecommendationTools) RecommendAvailabilityClasses(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var recParams RecommendAvailabilityClassesParams
	if err := json.Unmarshal(params, &recParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Get deployments to analyze
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{}
	if recParams.Namespace != "" {
		listOpts.Namespace = recParams.Namespace
	}
	if err := r.client.List(ctx, &deployments, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	// Filter deployments if specific ones requested
	var targetDeployments []appsv1.Deployment
	if len(recParams.Deployments) > 0 {
		deploymentSet := make(map[string]bool)
		for _, name := range recParams.Deployments {
			deploymentSet[name] = true
		}
		for _, dep := range deployments.Items {
			if deploymentSet[dep.Name] {
				targetDeployments = append(targetDeployments, dep)
			}
		}
	} else {
		targetDeployments = deployments.Items
	}

	result := &RecommendAvailabilityClassesResult{
		Recommendations: []AvailabilityRecommendation{},
		Summary: RecommendationSummary{
			ByClass: make(map[string]int),
		},
	}

	// Analyze each deployment
	for _, deployment := range targetDeployments {
		rec := r.analyzeDeploymentAvailability(&deployment)
		result.Recommendations = append(result.Recommendations, rec)

		// Update summary
		result.Summary.Total++
		result.Summary.ByClass[rec.RecommendedClass]++

		switch {
		case rec.Confidence >= 0.8:
			result.Summary.HighConfidence++
		case rec.Confidence >= 0.5:
			result.Summary.MediumConfidence++
		default:
			result.Summary.LowConfidence++
		}
	}

	// Sort recommendations by confidence
	sort.Slice(result.Recommendations, func(i, j int) bool {
		return result.Recommendations[i].Confidence > result.Recommendations[j].Confidence
	})

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// analyzeDeploymentAvailability analyzes a deployment and recommends availability class
func (r *RecommendationTools) analyzeDeploymentAvailability(deployment *appsv1.Deployment) AvailabilityRecommendation {
	rec := AvailabilityRecommendation{
		Deployment:   deployment.Name,
		Namespace:    deployment.Namespace,
		CurrentClass: deployment.Annotations["oda.tmforum.org/availability-class"],
		Reasoning:    []string{},
	}

	// Scoring system for determining availability class
	score := 0.0
	confidence := 0.0
	factors := 0

	// Factor 1: Component function
	componentFunc := deployment.Annotations["oda.tmforum.org/component-function"]
	if componentFunc == "" {
		componentFunc = r.inferComponentFunction(deployment.Name)
	}

	switch componentFunc {
	case "security":
		score += 3.0
		rec.Reasoning = append(rec.Reasoning, "Security component requires high availability")
		factors++
	case "management":
		score += 2.0
		rec.Reasoning = append(rec.Reasoning, "Management component needs good availability")
		factors++
	case "database":
		score += 2.5
		rec.Reasoning = append(rec.Reasoning, "Database component requires stable availability")
		factors++
	default:
		score += 1.0
		rec.Reasoning = append(rec.Reasoning, "Core component with standard requirements")
		factors++
	}

	// Factor 2: Replica count
	replicas := int32(1)
	if deployment.Spec.Replicas != nil {
		replicas = *deployment.Spec.Replicas
	}

	switch {
	case replicas >= 5:
		score += 2.5
		rec.Reasoning = append(rec.Reasoning, fmt.Sprintf("High replica count (%d) indicates critical service", replicas))
		factors++
	case replicas >= 3:
		score += 1.5
		rec.Reasoning = append(rec.Reasoning, fmt.Sprintf("Multiple replicas (%d) suggest important service", replicas))
		factors++
	case replicas == 2:
		score += 1.0
		rec.Reasoning = append(rec.Reasoning, "Dual replicas for basic redundancy")
		factors++
	default:
		score += 0.0
		rec.Reasoning = append(rec.Reasoning, "Single replica limits availability options")
		factors++
	}

	// Factor 3: Deployment name patterns
	name := deployment.Name
	if containsPattern(name, "prod") || containsPattern(name, "production") {
		score += 2.0
		rec.Reasoning = append(rec.Reasoning, "Production deployment detected")
		factors++
	} else if containsPattern(name, "staging") || containsPattern(name, "stage") {
		score += 1.0
		rec.Reasoning = append(rec.Reasoning, "Staging deployment detected")
		factors++
	} else if containsPattern(name, "dev") || containsPattern(name, "test") {
		score += 0.0
		rec.Reasoning = append(rec.Reasoning, "Development/test deployment detected")
		factors++
	}

	// Factor 4: Labels indicating criticality
	labels := deployment.Labels
	if tier, exists := labels["tier"]; exists {
		switch tier {
		case "critical", "gold", "platinum":
			score += 2.5
			rec.Reasoning = append(rec.Reasoning, fmt.Sprintf("Critical tier label: %s", tier))
			factors++
		case "standard", "silver":
			score += 1.5
			rec.Reasoning = append(rec.Reasoning, fmt.Sprintf("Standard tier label: %s", tier))
			factors++
		case "bronze", "basic":
			score += 0.5
			rec.Reasoning = append(rec.Reasoning, fmt.Sprintf("Basic tier label: %s", tier))
			factors++
		}
	}

	// Factor 5: API/Gateway detection
	if containsPattern(name, "api") || containsPattern(name, "gateway") {
		score += 1.5
		rec.Reasoning = append(rec.Reasoning, "API/Gateway service requires high availability")
		factors++
	}

	// Factor 6: Database/Stateful detection
	if containsPattern(name, "db") || containsPattern(name, "database") || containsPattern(name, "postgres") || containsPattern(name, "mysql") {
		score += 2.0
		rec.Reasoning = append(rec.Reasoning, "Database service requires careful disruption management")
		factors++
	}

	// Calculate average score and determine recommendation
	if factors > 0 {
		avgScore := score / float64(factors)
		confidence = float64(factors) / 6.0 // Max 6 factors

		switch {
		case avgScore >= 2.5:
			rec.RecommendedClass = "mission-critical"
			rec.Impact = AvailabilityImpact{
				MinAvailable: "90%",
				Description:  "Ensures maximum availability with minimal disruptions",
			}
		case avgScore >= 1.8:
			rec.RecommendedClass = "high-availability"
			rec.Impact = AvailabilityImpact{
				MinAvailable: "75%",
				Description:  "Provides high availability for important services",
			}
		case avgScore >= 1.0:
			rec.RecommendedClass = "standard"
			rec.Impact = AvailabilityImpact{
				MinAvailable: "50%",
				Description:  "Standard availability for typical production workloads",
			}
		default:
			rec.RecommendedClass = "non-critical"
			rec.Impact = AvailabilityImpact{
				MinAvailable: "20%",
				Description:  "Basic availability for development/test workloads",
			}
		}
	} else {
		rec.RecommendedClass = "standard"
		rec.Impact = AvailabilityImpact{
			MinAvailable: "50%",
			Description:  "Default recommendation when factors cannot be determined",
		}
		confidence = 0.3
	}

	rec.Confidence = confidence

	// Add comparison with current class if exists
	if rec.CurrentClass != "" && rec.CurrentClass != rec.RecommendedClass {
		rec.Reasoning = append(rec.Reasoning,
			fmt.Sprintf("Current class '%s' differs from recommendation", rec.CurrentClass))
	}

	return rec
}

// RecommendPoliciesParams represents parameters for policy recommendations
type RecommendPoliciesParams struct {
	Namespace string `json:"namespace,omitempty"`
	Scope     string `json:"scope,omitempty"` // "namespace", "cluster", "component"
}

// RecommendPoliciesResult represents policy recommendations
type RecommendPoliciesResult struct {
	Policies []PolicyRecommendation `json:"policies"`
	Summary  PolicySummary          `json:"summary"`
}

// PolicyRecommendation represents a recommended policy
type PolicyRecommendation struct {
	Name                string                 `json:"name"`
	Type                string                 `json:"type"`
	Scope               string                 `json:"scope"`
	AvailabilityClass   string                 `json:"availabilityClass"`
	Enforcement         string                 `json:"enforcement"`
	ComponentSelector   map[string]interface{} `json:"componentSelector"`
	Priority            int                    `json:"priority"`
	Reasoning           []string               `json:"reasoning"`
	AffectedDeployments []string               `json:"affectedDeployments"`
}

// PolicySummary provides a summary of policy recommendations
type PolicySummary struct {
	TotalPolicies      int            `json:"totalPolicies"`
	ByScope            map[string]int `json:"byScope"`
	ByEnforcement      map[string]int `json:"byEnforcement"`
	DeploymentsCovered int            `json:"deploymentsCovered"`
}

// RecommendPolicies recommends availability policies based on cluster analysis
func (r *RecommendationTools) RecommendPolicies(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var recParams RecommendPoliciesParams
	if err := json.Unmarshal(params, &recParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Get all deployments
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{}
	if recParams.Namespace != "" {
		listOpts.Namespace = recParams.Namespace
	}
	if err := r.client.List(ctx, &deployments, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	result := &RecommendPoliciesResult{
		Policies: []PolicyRecommendation{},
		Summary: PolicySummary{
			ByScope:       make(map[string]int),
			ByEnforcement: make(map[string]int),
		},
	}

	// Analyze deployment patterns
	patterns := r.analyzeDeploymentPatterns(deployments.Items)

	// Generate policy recommendations based on patterns
	policies := r.generatePolicyRecommendations(patterns, recParams.Scope)

	for _, policy := range policies {
		result.Policies = append(result.Policies, policy)
		result.Summary.TotalPolicies++
		result.Summary.ByScope[policy.Scope]++
		result.Summary.ByEnforcement[policy.Enforcement]++
		result.Summary.DeploymentsCovered += len(policy.AffectedDeployments)
	}

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// DeploymentPattern represents a pattern of deployments
type DeploymentPattern struct {
	Type        string
	Count       int
	Namespaces  map[string]bool
	Components  map[string]bool
	Deployments []string
}

// analyzeDeploymentPatterns analyzes patterns in deployments
func (r *RecommendationTools) analyzeDeploymentPatterns(deployments []appsv1.Deployment) map[string]*DeploymentPattern {
	patterns := make(map[string]*DeploymentPattern)

	// Pattern 1: Security components
	securityPattern := &DeploymentPattern{
		Type:       "security",
		Namespaces: make(map[string]bool),
		Components: make(map[string]bool),
	}

	// Pattern 2: Production workloads
	productionPattern := &DeploymentPattern{
		Type:       "production",
		Namespaces: make(map[string]bool),
		Components: make(map[string]bool),
	}

	// Pattern 3: Database/Stateful
	databasePattern := &DeploymentPattern{
		Type:       "database",
		Namespaces: make(map[string]bool),
		Components: make(map[string]bool),
	}

	// Pattern 4: API/Gateway
	apiPattern := &DeploymentPattern{
		Type:       "api",
		Namespaces: make(map[string]bool),
		Components: make(map[string]bool),
	}

	for _, dep := range deployments {
		name := dep.Name
		namespace := dep.Namespace
		componentFunc := dep.Annotations["oda.tmforum.org/component-function"]

		// Security pattern
		if componentFunc == "security" || containsPattern(name, "auth") || containsPattern(name, "security") {
			securityPattern.Count++
			securityPattern.Namespaces[namespace] = true
			securityPattern.Deployments = append(securityPattern.Deployments, name)
			if componentFunc != "" {
				securityPattern.Components[componentFunc] = true
			}
		}

		// Production pattern
		if containsPattern(namespace, "prod") || containsPattern(name, "prod") {
			productionPattern.Count++
			productionPattern.Namespaces[namespace] = true
			productionPattern.Deployments = append(productionPattern.Deployments, name)
			if componentFunc != "" {
				productionPattern.Components[componentFunc] = true
			}
		}

		// Database pattern
		if containsPattern(name, "db") || containsPattern(name, "database") || containsPattern(name, "postgres") || containsPattern(name, "mysql") {
			databasePattern.Count++
			databasePattern.Namespaces[namespace] = true
			databasePattern.Deployments = append(databasePattern.Deployments, name)
			if componentFunc != "" {
				databasePattern.Components[componentFunc] = true
			}
		}

		// API pattern
		if containsPattern(name, "api") || containsPattern(name, "gateway") {
			apiPattern.Count++
			apiPattern.Namespaces[namespace] = true
			apiPattern.Deployments = append(apiPattern.Deployments, name)
			if componentFunc != "" {
				apiPattern.Components[componentFunc] = true
			}
		}
	}

	// Add patterns if they have deployments
	if securityPattern.Count > 0 {
		patterns["security"] = securityPattern
	}
	if productionPattern.Count > 0 {
		patterns["production"] = productionPattern
	}
	if databasePattern.Count > 0 {
		patterns["database"] = databasePattern
	}
	if apiPattern.Count > 0 {
		patterns["api"] = apiPattern
	}

	return patterns
}

// generatePolicyRecommendations generates policy recommendations based on patterns
func (r *RecommendationTools) generatePolicyRecommendations(patterns map[string]*DeploymentPattern, scope string) []PolicyRecommendation {
	var policies []PolicyRecommendation

	// Security policy
	if pattern, exists := patterns["security"]; exists {
		policy := PolicyRecommendation{
			Name:              "security-components-policy",
			Type:              "security",
			Scope:             "cluster",
			AvailabilityClass: "mission-critical",
			Enforcement:       "strict",
			ComponentSelector: map[string]interface{}{
				"componentFunctions": []string{"security"},
			},
			Priority: 1000,
			Reasoning: []string{
				fmt.Sprintf("Found %d security components across cluster", pattern.Count),
				"Security components require strict availability enforcement",
				"Mission-critical class ensures maximum uptime",
			},
			AffectedDeployments: pattern.Deployments,
		}

		// Add namespace selector if pattern is namespace-specific
		if len(pattern.Namespaces) <= 3 {
			namespaces := []string{}
			for ns := range pattern.Namespaces {
				namespaces = append(namespaces, ns)
			}
			policy.ComponentSelector["namespaces"] = namespaces
		}

		policies = append(policies, policy)
	}

	// Production policy
	if pattern, exists := patterns["production"]; exists && len(pattern.Namespaces) > 0 {
		namespaces := []string{}
		for ns := range pattern.Namespaces {
			if containsPattern(ns, "prod") {
				namespaces = append(namespaces, ns)
			}
		}

		if len(namespaces) > 0 {
			policy := PolicyRecommendation{
				Name:              "production-workloads-policy",
				Type:              "environment",
				Scope:             "namespace",
				AvailabilityClass: "high-availability",
				Enforcement:       "flexible",
				ComponentSelector: map[string]interface{}{
					"namespaces": namespaces,
				},
				Priority: 500,
				Reasoning: []string{
					fmt.Sprintf("Found %d production workloads", pattern.Count),
					"Production services need high availability",
					"Flexible enforcement allows teams to opt for higher availability",
				},
				AffectedDeployments: pattern.Deployments,
			}
			policies = append(policies, policy)
		}
	}

	// Database policy
	if pattern, exists := patterns["database"]; exists {
		policy := PolicyRecommendation{
			Name:              "stateful-database-policy",
			Type:              "workload",
			Scope:             "component",
			AvailabilityClass: "custom",
			Enforcement:       "strict",
			ComponentSelector: map[string]interface{}{
				"componentFunctions": []string{"database"},
				"matchLabels": map[string]string{
					"type": "database",
				},
			},
			Priority: 750,
			Reasoning: []string{
				fmt.Sprintf("Found %d database deployments", pattern.Count),
				"Databases require careful disruption management",
				"Custom PDB with absolute minAvailable recommended",
			},
			AffectedDeployments: pattern.Deployments,
		}
		policies = append(policies, policy)
	}

	// API Gateway policy
	if pattern, exists := patterns["api"]; exists {
		policy := PolicyRecommendation{
			Name:              "api-gateway-policy",
			Type:              "workload",
			Scope:             "component",
			AvailabilityClass: "high-availability",
			Enforcement:       "advisory",
			ComponentSelector: map[string]interface{}{
				"matchExpressions": []map[string]interface{}{
					{
						"key":      "component",
						"operator": "In",
						"values":   []string{"api", "gateway", "edge"},
					},
				},
			},
			Priority: 400,
			Reasoning: []string{
				fmt.Sprintf("Found %d API/Gateway services", pattern.Count),
				"API gateways are critical entry points",
				"Advisory enforcement allows override for specific cases",
			},
			AffectedDeployments: pattern.Deployments,
		}
		policies = append(policies, policy)
	}

	// Default catch-all policy (if no specific patterns or as baseline)
	if scope == "cluster" {
		defaultPolicy := PolicyRecommendation{
			Name:              "default-availability-policy",
			Type:              "default",
			Scope:             "cluster",
			AvailabilityClass: "standard",
			Enforcement:       "advisory",
			ComponentSelector: map[string]interface{}{
				"matchLabels": map[string]string{}, // Empty selector matches all
			},
			Priority: 1,
			Reasoning: []string{
				"Catch-all policy for unclassified workloads",
				"Standard availability as baseline",
				"Advisory enforcement allows flexibility",
			},
			AffectedDeployments: []string{"all-unmatched"},
		}
		policies = append(policies, defaultPolicy)
	}

	return policies
}

// inferComponentFunction infers component function from deployment name
func (r *RecommendationTools) inferComponentFunction(name string) string {
	// Security patterns
	securityPatterns := []string{"auth", "security", "oauth", "keycloak", "vault"}
	for _, pattern := range securityPatterns {
		if containsPattern(name, pattern) {
			return "security"
		}
	}

	// Management patterns
	mgmtPatterns := []string{"controller", "operator", "manager", "admin"}
	for _, pattern := range mgmtPatterns {
		if containsPattern(name, pattern) {
			return "management"
		}
	}

	// Database patterns
	dbPatterns := []string{"db", "database", "postgres", "mysql", "mongo", "redis"}
	for _, pattern := range dbPatterns {
		if containsPattern(name, pattern) {
			return "database"
		}
	}

	return "core"
}

// RegisterRecommendationTools registers all recommendation tools with the MCP server
func RegisterRecommendationTools(server interface{ RegisterTool(*types.Tool) error }, tools *RecommendationTools) error {
	// Register availability class recommendation tool
	availabilityTool := &types.Tool{
		Name:        "recommend_availability_classes",
		Description: "Recommend optimal availability classes for deployments based on workload characteristics",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string",
					"description": "Specific namespace to analyze (optional)"
				},
				"deployments": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Specific deployments to analyze (optional)"
				}
			}
		}`),
		Handler: tools.RecommendAvailabilityClasses,
	}
	if err := server.RegisterTool(availabilityTool); err != nil {
		return fmt.Errorf("failed to register availability recommendation tool: %w", err)
	}

	// Register policy recommendation tool
	policyTool := &types.Tool{
		Name:        "recommend_policies",
		Description: "Recommend availability policies based on cluster analysis and workload patterns",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string",
					"description": "Specific namespace to analyze (optional)"
				},
				"scope": {
					"type": "string",
					"enum": ["namespace", "cluster", "component"],
					"description": "Scope of policy recommendations"
				}
			}
		}`),
		Handler: tools.RecommendPolicies,
	}
	if err := server.RegisterTool(policyTool); err != nil {
		return fmt.Errorf("failed to register policy recommendation tool: %w", err)
	}

	return nil
}
