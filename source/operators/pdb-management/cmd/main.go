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

package main

import (
	"context"
	_ "crypto/tls"
	"flag"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"sigs.k8s.io/controller-runtime/pkg/client"

	_ "k8s.io/client-go/plugin/pkg/client/auth" // Kubernetes auth plugins

	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/cache"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"sigs.k8s.io/controller-runtime/pkg/metrics/filters"
	"sigs.k8s.io/controller-runtime/pkg/metrics/server"
	"sigs.k8s.io/controller-runtime/pkg/webhook"

	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	internalcache "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/cache"
	internalclient "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/client"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/controller"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/events"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/logging"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/metrics"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/tracing"
	appsv1 "k8s.io/api/apps/v1"
)

var (
	scheme   = runtime.NewScheme()
	setupLog = ctrl.Log.WithName("setup")
)

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))
	utilruntime.Must(availabilityv1alpha1.AddToScheme(scheme))
}

func main() {
	var (
		metricsAddr             string
		enableLeaderElection    bool
		probeAddr               string
		secureMetrics           bool
		enableHTTP2             bool
		watchNamespace          string
		syncPeriod              time.Duration
		enableWebhook           bool
		webhookPort             int
		logLevel                string
		enableTracing           bool
		maxConcurrentReconciles int
	)

	flag.StringVar(&metricsAddr, "metrics-bind-address", "0", "The address the metric endpoint binds to.")
	flag.StringVar(&probeAddr, "health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.BoolVar(&enableLeaderElection, "leader-elect", true, "Enable leader election for controller manager.")
	flag.BoolVar(&secureMetrics, "metrics-secure", false, "Serve metrics endpoint securely via HTTPS.")
	flag.BoolVar(&enableHTTP2, "enable-http2", false, "Enable HTTP/2 for metrics and webhook servers.")
	flag.StringVar(&watchNamespace, "watch-namespace", "", "Namespace to watch. Leave empty to watch all namespaces.")
	flag.DurationVar(&syncPeriod, "sync-period", 10*time.Hour, "How often to reconcile resources even if no changes.")
	flag.BoolVar(&enableWebhook, "enable-webhook", false, "Enable admission webhook for AvailabilityPolicy validation.")
	flag.IntVar(&webhookPort, "webhook-port", 9443, "Port for admission webhook.")
	flag.StringVar(&logLevel, "log-level", "info", "Log level (debug, info, error)")
	flag.BoolVar(&enableTracing, "enable-tracing", true, "Enable OpenTelemetry tracing")
	flag.IntVar(&maxConcurrentReconciles, "max-concurrent-reconciles", 5, "Maximum concurrent reconciles per controller")

	opts := zap.Options{Development: logLevel == "debug"}
	opts.BindFlags(flag.CommandLine)
	flag.Parse()

	// Set up controller-runtime logger with zap
	ctrl.SetLogger(zap.New(zap.UseFlagOptions(&opts)))

	printStartupBanner()

	// Initialize tracing if enabled
	var tracingCleanup func()
	var err error
	if enableTracing {
		tracingCleanup, err = tracing.InitTracing(context.Background(), "pdb-management-operator")
		if err != nil {
			setupLog.Error(err, "Failed to initialize tracing, continuing without it")
		} else {
			defer tracingCleanup()
			setupLog.Info("Tracing initialized")
		}
	}

	config := validateConfiguration()

	// Create policy cache (optimized for 200+ deployments)
	policyCache := internalcache.NewPolicyCache(100, 5*time.Minute)
	defer policyCache.Stop()
	setupLog.Info("Policy cache initialized", "size", 100, "ttl", "5m")

	// Manager configuration
	metricsServerOptions := server.Options{
		BindAddress: metricsAddr,
	}
	if secureMetrics {
		metricsServerOptions.FilterProvider = filters.WithAuthenticationAndAuthorization
	}

	cacheOptions := cache.Options{
		SyncPeriod: &syncPeriod,
	}
	if watchNamespace != "" {
		cacheOptions.DefaultNamespaces = map[string]cache.Config{
			watchNamespace: {},
		}
		setupLog.Info("Watching single namespace", "namespace", watchNamespace)
	} else {
		setupLog.Info("Watching all namespaces")
	}

	webhookServer := webhook.NewServer(webhook.Options{
		Port: webhookPort,
	})

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme:                  scheme,
		Metrics:                 metricsServerOptions,
		WebhookServer:           webhookServer,
		HealthProbeBindAddress:  probeAddr,
		LeaderElection:          enableLeaderElection,
		LeaderElectionID:        "oda.tmforum.org.pdb-management",
		Cache:                   cacheOptions,
		LeaderElectionNamespace: config.LeaderElectionNamespace,
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		os.Exit(1)
	}

	// Use adaptive circuit breaker that learns from cluster performance
	setupLog.Info("Initializing adaptive circuit breaker client...")
	circuitBreakerClient := internalclient.NewAdaptiveCircuitBreakerClient(mgr.GetClient())
	setupLog.Info("Adaptive circuit breaker initialized - will learn cluster characteristics")

	// Create event recorder
	eventRecorder := events.NewEventRecorder(mgr.GetEventRecorderFor("pdb-management-operator"))

	// Create shared controller configuration
	controllerConfig := &controller.SharedConfig{
		PolicyCache:             policyCache,
		MaxConcurrentReconciles: maxConcurrentReconciles,
	}

	// Register AvailabilityPolicy controller
	if err = (&controller.AvailabilityPolicyReconciler{
		Client:      circuitBreakerClient,
		Scheme:      mgr.GetScheme(),
		Recorder:    mgr.GetEventRecorderFor("availabilitypolicy-controller"),
		Events:      eventRecorder,
		PolicyCache: policyCache,
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "AvailabilityPolicy")
		os.Exit(1)
	}

	// Register Deployment controller with enhanced client and cache
	if err = (&controller.DeploymentReconciler{
		Client:      circuitBreakerClient,
		Scheme:      mgr.GetScheme(),
		Recorder:    mgr.GetEventRecorderFor("deployment-controller"),
		Events:      eventRecorder,
		PolicyCache: policyCache,
		Config:      controllerConfig,
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "Deployment")
		os.Exit(1)
	}

	// Register PDB controller if enabled
	if config.EnablePDB {
		setupLog.Info("PDB controller is deprecated - deployment controller now handles all PDB management")
		setupLog.Info("Consider setting EnablePDB=false to avoid potential conflicts")

		if err = (&controller.PDBReconciler{
			Client:   circuitBreakerClient,
			Scheme:   mgr.GetScheme(),
			Recorder: mgr.GetEventRecorderFor("pdb-controller"),
			Events:   eventRecorder,
		}).SetupWithManager(mgr); err != nil {
			setupLog.Error(err, "unable to create controller", "controller", "PDB")
			os.Exit(1)
		}
		setupLog.Info("PDB controller enabled (deprecated)")
	} else {
		setupLog.Info("PDB controller disabled - deployment controller handles all PDB management")
	}

	// Setup webhooks if enabled
	if enableWebhook {
		if err = (&availabilityv1alpha1.AvailabilityPolicy{}).SetupWebhookWithManager(mgr); err != nil {
			setupLog.Error(err, "unable to create webhook", "webhook", "AvailabilityPolicy")
			os.Exit(1)
		}
		setupLog.Info("Webhook server enabled", "port", webhookPort)
	}

	// Setup health checks
	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check")
		os.Exit(1)
	}
	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check")
		os.Exit(1)
	}

	// Add a readiness check for cache
	if err := mgr.AddReadyzCheck("cache-sync", func(req *http.Request) error {
		if !mgr.GetCache().WaitForCacheSync(context.Background()) {
			return fmt.Errorf("cache not synced")
		}
		return nil
	}); err != nil {
		setupLog.Error(err, "unable to set up cache sync check")
		os.Exit(1)
	}

	// Create graceful shutdown manager
	shutdownMgr := NewGracefulShutdownManager(mgr, 30*time.Second)

	// Add pre-shutdown hooks
	shutdownMgr.AddPreShutdownHook(func(ctx context.Context) error {
		setupLog.Info("Flushing metrics before shutdown")
		// Metrics are automatically flushed by the metrics server
		return nil
	})

	shutdownMgr.AddPreShutdownHook(func(ctx context.Context) error {
		setupLog.Info("Clearing caches")
		policyCache.Clear()
		return nil
	})

	shutdownMgr.AddPreShutdownHook(func(ctx context.Context) error {
		setupLog.Info("Saving operator state")
		// Could save checkpoint to ConfigMap here
		return nil
	})

	setupLog.Info("Starting PDB Management Operator",
		"version", getBuildVersion(),
		"watchNamespace", getWatchNamespaceDisplay(watchNamespace),
		"leaderElection", enableLeaderElection,
		"enablePDB", config.EnablePDB,
		"metricsAddr", metricsAddr,
		"webhookEnabled", enableWebhook,
		"tracingEnabled", enableTracing,
		"maxConcurrentReconciles", maxConcurrentReconciles)

	// Create a separate context for background tasks
	bgCtx, bgCancel := context.WithCancel(context.Background())
	defer bgCancel()

	// Start the manager in a goroutine
	go func() {
		if err := mgr.Start(bgCtx); err != nil {
			setupLog.Error(err, "problem running manager")
			os.Exit(1)
		}
	}()

	// Wait for the manager cache to sync before starting metrics
	setupLog.Info("Waiting for manager cache to sync...")

	// Create a timeout context for cache sync
	syncCtx, syncCancel := context.WithTimeout(bgCtx, 60*time.Second)
	defer syncCancel()

	// Wait for cache sync with timeout
	cacheSynced := make(chan bool, 1)
	go func() {
		// Give manager time to initialize
		time.Sleep(2 * time.Second)

		if mgr.GetCache() != nil {
			cacheSynced <- mgr.GetCache().WaitForCacheSync(syncCtx)
		} else {
			cacheSynced <- false
		}
	}()

	select {
	case synced := <-cacheSynced:
		if synced {
			setupLog.Info("Cache synced, starting metrics updater")
			go startMetricsUpdater(bgCtx, circuitBreakerClient, policyCache)
		} else {
			setupLog.Error(nil, "Failed to sync cache, metrics updater will not start")
		}
	case <-syncCtx.Done():
		setupLog.Error(nil, "Timeout waiting for cache sync")
	}

	// Handle shutdown signals
	sigChan := make(chan os.Signal, 2)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Wait for shutdown signal
	<-sigChan
	setupLog.Info("Received shutdown signal, initiating graceful shutdown")

	// Cancel background context to stop manager
	bgCancel()

	// Run shutdown hooks
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	shutdownMgr.runPreShutdownHooks(shutdownCtx)

	setupLog.Info("Graceful shutdown completed")
}

