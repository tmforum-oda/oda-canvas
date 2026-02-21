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

package controller

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"go.opentelemetry.io/otel/attribute"

	appsv1 "k8s.io/api/apps/v1"
	policyv1 "k8s.io/api/policy/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	"github.com/go-logr/logr"
	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/cache"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/events"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/logging"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/metrics"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/tracing"
)

const (
	// ODA Canvas annotation keys
	AnnotationAvailabilityClass = "oda.tmforum.org/availability-class"
	AnnotationMaintenanceWindow = "oda.tmforum.org/maintenance-window"
	AnnotationComponentFunction = "oda.tmforum.org/component-function"
	AnnotationComponentName     = "oda.tmforum.org/componentName"
	AnnotationOverrideReason    = "oda.tmforum.org/override-reason"

	// Labels and annotations for PDBs
	LabelManagedBy         = "oda.tmforum.org/managed-by"
	LabelComponent         = "oda.tmforum.org/component"
	LabelFunction          = "oda.tmforum.org/function"
	LabelAvailabilityClass = "oda.tmforum.org/availability-class"

	AnnotationCreatedBy    = "oda.tmforum.org/created-by"
	AnnotationCreationTime = "oda.tmforum.org/creation-time"
	AnnotationLastModified = "oda.tmforum.org/last-modified"
	AnnotationDescription  = "oda.tmforum.org/description"
	AnnotationPolicySource = "oda.tmforum.org/policy-source"
	AnnotationEnforcement  = "oda.tmforum.org/enforcement-mode"

	// Finalizers
	FinalizerPDBCleanup = "oda.tmforum.org/pdb-cleanup"

	// Default values
	DefaultPDBSuffix = "-pdb"
	OperatorName     = "pdb-management"

	// Reconciliation rate limiting
	DefaultRequeueDelay = 30 * time.Second
)

// SharedConfig holds shared configuration for controllers
type SharedConfig struct {
	PolicyCache             *cache.PolicyCache
	MaxConcurrentReconciles int
}

// DeploymentReconciler reconciles a Deployment object
type DeploymentReconciler struct {
	client.Client
	Scheme      *runtime.Scheme
	Recorder    record.EventRecorder
	Events      *events.EventRecorder
	PolicyCache *cache.PolicyCache
	Config      *SharedConfig

	// Change detection to avoid unnecessary reconciliations
	lastDeploymentState map[types.NamespacedName]string
	mu                  sync.RWMutex
}

// AvailabilityConfig holds the configuration for a deployment's availability requirements
type AvailabilityConfig struct {
	AvailabilityClass availabilityv1alpha1.AvailabilityClass
	ComponentFunction availabilityv1alpha1.ComponentFunction
	MinAvailable      intstr.IntOrString
	Description       string
	MaintenanceWindow string
	Source            string // "annotation", "policy", etc.
	PolicyName        string // Name of the policy if from policy
	Enforcement       string // Enforcement mode if from policy
}

// +kubebuilder:rbac:groups="",resources=namespaces,verbs=get;list;watch
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;update;patch
// +kubebuilder:rbac:groups=policy,resources=poddisruptionbudgets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=availability.oda.tmforum.org,resources=availabilitypolicies,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// Reconcile handles Deployment changes and manages corresponding PDBs
// Reconcile handles Deployment changes and manages corresponding PDBs
func (r *DeploymentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	// Start timing for metrics
	startTime := time.Now()

	// Start tracing span - this creates the trace context
	ctx, span := tracing.ReconcileSpan(ctx, "deployment", req.Namespace, req.Name)
	defer span.End()

	// Generate IDs with controller prefixes
	reconcileID := "deployment-" + uuid.New().String()
	correlationID := uuid.New().String()

	// Add IDs to span
	span.SetAttributes(
		attribute.String("reconcile.id", reconcileID),
		attribute.String("correlation.id", correlationID),
	)

	// Create unified logger with clean, structured logging
	logger := logging.CreateUnifiedLogger(ctx,
		"deployment-pdb",        // controllerType
		"deployment-controller", // controllerName
		"apps",                  // group
		"Deployment",            // kind
		"deployment",            // resourceType
		req.Name,                // name
		req.Namespace,           // namespace
		reconcileID,             // reconcileID
		correlationID,           // correlationID
	)

	// Ensure we record metrics and audit at the end
	var reconcileErr error
	defer func() {
		duration := time.Since(startTime)
		metrics.RecordReconciliation("deployment", duration, reconcileErr)

		// Record tracing error if any
		if reconcileErr != nil {
			tracing.RecordError(span, reconcileErr, "Reconciliation failed")
		}

		// Audit the reconciliation using unified logger
		result := logging.AuditResultSuccess
		if reconcileErr != nil {
			result = logging.AuditResultFailure
		}
		logger.Audit(
			"RECONCILE",
			fmt.Sprintf("%s/%s", req.Namespace, req.Name),
			"deployment",
			req.Namespace,
			req.Name,
			result,
			map[string]interface{}{
				"controller": "deployment",
				"duration":   duration.String(),
				"durationMs": duration.Milliseconds(),
			},
		)

		logger.Info("Reconciliation completed", map[string]any{
			"duration": duration.String(),
			//"reconcileID": reconcileID,
		})
	}()

	// Add tracing event with reconcile ID
	tracing.AddEvent(ctx, "FetchingDeployment",
		attribute.String("reconcile.id", reconcileID),
	)

	// Fetch the Deployment
	deployment := &appsv1.Deployment{}
	if err := r.Get(ctx, req.NamespacedName, deployment); err != nil {
		if errors.IsNotFound(err) {
			logger.Info("Deployment not found, ignoring since object must be deleted", map[string]any{})
			return ctrl.Result{}, nil
		}
		reconcileErr = err
		logger.Error(err, "Failed to get deployment", map[string]any{})
		return ctrl.Result{}, err
	}

	// Handle deletion
	if deployment.DeletionTimestamp != nil {
		logger.Info("Deployment is being deleted", map[string]any{})

		// Clear cached state for this deployment
		r.clearDeploymentState(deployment)

		// Add deletion event to span
		tracing.AddEvent(ctx, "DeletingPDB")

		return r.handleDeletion(ctx, deployment, logger.ToLogr())
	}

	// Check replicas
	replicas := int32(1)
	if deployment.Spec.Replicas != nil {
		replicas = *deployment.Spec.Replicas
	}
	if replicas < 2 {
		logger.Info("Single replica, no PDB required", map[string]any{
			"replicas": replicas,
		})

		// Add event to span
		tracing.AddEvent(ctx, "SkippedPDB",
			attribute.String("reason", "insufficient_replicas"),
			attribute.Int("replicas", int(replicas)),
		)

		// Record event
		if r.Events != nil {
			r.Events.DeploymentSkipped(deployment, deployment.Name, "insufficient replicas")
		}

		// Update compliance status
		metrics.UpdateComplianceStatus(
			deployment.Namespace,
			deployment.Name,
			false,
			"insufficient_replicas",
		)

		return ctrl.Result{}, nil
	}

	// Find matching availability policy
	// Add policy evaluation event
	tracing.AddEvent(ctx, "EvaluatingPolicies")

	// Get availability configuration using the new method
	config, err := r.getAvailabilityConfigWithCache(ctx, deployment, logger.ToLogr())
	if err != nil {
		reconcileErr = err
		logger.Error(err, "Failed to get availability configuration", map[string]any{})
		return ctrl.Result{}, err
	}

	if config == nil {
		logger.Info("No availability configuration found, skipping PDB", map[string]any{})

		// Add skip event to span
		tracing.AddEvent(ctx, "SkippedPDB",
			attribute.String("reason", "no_availability_configuration"),
		)

		// Record event
		if r.Events != nil {
			r.Events.DeploymentUnmanaged(deployment, deployment.Name, "no availability configuration")
		}

		return ctrl.Result{}, nil
	}

	// ** Check if deployment state has changed **
	stateChanged, err := r.hasDeploymentStateChanged(ctx, deployment, config)
	if err != nil {
		// On error, log but continue processing to be safe
		logger.Error(err, "Failed to check deployment state changes, proceeding with reconciliation", map[string]any{})
		stateChanged = true
	}

	// Debug logging to understand change detection
	logger.Info("Change detection result", map[string]any{
		"stateChanged": stateChanged,
		"deployment":   deployment.Name,
		"namespace":    deployment.Namespace,
		"generation":   deployment.Generation,
		"debug":        true,
	})

	// Additional debug: Check if PDB exists currently
	pdbName := types.NamespacedName{
		Name:      deployment.Name + DefaultPDBSuffix,
		Namespace: deployment.Namespace,
	}
	currentPDB := &policyv1.PodDisruptionBudget{}
	pdbExists := r.Get(ctx, pdbName, currentPDB) == nil

	logger.Info("PDB existence check", map[string]any{
		"pdbName":   pdbName.Name,
		"pdbExists": pdbExists,
		"debug":     true,
	})

	if !stateChanged {
		logger.Info("Skipping reconciliation - no state change detected", map[string]any{
			"availabilityClass": string(config.AvailabilityClass),
			"source":            config.Source,
			"policyName":        config.PolicyName,
			"reason":            "no_state_change",
			"optimized":         true,
		})

		// Add skip event to span
		tracing.AddEvent(ctx, "SkippedPDB",
			attribute.String("reason", "no_state_change"),
		)

		return ctrl.Result{}, nil
	}

	logger.Info("Using availability configuration", map[string]any{
		"availabilityClass": string(config.AvailabilityClass),
		"source":            config.Source,
		"policyName":        config.PolicyName,
		"stateChanged":      stateChanged,
	})

	// Add configuration information to span
	span.SetAttributes(
		attribute.String("config.source", config.Source),
		attribute.String("config.policy_name", config.PolicyName),
	)

	// Now proceed with PDB creation/update
	// Add PDB reconciliation event
	tracing.AddEvent(ctx, "ReconcilingPDB",
		attribute.String("availability_class", string(config.AvailabilityClass)),
		attribute.String("source", config.Source),
	)

	// Ensure finalizer is present for cleanup
	if !controllerutil.ContainsFinalizer(deployment, FinalizerPDBCleanup) {
		patch := client.MergeFrom(deployment.DeepCopy())
		controllerutil.AddFinalizer(deployment, FinalizerPDBCleanup)
		if err := r.Patch(ctx, deployment, patch); err != nil {
			reconcileErr = err
			logger.Error(err, "Failed to add finalizer", map[string]any{})
			return ctrl.Result{}, err
		}
		logger.Info("Added finalizer for PDB cleanup", map[string]any{})

		// After adding finalizer, we need to update our cached state since the deployment changed
		// Return early to let the next reconciliation handle the PDB logic with the updated deployment
		return ctrl.Result{Requeue: true}, nil
	}

	result, err := r.reconcilePDB(ctx, deployment, config, log.FromContext(ctx))
	if err != nil {
		reconcileErr = err
		// If PDB creation/update fails, requeue with backoff
		logger.Error(err, "PDB reconciliation failed, will retry", map[string]any{})
		return ctrl.Result{RequeueAfter: DefaultRequeueDelay}, err
	}

	// Update metrics
	metrics.ManagedDeployments.WithLabelValues(
		deployment.Namespace,
		string(config.AvailabilityClass),
	).Set(1)

	// Update compliance status
	metrics.UpdateComplianceStatus(
		deployment.Namespace,
		deployment.Name,
		true,
		"managed",
	)

	// ** Update deployment state after successful reconciliation **
	if err := r.updateDeploymentState(ctx, deployment, config); err != nil {
		logger.Error(err, "Failed to update deployment state cache", map[string]any{})
		// Don't fail the reconciliation for this, just log
	} else {
		logger.Info("Updated deployment state cache", map[string]any{
			"deployment": deployment.Name,
			"namespace":  deployment.Namespace,
			"debug":      true,
		})
	}

	logger.Info("Successfully reconciled PDB", map[string]any{
		"availabilityClass": config.AvailabilityClass,
		"source":            config.Source,
		"reconcileID":       reconcileID,
	})

	return result, nil
}

