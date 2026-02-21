package controller

import (
	"context"
	"fmt"
	"sync"
	"time"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/util/wait"
	"sigs.k8s.io/controller-runtime/pkg/client"

	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/metrics"
)

// RetryConfig holds retry configuration
type RetryConfig struct {
	MaxRetries    int
	InitialDelay  time.Duration
	MaxDelay      time.Duration
	BackoffFactor float64
}

// Global retry configuration
var (
	globalRetryConfig = DefaultRetryConfig()
	retryConfigMu     sync.RWMutex
)

// SetGlobalRetryConfig sets the global retry configuration
func SetGlobalRetryConfig(config RetryConfig) {
	retryConfigMu.Lock()
	defer retryConfigMu.Unlock()
	globalRetryConfig = config
}

// GetGlobalRetryConfig returns the current global retry configuration
func GetGlobalRetryConfig() RetryConfig {
	retryConfigMu.RLock()
	defer retryConfigMu.RUnlock()
	return globalRetryConfig
}

// DefaultRetryConfig returns default retry configuration
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxRetries:    5,
		InitialDelay:  100 * time.Millisecond,
		MaxDelay:      30 * time.Second,
		BackoffFactor: 2.0,
	}
}

// RetryableError indicates if an error should be retried
func RetryableError(err error) bool {
	if err == nil {
		return false
	}

	// Check for conflict errors
	if errors.IsConflict(err) {
		return true
	}

	// Check for server timeout errors
	if errors.IsServerTimeout(err) {
		return true
	}

	// Check for network errors
	if errors.IsUnexpectedServerError(err) {
		return true
	}

	// Check for temporary errors
	if errors.IsTooManyRequests(err) {
		return true
	}

	// Check for service unavailable errors
	if errors.IsServiceUnavailable(err) {
		return true
	}

	return false
}

// RetryWithBackoff executes a function with exponential backoff retry.
//
// Deprecated: This wrapper is kept for backward compatibility and records retry metrics
// using the fixed operation name "unknown", which makes metrics less useful for debugging
// and monitoring. Callers should prefer RetryWithBackoffWithMetrics and provide a meaningful
// operationName so that retry metrics can be attributed correctly.
func RetryWithBackoff(ctx context.Context, config RetryConfig, operation func() error) error {
	return RetryWithBackoffWithMetrics(ctx, config, "unknown", operation)
}

// RetryWithBackoffWithMetrics executes a function with exponential backoff retry and records metrics
func RetryWithBackoffWithMetrics(ctx context.Context, config RetryConfig, operationName string, fn func() error) error {
	backoff := wait.Backoff{
		Duration: config.InitialDelay,
		Factor:   config.BackoffFactor,
		Jitter:   0.1,
		Steps:    config.MaxRetries,
		Cap:      config.MaxDelay,
	}

	attempt := 0
	var lastErr error

	err := wait.ExponentialBackoff(backoff, func() (bool, error) {
		select {
		case <-ctx.Done():
			return false, ctx.Err()
		default:
		}

		attempt++
		lastErr = fn()

		if lastErr == nil {
			// Success - record if we had to retry
			metrics.RecordRetrySuccess(operationName, attempt)
			return true, nil
		}

		// Record retry attempt
		errorType := GetErrorType(lastErr)
		metrics.RecordRetryAttempt(operationName, errorType, attempt)

		if !RetryableError(lastErr) {
			return false, lastErr
		}

		return false, nil
	})

	if err != nil && lastErr != nil {
		// Retries exhausted
		metrics.RecordRetryExhausted(operationName, GetErrorType(lastErr))
	}

	return err
}

// RetryUpdateWithBackoff retries a client update operation with exponential backoff
func RetryUpdateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoffWithMetrics(ctx, config, "update", func() error {
		return c.Update(ctx, obj)
	})
}

// RetryStatusUpdateWithBackoff retries a client status update operation with exponential backoff
func RetryStatusUpdateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoffWithMetrics(ctx, config, "status_update", func() error {
		return c.Status().Update(ctx, obj)
	})
}

// RetryCreateWithBackoff retries a client create operation with exponential backoff
func RetryCreateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoffWithMetrics(ctx, config, "create", func() error {
		return c.Create(ctx, obj)
	})
}

// RetryDeleteWithBackoff retries a client delete operation with exponential backoff
func RetryDeleteWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoffWithMetrics(ctx, config, "delete", func() error {
		return c.Delete(ctx, obj)
	})
}

// RetryGetWithBackoff retries a client get operation with exponential backoff
func RetryGetWithBackoff(ctx context.Context, c client.Client, key client.ObjectKey, obj client.Object, config RetryConfig) error {
	return RetryWithBackoffWithMetrics(ctx, config, "get", func() error {
		return c.Get(ctx, key, obj)
	})
}

// RetryListWithBackoff retries a client list operation with exponential backoff
func RetryListWithBackoff(ctx context.Context, c client.Client, list client.ObjectList, opts ...client.ListOption) error {
	config := GetGlobalRetryConfig()
	return RetryWithBackoffWithMetrics(ctx, config, "list", func() error {
		return c.List(ctx, list, opts...)
	})
}

// IsConflictError checks if an error is a conflict error
func IsConflictError(err error) bool {
	return errors.IsConflict(err)
}

// IsNotFoundError checks if an error is a not found error
func IsNotFoundError(err error) bool {
	return errors.IsNotFound(err)
}

// IsAlreadyExistsError checks if an error is an already exists error
func IsAlreadyExistsError(err error) bool {
	return errors.IsAlreadyExists(err)
}

// GetErrorType returns a human-readable error type
func GetErrorType(err error) string {
	if err == nil {
		return "none"
	}

	switch {
	case errors.IsConflict(err):
		return "conflict"
	case errors.IsNotFound(err):
		return "not_found"
	case errors.IsAlreadyExists(err):
		return "already_exists"
	case errors.IsServerTimeout(err):
		return "server_timeout"
	case errors.IsTooManyRequests(err):
		return "too_many_requests"
	case errors.IsUnexpectedServerError(err):
		return "server_error"
	case errors.IsServiceUnavailable(err):
		return "service_unavailable"
	default:
		return "unknown"
	}
}

// FormatRetryError formats a retry error with context
func FormatRetryError(operation string, attempts int, lastErr error) error {
	return fmt.Errorf("%s failed after %d attempts: %w", operation, attempts, lastErr)
}