// GracefulShutdownManager handles graceful shutdown of the operator
type GracefulShutdownManager struct {
	mgr              ctrl.Manager
	shutdownTimeout  time.Duration
	preShutdownHooks []func(context.Context) error
	wg               sync.WaitGroup
	mu               sync.RWMutex
	isShuttingDown   bool
}

func NewGracefulShutdownManager(mgr ctrl.Manager, timeout time.Duration) *GracefulShutdownManager {
	return &GracefulShutdownManager{
		mgr:             mgr,
		shutdownTimeout: timeout,
	}
}

func (gsm *GracefulShutdownManager) AddPreShutdownHook(hook func(context.Context) error) {
	gsm.mu.Lock()
	defer gsm.mu.Unlock()
	gsm.preShutdownHooks = append(gsm.preShutdownHooks, hook)
}

func (gsm *GracefulShutdownManager) Start(ctx context.Context) error {
	sigChan := make(chan os.Signal, 2)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	shutdownCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	errChan := make(chan error, 1)
	go func() {
		setupLog.Info("Starting manager")
		if err := gsm.mgr.Start(shutdownCtx); err != nil {
			errChan <- fmt.Errorf("manager exited with error: %w", err)
		}
		close(errChan)
	}()

	select {
	case <-sigChan:
		setupLog.Info("Received shutdown signal, initiating graceful shutdown")
		gsm.initiateShutdown(cancel)
	case err := <-errChan:
		if err != nil {
			return err
		}
	}

	gsm.wg.Wait()
	setupLog.Info("Graceful shutdown completed")

	return nil
}