// getAvailabilityConfigWithCache gets configuration with the new priority logic
func (r *DeploymentReconciler) getAvailabilityConfigWithCache(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) (*AvailabilityConfig, error) {
	// ** FIRST: Check for invalid configuration **
	if invalidClass := r.detectInvalidConfiguration(deployment); invalidClass != "" {
		err := fmt.Errorf("invalid availability class: %s", invalidClass)
		logger.Error(err, "Invalid configuration detected", "class", invalidClass)

		// Record the proper event for invalid configuration
		if r.Events != nil {
			r.Events.InvalidConfiguration(deployment, fmt.Sprintf("invalid availability class: %s", invalidClass))
		}

		return nil, err
	}

	// Get both configurations
	annotationConfig := r.getConfigFromAnnotations(deployment, logger)
	policyConfig, matchedPolicy, err := r.getConfigFromPolicyWithCacheAndPolicy(ctx, deployment, logger)
	if err != nil {
		return nil, err
	}

	// Apply resolution logic based on enforcement
	finalConfig := r.resolveConfiguration(ctx, deployment, annotationConfig, policyConfig, matchedPolicy, logger)

	if finalConfig == nil {
		logger.V(1).Info("No availability configuration found")
		return nil, nil
	}

	return finalConfig, nil
}

// detectInvalidConfiguration checks for invalid availability class annotations
func (r *DeploymentReconciler) detectInvalidConfiguration(deployment *appsv1.Deployment) string {
	annotations := deployment.Annotations
	if annotations == nil {
		return ""
	}

	// Check for ODA Canvas annotation
	if class, exists := annotations[AnnotationAvailabilityClass]; exists {
		odaClass := availabilityv1alpha1.AvailabilityClass(class)
		if !r.isValidAvailabilityClass(odaClass) {
			return class
		}
	}

	return ""
}

// getConfigFromAnnotations extracts availability configuration from deployment annotations
func (r *DeploymentReconciler) getConfigFromAnnotations(deployment *appsv1.Deployment, logger logr.Logger) *AvailabilityConfig {
	annotations := deployment.Annotations
	if annotations == nil {
		return nil
	}

	// Check for ODA Canvas annotation
	availabilityClass, exists := annotations[AnnotationAvailabilityClass]
	if !exists {
		return nil
	}

	// Parse availability class
	odaClass := availabilityv1alpha1.AvailabilityClass(availabilityClass)
	if !r.isValidAvailabilityClass(odaClass) {
		logger.Error(fmt.Errorf("invalid availability class"),
			"Unsupported availability class", "class", availabilityClass)
		return nil
	}

	// Get component function
	componentFunction := availabilityv1alpha1.ComponentFunction(annotations[AnnotationComponentFunction])
	if componentFunction == "" {
		componentFunction = availabilityv1alpha1.CoreFunction // default
	}

	// Calculate MinAvailable
	minAvailable := availabilityv1alpha1.GetMinAvailableForClass(odaClass, componentFunction)

	return &AvailabilityConfig{
		AvailabilityClass: odaClass,
		ComponentFunction: componentFunction,
		MinAvailable:      minAvailable,
		Description:       r.getDescriptionForClass(odaClass),
		MaintenanceWindow: annotations[AnnotationMaintenanceWindow],
		Source:            "oda-annotation",
	}
}

// getConfigFromPolicyWithCacheAndPolicy gets policy config AND the policy itself
func (r *DeploymentReconciler) getConfigFromPolicyWithCacheAndPolicy(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) (*AvailabilityConfig, *availabilityv1alpha1.AvailabilityPolicy, error) {
	// Try cache first
	cacheKey := "all-policies"

	var policies []availabilityv1alpha1.AvailabilityPolicy
	if r.PolicyCache != nil {
		if cachedPolicies, found := r.PolicyCache.GetList(cacheKey); found {
			logger.V(2).Info("Using cached policies", "cacheHit", true)
			metrics.IncrementCacheHit("policy")
			policies = cachedPolicies
		} else {
			// Cache miss - fetch from API
			logger.V(2).Info("Policy cache miss, fetching from API")
			metrics.IncrementCacheMiss("policy")

			policyList := &availabilityv1alpha1.AvailabilityPolicyList{}
			if err := r.List(ctx, policyList); err != nil {
				return nil, nil, err
			}

			policies = policyList.Items

			// Cache for next time
			r.PolicyCache.SetList(cacheKey, policies)
		}
	} else {
		// No cache configured, fetch directly
		policyList := &availabilityv1alpha1.AvailabilityPolicyList{}
		if err := r.List(ctx, policyList); err != nil {
			return nil, nil, err
		}
		policies = policyList.Items
	}

	// Find best matching policy with deterministic tie-breaking
	var bestMatch *availabilityv1alpha1.AvailabilityPolicy
	var highestPriority int32 = -1
	var matchingPolicies []*availabilityv1alpha1.AvailabilityPolicy

	for i := range policies {
		policy := &policies[i]
		if r.policyMatchesDeployment(policy, deployment) {
			matchingPolicies = append(matchingPolicies, policy)
			if policy.Spec.Priority > highestPriority {
				bestMatch = policy
				highestPriority = policy.Spec.Priority
			} else if policy.Spec.Priority == highestPriority && bestMatch != nil {
				// Deterministic tie-breaking: alphabetically by namespace/name
				currentKey := fmt.Sprintf("%s/%s", bestMatch.Namespace, bestMatch.Name)
				candidateKey := fmt.Sprintf("%s/%s", policy.Namespace, policy.Name)
				if candidateKey < currentKey {
					bestMatch = policy
				}
			}
		}
	}

	if bestMatch == nil {
		return nil, nil, nil
	}

	// Log conflict detection if multiple policies match
	if len(matchingPolicies) > 1 {
		r.logPolicyConflicts(ctx, deployment, matchingPolicies, bestMatch, logger)
	}

	logger.Info("Found matching AvailabilityPolicy",
		"policy", bestMatch.Name,
		"priority", bestMatch.Spec.Priority,
		"enforcement", bestMatch.Spec.GetEnforcement(),
		"fromCache", r.PolicyCache != nil,
		"totalMatchingPolicies", len(matchingPolicies))

	// Convert policy to config
	componentFunction := r.inferComponentFunction(deployment)
	minAvailable := availabilityv1alpha1.GetMinAvailableForClass(bestMatch.Spec.AvailabilityClass, componentFunction)

	// Use custom PDB config if specified
	if bestMatch.Spec.AvailabilityClass == availabilityv1alpha1.Custom && bestMatch.Spec.CustomPDBConfig != nil {
		if bestMatch.Spec.CustomPDBConfig.MinAvailable != nil {
			minAvailable = *bestMatch.Spec.CustomPDBConfig.MinAvailable
		}
	}

	config := &AvailabilityConfig{
		AvailabilityClass: bestMatch.Spec.AvailabilityClass,
		ComponentFunction: componentFunction,
		MinAvailable:      minAvailable,
		Description:       r.getDescriptionForClass(bestMatch.Spec.AvailabilityClass),
		Source:            "policy",
		PolicyName:        bestMatch.Name,
		Enforcement:       string(bestMatch.Spec.GetEnforcement()),
	}

	return config, bestMatch, nil
}

