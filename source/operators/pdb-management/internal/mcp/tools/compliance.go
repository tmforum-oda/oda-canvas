package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"strings"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// ComplianceTools provides compliance validation tools for MCP
type ComplianceTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewComplianceTools creates new compliance tools
func NewComplianceTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *ComplianceTools {
	return &ComplianceTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// ValidatePolicyComplianceParams represents parameters for policy compliance validation
type ValidatePolicyComplianceParams struct {
	Namespace    string   `json:"namespace,omitempty"`
	Deployments  []string `json:"deployments,omitempty"`
	PolicyName   string   `json:"policyName,omitempty"`
	ShowDetails  bool     `json:"showDetails,omitempty"`
	IncludeFixed bool     `json:"includeFixed,omitempty"`
}

// ValidatePolicyComplianceResult represents policy compliance validation result
type ValidatePolicyComplianceResult struct {
	Summary         ComplianceSummary          `json:"summary"`
	Violations      []ComplianceViolation      `json:"violations"`
	Compliant       []ComplianceEntry          `json:"compliant,omitempty"`
	Policies        []PolicyInfo               `json:"policies"`
	Recommendations []ComplianceRecommendation `json:"recommendations"`
}

// ComplianceSummary provides overall compliance status
type ComplianceSummary struct {
	TotalDeployments     int     `json:"totalDeployments"`
	CompliantDeployments int     `json:"compliantDeployments"`
	ViolationCount       int     `json:"violationCount"`
	ComplianceScore      float64 `json:"complianceScore"`
	CriticalViolations   int     `json:"criticalViolations"`
	WarningViolations    int     `json:"warningViolations"`
	PolicyCoverage       float64 `json:"policyCoverage"`
}

// ComplianceViolation represents a single compliance violation
type ComplianceViolation struct {
	Deployment    string      `json:"deployment"`
	Namespace     string      `json:"namespace"`
	PolicyName    string      `json:"policyName,omitempty"`
	ViolationType string      `json:"violationType"`
	Severity      string      `json:"severity"`
	Description   string      `json:"description"`
	CurrentValue  interface{} `json:"currentValue,omitempty"`
	ExpectedValue interface{} `json:"expectedValue,omitempty"`
	Remediation   string      `json:"remediation"`
	Tags          []string    `json:"tags,omitempty"`
}

// ComplianceEntry represents a compliant deployment
type ComplianceEntry struct {
	Deployment string `json:"deployment"`
	Namespace  string `json:"namespace"`
	PolicyName string `json:"policyName,omitempty"`
	Status     string `json:"status"`
	Details    string `json:"details,omitempty"`
}

// PolicyInfo provides information about policies affecting compliance
type PolicyInfo struct {
	Name                  string `json:"name"`
	Namespace             string `json:"namespace"`
	AvailabilityClass     string `json:"availabilityClass"`
	Enforcement           string `json:"enforcement"`
	Priority              int32  `json:"priority"`
	ApplicableDeployments int    `json:"applicableDeployments"`
	ComponentSelector     string `json:"componentSelector"`
}

// ComplianceRecommendation provides actionable recommendations
type ComplianceRecommendation struct {
	Type        string `json:"type"`
	Priority    string `json:"priority"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Action      string `json:"action"`
	Impact      string `json:"impact"`
}

// ValidatePolicyCompliance validates deployment compliance with availability policies
func (c *ComplianceTools) ValidatePolicyCompliance(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var validateParams ValidatePolicyComplianceParams
	if err := json.Unmarshal(params, &validateParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}
	result := &ValidatePolicyComplianceResult{
		Violations:      []ComplianceViolation{},
		Compliant:       []ComplianceEntry{},
		Policies:        []PolicyInfo{},
		Recommendations: []ComplianceRecommendation{},
	}

	// Get all availability policies
	policies := &v1alpha1.AvailabilityPolicyList{}
	opts := []client.ListOption{}
	if validateParams.Namespace != "" {
		opts = append(opts, client.InNamespace(validateParams.Namespace))
	}

	if err := c.client.List(ctx, policies, opts...); err != nil {
		return nil, fmt.Errorf("failed to list availability policies: %w", err)
	}

	// Get deployments
	deployments := &appsv1.DeploymentList{}
	if err := c.client.List(ctx, deployments, opts...); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	// Filter deployments if specific ones are requested
	filteredDeployments := []appsv1.Deployment{}
	if len(validateParams.Deployments) > 0 {
		deploymentSet := make(map[string]bool)
		for _, name := range validateParams.Deployments {
			deploymentSet[name] = true
		}
		for _, deployment := range deployments.Items {
			if deploymentSet[deployment.Name] {
				filteredDeployments = append(filteredDeployments, deployment)
			}
		}
	} else {
		filteredDeployments = deployments.Items
	}

	// Build policy information
	for _, policy := range policies.Items {
		if validateParams.PolicyName != "" && policy.Name != validateParams.PolicyName {
			continue
		}

		applicableCount := 0
		for _, deployment := range filteredDeployments {
			if c.isPolicyApplicable(policy, deployment) {
				applicableCount++
			}
		}

		result.Policies = append(result.Policies, PolicyInfo{
			Name:                  policy.Name,
			Namespace:             policy.Namespace,
			AvailabilityClass:     string(policy.Spec.AvailabilityClass),
			Enforcement:           string(policy.Spec.GetEnforcement()),
			Priority:              policy.Spec.Priority,
			ApplicableDeployments: applicableCount,
			ComponentSelector:     c.formatSelector(policy.Spec.ComponentSelector),
		})
	}

	// Get existing PDBs
	pdbs := &policyv1.PodDisruptionBudgetList{}
	if err := c.client.List(ctx, pdbs, opts...); err != nil {
		return nil, fmt.Errorf("failed to list PDBs: %w", err)
	}

	pdbMap := make(map[string]*policyv1.PodDisruptionBudget)
	for _, pdb := range pdbs.Items {
		key := fmt.Sprintf("%s/%s", pdb.Namespace, pdb.Name)
		pdbCopy := pdb
		pdbMap[key] = &pdbCopy
	}

	// Validate each deployment
	for _, deployment := range filteredDeployments {
		violations, complianceEntry := c.validateDeploymentCompliance(ctx, deployment, policies.Items, pdbMap)
		result.Violations = append(result.Violations, violations...)

		if complianceEntry != nil && (validateParams.IncludeFixed || len(violations) == 0) {
			result.Compliant = append(result.Compliant, *complianceEntry)
		}
	}

	// Calculate summary
	result.Summary = c.calculateComplianceSummary(filteredDeployments, result.Violations, policies.Items)

	// Generate recommendations
	result.Recommendations = c.generateComplianceRecommendations(result.Violations, result.Summary)

	// Sort violations by severity and deployment name
	sort.Slice(result.Violations, func(i, j int) bool {
		if result.Violations[i].Severity != result.Violations[j].Severity {
			return c.getSeverityOrder(result.Violations[i].Severity) < c.getSeverityOrder(result.Violations[j].Severity)
		}
		return result.Violations[i].Deployment < result.Violations[j].Deployment
	})

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// validateDeploymentCompliance validates a single deployment against all applicable policies
func (c *ComplianceTools) validateDeploymentCompliance(ctx context.Context, deployment appsv1.Deployment, policies []v1alpha1.AvailabilityPolicy, pdbMap map[string]*policyv1.PodDisruptionBudget) ([]ComplianceViolation, *ComplianceEntry) {
	violations := []ComplianceViolation{}

	// Find applicable policies
	applicablePolicies := []v1alpha1.AvailabilityPolicy{}
	for _, policy := range policies {
		if c.isPolicyApplicable(policy, deployment) {
			applicablePolicies = append(applicablePolicies, policy)
		}
	}

	// Check if deployment has no applicable policies
	if len(applicablePolicies) == 0 {
		violations = append(violations, ComplianceViolation{
			Deployment:    deployment.Name,
			Namespace:     deployment.Namespace,
			ViolationType: "NO_POLICY",
			Severity:      "WARNING",
			Description:   "Deployment has no applicable availability policies",
			Remediation:   "Create or update availability policies to cover this deployment",
			Tags:          []string{"coverage", "policy"},
		})
		return violations, nil
	}

	// Get the highest priority policy
	sort.Slice(applicablePolicies, func(i, j int) bool {
		return applicablePolicies[i].Spec.Priority > applicablePolicies[j].Spec.Priority
	})
	primaryPolicy := applicablePolicies[0]

	// Check PDB existence and configuration
	expectedPDBName := c.generatePDBName(deployment)
	pdbKey := fmt.Sprintf("%s/%s", deployment.Namespace, expectedPDBName)
	pdb, exists := pdbMap[pdbKey]

	if !exists {
		violations = append(violations, ComplianceViolation{
			Deployment:    deployment.Name,
			Namespace:     deployment.Namespace,
			PolicyName:    primaryPolicy.Name,
			ViolationType: "MISSING_PDB",
			Severity:      c.getSeverityFromEnforcement(primaryPolicy.Spec.GetEnforcement()),
			Description:   "Pod Disruption Budget does not exist",
			ExpectedValue: expectedPDBName,
			Remediation:   "Create a Pod Disruption Budget for this deployment",
			Tags:          []string{"pdb", "availability"},
		})
		return violations, nil
	}

	// Validate PDB configuration
	violations = append(violations, c.validatePDBConfiguration(deployment, primaryPolicy, *pdb)...)

	// Validate deployment configuration
	violations = append(violations, c.validateDeploymentConfiguration(deployment, primaryPolicy)...)

	// Create compliance entry if no violations
	var complianceEntry *ComplianceEntry
	if len(violations) == 0 {
		complianceEntry = &ComplianceEntry{
			Deployment: deployment.Name,
			Namespace:  deployment.Namespace,
			PolicyName: primaryPolicy.Name,
			Status:     "COMPLIANT",
			Details:    fmt.Sprintf("Complies with %s policy", primaryPolicy.Spec.AvailabilityClass),
		}
	}

	return violations, complianceEntry
}

// validatePDBConfiguration validates PDB settings against policy requirements
func (c *ComplianceTools) validatePDBConfiguration(deployment appsv1.Deployment, policy v1alpha1.AvailabilityPolicy, pdb policyv1.PodDisruptionBudget) []ComplianceViolation {
	violations := []ComplianceViolation{}

	// Get expected PDB values based on availability class
	expectedMin, expectedMax := c.getExpectedPDBValues(deployment, policy)

	// Check minAvailable
	if pdb.Spec.MinAvailable != nil {
		if expectedMin != nil {
			if pdb.Spec.MinAvailable.String() != expectedMin.String() {
				violations = append(violations, ComplianceViolation{
					Deployment:    deployment.Name,
					Namespace:     deployment.Namespace,
					PolicyName:    policy.Name,
					ViolationType: "PDB_MIN_AVAILABLE",
					Severity:      c.getSeverityFromEnforcement(policy.Spec.GetEnforcement()),
					Description:   "PDB minAvailable does not match policy requirements",
					CurrentValue:  pdb.Spec.MinAvailable.String(),
					ExpectedValue: expectedMin.String(),
					Remediation:   fmt.Sprintf("Update PDB minAvailable to %s", expectedMin.String()),
					Tags:          []string{"pdb", "configuration"},
				})
			}
		}
	}

	// Check maxUnavailable
	if pdb.Spec.MaxUnavailable != nil {
		if expectedMax != nil {
			if pdb.Spec.MaxUnavailable.String() != expectedMax.String() {
				violations = append(violations, ComplianceViolation{
					Deployment:    deployment.Name,
					Namespace:     deployment.Namespace,
					PolicyName:    policy.Name,
					ViolationType: "PDB_MAX_UNAVAILABLE",
					Severity:      c.getSeverityFromEnforcement(policy.Spec.GetEnforcement()),
					Description:   "PDB maxUnavailable does not match policy requirements",
					CurrentValue:  pdb.Spec.MaxUnavailable.String(),
					ExpectedValue: expectedMax.String(),
					Remediation:   fmt.Sprintf("Update PDB maxUnavailable to %s", expectedMax.String()),
					Tags:          []string{"pdb", "configuration"},
				})
			}
		}
	}

	return violations
}

// validateDeploymentConfiguration validates deployment settings for availability
func (c *ComplianceTools) validateDeploymentConfiguration(deployment appsv1.Deployment, policy v1alpha1.AvailabilityPolicy) []ComplianceViolation {
	violations := []ComplianceViolation{}

	// Check replica count
	if deployment.Spec.Replicas != nil && *deployment.Spec.Replicas < 2 {
		severity := "WARNING"
		if policy.Spec.AvailabilityClass == v1alpha1.MissionCritical {
			severity = "CRITICAL"
		}

		violations = append(violations, ComplianceViolation{
			Deployment:    deployment.Name,
			Namespace:     deployment.Namespace,
			PolicyName:    policy.Name,
			ViolationType: "LOW_REPLICA_COUNT",
			Severity:      severity,
			Description:   "Deployment has insufficient replicas for high availability",
			CurrentValue:  *deployment.Spec.Replicas,
			ExpectedValue: ">=2",
			Remediation:   "Increase replica count to at least 2 for availability",
			Tags:          []string{"replicas", "availability"},
		})
	}

	// Check for anti-affinity (for mission-critical workloads)
	if policy.Spec.AvailabilityClass == v1alpha1.MissionCritical {
		hasAntiAffinity := deployment.Spec.Template.Spec.Affinity != nil &&
			deployment.Spec.Template.Spec.Affinity.PodAntiAffinity != nil

		if !hasAntiAffinity {
			violations = append(violations, ComplianceViolation{
				Deployment:    deployment.Name,
				Namespace:     deployment.Namespace,
				PolicyName:    policy.Name,
				ViolationType: "MISSING_ANTI_AFFINITY",
				Severity:      "WARNING",
				Description:   "Mission-critical deployment should use pod anti-affinity",
				ExpectedValue: "PodAntiAffinity rules",
				Remediation:   "Add pod anti-affinity rules to spread pods across nodes",
				Tags:          []string{"affinity", "mission-critical"},
			})
		}
	}

	return violations
}

// Helper methods

func (c *ComplianceTools) isPolicyApplicable(policy v1alpha1.AvailabilityPolicy, deployment appsv1.Deployment) bool {
	selector := policy.Spec.ComponentSelector

	// Check component names
	for _, name := range selector.ComponentNames {
		if name == deployment.Name {
			return true
		}
	}

	// Check labels
	if len(selector.MatchLabels) > 0 {
		for key, value := range selector.MatchLabels {
			if deploymentValue, exists := deployment.Labels[key]; exists && deploymentValue == value {
				return true
			}
		}
	}

	// If no specific selectors, check if it's a general policy
	if len(selector.ComponentNames) == 0 && len(selector.MatchLabels) == 0 {
		return true
	}

	return false
}

func (c *ComplianceTools) formatSelector(selector v1alpha1.ComponentSelector) string {
	parts := []string{}

	if len(selector.ComponentNames) > 0 {
		parts = append(parts, fmt.Sprintf("names: %s", strings.Join(selector.ComponentNames, ", ")))
	}

	if len(selector.MatchLabels) > 0 {
		labels := []string{}
		for k, v := range selector.MatchLabels {
			labels = append(labels, fmt.Sprintf("%s=%s", k, v))
		}
		parts = append(parts, fmt.Sprintf("labels: %s", strings.Join(labels, ", ")))
	}

	if len(parts) == 0 {
		return "all deployments"
	}

	return strings.Join(parts, "; ")
}

func (c *ComplianceTools) generatePDBName(deployment appsv1.Deployment) string {
	return fmt.Sprintf("%s-pdb", deployment.Name)
}

func (c *ComplianceTools) getExpectedPDBValues(deployment appsv1.Deployment, policy v1alpha1.AvailabilityPolicy) (*intstr.IntOrString, *intstr.IntOrString) {
	// Simplified logic - in reality this would be more sophisticated
	switch policy.Spec.AvailabilityClass {
	case v1alpha1.MissionCritical:
		min := intstr.FromString("75%")
		return &min, nil
	case v1alpha1.HighAvailability:
		min := intstr.FromString("50%")
		return &min, nil
	case v1alpha1.Standard:
		max := intstr.FromInt(1)
		return nil, &max
	default:
		max := intstr.FromInt(1)
		return nil, &max
	}
}

func (c *ComplianceTools) getSeverityFromEnforcement(enforcement v1alpha1.EnforcementMode) string {
	switch enforcement {
	case v1alpha1.EnforcementStrict:
		return "CRITICAL"
	case v1alpha1.EnforcementFlexible:
		return "WARNING"
	case v1alpha1.EnforcementAdvisory:
		return "INFO"
	default:
		return "WARNING"
	}
}

func (c *ComplianceTools) getSeverityOrder(severity string) int {
	switch severity {
	case "CRITICAL":
		return 1
	case "WARNING":
		return 2
	case "INFO":
		return 3
	default:
		return 4
	}
}

func (c *ComplianceTools) calculateComplianceSummary(deployments []appsv1.Deployment, violations []ComplianceViolation, policies []v1alpha1.AvailabilityPolicy) ComplianceSummary {
	totalDeployments := len(deployments)

	// Count violations by deployment
	violationsByDeployment := make(map[string][]ComplianceViolation)
	criticalCount := 0
	warningCount := 0

	for _, violation := range violations {
		key := fmt.Sprintf("%s/%s", violation.Namespace, violation.Deployment)
		violationsByDeployment[key] = append(violationsByDeployment[key], violation)

		switch violation.Severity {
		case "CRITICAL":
			criticalCount++
		case "WARNING":
			warningCount++
		}
	}

	compliantDeployments := totalDeployments - len(violationsByDeployment)
	complianceScore := 0.0
	if totalDeployments > 0 {
		complianceScore = float64(compliantDeployments) / float64(totalDeployments) * 100
	}

	policyCoverage := 0.0
	if totalDeployments > 0 {
		coveredDeployments := 0
		for _, deployment := range deployments {
			for _, policy := range policies {
				if c.isPolicyApplicable(policy, deployment) {
					coveredDeployments++
					break
				}
			}
		}
		policyCoverage = float64(coveredDeployments) / float64(totalDeployments) * 100
	}

	return ComplianceSummary{
		TotalDeployments:     totalDeployments,
		CompliantDeployments: compliantDeployments,
		ViolationCount:       len(violations),
		ComplianceScore:      complianceScore,
		CriticalViolations:   criticalCount,
		WarningViolations:    warningCount,
		PolicyCoverage:       policyCoverage,
	}
}

func (c *ComplianceTools) generateComplianceRecommendations(violations []ComplianceViolation, summary ComplianceSummary) []ComplianceRecommendation {
	recommendations := []ComplianceRecommendation{}

	// Analyze violations for common patterns
	violationTypes := make(map[string]int)
	for _, violation := range violations {
		violationTypes[violation.ViolationType]++
	}

	// Generate recommendations based on violation patterns
	if violationTypes["NO_POLICY"] > 0 {
		recommendations = append(recommendations, ComplianceRecommendation{
			Type:        "POLICY_COVERAGE",
			Priority:    "HIGH",
			Title:       "Improve Policy Coverage",
			Description: fmt.Sprintf("%d deployments lack availability policies", violationTypes["NO_POLICY"]),
			Action:      "Create availability policies to cover unmanaged deployments",
			Impact:      "Reduces risk of availability issues during disruptions",
		})
	}

	if violationTypes["MISSING_PDB"] > 0 {
		recommendations = append(recommendations, ComplianceRecommendation{
			Type:        "PDB_CREATION",
			Priority:    "CRITICAL",
			Title:       "Create Missing PDBs",
			Description: fmt.Sprintf("%d deployments are missing Pod Disruption Budgets", violationTypes["MISSING_PDB"]),
			Action:      "Use create_availability_policy tool to generate PDBs automatically",
			Impact:      "Prevents uncontrolled pod evictions during cluster maintenance",
		})
	}

	if violationTypes["LOW_REPLICA_COUNT"] > 0 {
		recommendations = append(recommendations, ComplianceRecommendation{
			Type:        "SCALING",
			Priority:    "MEDIUM",
			Title:       "Increase Replica Counts",
			Description: fmt.Sprintf("%d deployments have insufficient replicas for high availability", violationTypes["LOW_REPLICA_COUNT"]),
			Action:      "Scale deployments to at least 2 replicas",
			Impact:      "Improves service availability during pod failures",
		})
	}

	// Overall compliance recommendations
	if summary.ComplianceScore < 80 {
		recommendations = append(recommendations, ComplianceRecommendation{
			Type:        "COMPLIANCE_IMPROVEMENT",
			Priority:    "HIGH",
			Title:       "Improve Overall Compliance",
			Description: fmt.Sprintf("Current compliance score is %.1f%% - below recommended 80%%", summary.ComplianceScore),
			Action:      "Address critical violations first, then systematic improvement",
			Impact:      "Reduces operational risk and improves service reliability",
		})
	}

	return recommendations
}

// RegisterComplianceTools registers all compliance tools with the MCP server
func RegisterComplianceTools(server interface{ RegisterTool(*types.Tool) error }, tools *ComplianceTools) error {
	// Register policy compliance validation tool
	complianceTool := &types.Tool{
		Name:        "validate_policy_compliance",
		Description: "Validate deployment compliance with availability policies and identify violations",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string",
					"description": "Specific namespace to validate (optional)"
				},
				"deployments": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Specific deployments to validate (optional)"
				},
				"policyName": {
					"type": "string",
					"description": "Specific policy to check compliance against (optional)"
				},
				"showDetails": {
					"type": "boolean",
					"description": "Include detailed compliance information",
					"default": true
				},
				"includeFixed": {
					"type": "boolean", 
					"description": "Include compliant deployments in results",
					"default": false
				}
			}
		}`),
		Handler: tools.ValidatePolicyCompliance,
	}
	if err := server.RegisterTool(complianceTool); err != nil {
		return fmt.Errorf("failed to register policy compliance tool: %w", err)
	}

	return nil
}