func (gsm *GracefulShutdownManager) initiateShutdown(cancel context.CancelFunc) {
	gsm.mu.Lock()
	gsm.isShuttingDown = true
	gsm.mu.Unlock()

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), gsm.shutdownTimeout)
	defer shutdownCancel()

	gsm.runPreShutdownHooks(shutdownCtx)

	cancel()

	select {
	case <-time.After(gsm.shutdownTimeout):
		setupLog.Error(nil, "Shutdown timeout exceeded, forcing exit")
	case <-shutdownCtx.Done():
		setupLog.Info("Manager stopped gracefully")
	}
}

func (gsm *GracefulShutdownManager) runPreShutdownHooks(ctx context.Context) {
	setupLog.Info("Running pre-shutdown hooks", "count", len(gsm.preShutdownHooks))

	for i, hook := range gsm.preShutdownHooks {
		hookCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()

		if err := hook(hookCtx); err != nil {
			setupLog.Error(err, "Pre-shutdown hook failed", "index", i)
		}
	}
}

// startMetricsUpdater periodically updates global metrics with cache stats
func startMetricsUpdater(ctx context.Context, c client.Client, cache *internalcache.PolicyCache) {
	// Initial delay to ensure everything is initialized
	select {
	case <-time.After(5 * time.Second):
	case <-ctx.Done():
		return
	}

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Safe update function
	safeUpdate := func() {
		defer func() {
			if r := recover(); r != nil {
				setupLog.Error(nil, "Panic in metrics update", "error", r)
			}
		}()

		if c != nil {
			updateGlobalMetrics(ctx, c)
		}
		if cache != nil {
			metrics.UpdateCacheMetrics(cache.GetStats())
		}
	}

	// Initial update
	safeUpdate()

	for {
		select {
		case <-ctx.Done():
			setupLog.Info("Metrics updater stopped")
			return
		case <-ticker.C:
			safeUpdate()
		}
	}
}