// resolveConfiguration implements the best practice priority logic
func (r *DeploymentReconciler) resolveConfiguration(
	ctx context.Context,
	deployment *appsv1.Deployment,
	annotationConfig *AvailabilityConfig,
	policyConfig *AvailabilityConfig,
	policy *availabilityv1alpha1.AvailabilityPolicy,
	logger logr.Logger,
) *AvailabilityConfig {

	// Case 1: No policy found
	if policyConfig == nil {
		if annotationConfig != nil {
			logger.V(2).Info("Using annotation-based configuration (no policy found)")
			annotationConfig.Source = "annotation-no-policy"
		}
		return annotationConfig
	}

	// Case 2: Policy exists
	enforcement := policy.Spec.GetEnforcement()

	// Log the resolution process
	logger.Info("Resolving configuration",
		"hasAnnotation", annotationConfig != nil,
		"hasPolicy", true,
		"enforcement", enforcement,
		"policyClass", policyConfig.AvailabilityClass,
		"annotationClass", func() string {
			if annotationConfig != nil {
				return string(annotationConfig.AvailabilityClass)
			}
			return "none"
		}())

	// Record enforcement decision metric
	metrics.RecordEnforcementDecision(string(enforcement), "processing", deployment.Namespace)

	switch enforcement {
	case availabilityv1alpha1.EnforcementStrict:
		// Policy always wins
		logger.V(1).Info("Strict enforcement: using policy configuration",
			"policy", policy.Name)

		// Record event if annotation was overridden
		if annotationConfig != nil {
			r.Events.Warnf(deployment, "PolicyEnforced",
				"Annotation override blocked by strict policy %s", policy.Name)

			metrics.RecordOverrideAttempt("blocked", "strict-enforcement", deployment.Namespace)

			// Audit override attempt - NO DUPLICATES
			auditLogger := logging.NewStructuredLogger(ctx)
			auditLogger.AuditStructured(
				"OVERRIDE_BLOCKED",
				deployment.Name,
				"Deployment",
				deployment.Namespace,
				deployment.Name,
				logging.AuditResultSuccess,
				map[string]interface{}{
					"policy":          policy.Name,
					"policyClass":     policyConfig.AvailabilityClass,
					"annotationClass": annotationConfig.AvailabilityClass,
					"enforcement":     "strict",
				},
			)
		}

		policyConfig.Source = "policy-strict"
		metrics.RecordEnforcementDecision(string(enforcement), "policy-wins", deployment.Namespace)
		return policyConfig

	case availabilityv1alpha1.EnforcementFlexible:
		// Allow annotation only if it's higher than policy
		if annotationConfig == nil {
			logger.V(1).Info("Flexible enforcement: using policy (no annotation)")
			policyConfig.Source = "policy-flexible"
			metrics.RecordEnforcementDecision(string(enforcement), "policy-no-annotation", deployment.Namespace)
			return policyConfig
		}

		// Check minimum class if specified
		minimumClass := policy.Spec.MinimumClass
		if minimumClass == "" {
			minimumClass = policy.Spec.AvailabilityClass
		}

		// Compare annotation against minimum
		comparison := availabilityv1alpha1.CompareAvailabilityClasses(
			annotationConfig.AvailabilityClass, minimumClass)

		if comparison >= 0 {
			// Annotation meets or exceeds minimum
			logger.Info("Flexible enforcement: annotation accepted",
				"annotationClass", annotationConfig.AvailabilityClass,
				"minimumClass", minimumClass)

			r.Events.Infof(deployment, "AnnotationAccepted",
				"Annotation %s meets minimum requirement %s",
				annotationConfig.AvailabilityClass, minimumClass)

			metrics.RecordOverrideAttempt("accepted", "meets-minimum", deployment.Namespace)
			metrics.RecordEnforcementDecision(string(enforcement), "annotation-accepted", deployment.Namespace)

			annotationConfig.Source = "annotation-flexible"
			annotationConfig.PolicyName = policy.Name
			annotationConfig.Enforcement = string(enforcement)
			return annotationConfig
		} else {
			// Annotation below minimum
			logger.V(1).Info("Flexible enforcement: annotation below minimum",
				"annotationClass", annotationConfig.AvailabilityClass,
				"minimumClass", minimumClass,
				"using", minimumClass)

			r.Events.Warnf(deployment, "BelowMinimum",
				"Annotation %s below minimum %s, using %s",
				annotationConfig.AvailabilityClass, minimumClass, minimumClass)

			metrics.RecordOverrideAttempt("rejected", "below-minimum", deployment.Namespace)
			metrics.RecordEnforcementDecision(string(enforcement), "minimum-enforced", deployment.Namespace)

			// Use minimum class
			policyConfig.AvailabilityClass = minimumClass
			policyConfig.MinAvailable = availabilityv1alpha1.GetMinAvailableForClass(
				minimumClass, policyConfig.ComponentFunction)
			policyConfig.Source = "policy-flexible-minimum"
			return policyConfig
		}

	case availabilityv1alpha1.EnforcementAdvisory:
		// Current behavior - annotation wins if present
		if annotationConfig != nil {
			// Check if override is allowed
			if policy.Spec.AllowOverride != nil && !*policy.Spec.AllowOverride {
				logger.V(1).Info("Advisory policy does not allow override")
				metrics.RecordOverrideAttempt("blocked", "override-not-allowed", deployment.Namespace)
				policyConfig.Source = "policy-advisory-no-override"
				return policyConfig
			}

			// Check if override requires specific annotation
			if policy.Spec.OverrideRequiresAnnotation != "" {
				if deployment.Annotations == nil ||
					deployment.Annotations[policy.Spec.OverrideRequiresAnnotation] == "" {
					logger.V(1).Info("Override requires annotation",
						"required", policy.Spec.OverrideRequiresAnnotation)

					r.Events.Warnf(deployment, "OverrideRequiresAnnotation",
						"Override requires annotation %s",
						policy.Spec.OverrideRequiresAnnotation)

					metrics.RecordOverrideAttempt("blocked", "missing-required-annotation", deployment.Namespace)
					policyConfig.Source = "policy-advisory-missing-annotation"
					return policyConfig
				}
			}

			// Check if override requires reason
			if policy.Spec.OverrideRequiresReason != nil && *policy.Spec.OverrideRequiresReason {
				if deployment.Annotations == nil || deployment.Annotations[AnnotationOverrideReason] == "" {
					logger.V(1).Info("Override requires reason annotation")

					r.Events.Warnf(deployment, "OverrideRequiresReason",
						"Override requires reason in annotation %s", AnnotationOverrideReason)

					metrics.RecordOverrideAttempt("blocked", "missing-reason", deployment.Namespace)
					policyConfig.Source = "policy-advisory-missing-reason"
					return policyConfig
				}

				// Log the override reason
				logger.Info("Annotation override allowed",
					"reason", deployment.Annotations[AnnotationOverrideReason])

				// Audit the override with reason - NO DUPLICATES
				auditLogger := logging.NewStructuredLogger(ctx)
				auditLogger.AuditStructured(
					"OVERRIDE_ALLOWED",
					deployment.Name,
					"Deployment",
					deployment.Namespace,
					deployment.Name,
					logging.AuditResultSuccess,
					map[string]interface{}{
						"policy":          policy.Name,
						"policyClass":     policyConfig.AvailabilityClass,
						"annotationClass": annotationConfig.AvailabilityClass,
						"enforcement":     "advisory",
						"reason":          deployment.Annotations[AnnotationOverrideReason],
					},
				)
			}

			logger.V(1).Info("Advisory enforcement: using annotation")
			metrics.RecordOverrideAttempt("accepted", "advisory-mode", deployment.Namespace)
			metrics.RecordEnforcementDecision(string(enforcement), "annotation-wins", deployment.Namespace)

			annotationConfig.Source = "annotation-advisory"
			annotationConfig.PolicyName = policy.Name
			annotationConfig.Enforcement = string(enforcement)
			return annotationConfig
		}

		logger.V(1).Info("Advisory enforcement: using policy (no annotation)")
		policyConfig.Source = "policy-advisory"
		metrics.RecordEnforcementDecision(string(enforcement), "policy-no-annotation", deployment.Namespace)
		return policyConfig

	default:
		// Unknown enforcement, default to policy
		logger.V(1).Info("Unknown enforcement mode, defaulting to policy",
			"enforcement", enforcement)
		policyConfig.Source = "policy-default"
		metrics.RecordEnforcementDecision("unknown", "defaulting-to-policy", deployment.Namespace)
		return policyConfig
	}
}

