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

package metrics

import (
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/cache"
	"sigs.k8s.io/controller-runtime/pkg/metrics"
)

// CacheStats is a type alias for the cache package's CacheStats
type CacheStats = cache.CacheStats

var (
	// PDB lifecycle metrics
	PDBsCreated = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_pdbs_created_total",
			Help: "Total number of PDBs created by the operator",
		},
		[]string{"namespace", "availability_class", "component_function"},
	)

	PDBsUpdated = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_pdbs_updated_total",
			Help: "Total number of PDBs updated by the operator",
		},
		[]string{"namespace", "availability_class"},
	)

	PDBsDeleted = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_pdbs_deleted_total",
			Help: "Total number of PDBs deleted by the operator",
		},
		[]string{"namespace", "reason"},
	)

	ReconciliationDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "pdb_management_reconciliation_duration_seconds",
			Help:    "Duration of reconciliation in seconds",
			Buckets: []float64{0.001, 0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0},
		},
		[]string{"controller", "result"},
	)

	ReconciliationErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_reconciliation_errors_total",
			Help: "Total number of reconciliation errors",
		},
		[]string{"controller", "error_type"},
	)

	ManagedDeployments = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "pdb_management_deployments_managed",
			Help: "Current number of deployments being managed",
		},
		[]string{"namespace", "availability_class"},
	)

	PDBComplianceStatus = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "pdb_management_compliance_status",
			Help: "PDB compliance status (1=compliant, 0=non-compliant)",
		},
		[]string{"namespace", "deployment", "reason"},
	)

	AvailabilityPoliciesActive = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "pdb_management_policies_active",
			Help: "Number of active availability policies",
		},
		[]string{"namespace"},
	)

	MaintenanceWindowActive = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "pdb_management_maintenance_window_active",
			Help: "Whether a deployment is in maintenance window (1=yes, 0=no)",
		},
		[]string{"namespace", "deployment"},
	)

	// Operator health metrics
	OperatorInfo = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "pdb_management_operator_info",
			Help: "Operator information",
		},
		[]string{"version", "git_commit", "build_date"},
	)

	// Cache metrics
	CacheHits = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_cache_hits_total",
			Help: "Total number of cache hits",
		},
		[]string{"cache_type"},
	)

	CacheMisses = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_cache_misses_total",
			Help: "Total number of cache misses",
		},
		[]string{"cache_type"},
	)

	// Enforcement metrics
	PolicyEnforcementDecisions = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_enforcement_decisions_total",
			Help: "Total enforcement decisions by type and result",
		},
		[]string{"enforcement_mode", "decision", "namespace"},
	)

	OverrideAttempts = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_override_attempts_total",
			Help: "Total annotation override attempts",
		},
		[]string{"result", "reason", "namespace"},
	)

	// Policy metrics
	PolicyEvaluations = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_policy_evaluations_total",
			Help: "Total policy evaluations by enforcement mode",
		},
		[]string{"enforcement_mode", "namespace"},
	)

	PolicyConflicts = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "pdb_management_policy_conflicts_total",
			Help: "Total conflicts between policies and annotations",
		},
		[]string{"resolution", "enforcement_mode", "namespace"},
	)

	// Resource usage metrics
	ReconcileQueueLength = prometheus.NewGaugeFunc(
		prometheus.GaugeOpts{
			Name: "pdb_management_reconcile_queue_length",
			Help: "Length of the reconcile queue",
		},
		func() float64 {
			// This will be set by the controller
			return 0
		},
	)
)

func init() {
	// Register all metrics
	metrics.Registry.MustRegister(
		PDBsCreated,
		PDBsUpdated,
		PDBsDeleted,
		ReconciliationDuration,
		ReconciliationErrors,
		ManagedDeployments,
		PDBComplianceStatus,
		AvailabilityPoliciesActive,
		MaintenanceWindowActive,
		OperatorInfo,
		ReconcileQueueLength,
		CacheHits,
		CacheMisses,
		PolicyEnforcementDecisions,
		OverrideAttempts,
		PolicyEvaluations,
		PolicyConflicts,
	)

	// Set operator info (these should be set via build flags)
	OperatorInfo.WithLabelValues(
		getVersion(),
		getGitCommit(),
		getBuildDate(),
	).Set(1)
}

