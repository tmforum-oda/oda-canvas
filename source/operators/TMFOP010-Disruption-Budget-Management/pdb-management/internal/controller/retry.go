package controller

import (
	"context"
	"fmt"
	"time"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/util/wait"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// RetryConfig holds retry configuration
type RetryConfig struct {
	MaxRetries    int
	InitialDelay  time.Duration
	MaxDelay      time.Duration
	BackoffFactor float64
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

	return false
}

// RetryWithBackoff executes a function with exponential backoff retry
func RetryWithBackoff(ctx context.Context, config RetryConfig, operation func() error) error {
	backoff := wait.Backoff{
		Duration: config.InitialDelay,
		Factor:   config.BackoffFactor,
		Jitter:   0.1,
		Steps:    config.MaxRetries,
		Cap:      config.MaxDelay,
	}

	return wait.ExponentialBackoff(backoff, func() (bool, error) {
		select {
		case <-ctx.Done():
			return false, ctx.Err()
		default:
		}

		err := operation()
		if err == nil {
			return true, nil
		}

		if !RetryableError(err) {
			return false, err
		}

		return false, nil
	})
}

// RetryUpdateWithBackoff retries a client update operation with exponential backoff
func RetryUpdateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoff(ctx, config, func() error {
		return c.Update(ctx, obj)
	})
}

// RetryStatusUpdateWithBackoff retries a client status update operation with exponential backoff
func RetryStatusUpdateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoff(ctx, config, func() error {
		return c.Status().Update(ctx, obj)
	})
}

// RetryCreateWithBackoff retries a client create operation with exponential backoff
func RetryCreateWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoff(ctx, config, func() error {
		return c.Create(ctx, obj)
	})
}

// RetryDeleteWithBackoff retries a client delete operation with exponential backoff
func RetryDeleteWithBackoff(ctx context.Context, c client.Client, obj client.Object, config RetryConfig) error {
	return RetryWithBackoff(ctx, config, func() error {
		return c.Delete(ctx, obj)
	})
}

// RetryGetWithBackoff retries a client get operation with exponential backoff
func RetryGetWithBackoff(ctx context.Context, c client.Client, key client.ObjectKey, obj client.Object, config RetryConfig) error {
	return RetryWithBackoff(ctx, config, func() error {
		return c.Get(ctx, key, obj)
	})
}

// RetryListWithBackoff retries a client list operation with exponential backoff
func RetryListWithBackoff(ctx context.Context, c client.Client, list client.ObjectList, opts ...client.ListOption) error {
	config := DefaultRetryConfig()
	return RetryWithBackoff(ctx, config, func() error {
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
	default:
		return "unknown"
	}
}

// FormatRetryError formats a retry error with context
func FormatRetryError(operation string, attempts int, lastErr error) error {
	return fmt.Errorf("%s failed after %d attempts: %w", operation, attempts, lastErr)
}