// policyMatchesDeployment checks if a policy matches a deployment
func (r *DeploymentReconciler) policyMatchesDeployment(policy *availabilityv1alpha1.AvailabilityPolicy, deployment *appsv1.Deployment) bool {
	selector := policy.Spec.ComponentSelector

	// Check namespace
	if len(selector.Namespaces) > 0 {
		namespaceMatch := false
		for _, ns := range selector.Namespaces {
			if ns == deployment.Namespace {
				namespaceMatch = true
				break
			}
		}
		if !namespaceMatch {
			return false
		}
	}

	// Check component names
	if len(selector.ComponentNames) > 0 {
		componentName := ""
		if deployment.Annotations != nil {
			componentName = deployment.Annotations[AnnotationComponentName]
		}
		if componentName == "" {
			componentName = deployment.Name // fallback to deployment name
		}

		nameMatch := false
		for _, name := range selector.ComponentNames {
			if name == componentName {
				nameMatch = true
				break
			}
		}
		if !nameMatch {
			return false
		}
	}

	// Check component functions
	if len(selector.ComponentFunctions) > 0 {
		deploymentFunction := availabilityv1alpha1.CoreFunction // default
		if deployment.Annotations != nil {
			if function := deployment.Annotations[AnnotationComponentFunction]; function != "" {
				deploymentFunction = availabilityv1alpha1.ComponentFunction(function)
			}
		}

		functionMatch := false
		for _, function := range selector.ComponentFunctions {
			if function == deploymentFunction {
				functionMatch = true
				break
			}
		}
		if !functionMatch {
			return false
		}
	}

	// Check match labels
	if len(selector.MatchLabels) > 0 {
		deploymentLabels := deployment.Labels
		if deploymentLabels == nil {
			return false
		}

		for key, value := range selector.MatchLabels {
			if deploymentLabels[key] != value {
				return false
			}
		}
	}

	// Check match expressions
	if len(selector.MatchExpressions) > 0 {
		for _, expr := range selector.MatchExpressions {
			if !r.evaluateMatchExpression(expr, deployment.Labels) {
				return false
			}
		}
	}

	return true
}

// evaluateMatchExpression evaluates a single match expression against labels
func (r *DeploymentReconciler) evaluateMatchExpression(expr metav1.LabelSelectorRequirement, labels map[string]string) bool {
	value, exists := labels[expr.Key]

	switch expr.Operator {
	case metav1.LabelSelectorOpIn:
		if !exists {
			return false
		}
		for _, v := range expr.Values {
			if value == v {
				return true
			}
		}
		return false

	case metav1.LabelSelectorOpNotIn:
		if !exists {
			return true
		}
		for _, v := range expr.Values {
			if value == v {
				return false
			}
		}
		return true

	case metav1.LabelSelectorOpExists:
		return exists

	case metav1.LabelSelectorOpDoesNotExist:
		return !exists

	default:
		return false
	}
}

// logPolicyConflicts logs when multiple policies match a deployment
func (r *DeploymentReconciler) logPolicyConflicts(
	ctx context.Context,
	deployment *appsv1.Deployment,
	matchingPolicies []*availabilityv1alpha1.AvailabilityPolicy,
	selected *availabilityv1alpha1.AvailabilityPolicy,
	logger logr.Logger,
) {
	// Count policies at the same priority as selected
	samePriorityCount := 0
	policyNames := make([]string, 0, len(matchingPolicies))
	for _, p := range matchingPolicies {
		policyNames = append(policyNames, fmt.Sprintf("%s/%s", p.Namespace, p.Name))
		if p.Spec.Priority == selected.Spec.Priority {
			samePriorityCount++
		}
	}

	// Record metrics for multi-policy match
	metrics.RecordMultiPolicyMatch(deployment.Namespace, len(matchingPolicies))

	if samePriorityCount > 1 {
		// Multiple policies at same priority - potential conflict requiring tie-break
		metrics.RecordPolicyTieBreak(deployment.Namespace, "alphabetical")

		logger.Info("Multiple policies match deployment at same priority, using tie-break",
			"deployment", deployment.Name,
			"matchingPolicies", policyNames,
			"selectedPolicy", fmt.Sprintf("%s/%s", selected.Namespace, selected.Name),
			"priority", selected.Spec.Priority,
			"tieBreakReason", "alphabetical",
		)

		// Record event on deployment
		if r.Events != nil {
			r.Events.Warnf(deployment, "PolicyConflict",
				"Multiple policies (%d) match at priority %d, selected %s via alphabetical tie-break",
				samePriorityCount, selected.Spec.Priority, selected.Name)
		}
	} else {
		// Multiple policies but clear priority winner
		logger.V(1).Info("Multiple policies match deployment, selected by priority",
			"deployment", deployment.Name,
			"matchingPolicies", policyNames,
			"selectedPolicy", fmt.Sprintf("%s/%s", selected.Namespace, selected.Name),
			"selectedPriority", selected.Spec.Priority,
		)
	}
}

// handleDeletion handles the deletion of a deployment
func (r *DeploymentReconciler) handleDeletion(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) (ctrl.Result, error) {
	logger.Info("Handling deployment deletion")

	// Clean up PDB if it exists
	if err := r.cleanupPDB(ctx, deployment, logger); err != nil {
		logger.Error(err, "Failed to cleanup PDB during deletion")
		return ctrl.Result{}, err
	}

	// Remove finalizer
	if err := r.removeFinalizer(ctx, deployment, logger); err != nil {
		logger.Error(err, "Failed to remove finalizer during deletion")
		return ctrl.Result{}, err
	}

	return ctrl.Result{}, nil
}

// removeFinalizer removes the PDB cleanup finalizer from a deployment
func (r *DeploymentReconciler) removeFinalizer(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) error {
	if !controllerutil.ContainsFinalizer(deployment, FinalizerPDBCleanup) {
		return nil
	}

	patch := client.MergeFrom(deployment.DeepCopy())
	controllerutil.RemoveFinalizer(deployment, FinalizerPDBCleanup)

	if err := r.Patch(ctx, deployment, patch); err != nil {
		if errors.IsNotFound(err) {
			return nil
		}
		// Handle conflict by fetching latest and retrying
		if errors.IsConflict(err) {
			latestDeployment := &appsv1.Deployment{}
			if err := r.Get(ctx, types.NamespacedName{
				Name:      deployment.Name,
				Namespace: deployment.Namespace,
			}, latestDeployment); err != nil {
				return err
			}

			patch := client.MergeFrom(latestDeployment.DeepCopy())
			controllerutil.RemoveFinalizer(latestDeployment, FinalizerPDBCleanup)
			return r.Patch(ctx, latestDeployment, patch)
		}
		return err
	}

	logger.Info("Successfully removed finalizer", "finalizer", FinalizerPDBCleanup)
	return nil
}

