package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// BackupTools handles backup and restore operations for PDB policies
type BackupTools struct {
	client     client.Client
	kubeClient kubernetes.Interface
	logger     logr.Logger
}

// NewBackupTools creates a new BackupTools instance
func NewBackupTools(client client.Client, kubeClient kubernetes.Interface, logger logr.Logger) *BackupTools {
	return &BackupTools{
		client:     client,
		kubeClient: kubeClient,
		logger:     logger,
	}
}

// BackupPoliciesParams defines parameters for backing up policies
type BackupPoliciesParams struct {
	Namespaces         []string `json:"namespaces,omitempty"`
	IncludeDeployments bool     `json:"includeDeployments,omitempty"`
	IncludePDBs        bool     `json:"includePDBs,omitempty"`
	Format             string   `json:"format,omitempty"` // "yaml" or "json"
	CompressionEnabled bool     `json:"compressionEnabled,omitempty"`
}

// RestorePoliciesParams defines parameters for restoring policies
type RestorePoliciesParams struct {
	BackupData    json.RawMessage `json:"backupData"`
	DryRun        bool            `json:"dryRun,omitempty"`
	OverwriteMode string          `json:"overwriteMode,omitempty"` // "skip", "overwrite", "merge"
	Namespaces    []string        `json:"namespaces,omitempty"`
}

// PolicyBackup represents a complete backup of policies and related resources
type PolicyBackup struct {
	Metadata             BackupMetadata                 `json:"metadata"`
	AvailabilityPolicies []v1alpha1.AvailabilityPolicy  `json:"availabilityPolicies"`
	Deployments          []appsv1.Deployment            `json:"deployments,omitempty"`
	PodDisruptionBudgets []policyv1.PodDisruptionBudget `json:"podDisruptionBudgets,omitempty"`
}

// BackupMetadata contains information about the backup
type BackupMetadata struct {
	CreatedAt   time.Time   `json:"createdAt"`
	Version     string      `json:"version"`
	ClusterInfo ClusterInfo `json:"clusterInfo"`
	BackupStats BackupStats `json:"backupStats"`
}

// ClusterInfo contains information about the cluster
type ClusterInfo struct {
	ServerVersion string            `json:"serverVersion,omitempty"`
	Nodes         int               `json:"nodes,omitempty"`
	Namespaces    []string          `json:"namespaces"`
	Labels        map[string]string `json:"labels,omitempty"`
}

// BackupStats contains statistics about the backup
type BackupStats struct {
	PoliciesCount    int `json:"policiesCount"`
	DeploymentsCount int `json:"deploymentsCount"`
	PDBsCount        int `json:"pdbsCount"`
	NamespacesCount  int `json:"namespacesCount"`
	SizeBytes        int `json:"sizeBytes"`
}

// RestoreResult represents the result of a restore operation
type RestoreResult struct {
	Summary         RestoreSummary `json:"summary"`
	CreatedPolicies []PolicyResult `json:"createdPolicies"`
	UpdatedPolicies []PolicyResult `json:"updatedPolicies"`
	SkippedPolicies []PolicyResult `json:"skippedPolicies"`
	Errors          []RestoreError `json:"errors"`
	DryRun          bool           `json:"dryRun"`
}

// RestoreSummary provides a summary of the restore operation
type RestoreSummary struct {
	TotalPolicies int    `json:"totalPolicies"`
	CreatedCount  int    `json:"createdCount"`
	UpdatedCount  int    `json:"updatedCount"`
	SkippedCount  int    `json:"skippedCount"`
	ErrorCount    int    `json:"errorCount"`
	Duration      string `json:"duration"`
}

// PolicyResult represents the result of a policy operation
type PolicyResult struct {
	Name      string `json:"name"`
	Namespace string `json:"namespace"`
	Action    string `json:"action"`
	Reason    string `json:"reason,omitempty"`
}

// RestoreError represents an error during restore
type RestoreError struct {
	PolicyName string `json:"policyName"`
	Namespace  string `json:"namespace"`
	Error      string `json:"error"`
}

