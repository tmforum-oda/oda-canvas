package transport

import (
	"net/http"
	"sync"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/metrics"
	"golang.org/x/time/rate"
)

// RateLimitConfig holds rate limiting configuration
type RateLimitConfig struct {
	// Enabled enables rate limiting
	Enabled bool
	// RequestsPerSecond is the rate limit in requests per second
	RequestsPerSecond float64
	// BurstSize is the maximum burst size
	BurstSize int
	// PerClientLimit enables per-client rate limiting (by IP)
	PerClientLimit bool
	// CleanupInterval is how often to clean up old client limiters
	CleanupInterval time.Duration
}

// DefaultRateLimitConfig returns sensible defaults
func DefaultRateLimitConfig() RateLimitConfig {
	return RateLimitConfig{
		Enabled:           false,
		RequestsPerSecond: 10.0,
		BurstSize:         20,
		PerClientLimit:    true,
		CleanupInterval:   5 * time.Minute,
	}
}

// RateLimiter provides rate limiting for HTTP requests
type RateLimiter struct {
	config        RateLimitConfig
	globalLimiter *rate.Limiter
	clientLimiter map[string]*clientLimiterEntry
	mu            sync.RWMutex
	logger        logr.Logger
	stopCleanup   chan struct{}
}

type clientLimiterEntry struct {
	limiter  *rate.Limiter
	lastSeen time.Time
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(config RateLimitConfig, logger logr.Logger) *RateLimiter {
	rl := &RateLimiter{
		config:        config,
		globalLimiter: rate.NewLimiter(rate.Limit(config.RequestsPerSecond), config.BurstSize),
		clientLimiter: make(map[string]*clientLimiterEntry),
		logger:        logger,
		stopCleanup:   make(chan struct{}),
	}

	if config.PerClientLimit && config.Enabled {
		go rl.cleanupLoop()
	}

	return rl
}

// Allow checks if a request is allowed
func (rl *RateLimiter) Allow(clientIP string) bool {
	if !rl.config.Enabled {
		return true
	}

	if rl.config.PerClientLimit {
		return rl.allowClient(clientIP)
	}

	return rl.globalLimiter.Allow()
}

// allowClient checks rate limit for a specific client
func (rl *RateLimiter) allowClient(clientIP string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	entry, exists := rl.clientLimiter[clientIP]
	if !exists {
		entry = &clientLimiterEntry{
			limiter:  rate.NewLimiter(rate.Limit(rl.config.RequestsPerSecond), rl.config.BurstSize),
			lastSeen: time.Now(),
		}
		rl.clientLimiter[clientIP] = entry
	} else {
		entry.lastSeen = time.Now()
	}

	return entry.limiter.Allow()
}

// cleanupLoop periodically removes stale client limiters
func (rl *RateLimiter) cleanupLoop() {
	ticker := time.NewTicker(rl.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			rl.cleanup()
		case <-rl.stopCleanup:
			return
		}
	}
}

// cleanup removes stale client limiters
func (rl *RateLimiter) cleanup() {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	threshold := time.Now().Add(-rl.config.CleanupInterval * 2)
	for ip, entry := range rl.clientLimiter {
		if entry.lastSeen.Before(threshold) {
			delete(rl.clientLimiter, ip)
		}
	}
}

// Stop stops the rate limiter cleanup goroutine
func (rl *RateLimiter) Stop() {
	if rl.config.PerClientLimit && rl.config.Enabled {
		close(rl.stopCleanup)
	}
}

// RateLimitMiddleware creates an HTTP middleware for rate limiting
func RateLimitMiddleware(rl *RateLimiter, logger logr.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			clientIP := getClientIP(r)

			if !rl.Allow(clientIP) {
				logger.Info("Rate limit exceeded",
					"client", clientIP,
					"path", r.URL.Path,
					"method", r.Method,
				)
				metrics.RecordMCPRateLimitExceeded(clientIP, r.URL.Path)

				w.Header().Set("Retry-After", "1")
				http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// getClientIP extracts the client IP from the request
func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header first (for proxied requests)
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// Take the first IP in the chain
		if idx := len(xff); idx > 0 {
			for i := 0; i < len(xff); i++ {
				if xff[i] == ',' {
					return xff[:i]
				}
			}
			return xff
		}
	}

	// Check X-Real-IP header
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	// Fall back to RemoteAddr
	return r.RemoteAddr
}