// cleanupPDB removes the PDB associated with a deployment
func (r *DeploymentReconciler) cleanupPDB(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) error {
	pdbName := types.NamespacedName{
		Name:      deployment.Name + DefaultPDBSuffix,
		Namespace: deployment.Namespace,
	}

	pdb := &policyv1.PodDisruptionBudget{}
	if err := r.Get(ctx, pdbName, pdb); err != nil {
		if errors.IsNotFound(err) {
			logger.V(1).Info("PDB doesn't exist, nothing to clean up")
			return nil
		}
		return err
	}

	// Only delete if we own it
	if ownerRef := metav1.GetControllerOf(pdb); ownerRef != nil &&
		ownerRef.Kind == "Deployment" && ownerRef.Name == deployment.Name {
		if err := r.Delete(ctx, pdb); err != nil && !errors.IsNotFound(err) {
			return err
		}

		// Record metrics and events
		metrics.RecordPDBDeleted(deployment.Namespace, "deployment_deleted")
		r.Events.PDBDeleted(deployment, deployment.Name, pdbName.Name, "deployment_deleted")

		// Update compliance status
		metrics.UpdateComplianceStatus(
			deployment.Namespace,
			deployment.Name,
			true,
			"deleted",
		)

		logger.Info("Successfully deleted PDB", "pdb", pdbName.Name)
	}

	return nil
}

// cleanupDuplicatePDBs removes duplicate PDBs for the same deployment, keeping only the expected one
func (r *DeploymentReconciler) cleanupDuplicatePDBs(ctx context.Context, deployment *appsv1.Deployment, expectedPDBName types.NamespacedName, logger logr.Logger) error {
	// List all PDBs in the namespace
	pdbList := &policyv1.PodDisruptionBudgetList{}
	if err := r.List(ctx, pdbList, client.InNamespace(deployment.Namespace)); err != nil {
		return err
	}

	// Find PDBs that match this deployment's selector (including partial matches)
	var matchingPDBs []policyv1.PodDisruptionBudget
	for _, pdb := range pdbList.Items {
		if pdb.Spec.Selector != nil && r.selectorsOverlap(pdb.Spec.Selector, deployment.Spec.Selector) {
			matchingPDBs = append(matchingPDBs, pdb)
		}
	}

	// If we have multiple PDBs for the same deployment, keep only the expected one
	if len(matchingPDBs) > 1 {
		logger.Info("Found multiple PDBs for deployment, cleaning up duplicates",
			"deployment", deployment.Name,
			"expectedPDB", expectedPDBName.Name,
			"totalPDBs", len(matchingPDBs))

		for _, pdb := range matchingPDBs {
			// Keep the expected PDB, delete others
			if pdb.Name != expectedPDBName.Name {
				logger.Info("Deleting duplicate PDB",
					"name", pdb.Name,
					"namespace", pdb.Namespace,
					"reason", "duplicate")
				if err := r.Delete(ctx, &pdb); err != nil {
					logger.Error(err, "Failed to delete duplicate PDB", "name", pdb.Name)
					return err
				}
			}
		}
	}

	return nil
}

// reconcilePDB creates or updates the PDB with optimization
func (r *DeploymentReconciler) reconcilePDB(ctx context.Context, deployment *appsv1.Deployment, config *AvailabilityConfig, logger logr.Logger) (ctrl.Result, error) {
	// Skip PDB creation for single replica deployments
	if deployment.Spec.Replicas != nil && *deployment.Spec.Replicas <= 1 {
		logger.V(1).Info("Deployment has 1 or fewer replicas, skipping PDB creation",
			"replicas", *deployment.Spec.Replicas)

		// Record event and update compliance
		r.Events.DeploymentSkipped(deployment, deployment.Name, "insufficient replicas")
		metrics.UpdateComplianceStatus(
			deployment.Namespace,
			deployment.Name,
			false,
			"insufficient_replicas",
		)

		// Clean up any existing PDB
		if err := r.cleanupPDB(ctx, deployment, logger); err != nil {
			logger.Error(err, "Failed to cleanup PDB for single replica deployment")
		}
		return ctrl.Result{}, nil
	}

	pdbName := types.NamespacedName{
		Name:      deployment.Name + DefaultPDBSuffix,
		Namespace: deployment.Namespace,
	}

	// First, check for any existing PDBs for this deployment and clean up duplicates
	if err := r.cleanupDuplicatePDBs(ctx, deployment, pdbName, logger); err != nil {
		logger.Error(err, "Failed to cleanup duplicate PDBs")
		return ctrl.Result{}, err
	}

	pdb := &policyv1.PodDisruptionBudget{}
	err := r.Get(ctx, pdbName, pdb)

	if errors.IsNotFound(err) {
		return r.createPDB(ctx, pdbName, config, deployment, logger)
	} else if err != nil {
		logger.Error(err, "Failed to get PDB")
		return ctrl.Result{}, err
	}

	// PDB exists, check if update needed
	return r.updatePDB(ctx, pdb, config, deployment, logger)
}

// createPDB creates a new PDB for the deployment
func (r *DeploymentReconciler) createPDB(ctx context.Context, pdbName types.NamespacedName, config *AvailabilityConfig, deployment *appsv1.Deployment, logger logr.Logger) (ctrl.Result, error) {
	// Use structured logger with context for trace information
	structuredLogger := logging.NewStructuredLogger(ctx)
	structuredLogger.Info("Creating PDB", map[string]any{
		"name":              pdbName.Name,
		"availabilityClass": config.AvailabilityClass,
		"minAvailable":      config.MinAvailable.String(),
		"source":            config.Source,
		"policy":            config.PolicyName,
	})

	// Create labels for the PDB
	labels := map[string]string{
		LabelManagedBy:         OperatorName,
		LabelAvailabilityClass: string(config.AvailabilityClass),
		LabelFunction:          string(config.ComponentFunction),
	}

	// Add component label if available
	if deployment.Annotations != nil && deployment.Annotations[AnnotationComponentName] != "" {
		labels[LabelComponent] = deployment.Annotations[AnnotationComponentName]
	}

	// Clean up empty labels
	for k, v := range labels {
		if v == "" {
			delete(labels, k)
		}
	}

	// Create annotations for metadata
	annotations := make(map[string]string)
	annotations[AnnotationCreatedBy] = OperatorName
	annotations[AnnotationCreationTime] = time.Now().Format(time.RFC3339)
	annotations[AnnotationAvailabilityClass] = string(config.AvailabilityClass)
	if config.Description != "" {
		annotations[AnnotationDescription] = config.Description
	}
	if config.PolicyName != "" {
		annotations[AnnotationPolicySource] = config.PolicyName
		annotations[AnnotationEnforcement] = config.Enforcement
	}

	pdb := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:        pdbName.Name,
			Namespace:   pdbName.Namespace,
			Labels:      labels,
			Annotations: annotations,
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable: &config.MinAvailable,
			Selector: &metav1.LabelSelector{
				MatchLabels: deployment.Spec.Selector.MatchLabels,
			},
		},
	}

	// Set owner reference to Deployment
	if err := ctrl.SetControllerReference(deployment, pdb, r.Scheme); err != nil {
		structuredLogger.Error(err, "Failed to set controller reference", nil)
		return ctrl.Result{}, err
	}

	if createErr := r.Create(ctx, pdb); createErr != nil {
		structuredLogger.Error(createErr, "Failed to create PDB", nil)

		// Check if deployment still exists before creating event
		if err := r.Get(ctx, client.ObjectKeyFromObject(deployment), deployment); err == nil {
			r.Events.PDBCreationFailed(deployment, deployment.Name, createErr)
		}

		metrics.UpdateComplianceStatus(
			deployment.Namespace,
			deployment.Name,
			false,
			"creation_failed",
		)
		return ctrl.Result{}, createErr
	}

	// Record metrics and events for successful creation
	metrics.RecordPDBCreated(
		deployment.Namespace,
		string(config.AvailabilityClass),
		string(config.ComponentFunction),
	)

	// Check if deployment still exists before creating event
	if err := r.Get(ctx, client.ObjectKeyFromObject(deployment), deployment); err == nil {
		r.Events.PDBCreated(
			deployment,
			deployment.Name,
			pdbName.Name,
			string(config.AvailabilityClass),
			config.MinAvailable.String(),
		)
	}

	// Audit PDB creation - NO DUPLICATES
	auditLogger := logging.NewStructuredLogger(ctx)
	auditLogger.AuditStructured(
		"CREATE",
		pdbName.Name,
		"PodDisruptionBudget",
		deployment.Namespace,
		deployment.Name,
		logging.AuditResultSuccess,
		map[string]interface{}{
			"availabilityClass": config.AvailabilityClass,
			"minAvailable":      config.MinAvailable.String(),
			"source":            config.Source,
			"policy":            config.PolicyName,
			"enforcement":       config.Enforcement,
		},
	)

	// Update compliance status
	metrics.UpdateComplianceStatus(
		deployment.Namespace,
		deployment.Name,
		true,
		"created",
	)

	structuredLogger.Info("Successfully created PDB", map[string]any{
		"name": pdbName.Name,
	})
	return ctrl.Result{}, nil
}