// BackupPolicies creates a backup of availability policies and related resources
func (b *BackupTools) BackupPolicies(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var backupParams BackupPoliciesParams
	if err := json.Unmarshal(params, &backupParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Set defaults
	if backupParams.Format == "" {
		backupParams.Format = "json"
	}

	// Validate format
	if backupParams.Format != "json" && backupParams.Format != "yaml" {
		return nil, fmt.Errorf("unsupported format: %s", backupParams.Format)
	}

	b.logger.Info("Starting policy backup", "namespaces", backupParams.Namespaces, "format", backupParams.Format)

	// Get cluster information
	clusterInfo, err := b.getClusterInfo(ctx, backupParams.Namespaces)
	if err != nil {
		return nil, fmt.Errorf("failed to get cluster info: %w", err)
	}

	// Backup availability policies
	policies, err := b.backupAvailabilityPolicies(ctx, backupParams.Namespaces)
	if err != nil {
		return nil, fmt.Errorf("failed to backup availability policies: %w", err)
	}

	backup := PolicyBackup{
		Metadata: BackupMetadata{
			CreatedAt:   time.Now(),
			Version:     "v1alpha1",
			ClusterInfo: clusterInfo,
		},
		AvailabilityPolicies: policies,
	}

	// Optionally backup deployments
	if backupParams.IncludeDeployments {
		deployments, err := b.backupDeployments(ctx, backupParams.Namespaces)
		if err != nil {
			return nil, fmt.Errorf("failed to backup deployments: %w", err)
		}
		backup.Deployments = deployments
	}

	// Optionally backup PDBs
	if backupParams.IncludePDBs {
		pdbs, err := b.backupPDBs(ctx, backupParams.Namespaces)
		if err != nil {
			return nil, fmt.Errorf("failed to backup PDBs: %w", err)
		}
		backup.PodDisruptionBudgets = pdbs
	}

	// Calculate backup statistics
	backup.Metadata.BackupStats = BackupStats{
		PoliciesCount:    len(backup.AvailabilityPolicies),
		DeploymentsCount: len(backup.Deployments),
		PDBsCount:        len(backup.PodDisruptionBudgets),
		NamespacesCount:  len(clusterInfo.Namespaces),
	}

	// Calculate size
	backupData, err := json.Marshal(backup)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal backup: %w", err)
	}
	backup.Metadata.BackupStats.SizeBytes = len(backupData)

	b.logger.Info("Policy backup completed",
		"policies", backup.Metadata.BackupStats.PoliciesCount,
		"deployments", backup.Metadata.BackupStats.DeploymentsCount,
		"pdbs", backup.Metadata.BackupStats.PDBsCount,
		"sizeBytes", backup.Metadata.BackupStats.SizeBytes)

	return &types.ToolResult{
		IsError: false,
		Content: backup,
	}, nil
}

// RestorePolicies restores availability policies from a backup
func (b *BackupTools) RestorePolicies(ctx context.Context, params json.RawMessage) (*types.ToolResult, error) {
	var restoreParams RestorePoliciesParams
	if err := json.Unmarshal(params, &restoreParams); err != nil {
		return nil, fmt.Errorf("invalid parameters: %w", err)
	}

	// Set defaults
	if restoreParams.OverwriteMode == "" {
		restoreParams.OverwriteMode = "skip"
	}

	startTime := time.Now()
	b.logger.Info("Starting policy restore", "dryRun", restoreParams.DryRun, "overwriteMode", restoreParams.OverwriteMode)

	// Parse backup data
	var backup PolicyBackup
	if err := json.Unmarshal(restoreParams.BackupData, &backup); err != nil {
		return nil, fmt.Errorf("failed to parse backup data: %w", err)
	}

	result := RestoreResult{
		DryRun:          restoreParams.DryRun,
		CreatedPolicies: []PolicyResult{},
		UpdatedPolicies: []PolicyResult{},
		SkippedPolicies: []PolicyResult{},
		Errors:          []RestoreError{},
	}

	// Filter policies by namespace if specified
	policiesToRestore := backup.AvailabilityPolicies
	if len(restoreParams.Namespaces) > 0 {
		policiesToRestore = b.filterPoliciesByNamespace(policiesToRestore, restoreParams.Namespaces)
	}

	// Restore each policy
	for _, policy := range policiesToRestore {
		err := b.restorePolicy(ctx, policy, restoreParams, &result)
		if err != nil {
			result.Errors = append(result.Errors, RestoreError{
				PolicyName: policy.Name,
				Namespace:  policy.Namespace,
				Error:      err.Error(),
			})
		}
	}

	duration := time.Since(startTime)
	result.Summary = RestoreSummary{
		TotalPolicies: len(policiesToRestore),
		CreatedCount:  len(result.CreatedPolicies),
		UpdatedCount:  len(result.UpdatedPolicies),
		SkippedCount:  len(result.SkippedPolicies),
		ErrorCount:    len(result.Errors),
		Duration:      duration.String(),
	}

	b.logger.Info("Policy restore completed",
		"duration", duration.String(),
		"created", result.Summary.CreatedCount,
		"updated", result.Summary.UpdatedCount,
		"skipped", result.Summary.SkippedCount,
		"errors", result.Summary.ErrorCount)

	return &types.ToolResult{
		IsError: false,
		Content: result,
	}, nil
}

