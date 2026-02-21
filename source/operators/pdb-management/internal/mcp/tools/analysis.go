package tools

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// AnalysisTools provides cluster analysis tools for MCP
type AnalysisTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewAnalysisTools creates new analysis tools
func NewAnalysisTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *AnalysisTools {
	return &AnalysisTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// AnalyzeClusterAvailabilityParams represents parameters for cluster availability analysis
type AnalyzeClusterAvailabilityParams struct {
	Namespace string `json:"namespace,omitempty"`
	Detailed  bool   `json:"detailed,omitempty"`
}

// AnalyzeClusterAvailabilityResult represents the result of cluster availability analysis
type AnalyzeClusterAvailabilityResult struct {
	Summary    AvailabilitySummary `json:"summary"`
	Coverage   PDBCoverage         `json:"coverage"`
	Issues     []AvailabilityIssue `json:"issues"`
	Namespaces []NamespaceAnalysis `json:"namespaces,omitempty"`
}

// AvailabilitySummary provides a summary of availability status
type AvailabilitySummary struct {
	TotalDeployments      int            `json:"totalDeployments"`
	DeploymentsWithPDB    int            `json:"deploymentsWithPDB"`
	DeploymentsWithoutPDB int            `json:"deploymentsWithoutPDB"`
	CoveragePercentage    float64        `json:"coveragePercentage"`
	AvailabilityClasses   map[string]int `json:"availabilityClasses"`
}

// PDBCoverage provides PDB coverage statistics
type PDBCoverage struct {
	Covered     int                           `json:"covered"`
	Uncovered   int                           `json:"uncovered"`
	Percentage  float64                       `json:"percentage"`
	ByNamespace map[string]*NamespaceCoverage `json:"byNamespace"`
}

// NamespaceCoverage provides PDB coverage for a namespace
type NamespaceCoverage struct {
	Covered    int     `json:"covered"`
	Uncovered  int     `json:"uncovered"`
	Percentage float64 `json:"percentage"`
}

// AvailabilityIssue represents an availability issue
type AvailabilityIssue struct {
	Type        string `json:"type"`
	Severity    string `json:"severity"`
	Resource    string `json:"resource"`
	Namespace   string `json:"namespace"`
	Description string `json:"description"`
}

// NamespaceAnalysis provides analysis for a specific namespace
type NamespaceAnalysis struct {
	Name        string               `json:"name"`
	Deployments []DeploymentAnalysis `json:"deployments"`
	Coverage    NamespaceCoverage    `json:"coverage"`
}

// DeploymentAnalysis provides analysis for a specific deployment
type DeploymentAnalysis struct {
	Name              string   `json:"name"`
	Namespace         string   `json:"namespace"`
	Replicas          int32    `json:"replicas"`
	HasPDB            bool     `json:"hasPDB"`
	AvailabilityClass string   `json:"availabilityClass,omitempty"`
	ComponentFunction string   `json:"componentFunction,omitempty"`
	Issues            []string `json:"issues,omitempty"`
}

// AnalyzeClusterAvailability analyzes cluster-wide PDB coverage and availability
func (a *AnalysisTools) AnalyzeClusterAvailability(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var analyzeParams AnalyzeClusterAvailabilityParams
	if err := json.Unmarshal(params, &analyzeParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Get all deployments
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{}
	if analyzeParams.Namespace != "" {
		listOpts.Namespace = analyzeParams.Namespace
	}
	if err := a.client.List(ctx, &deployments, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	// Get all PDBs
	var pdbs policyv1.PodDisruptionBudgetList
	if err := a.client.List(ctx, &pdbs, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list PDBs: %w", err)
	}

	// Build PDB map by selector
	pdbMap := make(map[string]*policyv1.PodDisruptionBudget)
	for i := range pdbs.Items {
		pdb := &pdbs.Items[i]
		key := fmt.Sprintf("%s/%s", pdb.Namespace, pdb.Name)
		pdbMap[key] = pdb
	}

	// Analyze deployments
	result := &AnalyzeClusterAvailabilityResult{
		Summary: AvailabilitySummary{
			AvailabilityClasses: make(map[string]int),
		},
		Coverage: PDBCoverage{
			ByNamespace: make(map[string]*NamespaceCoverage),
		},
		Issues:     []AvailabilityIssue{},
		Namespaces: []NamespaceAnalysis{},
	}

	namespaceDeployments := make(map[string][]DeploymentAnalysis)

	for _, deployment := range deployments.Items {
		hasPDB := a.deploymentHasPDB(&deployment, pdbMap)

		// Update summary
		result.Summary.TotalDeployments++
		if hasPDB {
			result.Summary.DeploymentsWithPDB++
			result.Coverage.Covered++
		} else {
			result.Summary.DeploymentsWithoutPDB++
			result.Coverage.Uncovered++
		}

		// Get availability class
		availClass := deployment.Annotations["oda.tmforum.org/availability-class"]
		if availClass != "" {
			result.Summary.AvailabilityClasses[availClass]++
		}

		// Update namespace coverage
		ns := deployment.Namespace
		if _, exists := result.Coverage.ByNamespace[ns]; !exists {
			result.Coverage.ByNamespace[ns] = &NamespaceCoverage{}
		}
		if hasPDB {
			result.Coverage.ByNamespace[ns].Covered++
		} else {
			result.Coverage.ByNamespace[ns].Uncovered++
		}

		// Check for issues
		issues := a.checkDeploymentIssues(&deployment, hasPDB)
		for _, issue := range issues {
			result.Issues = append(result.Issues, AvailabilityIssue{
				Type:        "deployment",
				Severity:    "warning",
				Resource:    deployment.Name,
				Namespace:   deployment.Namespace,
				Description: issue,
			})
		}

		// Add to namespace analysis if detailed
		if analyzeParams.Detailed {
			// Safe dereference of Replicas (defaults to 1 if nil)
			replicas := int32(1)
			if deployment.Spec.Replicas != nil {
				replicas = *deployment.Spec.Replicas
			}
			analysis := DeploymentAnalysis{
				Name:              deployment.Name,
				Namespace:         deployment.Namespace,
				Replicas:          replicas,
				HasPDB:            hasPDB,
				AvailabilityClass: availClass,
				ComponentFunction: deployment.Annotations["oda.tmforum.org/component-function"],
				Issues:            issues,
			}
			namespaceDeployments[ns] = append(namespaceDeployments[ns], analysis)
		}
	}

	// Calculate percentages
	if result.Summary.TotalDeployments > 0 {
		result.Coverage.Percentage = float64(result.Coverage.Covered) / float64(result.Summary.TotalDeployments) * 100
		result.Summary.CoveragePercentage = result.Coverage.Percentage
	}

	for ns, coverage := range result.Coverage.ByNamespace {
		total := coverage.Covered + coverage.Uncovered
		if total > 0 {
			coverage.Percentage = float64(coverage.Covered) / float64(total) * 100
		}

		// Add namespace analysis if detailed
		if analyzeParams.Detailed {
			result.Namespaces = append(result.Namespaces, NamespaceAnalysis{
				Name:        ns,
				Deployments: namespaceDeployments[ns],
				Coverage:    *coverage,
			})
		}
	}

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// deploymentHasPDB checks if a deployment has a matching PDB
func (a *AnalysisTools) deploymentHasPDB(deployment *appsv1.Deployment, pdbMap map[string]*policyv1.PodDisruptionBudget) bool {
	// Check for managed PDB (created by our operator)
	managedPDBName := fmt.Sprintf("%s-pdb", deployment.Name)
	key := fmt.Sprintf("%s/%s", deployment.Namespace, managedPDBName)
	if _, exists := pdbMap[key]; exists {
		return true
	}

	// Check for PDBs that might match this deployment's pods
	for _, pdb := range pdbMap {
		if pdb.Namespace != deployment.Namespace {
			continue
		}

		// Check if PDB selector matches deployment selector
		if a.selectorsMatch(pdb.Spec.Selector, deployment.Spec.Selector) {
			return true
		}
	}

	return false
}

// selectorsMatch checks if two label selectors match
func (a *AnalysisTools) selectorsMatch(pdbSelector *metav1.LabelSelector, deploySelector *metav1.LabelSelector) bool {
	if pdbSelector == nil || deploySelector == nil {
		return false
	}

	// Convert to labels.Selector for comparison
	pdbSel, err := metav1.LabelSelectorAsSelector(pdbSelector)
	if err != nil {
		return false
	}

	deploySel, err := metav1.LabelSelectorAsSelector(deploySelector)
	if err != nil {
		return false
	}

	// Check if PDB selector would match pods selected by deployment selector
	// PDB selector should be a subset of deployment selector labels
	if pdbSelector.MatchLabels != nil && deploySelector.MatchLabels != nil {
		// Check if all PDB labels exist in deployment labels with same values
		for pdbKey, pdbValue := range pdbSelector.MatchLabels {
			if deployValue, exists := deploySelector.MatchLabels[pdbKey]; !exists || deployValue != pdbValue {
				return false
			}
		}
		return true
	}

	// Fallback to exact selector string match
	return pdbSel.String() == deploySel.String()
}

// checkDeploymentIssues checks for potential issues with a deployment
func (a *AnalysisTools) checkDeploymentIssues(deployment *appsv1.Deployment, hasPDB bool) []string {
	var issues []string

	// Check for missing PDB
	if !hasPDB && deployment.Spec.Replicas != nil && *deployment.Spec.Replicas > 1 {
		issues = append(issues, "Multi-replica deployment without PDB")
	}

	// Check for missing availability class
	if deployment.Annotations["oda.tmforum.org/availability-class"] == "" {
		issues = append(issues, "Missing availability class annotation")
	}

	// Check for single replica with high availability requirement
	if deployment.Spec.Replicas != nil && *deployment.Spec.Replicas == 1 {
		availClass := deployment.Annotations["oda.tmforum.org/availability-class"]
		if availClass == "high-availability" || availClass == "mission-critical" {
			issues = append(issues, fmt.Sprintf("Single replica with %s requirement", availClass))
		}
	}

	// Check for security components without proper availability
	componentFunc := deployment.Annotations["oda.tmforum.org/component-function"]
	if componentFunc == "security" {
		availClass := deployment.Annotations["oda.tmforum.org/availability-class"]
		if availClass == "" || availClass == "non-critical" {
			issues = append(issues, "Security component with insufficient availability class")
		}
	}

	return issues
}

// AnalyzeWorkloadPatternsParams represents parameters for workload pattern analysis
type AnalyzeWorkloadPatternsParams struct {
	Namespace  string   `json:"namespace,omitempty"`
	Components []string `json:"components,omitempty"`
}

// AnalyzeWorkloadPatternsResult represents the result of workload pattern analysis
type AnalyzeWorkloadPatternsResult struct {
	Patterns            []WorkloadPattern `json:"patterns"`
	ComponentFunctions  map[string]int    `json:"componentFunctions"`
	ReplicaDistribution map[string]int    `json:"replicaDistribution"`
	Recommendations     []string          `json:"recommendations"`
}

// WorkloadPattern represents a detected workload pattern
type WorkloadPattern struct {
	Name        string   `json:"name"`
	Type        string   `json:"type"`
	Count       int      `json:"count"`
	Description string   `json:"description"`
	Examples    []string `json:"examples"`
}

// AnalyzeWorkloadPatterns analyzes deployment patterns in the cluster
func (a *AnalysisTools) AnalyzeWorkloadPatterns(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var analyzeParams AnalyzeWorkloadPatternsParams
	if err := json.Unmarshal(params, &analyzeParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Get deployments
	var deployments appsv1.DeploymentList
	listOpts := &client.ListOptions{}
	if analyzeParams.Namespace != "" {
		listOpts.Namespace = analyzeParams.Namespace
	}
	if err := a.client.List(ctx, &deployments, listOpts); err != nil {
		return nil, fmt.Errorf("failed to list deployments: %w", err)
	}

	result := &AnalyzeWorkloadPatternsResult{
		Patterns:            []WorkloadPattern{},
		ComponentFunctions:  make(map[string]int),
		ReplicaDistribution: make(map[string]int),
		Recommendations:     []string{},
	}

	// Analyze patterns
	patterns := make(map[string]*WorkloadPattern)

	for _, deployment := range deployments.Items {
		// Component function analysis
		componentFunc := deployment.Annotations["oda.tmforum.org/component-function"]
		if componentFunc == "" {
			componentFunc = a.inferComponentFunction(deployment.Name)
		}
		result.ComponentFunctions[componentFunc]++

		// Replica distribution
		replicas := int32(1)
		if deployment.Spec.Replicas != nil {
			replicas = *deployment.Spec.Replicas
		}

		replicaRange := a.getReplicaRange(replicas)
		result.ReplicaDistribution[replicaRange]++

		// Pattern detection
		pattern := a.detectPattern(&deployment)
		if pattern != "" {
			if p, exists := patterns[pattern]; exists {
				p.Count++
				if len(p.Examples) < 3 {
					p.Examples = append(p.Examples, deployment.Name)
				}
			} else {
				patterns[pattern] = &WorkloadPattern{
					Name:        pattern,
					Type:        a.getPatternType(pattern),
					Count:       1,
					Description: a.getPatternDescription(pattern),
					Examples:    []string{deployment.Name},
				}
			}
		}
	}

	// Convert patterns map to slice
	for _, pattern := range patterns {
		result.Patterns = append(result.Patterns, *pattern)
	}

	// Generate recommendations
	result.Recommendations = a.generatePatternRecommendations(result)

	return &types.ToolResult{
		Content: *result,
	}, nil
}

// inferComponentFunction infers component function from deployment name
func (a *AnalysisTools) inferComponentFunction(name string) string {
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

// getReplicaRange categorizes replica count into ranges
func (a *AnalysisTools) getReplicaRange(replicas int32) string {
	switch {
	case replicas == 1:
		return "single"
	case replicas >= 2 && replicas <= 3:
		return "low (2-3)"
	case replicas >= 4 && replicas <= 6:
		return "medium (4-6)"
	case replicas >= 7 && replicas <= 10:
		return "high (7-10)"
	default:
		return "very high (>10)"
	}
}

// detectPattern detects workload patterns
func (a *AnalysisTools) detectPattern(deployment *appsv1.Deployment) string {
	name := deployment.Name

	// API pattern
	if containsPattern(name, "api") || containsPattern(name, "gateway") {
		return "api-gateway"
	}

	// Frontend pattern
	if containsPattern(name, "frontend") || containsPattern(name, "ui") || containsPattern(name, "web") {
		return "frontend"
	}

	// Backend service pattern
	if containsPattern(name, "service") || containsPattern(name, "backend") {
		return "backend-service"
	}

	// Database pattern
	if containsPattern(name, "db") || containsPattern(name, "database") {
		return "stateful-database"
	}

	// Message queue pattern
	if containsPattern(name, "queue") || containsPattern(name, "kafka") || containsPattern(name, "rabbitmq") {
		return "message-queue"
	}

	// Cache pattern
	if containsPattern(name, "cache") || containsPattern(name, "redis") || containsPattern(name, "memcached") {
		return "cache"
	}

	// Batch job pattern
	if containsPattern(name, "job") || containsPattern(name, "batch") || containsPattern(name, "cron") {
		return "batch-processor"
	}

	return "general-workload"
}

// getPatternType returns the type of a pattern
func (a *AnalysisTools) getPatternType(pattern string) string {
	switch pattern {
	case "api-gateway", "frontend", "backend-service":
		return "application"
	case "stateful-database", "cache", "message-queue":
		return "data"
	case "batch-processor":
		return "processing"
	default:
		return "general"
	}
}

// getPatternDescription returns a description for a pattern
func (a *AnalysisTools) getPatternDescription(pattern string) string {
	descriptions := map[string]string{
		"api-gateway":       "API gateways and edge services",
		"frontend":          "Frontend applications and UI services",
		"backend-service":   "Backend business logic services",
		"stateful-database": "Stateful database deployments",
		"message-queue":     "Message queuing systems",
		"cache":             "Caching layers",
		"batch-processor":   "Batch processing and scheduled jobs",
		"general-workload":  "General purpose workloads",
	}

	if desc, exists := descriptions[pattern]; exists {
		return desc
	}
	return "Unknown pattern"
}

// generatePatternRecommendations generates recommendations based on patterns
func (a *AnalysisTools) generatePatternRecommendations(result *AnalyzeWorkloadPatternsResult) []string {
	var recommendations []string

	// Check for high percentage of single replicas
	if singleCount, exists := result.ReplicaDistribution["single"]; exists {
		total := 0
		for _, count := range result.ReplicaDistribution {
			total += count
		}
		if float64(singleCount)/float64(total) > 0.5 {
			recommendations = append(recommendations,
				"Over 50% of deployments have single replicas - consider scaling critical services for high availability")
		}
	}

	// Check for missing security components
	if secCount, exists := result.ComponentFunctions["security"]; !exists || secCount == 0 {
		recommendations = append(recommendations,
			"No security components detected - ensure authentication and authorization services are properly labeled")
	}

	// Check for database patterns without proper availability
	for _, pattern := range result.Patterns {
		if pattern.Name == "stateful-database" && pattern.Count > 0 {
			recommendations = append(recommendations,
				fmt.Sprintf("Found %d database deployments - ensure they have appropriate PDB configurations for data consistency", pattern.Count))
		}
	}

	// Check for API gateways
	for _, pattern := range result.Patterns {
		if pattern.Name == "api-gateway" && pattern.Count > 0 {
			recommendations = append(recommendations,
				fmt.Sprintf("Found %d API gateway deployments - these should have high availability configurations", pattern.Count))
		}
	}

	return recommendations
}

// containsPattern checks if a string contains a pattern (case-insensitive)
func containsPattern(s, pattern string) bool {
	// Simple case-insensitive contains check
	// In production, might want to use strings.Contains with strings.ToLower
	return len(s) >= len(pattern) && containsIgnoreCase(s, pattern)
}

// containsIgnoreCase performs case-insensitive string contains
func containsIgnoreCase(s, substr string) bool {
	if len(substr) > len(s) {
		return false
	}
	// Convert both to lowercase for comparison
	sLower := toLower(s)
	substrLower := toLower(substr)

	for i := 0; i <= len(sLower)-len(substrLower); i++ {
		if sLower[i:i+len(substrLower)] == substrLower {
			return true
		}
	}
	return false
}

// toLower converts string to lowercase
func toLower(s string) string {
	// Simple ASCII lowercase conversion
	result := make([]byte, len(s))
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c >= 'A' && c <= 'Z' {
			result[i] = c + 32
		} else {
			result[i] = c
		}
	}
	return string(result)
}

// RegisterAnalysisTools registers all analysis tools with the MCP server
func RegisterAnalysisTools(server interface{ RegisterTool(*types.Tool) error }, tools *AnalysisTools) error {
	// Register cluster availability analysis tool
	clusterAnalysisTool := &types.Tool{
		Name:        "analyze_cluster_availability",
		Description: "Analyze cluster-wide PDB coverage and availability status",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string",
					"description": "Specific namespace to analyze (optional)"
				},
				"detailed": {
					"type": "boolean",
					"description": "Include detailed deployment analysis"
				}
			}
		}`),
		Handler: tools.AnalyzeClusterAvailability,
	}
	if err := server.RegisterTool(clusterAnalysisTool); err != nil {
		return fmt.Errorf("failed to register cluster analysis tool: %w", err)
	}

	// Register workload pattern analysis tool
	workloadPatternTool := &types.Tool{
		Name:        "analyze_workload_patterns",
		Description: "Analyze deployment patterns and workload characteristics in the cluster",
		InputSchema: json.RawMessage(`{
			"type": "object",
			"properties": {
				"namespace": {
					"type": "string",
					"description": "Specific namespace to analyze (optional)"
				},
				"components": {
					"type": "array",
					"items": {"type": "string"},
					"description": "Specific components to analyze (optional)"
				}
			}
		}`),
		Handler: tools.AnalyzeWorkloadPatterns,
	}
	if err := server.RegisterTool(workloadPatternTool); err != nil {
		return fmt.Errorf("failed to register workload pattern tool: %w", err)
	}

	return nil
}