// updatePDB updates the PDB if configuration has changed
func (r *DeploymentReconciler) updatePDB(ctx context.Context, pdb *policyv1.PodDisruptionBudget, config *AvailabilityConfig, deployment *appsv1.Deployment, logger logr.Logger) (ctrl.Result, error) {
	// Store old value for event
	oldMinAvailable := ""
	if pdb.Spec.MinAvailable != nil {
		oldMinAvailable = pdb.Spec.MinAvailable.String()
	}

	// Use structured logger with context for trace information
	structuredLogger := logging.NewStructuredLogger(ctx)
	structuredLogger.Info("Updating PDB", map[string]any{
		"name":            pdb.Name,
		"oldMinAvailable": oldMinAvailable,
		"newMinAvailable": config.MinAvailable.String(),
	})

	// Check if update is needed
	needsUpdate := false
	patch := client.MergeFrom(pdb.DeepCopy())

	// Update MinAvailable if changed
	if pdb.Spec.MinAvailable == nil || pdb.Spec.MinAvailable.String() != config.MinAvailable.String() {
		pdb.Spec.MinAvailable = &config.MinAvailable
		needsUpdate = true
	}

	// Update labels
	if pdb.Labels == nil {
		pdb.Labels = make(map[string]string)
	}
	if pdb.Labels[LabelAvailabilityClass] != string(config.AvailabilityClass) {
		pdb.Labels[LabelAvailabilityClass] = string(config.AvailabilityClass)
		needsUpdate = true
	}
	if pdb.Labels[LabelFunction] != string(config.ComponentFunction) {
		pdb.Labels[LabelFunction] = string(config.ComponentFunction)
		needsUpdate = true
	}

	// Update annotations
	if pdb.Annotations == nil {
		pdb.Annotations = make(map[string]string)
	}
	pdb.Annotations[AnnotationLastModified] = time.Now().Format(time.RFC3339)
	pdb.Annotations[AnnotationAvailabilityClass] = string(config.AvailabilityClass)

	// Update policy source if changed
	if config.PolicyName != "" && pdb.Annotations[AnnotationPolicySource] != config.PolicyName {
		pdb.Annotations[AnnotationPolicySource] = config.PolicyName
		pdb.Annotations[AnnotationEnforcement] = config.Enforcement
		needsUpdate = true
	}

	// Check if we're exiting maintenance mode
	if pdb.Annotations["oda.tmforum.org/maintenance-mode"] == "true" {
		delete(pdb.Annotations, "oda.tmforum.org/maintenance-mode")
		delete(pdb.Annotations, "oda.tmforum.org/maintenance-start")
		needsUpdate = true
	}

	// Update selector if deployment selector changed
	if !selectorEquals(pdb.Spec.Selector, deployment.Spec.Selector) {
		pdb.Spec.Selector = deployment.Spec.Selector.DeepCopy()
		needsUpdate = true
	}

	if !needsUpdate {
		structuredLogger.Debug("PDB is up to date, no changes needed", nil)
		return ctrl.Result{}, nil
	}

	// Apply the patch
	if err := r.Patch(ctx, pdb, patch); err != nil {
		structuredLogger.Error(err, "Failed to update PDB", nil)

		// Check if deployment still exists before creating event
		if err := r.Get(ctx, client.ObjectKeyFromObject(deployment), deployment); err == nil {
			r.Events.PDBUpdateFailed(deployment, deployment.Name, err)
		}

		metrics.UpdateComplianceStatus(
			deployment.Namespace,
			deployment.Name,
			false,
			"update_failed",
		)
		return ctrl.Result{}, err
	}

	// Record events and metrics
	// Check if deployment still exists before creating event
	if err := r.Get(ctx, client.ObjectKeyFromObject(deployment), deployment); err == nil {
		r.Events.PDBUpdated(
			deployment,
			deployment.Name,
			pdb.Name,
			oldMinAvailable,
			config.MinAvailable.String(),
		)
	}

	metrics.RecordPDBUpdated(deployment.Namespace, "config_change")

	// Audit PDB update - NO DUPLICATES
	auditLogger := logging.NewStructuredLogger(ctx)
	auditLogger.AuditStructured(
		"UPDATE",
		pdb.Name,
		"PodDisruptionBudget",
		deployment.Namespace,
		deployment.Name,
		logging.AuditResultSuccess,
		map[string]interface{}{
			"oldMinAvailable": oldMinAvailable,
			"newMinAvailable": config.MinAvailable.String(),
			"source":          config.Source,
			"policy":          config.PolicyName,
			"enforcement":     config.Enforcement,
		},
	)

	structuredLogger.Info("Successfully updated PDB", map[string]any{
		"name": pdb.Name,
	})
	return ctrl.Result{}, nil
}

// Helper functions

// isInMaintenanceWindow checks if currently in a maintenance window
func (r *DeploymentReconciler) isInMaintenanceWindow(config *AvailabilityConfig, logger logr.Logger) bool {
	if config.MaintenanceWindow == "" {
		return false
	}

	// Cache key for maintenance window
	cacheKey := fmt.Sprintf("maintenance-window-%s", config.MaintenanceWindow)

	// Check cache first if available
	if r.PolicyCache != nil {
		if cachedResult, found := r.PolicyCache.GetMaintenanceWindow(cacheKey); found {
			return cachedResult
		}
	}

	// Parse maintenance window (format: "02:00-04:00 UTC")
	parts := strings.Fields(config.MaintenanceWindow)
	if len(parts) < 1 {
		logger.Error(fmt.Errorf("invalid maintenance window format"),
			"Expected format: 'HH:MM-HH:MM UTC'",
			"got", config.MaintenanceWindow)
		return false
	}

	timeRange := parts[0]
	timezone := "UTC"
	if len(parts) > 1 {
		timezone = parts[1]
	}

	// Parse time range
	timeParts := strings.Split(timeRange, "-")
	if len(timeParts) != 2 {
		logger.Error(fmt.Errorf("invalid time range format"),
			"Expected format: 'HH:MM-HH:MM'",
			"got", timeRange)
		return false
	}

	location, err := time.LoadLocation(timezone)
	if err != nil {
		logger.Error(err, "Invalid timezone", "timezone", timezone)
		return false
	}

	now := time.Now().In(location)

	// Convert to today's time in the specified timezone
	today := now.Format("2006-01-02")
	todayStart, err := time.ParseInLocation("2006-01-02 15:04", fmt.Sprintf("%s %s", today, timeParts[0]), location)
	if err != nil {
		logger.Error(err, "Invalid start time format", "startTime", timeParts[0])
		return false
	}

	todayEnd, err := time.ParseInLocation("2006-01-02 15:04", fmt.Sprintf("%s %s", today, timeParts[1]), location)
	if err != nil {
		logger.Error(err, "Invalid end time format", "endTime", timeParts[1])
		return false
	}

	// Handle overnight maintenance windows
	var result bool
	if todayEnd.Before(todayStart) {
		// Maintenance window spans midnight
		result = now.After(todayStart) || now.Before(todayEnd)
	} else {
		result = now.After(todayStart) && now.Before(todayEnd)
	}

	// Cache the result for 1 minute if cache is available
	if r.PolicyCache != nil {
		r.PolicyCache.SetMaintenanceWindow(cacheKey, result, 1*time.Minute)
	}

	return result
}

// removePDBTemporarily disables PDB during maintenance window
// nolint:unused // Kept for future maintenance window feature implementation
func (r *DeploymentReconciler) removePDBTemporarily(ctx context.Context, deployment *appsv1.Deployment, logger logr.Logger) error {
	pdbName := types.NamespacedName{
		Name:      deployment.Name + DefaultPDBSuffix,
		Namespace: deployment.Namespace,
	}

	pdb := &policyv1.PodDisruptionBudget{}
	if err := r.Get(ctx, pdbName, pdb); err != nil {
		if errors.IsNotFound(err) {
			return nil // PDB doesn't exist
		}
		return err
	}

	// Create a patch
	patch := client.MergeFrom(pdb.DeepCopy())

	// Add annotation to track maintenance mode
	if pdb.Annotations == nil {
		pdb.Annotations = make(map[string]string)
	}
	pdb.Annotations["oda.tmforum.org/maintenance-mode"] = "true"
	pdb.Annotations["oda.tmforum.org/maintenance-start"] = time.Now().Format(time.RFC3339)

	// Temporarily disable PDB by setting minAvailable to 0
	pdb.Spec.MinAvailable = &intstr.IntOrString{Type: intstr.Int, IntVal: 0}

	if err := r.Patch(ctx, pdb, patch); err != nil {
		return err
	}

	logger.Info("Temporarily disabled PDB for maintenance window", "pdb", pdbName.Name)
	return nil
}