func (b *BackupTools) getClusterInfo(ctx context.Context, namespaces []string) (ClusterInfo, error) {
	info := ClusterInfo{}

	// Get server version
	version, err := b.kubeClient.Discovery().ServerVersion()
	if err == nil {
		info.ServerVersion = version.GitVersion
	}

	// Get nodes count
	nodes, err := b.kubeClient.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err == nil {
		info.Nodes = len(nodes.Items)
	}

	// Set namespaces
	if len(namespaces) > 0 {
		info.Namespaces = namespaces
	} else {
		// Get all namespaces
		nsList, err := b.kubeClient.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err == nil {
			for _, ns := range nsList.Items {
				info.Namespaces = append(info.Namespaces, ns.Name)
			}
		}
	}

	return info, nil
}

func (b *BackupTools) backupAvailabilityPolicies(ctx context.Context, namespaces []string) ([]v1alpha1.AvailabilityPolicy, error) {
	var policies v1alpha1.AvailabilityPolicyList

	listOpts := []client.ListOption{}
	if len(namespaces) > 0 {
		for _, ns := range namespaces {
			var nsPolicies v1alpha1.AvailabilityPolicyList
			if err := b.client.List(ctx, &nsPolicies, client.InNamespace(ns)); err != nil {
				return nil, fmt.Errorf("failed to list policies in namespace %s: %w", ns, err)
			}
			policies.Items = append(policies.Items, nsPolicies.Items...)
		}
	} else {
		if err := b.client.List(ctx, &policies, listOpts...); err != nil {
			return nil, fmt.Errorf("failed to list policies: %w", err)
		}
	}

	// Sort policies by namespace and name for consistent output
	sort.Slice(policies.Items, func(i, j int) bool {
		if policies.Items[i].Namespace != policies.Items[j].Namespace {
			return policies.Items[i].Namespace < policies.Items[j].Namespace
		}
		return policies.Items[i].Name < policies.Items[j].Name
	})

	return policies.Items, nil
}

func (b *BackupTools) backupDeployments(ctx context.Context, namespaces []string) ([]appsv1.Deployment, error) {
	var deployments []appsv1.Deployment

	if len(namespaces) > 0 {
		for _, ns := range namespaces {
			depList, err := b.kubeClient.AppsV1().Deployments(ns).List(ctx, metav1.ListOptions{})
			if err != nil {
				return nil, fmt.Errorf("failed to list deployments in namespace %s: %w", ns, err)
			}
			deployments = append(deployments, depList.Items...)
		}
	} else {
		depList, err := b.kubeClient.AppsV1().Deployments("").List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to list deployments: %w", err)
		}
		deployments = depList.Items
	}

	return deployments, nil
}

func (b *BackupTools) backupPDBs(ctx context.Context, namespaces []string) ([]policyv1.PodDisruptionBudget, error) {
	var pdbs []policyv1.PodDisruptionBudget

	if len(namespaces) > 0 {
		for _, ns := range namespaces {
			pdbList, err := b.kubeClient.PolicyV1().PodDisruptionBudgets(ns).List(ctx, metav1.ListOptions{})
			if err != nil {
				return nil, fmt.Errorf("failed to list PDBs in namespace %s: %w", ns, err)
			}
			pdbs = append(pdbs, pdbList.Items...)
		}
	} else {
		pdbList, err := b.kubeClient.PolicyV1().PodDisruptionBudgets("").List(ctx, metav1.ListOptions{})
		if err != nil {
			return nil, fmt.Errorf("failed to list PDBs: %w", err)
		}
		pdbs = pdbList.Items
	}

	return pdbs, nil
}

func (b *BackupTools) filterPoliciesByNamespace(policies []v1alpha1.AvailabilityPolicy, namespaces []string) []v1alpha1.AvailabilityPolicy {
	nsMap := make(map[string]bool)
	for _, ns := range namespaces {
		nsMap[ns] = true
	}

	var filtered []v1alpha1.AvailabilityPolicy
	for _, policy := range policies {
		if nsMap[policy.Namespace] {
			filtered = append(filtered, policy)
		}
	}
	return filtered
}