// Helper to record reconciliation metrics
func RecordReconciliation(controller string, duration time.Duration, err error) {
	result := "success"
	if err != nil {
		result = "error"
		ReconciliationErrors.WithLabelValues(controller, getErrorType(err)).Inc()
	}
	ReconciliationDuration.WithLabelValues(controller, result).Observe(duration.Seconds())
}

// Helper to track PDB creation
func RecordPDBCreated(namespace, availabilityClass, componentFunction string) {
	PDBsCreated.WithLabelValues(namespace, availabilityClass, componentFunction).Inc()
}

// Helper to track PDB updates
func RecordPDBUpdated(namespace, availabilityClass string) {
	PDBsUpdated.WithLabelValues(namespace, availabilityClass).Inc()
}

// Helper to track PDB deletion
func RecordPDBDeleted(namespace, reason string) {
	PDBsDeleted.WithLabelValues(namespace, reason).Inc()
}

// Helper to update managed deployments gauge
func UpdateManagedDeployments(counts map[string]map[string]int) {
	// Reset the gauge
	ManagedDeployments.Reset()

	for namespace, classCounts := range counts {
		for class, count := range classCounts {
			ManagedDeployments.WithLabelValues(namespace, class).Set(float64(count))
		}
	}
}

// Helper to update compliance status
func UpdateComplianceStatus(namespace, deployment string, compliant bool, reason string) {
	value := 0.0
	if compliant {
		value = 1.0
	}
	PDBComplianceStatus.WithLabelValues(namespace, deployment, reason).Set(value)
}

// Helper to update maintenance window status
func UpdateMaintenanceWindowStatus(namespace, deployment string, inWindow bool) {
	value := 0.0
	if inWindow {
		value = 1.0
	}
	MaintenanceWindowActive.WithLabelValues(namespace, deployment).Set(value)
}

// Helper to update active policies count
func UpdateActivePoliciesCount(counts map[string]int) {
	AvailabilityPoliciesActive.Reset()
	for namespace, count := range counts {
		AvailabilityPoliciesActive.WithLabelValues(namespace).Set(float64(count))
	}
}

// IncrementCacheHit increments the cache hit counter
func IncrementCacheHit(cacheType string) {
	CacheHits.WithLabelValues(cacheType).Inc()
}

// IncrementCacheMiss increments the cache miss counter
func IncrementCacheMiss(cacheType string) {
	CacheMisses.WithLabelValues(cacheType).Inc()
}

// UpdateCacheMetrics updates cache-related metrics
func UpdateCacheMetrics(stats CacheStats) {
	// This would update cache-specific gauges if we had them
	// For now, the hit/miss counters are sufficient
	// Could add cache size, eviction rate, etc. if needed
}

// RecordEnforcementDecision records a policy enforcement decision
func RecordEnforcementDecision(mode, decision, namespace string) {
	PolicyEnforcementDecisions.WithLabelValues(mode, decision, namespace).Inc()
}

// RecordOverrideAttempt records an annotation override attempt
func RecordOverrideAttempt(result, reason, namespace string) {
	OverrideAttempts.WithLabelValues(result, reason, namespace).Inc()
}

// RecordPolicyEvaluation records a policy evaluation
func RecordPolicyEvaluation(mode, namespace string) {
	PolicyEvaluations.WithLabelValues(mode, namespace).Inc()
}

// RecordPolicyConflict records a conflict between policy and annotation
func RecordPolicyConflict(resolution, mode, namespace string) {
	PolicyConflicts.WithLabelValues(resolution, mode, namespace).Inc()
}

// Helper functions
func getErrorType(err error) string {
	if err == nil {
		return "none"
	}

	errStr := err.Error()
	switch {
	case errStr == "conflict":
		return "conflict"
	case errStr == "not found":
		return "not_found"
	case errStr == "forbidden":
		return "forbidden"
	case errStr == "timeout":
		return "timeout"
	default:
		return "unknown"
	}
}

// These should be set during build using ldflags
var (
	version   = "dev"
	gitCommit = "unknown"
	buildDate = "unknown"
)

func getVersion() string {
	return version
}

func getGitCommit() string {
	return gitCommit
}

func getBuildDate() string {
	if buildDate == "unknown" {
		return time.Now().Format(time.RFC3339)
	}
	return buildDate
}