// selectorsOverlap checks if two selectors overlap (one is a subset of the other)
func (r *DeploymentReconciler) selectorsOverlap(pdbSelector, deploymentSelector *metav1.LabelSelector) bool {
	// If either selector is nil, they don't overlap
	if pdbSelector == nil || deploymentSelector == nil {
		return false
	}

	// Check if deployment selector is a subset of PDB selector
	deploymentSubset := true
	for k, v := range deploymentSelector.MatchLabels {
		if pdbSelector.MatchLabels[k] != v {
			deploymentSubset = false
			break
		}
	}

	// Check if PDB selector is a subset of deployment selector
	pdbSubset := true
	for k, v := range pdbSelector.MatchLabels {
		if deploymentSelector.MatchLabels[k] != v {
			pdbSubset = false
			break
		}
	}

	// They overlap if either is a subset of the other
	return deploymentSubset || pdbSubset
}

// selectorEquals compares two label selectors
func selectorEquals(a, b *metav1.LabelSelector) bool {
	if a == nil && b == nil {
		return true
	}
	if a == nil || b == nil {
		return false
	}

	// Compare MatchLabels
	if len(a.MatchLabels) != len(b.MatchLabels) {
		return false
	}
	for k, v := range a.MatchLabels {
		if b.MatchLabels[k] != v {
			return false
		}
	}

	// Compare MatchExpressions (simplified - just check length)
	if len(a.MatchExpressions) != len(b.MatchExpressions) {
		return false
	}

	return true
}

// isPDBUpdateByUs checks if the PDB update was made by our controller
func isPDBUpdateByUs(oldPDB, newPDB *policyv1.PodDisruptionBudget) bool {
	// If only the last-modified annotation changed, it's likely our update
	oldModified := ""
	newModified := ""

	if oldPDB.Annotations != nil {
		oldModified = oldPDB.Annotations[AnnotationLastModified]
	}
	if newPDB.Annotations != nil {
		newModified = newPDB.Annotations[AnnotationLastModified]
	}

	return oldModified != newModified
}

func (r *DeploymentReconciler) isValidAvailabilityClass(class availabilityv1alpha1.AvailabilityClass) bool {
	switch class {
	case availabilityv1alpha1.NonCritical, availabilityv1alpha1.Standard,
		availabilityv1alpha1.HighAvailability, availabilityv1alpha1.MissionCritical,
		availabilityv1alpha1.Custom:
		return true
	default:
		return false
	}
}

func (r *DeploymentReconciler) getDescriptionForClass(class availabilityv1alpha1.AvailabilityClass) string {
	descriptions := map[availabilityv1alpha1.AvailabilityClass]string{
		availabilityv1alpha1.NonCritical:      "Non-critical apps (batch jobs, testing)",
		availabilityv1alpha1.Standard:         "Typical microservices & APIs",
		availabilityv1alpha1.HighAvailability: "Stateful apps, DBs, Kafka consumers",
		availabilityv1alpha1.MissionCritical:  "Critical services that must not go down",
		availabilityv1alpha1.Custom:           "Custom availability configuration",
	}
	return descriptions[class]
}

func (r *DeploymentReconciler) inferComponentFunction(deployment *appsv1.Deployment) availabilityv1alpha1.ComponentFunction {
	// Check annotation first
	if deployment.Annotations != nil {
		if function := deployment.Annotations[AnnotationComponentFunction]; function != "" {
			return availabilityv1alpha1.ComponentFunction(function)
		}
	}

	// Try to infer from labels or name patterns
	name := strings.ToLower(deployment.Name)

	// Security-related patterns
	securityPatterns := []string{"auth", "security", "identity", "keycloak", "oauth", "jwt", "rbac"}
	for _, pattern := range securityPatterns {
		if strings.Contains(name, pattern) {
			return availabilityv1alpha1.SecurityFunction
		}
	}

	// Management-related patterns
	managementPatterns := []string{"operator", "controller", "manager", "webhook", "admission"}
	for _, pattern := range managementPatterns {
		if strings.Contains(name, pattern) {
			return availabilityv1alpha1.ManagementFunction
		}
	}

	// Default to core
	return availabilityv1alpha1.CoreFunction
}

// calculateDeploymentFingerprint calculates a fingerprint of the deployment state
// that affects PDB creation/update to detect changes
func (r *DeploymentReconciler) calculateDeploymentFingerprint(
	ctx context.Context,
	deployment *appsv1.Deployment,
	config *AvailabilityConfig,
) (string, error) {
	h := sha256.New()

	// Include deployment generation (changes on spec updates)
	_, _ = fmt.Fprintf(h, "generation:%d", deployment.Generation)

	// Include replica count
	replicas := int32(1)
	if deployment.Spec.Replicas != nil {
		replicas = *deployment.Spec.Replicas
	}
	_, _ = fmt.Fprintf(h, "replicas:%d", replicas)

	// Include relevant annotations
	if deployment.Annotations != nil {
		for _, key := range []string{
			AnnotationAvailabilityClass,
			AnnotationMaintenanceWindow,
			AnnotationComponentFunction,
			AnnotationOverrideReason,
		} {
			if value, exists := deployment.Annotations[key]; exists {
				_, _ = fmt.Fprintf(h, "%s:%s", key, value)
			}
		}
	}

	// Include relevant labels that affect policy matching
	if deployment.Labels != nil {
		for key, value := range deployment.Labels {
			_, _ = fmt.Fprintf(h, "label:%s=%s", key, value)
		}
	}

	// Include selector (affects PDB selector)
	if deployment.Spec.Selector != nil {
		if deployment.Spec.Selector.MatchLabels != nil {
			for key, value := range deployment.Spec.Selector.MatchLabels {
				_, _ = fmt.Fprintf(h, "selector:%s=%s", key, value)
			}
		}
	}

	// Include availability configuration if found
	if config != nil {
		_, _ = fmt.Fprintf(h, "config:class=%s", config.AvailabilityClass)
		_, _ = fmt.Fprintf(h, "config:source=%s", config.Source)
		_, _ = fmt.Fprintf(h, "config:policy=%s", config.PolicyName)
		_, _ = fmt.Fprintf(h, "config:enforcement=%s", config.Enforcement)
		_, _ = fmt.Fprintf(h, "config:minAvailable=%s", config.MinAvailable.String())
	}

	// Include current PDB state - this is CRITICAL for detecting PDB deletion
	pdbName := types.NamespacedName{
		Name:      deployment.Name + DefaultPDBSuffix,
		Namespace: deployment.Namespace,
	}

	currentPDB := &policyv1.PodDisruptionBudget{}
	if err := r.Get(ctx, pdbName, currentPDB); err == nil {
		// PDB exists - include its current spec
		_, _ = h.Write([]byte("pdb:exists=true"))
		_, _ = fmt.Fprintf(h, "pdb:minAvailable=%s", currentPDB.Spec.MinAvailable.String())
		if currentPDB.Spec.Selector != nil && currentPDB.Spec.Selector.MatchLabels != nil {
			for key, value := range currentPDB.Spec.Selector.MatchLabels {
				_, _ = fmt.Fprintf(h, "pdb:selector:%s=%s", key, value)
			}
		}
	} else {
		// PDB doesn't exist - include marker so fingerprint changes when PDB is deleted
		_, _ = h.Write([]byte("pdb:exists=false"))
	}

	// Also include expected PDB state based on configuration
	if config != nil {
		_, _ = fmt.Fprintf(h, "expected:pdb:minAvailable=%s", config.MinAvailable.String())
		// Include expected selector based on deployment selector
		if deployment.Spec.Selector != nil && deployment.Spec.Selector.MatchLabels != nil {
			for key, value := range deployment.Spec.Selector.MatchLabels {
				_, _ = fmt.Fprintf(h, "expected:pdb:selector:%s=%s", key, value)
			}
		}
	}

	return hex.EncodeToString(h.Sum(nil)), nil
}

// hasDeploymentStateChanged checks if the deployment state has changed
// since the last reconciliation
func (r *DeploymentReconciler) hasDeploymentStateChanged(
	ctx context.Context,
	deployment *appsv1.Deployment,
	config *AvailabilityConfig,
) (bool, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	if r.lastDeploymentState == nil {
		return true, nil // First time, always process
	}

	key := types.NamespacedName{
		Name:      deployment.Name,
		Namespace: deployment.Namespace,
	}

	currentFingerprint, err := r.calculateDeploymentFingerprint(ctx, deployment, config)
	if err != nil {
		return true, err // On error, process to be safe
	}

	lastFingerprint, exists := r.lastDeploymentState[key]
	if !exists {
		// Log for debugging - make this visible
		log.FromContext(ctx).Info("No previous state found, processing",
			"deployment", deployment.Name,
			"namespace", deployment.Namespace,
			"currentFingerprint", currentFingerprint[:12]+"...",
			"debug", true)
		return true, nil // No previous state, process
	}

	changed := currentFingerprint != lastFingerprint

	// Debug logging - make this visible
	log.FromContext(ctx).Info("Fingerprint comparison",
		"deployment", deployment.Name,
		"namespace", deployment.Namespace,
		"currentFingerprint", currentFingerprint[:12]+"...",
		"lastFingerprint", lastFingerprint[:12]+"...",
		"changed", changed,
		"debug", true)

	return changed, nil
}