// Rest of the existing helper functions...
func updateGlobalMetrics(ctx context.Context, c client.Client) {
	ctx = logging.WithCorrelationID(ctx)
	ctx = logging.WithOperation(ctx, "metrics-update")

	logger := ctrl.Log.WithName("metrics")

	deploymentList := &appsv1.DeploymentList{}
	if err := c.List(ctx, deploymentList); err != nil {
		logger.Error(err, "Failed to list deployments for metrics")
		return
	}

	deploymentCounts := make(map[string]map[string]int)
	managedCount := 0

	for _, deployment := range deploymentList.Items {
		if deployment.Annotations != nil {
			if class, exists := deployment.Annotations[controller.AnnotationAvailabilityClass]; exists {
				namespace := deployment.Namespace
				if deploymentCounts[namespace] == nil {
					deploymentCounts[namespace] = make(map[string]int)
				}
				deploymentCounts[namespace][class]++
				managedCount++
			}
		}
	}

	metrics.UpdateManagedDeployments(deploymentCounts)

	policyList := &availabilityv1alpha1.AvailabilityPolicyList{}
	if err := c.List(ctx, policyList); err != nil {
		logger.Error(err, "Failed to list policies for metrics")
		return
	}

	policyCounts := make(map[string]int)
	for _, policy := range policyList.Items {
		policyCounts[policy.Namespace]++
	}

	metrics.UpdateActivePoliciesCount(policyCounts)

	logger.V(1).Info("Updated global metrics",
		"managedDeployments", managedCount,
		"activePolicies", len(policyList.Items))
}

type Configuration struct {
	EnablePDB               bool
	DefaultNamespace        string
	MetricsNamespace        string
	LeaderElectionNamespace string
}

func printStartupBanner() {
	setupLog.Info("==============================================")
	setupLog.Info("PDB Management Operator for ODA Canvas")
	setupLog.Info("==============================================")
	setupLog.Info("TM Forum Open Digital Architecture Support")
	setupLog.Info("Pod Disruption Budget Automation")
	setupLog.Info("Mode: Annotation and Policy-based processing")
	setupLog.Info("Optimized for a high number of deployments")
	setupLog.Info("==============================================")
}

func validateConfiguration() *Configuration {
	config := &Configuration{
		EnablePDB:               getEnvBool("ENABLE_PDB", true),
		DefaultNamespace:        getEnvOrDefault("DEFAULT_NAMESPACE", "default"),
		MetricsNamespace:        getEnvOrDefault("METRICS_NAMESPACE", "canvas"),
		LeaderElectionNamespace: getEnvOrDefault("LEADER_ELECTION_NAMESPACE", "canvas"),
	}

	setupLog.Info("Operator Configuration",
		"enablePDB", config.EnablePDB,
		"defaultNamespace", config.DefaultNamespace,
		"leaderElectionNamespace", config.LeaderElectionNamespace)

	return config
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value == "true"
}

func getBuildVersion() string {
	version := os.Getenv("BUILD_VERSION")
	if version == "" {
		return "dev"
	}
	return version
}

func getWatchNamespaceDisplay(namespace string) string {
	if namespace == "" {
		return "all"
	}
	return namespace
}