func (b *BackupTools) restorePolicy(ctx context.Context, policy v1alpha1.AvailabilityPolicy, params RestorePoliciesParams, result *RestoreResult) error {
	// Check if policy already exists
	existingPolicy := &v1alpha1.AvailabilityPolicy{}
	err := b.client.Get(ctx, client.ObjectKey{
		Name:      policy.Name,
		Namespace: policy.Namespace,
	}, existingPolicy)

	policyExists := err == nil

	// Clean metadata for restore
	policy.ResourceVersion = ""
	policy.UID = ""
	policy.Generation = 0
	policy.CreationTimestamp = metav1.Time{}
	policy.Status = v1alpha1.AvailabilityPolicyStatus{}

	if !policyExists {
		// Create new policy
		if !params.DryRun {
			if err := b.client.Create(ctx, &policy); err != nil {
				return fmt.Errorf("failed to create policy: %w", err)
			}
		}
		result.CreatedPolicies = append(result.CreatedPolicies, PolicyResult{
			Name:      policy.Name,
			Namespace: policy.Namespace,
			Action:    "created",
		})
	} else {
		// Handle existing policy based on overwrite mode
		switch params.OverwriteMode {
		case "skip":
			result.SkippedPolicies = append(result.SkippedPolicies, PolicyResult{
				Name:      policy.Name,
				Namespace: policy.Namespace,
				Action:    "skipped",
				Reason:    "policy already exists",
			})
		case "overwrite":
			policy.ResourceVersion = existingPolicy.ResourceVersion
			if !params.DryRun {
				if err := b.client.Update(ctx, &policy); err != nil {
					return fmt.Errorf("failed to update policy: %w", err)
				}
			}
			result.UpdatedPolicies = append(result.UpdatedPolicies, PolicyResult{
				Name:      policy.Name,
				Namespace: policy.Namespace,
				Action:    "overwritten",
			})
		case "merge":
			// Merge specs (prefer backup data but keep existing metadata)
			existingPolicy.Spec = policy.Spec
			if !params.DryRun {
				if err := b.client.Update(ctx, existingPolicy); err != nil {
					return fmt.Errorf("failed to merge policy: %w", err)
				}
			}
			result.UpdatedPolicies = append(result.UpdatedPolicies, PolicyResult{
				Name:      policy.Name,
				Namespace: policy.Namespace,
				Action:    "merged",
			})
		}
	}

	return nil
}

// RegisterBackupTools registers backup and restore tools with the MCP server
func RegisterBackupTools(server interface{ RegisterTool(*types.Tool) error }, tools *BackupTools) error {
	backupTool := &types.Tool{
		Name:        "backup_policies",
		Description: "Create a backup of availability policies and related resources",
		InputSchema: func() json.RawMessage {
			schema := map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"namespaces": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string"},
						"description": "List of namespaces to backup (empty for all)",
					},
					"includeDeployments": map[string]interface{}{
						"type":        "boolean",
						"description": "Include deployments in the backup",
						"default":     false,
					},
					"includePDBs": map[string]interface{}{
						"type":        "boolean",
						"description": "Include Pod Disruption Budgets in the backup",
						"default":     false,
					},
					"format": map[string]interface{}{
						"type":        "string",
						"description": "Output format (json or yaml)",
						"enum":        []string{"json", "yaml"},
						"default":     "json",
					},
					"compressionEnabled": map[string]interface{}{
						"type":        "boolean",
						"description": "Enable compression for the backup",
						"default":     false,
					},
				},
			}
			data, _ := json.Marshal(schema)
			return data
		}(),
		Handler: tools.BackupPolicies,
	}

	restoreTool := &types.Tool{
		Name:        "restore_policies",
		Description: "Restore availability policies from a backup",
		InputSchema: func() json.RawMessage {
			schema := map[string]interface{}{
				"type":     "object",
				"required": []string{"backupData"},
				"properties": map[string]interface{}{
					"backupData": map[string]interface{}{
						"type":        "object",
						"description": "Backup data to restore from",
					},
					"dryRun": map[string]interface{}{
						"type":        "boolean",
						"description": "Perform a dry run without making changes",
						"default":     false,
					},
					"overwriteMode": map[string]interface{}{
						"type":        "string",
						"description": "How to handle existing policies",
						"enum":        []string{"skip", "overwrite", "merge"},
						"default":     "skip",
					},
					"namespaces": map[string]interface{}{
						"type":        "array",
						"items":       map[string]interface{}{"type": "string"},
						"description": "Restore only to these namespaces (empty for all)",
					},
				},
			}
			data, _ := json.Marshal(schema)
			return data
		}(),
		Handler: tools.RestorePolicies,
	}

	if err := server.RegisterTool(backupTool); err != nil {
		return fmt.Errorf("failed to register backup_policies tool: %w", err)
	}

	if err := server.RegisterTool(restoreTool); err != nil {
		return fmt.Errorf("failed to register restore_policies tool: %w", err)
	}

	return nil
}
