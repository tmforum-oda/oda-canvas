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
	"fmt"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/tracing"
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
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/events"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/logging"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/metrics"
)

type PDBReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder record.EventRecorder
	Events   *events.EventRecorder
}

func (r *PDBReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	// Start timing for metrics
	startTime := time.Now()

	// Generate reconcile ID for this specific reconciliation with controller prefix
	reconcileID := "pdb-" + uuid.New().String()

	// Start tracing span
	ctx, span := tracing.ReconcileSpan(ctx, "pdb", req.Namespace, req.Name)
	defer span.End()

	// Generate correlation ID
	correlationID := uuid.New().String()

	// Add reconcile ID and correlation ID to span
	span.SetAttributes(
		attribute.String("reconcile.id", reconcileID),
		attribute.String("correlation.id", correlationID),
	)

	// Create unified logger with clean, structured logging
	logger := logging.CreateUnifiedLogger(ctx,
		"pdb-direct",            // controllerType
		"pdb-direct-controller", // controllerName
		"apps",                  // group
		"Deployment",            // kind
		"poddisruptionbudget",   // resourceType
		req.Name,                // name
		req.Namespace,           // namespace
		reconcileID,             // reconcileID
		correlationID,           // correlationID
	)

	// Ensure we record metrics at the end
	var reconcileErr error
	defer func() {
		duration := time.Since(startTime)
		metrics.RecordReconciliation("pdb", duration, reconcileErr)

		// Record tracing error if any
		if reconcileErr != nil {
			tracing.RecordError(span, reconcileErr, "PDB reconciliation failed")
		}

		// Audit the reconciliation using unified logger
		result := logging.AuditResultSuccess
		if reconcileErr != nil {
			result = logging.AuditResultFailure
		}
		logger.Audit(
			"RECONCILE",
			fmt.Sprintf("%s/%s", req.Namespace, req.Name),
			"pdb",
			req.Namespace,
			req.Name,
			result,
			map[string]interface{}{
				"controller": "pdb",
				"duration":   duration.String(),
				"durationMs": duration.Milliseconds(),
			},
		)

		logger.Info("PDB reconciliation completed", map[string]any{
			"duration": duration.String(),
			//"reconcileID": reconcileID,
		})
	}()

	// Check if PDB enforcement is enabled
	if os.Getenv("ENABLE_PDB") != "true" {
		logger.Info("PDB enforcement disabled, skipping", map[string]any{})

		// Add skip event to span
		tracing.AddEvent(ctx, "PDBEnforcementDisabled")

		return ctrl.Result{}, nil
	}

	// Add fetch event
	tracing.AddEvent(ctx, "FetchingDeployment",
		attribute.String("reconcile.id", reconcileID),
	)

	deployment := &appsv1.Deployment{}
	if err := r.Get(ctx, req.NamespacedName, deployment); err != nil {
		if errors.IsNotFound(err) {
			logger.Info("Deployment not found, skipping", map[string]any{})

			// Add not found event
			tracing.AddEvent(ctx, "DeploymentNotFound")

			return ctrl.Result{}, nil
		}
		reconcileErr = err
		return ctrl.Result{}, err
	}

	// Check replicas
	replicas := int32(1)
	if deployment.Spec.Replicas != nil {
		replicas = *deployment.Spec.Replicas
	}
	if replicas < 2 {
		logger.WithDetail("replicas", replicas).Info("Single replica, no PDB required", map[string]any{})

		// Add skip event with reason
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

	// Check for availability class annotation
	availabilityClass := deployment.Annotations[AnnotationAvailabilityClass]
	componentFunc := deployment.Annotations[AnnotationComponentFunction]

	if availabilityClass == "" {
		logger.Info("No availability annotation, skipping PDB", map[string]any{})

		// Add skip event
		tracing.AddEvent(ctx, "SkippedPDB",
			attribute.String("reason", "no_availability_annotation"),
		)

		// Record event
		if r.Events != nil {
			r.Events.DeploymentUnmanaged(deployment, deployment.Name, "no availability annotation")
		}

		return ctrl.Result{}, nil
	}

	// Log availability class context
	ctx = logging.WithAvailabilityClass(ctx, availabilityClass)
	ctx = logging.WithComponent(ctx, deployment.Labels["oda.tmforum.org/componentName"], componentFunc)

	// Add availability info to span
	span.SetAttributes(
		attribute.String("availability.class", availabilityClass),
		attribute.String("component.function", componentFunc),
	)

	logger.WithDetails(logging.Details{
		"availabilityClass": availabilityClass,
		"componentFunction": componentFunc,
		"replicas":          replicas,
	}).Info("Processing PDB for deployment", map[string]any{})

	// Calculate PDB requirements
	ctx = logging.WithOperation(ctx, "calculate_pdb")

	// Add calculation event
	tracing.AddEvent(ctx, "CalculatingPDBRequirements",
		attribute.String("availability_class", availabilityClass),
	)

	minAvailable, maxUnavailable := calculatePDBValues(availabilityClass, componentFunc, replicas)

	// Create or update PDB
	pdbName := fmt.Sprintf("%s-pdb", deployment.Name)
	ctx = logging.WithPDBContext(ctx, deployment.Namespace, pdbName)

	pdb := &policyv1.PodDisruptionBudget{}
	err := r.Get(ctx, client.ObjectKey{
		Namespace: deployment.Namespace,
		Name:      pdbName,
	}, pdb)

	if err != nil {
		if errors.IsNotFound(err) {
			// PDB doesn't exist, create new one
			ctx = logging.WithOperation(ctx, "create")

			// Add creation event
			tracing.AddEvent(ctx, "CreatingPDB",
				attribute.String("pdb.name", pdbName),
			)

			pdb = r.buildPDB(deployment, pdbName, minAvailable, maxUnavailable, availabilityClass, componentFunc)

			if err := r.Create(ctx, pdb); err != nil {
				reconcileErr = err
				logger.Error(err, "Failed to create PDB", map[string]any{})
				return ctrl.Result{}, err
			}

			logger.Info("Created PDB", map[string]any{
				"pdb":            pdbName,
				"minAvailable":   minAvailable,
				"maxUnavailable": maxUnavailable,
			})

			// Record metrics
			metrics.RecordPDBCreated(deployment.Namespace, availabilityClass, componentFunc)

			// Audit PDB creation using unified logger
			logger.Audit(
				"CREATE",
				pdbName,
				"PodDisruptionBudget",
				deployment.Namespace,
				deployment.Name,
				logging.AuditResultSuccess,
				map[string]interface{}{
					"availabilityClass": availabilityClass,
					"minAvailable":      minAvailable,
					"maxUnavailable":    maxUnavailable,
				},
			)

			// Record event
			if r.Events != nil {
				r.Events.PDBCreated(deployment, deployment.Name, pdbName, availabilityClass, minAvailable.String())
			}
		} else {
			// Other error occurred (API server issues, network, permissions, etc.)
			reconcileErr = err
			logger.Error(err, "Failed to get PDB, will retry", map[string]any{
				"pdb":        pdbName,
				"error_type": fmt.Sprintf("%T", err),
			})
			return ctrl.Result{RequeueAfter: 30 * time.Second}, err
		}
	} else {
		// PDB exists, check if update is needed
		ctx = logging.WithOperation(ctx, "update")

		// Add update check event
		tracing.AddEvent(ctx, "CheckingPDBUpdate",
			attribute.String("pdb.name", pdbName),
		)

		updated := false

		// Check if update is needed
		if pdb.Spec.MinAvailable != nil && minAvailable != nil {
			if pdb.Spec.MinAvailable.IntVal != minAvailable.IntVal {
				updated = true
			}
		} else if pdb.Spec.MaxUnavailable != nil && maxUnavailable != nil {
			if pdb.Spec.MaxUnavailable.IntVal != maxUnavailable.IntVal {
				updated = true
			}
		}

		if updated {
			pdb.Spec.MinAvailable = minAvailable
			pdb.Spec.MaxUnavailable = maxUnavailable

			// Update labels
			if pdb.Labels == nil {
				pdb.Labels = make(map[string]string)
			}
			pdb.Labels["availability-class"] = availabilityClass
			pdb.Labels["component-function"] = componentFunc

			// Add update event
			tracing.AddEvent(ctx, "UpdatingPDB",
				attribute.String("pdb.name", pdbName),
				attribute.Bool("spec_changed", true),
			)

			if err := RetryUpdateWithBackoff(ctx, r.Client, pdb, DefaultRetryConfig()); err != nil {
				reconcileErr = err
				logger.Error(err, "Failed to update PDB after retries", map[string]any{
					"error_type": GetErrorType(err),
				})
				return ctrl.Result{}, err
			}

			logger.WithDetails(logging.Details{
				"pdb":            pdbName,
				"minAvailable":   minAvailable,
				"maxUnavailable": maxUnavailable,
			}).Info("Updated PDB", map[string]any{})

			// Record metrics
			metrics.RecordPDBUpdated(deployment.Namespace, availabilityClass)

			// Record event
			if r.Events != nil {
				r.Events.PDBUpdated(deployment, deployment.Name, pdbName, "old_value", "new_value")
			}
		} else {
			logger.Info("PDB is up to date", map[string]any{
				"pdb": pdbName,
			})

			// Add no-op event
			tracing.AddEvent(ctx, "PDBUpToDate",
				attribute.String("pdb.name", pdbName),
			)
		}
	}

	// Update compliance status
	metrics.UpdateComplianceStatus(
		deployment.Namespace,
		deployment.Name,
		true,
		"compliant",
	)

	logger.WithDetail("reconcile_id", reconcileID).Info("Successfully reconciled PDB", map[string]any{})

	return ctrl.Result{}, nil
}

func calculateMinAvailable(class, function string) intstr.IntOrString {
	// Security gets boosted
	if function == "security" && class == "standard" {
		return intstr.FromString("75%")
	}

	switch class {
	case "non-critical":
		return intstr.FromString("20%")
	case "standard":
		return intstr.FromString("50%")
	case "high-availability":
		return intstr.FromString("75%")
	case "mission-critical":
		return intstr.FromString("90%")
	default:
		return intstr.FromString("50%")
	}
}

// calculatePDBValues calculates minAvailable and maxUnavailable for PDB
func calculatePDBValues(availabilityClass, componentFunc string, replicas int32) (*intstr.IntOrString, *intstr.IntOrString) {
	minAvailable := calculateMinAvailable(availabilityClass, componentFunc)
	return &minAvailable, nil
}

// buildPDB creates a new PodDisruptionBudget
func (r *PDBReconciler) buildPDB(deployment *appsv1.Deployment, pdbName string, minAvailable, maxUnavailable *intstr.IntOrString, availabilityClass, componentFunc string) *policyv1.PodDisruptionBudget {
	pdb := &policyv1.PodDisruptionBudget{
		ObjectMeta: metav1.ObjectMeta{
			Name:      pdbName,
			Namespace: deployment.Namespace,
			Labels: map[string]string{
				"app":                deployment.Name,
				"availability-class": availabilityClass,
				"component-function": componentFunc,
				"managed-by":         "pdb-management-operator",
			},
			OwnerReferences: []metav1.OwnerReference{
				{
					APIVersion: deployment.APIVersion,
					Kind:       deployment.Kind,
					Name:       deployment.Name,
					UID:        deployment.UID,
				},
			},
		},
		Spec: policyv1.PodDisruptionBudgetSpec{
			MinAvailable:   minAvailable,
			MaxUnavailable: maxUnavailable,
			Selector: &metav1.LabelSelector{
				MatchLabels: deployment.Spec.Selector.MatchLabels,
			},
		},
	}
	return pdb
}

// SetupWithManager sets up the controller with the Manager.
func (r *PDBReconciler) SetupWithManager(mgr ctrl.Manager) error {
	// Create event recorder if not already set
	if r.Recorder == nil && mgr != nil {
		r.Recorder = mgr.GetEventRecorderFor("pdb-direct-controller")
	}
	if r.Events == nil && r.Recorder != nil {
		r.Events = events.NewEventRecorder(r.Recorder)
	}

	return r.SetupWithManagerWithOptions(mgr, controller.Options{
		MaxConcurrentReconciles: 3,
	})
}

// SetupWithManagerWithOptions allows custom controller options
func (r *PDBReconciler) SetupWithManagerWithOptions(mgr ctrl.Manager, opts controller.Options) error {
	// PDB predicate to handle deletion events properly
	pdbPredicate := predicate.Funcs{
		CreateFunc: func(e event.CreateEvent) bool {
			return false // Don't reconcile on PDB creation (we created it)
		},
		UpdateFunc: func(e event.UpdateEvent) bool {
			return false // Don't reconcile on PDB updates for this controller
		},
		DeleteFunc: func(e event.DeleteEvent) bool {
			// CRITICAL: Always reconcile when our managed PDB is deleted
			pdb, ok := e.Object.(*policyv1.PodDisruptionBudget)
			if !ok {
				return false
			}

			// Check if we manage this PDB
			if labels := pdb.GetLabels(); labels != nil {
				managed := labels["managed-by"] == "pdb-management-operator"
				if managed {
					log.Log.Info("Managed PDB deleted, will reconcile deployment",
						"pdb", pdb.Name,
						"namespace", pdb.Namespace)
				}
				return managed
			}
			return false
		},
		GenericFunc: func(e event.GenericEvent) bool {
			return false
		},
	}

	// PDB event handler that maps PDB events to deployment reconciliation
	pdbToDeploymentHandler := handler.EnqueueRequestsFromMapFunc(func(ctx context.Context, obj client.Object) []ctrl.Request {
		pdb, ok := obj.(*policyv1.PodDisruptionBudget)
		if !ok {
			return nil
		}

		// Only handle PDBs we manage
		if labels := pdb.GetLabels(); labels == nil || labels["managed-by"] != "pdb-management-operator" {
			return nil
		}

		// Extract deployment name from PDB name (remove "-pdb" suffix)
		deploymentName := pdb.Name
		if len(deploymentName) > 4 && deploymentName[len(deploymentName)-4:] == "-pdb" {
			deploymentName = deploymentName[:len(deploymentName)-4]
		} else {
			// If PDB doesn't follow naming convention, try owner references
			for _, ownerRef := range pdb.GetOwnerReferences() {
				if ownerRef.Kind == "Deployment" && ownerRef.Controller != nil && *ownerRef.Controller {
					deploymentName = ownerRef.Name
					break
				}
			}
		}

		log.Log.Info("Mapping PDB deletion to deployment reconciliation",
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

	return ctrl.NewControllerManagedBy(mgr).
		Named("pdb-direct-controller").
		WithOptions(opts).
		For(&appsv1.Deployment{}).
		Watches(
			&policyv1.PodDisruptionBudget{},
			pdbToDeploymentHandler,
			builder.WithPredicates(pdbPredicate),
		).
		Complete(r)
}