// updateDeploymentState updates the last known state of the deployment
func (r *DeploymentReconciler) updateDeploymentState(
	ctx context.Context,
	deployment *appsv1.Deployment,
	config *AvailabilityConfig,
) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.lastDeploymentState == nil {
		r.lastDeploymentState = make(map[types.NamespacedName]string)
	}

	key := types.NamespacedName{
		Name:      deployment.Name,
		Namespace: deployment.Namespace,
	}

	fingerprint, err := r.calculateDeploymentFingerprint(ctx, deployment, config)
	if err != nil {
		return err
	}

	r.lastDeploymentState[key] = fingerprint
	return nil
}

// clearDeploymentState clears the cached state for a deployment (used on deletion)
func (r *DeploymentReconciler) clearDeploymentState(deployment *appsv1.Deployment) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.lastDeploymentState == nil {
		return
	}

	key := types.NamespacedName{
		Name:      deployment.Name,
		Namespace: deployment.Namespace,
	}

	delete(r.lastDeploymentState, key)
}

// SetupWithManager sets up the controller with the Manager with optimized predicates
func (r *DeploymentReconciler) SetupWithManager(mgr ctrl.Manager) error {
	// Use shared config for concurrent reconciles
	maxConcurrent := 3
	if r.Config != nil && r.Config.MaxConcurrentReconciles > 0 {
		maxConcurrent = r.Config.MaxConcurrentReconciles
	}

	return r.SetupWithManagerWithOptions(mgr, controller.Options{
		MaxConcurrentReconciles: maxConcurrent,
	})
}

// SetupWithManagerWithOptions sets up the controller with custom options
func (r *DeploymentReconciler) SetupWithManagerWithOptions(mgr ctrl.Manager, opts controller.Options) error {
	// Initialize change detection state
	r.mu.Lock()
	if r.lastDeploymentState == nil {
		r.lastDeploymentState = make(map[types.NamespacedName]string)
	}
	r.mu.Unlock()

	// Create event recorder if not already set
	if r.Recorder == nil && mgr != nil {
		r.Recorder = mgr.GetEventRecorderFor("deployment-pdb-controller")
	}
	if r.Events == nil && r.Recorder != nil {
		r.Events = events.NewEventRecorder(r.Recorder)
	}

	// Create predicates to filter events
	deploymentPredicate := predicate.Funcs{
		CreateFunc: func(e event.CreateEvent) bool {
			// Process ALL deployments (we'll check for config inside reconcile)
			_, ok := e.Object.(*appsv1.Deployment)
			return ok
		},
		UpdateFunc: func(e event.UpdateEvent) bool {
			// Process all deployment updates
			oldDeployment, ok := e.ObjectOld.(*appsv1.Deployment)
			if !ok {
				return false
			}
			newDeployment, ok := e.ObjectNew.(*appsv1.Deployment)
			if !ok {
				return false
			}

			// Skip if only status changed
			if oldDeployment.Generation == newDeployment.Generation {
				// Check if deletion timestamp was set
				if oldDeployment.DeletionTimestamp == nil && newDeployment.DeletionTimestamp != nil {
					return true
				}
				return false
			}

			return true
		},
		DeleteFunc: func(e event.DeleteEvent) bool {
			// Always process deletes for cleanup
			return true
		},
		GenericFunc: func(e event.GenericEvent) bool {
			return false
		},
	}

	// Enhanced PDB predicate to handle all PDB events properly
	pdbPredicate := predicate.Funcs{
		CreateFunc: func(e event.CreateEvent) bool {
			// Don't reconcile on PDB creation (we created it)
			return false
		},
		UpdateFunc: func(e event.UpdateEvent) bool {
			// Only reconcile if the PDB is managed by us and was externally modified
			pdb, ok := e.ObjectNew.(*policyv1.PodDisruptionBudget)
			if !ok {
				return false
			}

			// Check if we manage this PDB
			if labels := pdb.GetLabels(); labels != nil {
				if labels[LabelManagedBy] == OperatorName {
					// Check if the update was external (not by our controller)
					oldPDB := e.ObjectOld.(*policyv1.PodDisruptionBudget)
					return !isPDBUpdateByUs(oldPDB, pdb)
				}
			}
			return false
		},
		DeleteFunc: func(e event.DeleteEvent) bool {
			// CRITICAL: Always reconcile if our PDB was deleted
			pdb, ok := e.Object.(*policyv1.PodDisruptionBudget)
			if !ok {
				return false
			}

			// Check if we manage this PDB
			if labels := pdb.GetLabels(); labels != nil {
				managed := labels[LabelManagedBy] == OperatorName
				if managed {
					// Log the deletion event for debugging
					log.Log.Info("Managed PDB deleted, will reconcile deployment",
						"pdb", pdb.Name,
						"namespace", pdb.Namespace,
						"labels", labels)
				}
				return managed
			}
			return false
		},
		GenericFunc: func(e event.GenericEvent) bool {
			return false
		},
	}

	// Enhanced PDB event handler that maps PDB events to deployment reconciliation
	pdbToDeploymentHandler := handler.EnqueueRequestsFromMapFunc(func(ctx context.Context, obj client.Object) []ctrl.Request {
		pdb, ok := obj.(*policyv1.PodDisruptionBudget)
		if !ok {
			return nil
		}

		// Only handle PDBs we manage
		if labels := pdb.GetLabels(); labels == nil || labels[LabelManagedBy] != OperatorName {
			return nil
		}

		// Extract deployment name from PDB name (remove "-pdb" suffix)
		deploymentName := pdb.Name
		if len(deploymentName) > len(DefaultPDBSuffix) &&
			deploymentName[len(deploymentName)-len(DefaultPDBSuffix):] == DefaultPDBSuffix {
			deploymentName = deploymentName[:len(deploymentName)-len(DefaultPDBSuffix)]
		} else {
			// If PDB doesn't follow naming convention, try to find deployment via owner reference
			for _, ownerRef := range pdb.GetOwnerReferences() {
				if ownerRef.Kind == "Deployment" && ownerRef.Controller != nil && *ownerRef.Controller {
					deploymentName = ownerRef.Name
					break
				}
			}
		}

		log.Log.Info("Mapping PDB event to deployment reconciliation",
			"pdb", pdb.Name,
			"deployment", deploymentName,
			"namespace", pdb.Namespace)

		return []ctrl.Request{
			{
				NamespacedName: types.NamespacedName{
					Name:      deploymentName,
					Namespace: pdb.Namespace,
				},
			},
		}
	})

	// Handler for AvailabilityPolicy changes
	policyHandler := handler.EnqueueRequestsFromMapFunc(func(ctx context.Context, obj client.Object) []ctrl.Request {
		policy, ok := obj.(*availabilityv1alpha1.AvailabilityPolicy)
		if !ok {
			return nil
		}

		logger := log.FromContext(ctx)

		// Find all deployments that might be affected by this policy
		deploymentList := &appsv1.DeploymentList{}
		if err := r.List(ctx, deploymentList); err != nil {
			logger.Error(err, "Failed to list deployments for policy change")
			return nil
		}

		var requests []ctrl.Request
		for _, deployment := range deploymentList.Items {
			if r.policyMatchesDeployment(policy, &deployment) {
				requests = append(requests, ctrl.Request{
					NamespacedName: types.NamespacedName{
						Name:      deployment.Name,
						Namespace: deployment.Namespace,
					},
				})
			}
		}

		logger.V(2).Info("Policy change affects deployments",
			"policy", policy.Name,
			"affectedDeployments", len(requests))

		return requests
	})

	// Build the controller with SEPARATE PDB watching instead of Owns()
	bldr := ctrl.NewControllerManagedBy(mgr).
		Named("deployment-pdb"). // UNIQUE CONTROLLER NAME
		For(&appsv1.Deployment{}, builder.WithPredicates(deploymentPredicate)).
		Watches(
			&policyv1.PodDisruptionBudget{},
			pdbToDeploymentHandler,
			builder.WithPredicates(pdbPredicate),
		).
		Watches(
			&availabilityv1alpha1.AvailabilityPolicy{},
			policyHandler,
		).
		WithOptions(opts)

	return bldr.Complete(r)
}
