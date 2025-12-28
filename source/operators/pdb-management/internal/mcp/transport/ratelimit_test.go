package transport

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

func TestNewRateLimiter(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := DefaultRateLimitConfig()

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	assert.NotNil(t, rl)
	assert.NotNil(t, rl.globalLimiter)
	assert.NotNil(t, rl.clientLimiter)
}

func TestRateLimiter_Disabled(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := DefaultRateLimitConfig()
	config.Enabled = false

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	// Should always allow when disabled
	for i := 0; i < 100; i++ {
		assert.True(t, rl.Allow("192.168.1.1"))
	}
}

func TestRateLimiter_Enabled_GlobalLimit(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := RateLimitConfig{
		Enabled:           true,
		RequestsPerSecond: 5.0,
		BurstSize:         5,
		PerClientLimit:    false,
		CleanupInterval:   5 * time.Minute,
	}

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	// Should allow up to burst size
	allowed := 0
	for i := 0; i < 10; i++ {
		if rl.Allow("192.168.1.1") {
			allowed++
		}
	}
	// Should allow approximately burst size (5)
	assert.LessOrEqual(t, allowed, 6)
	assert.GreaterOrEqual(t, allowed, 4)
}

func TestRateLimiter_Enabled_PerClientLimit(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := RateLimitConfig{
		Enabled:           true,
		RequestsPerSecond: 5.0,
		BurstSize:         5,
		PerClientLimit:    true,
		CleanupInterval:   5 * time.Minute,
	}

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	// Client 1 should have its own limit
	client1Allowed := 0
	for i := 0; i < 10; i++ {
		if rl.Allow("192.168.1.1") {
			client1Allowed++
		}
	}

	// Client 2 should have independent limit
	client2Allowed := 0
	for i := 0; i < 10; i++ {
		if rl.Allow("192.168.1.2") {
			client2Allowed++
		}
	}

	// Both should allow approximately burst size
	assert.LessOrEqual(t, client1Allowed, 6)
	assert.GreaterOrEqual(t, client1Allowed, 4)
	assert.LessOrEqual(t, client2Allowed, 6)
	assert.GreaterOrEqual(t, client2Allowed, 4)
}

func TestRateLimiter_Cleanup(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := RateLimitConfig{
		Enabled:           true,
		RequestsPerSecond: 10.0,
		BurstSize:         10,
		PerClientLimit:    true,
		CleanupInterval:   100 * time.Millisecond,
	}

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	// Make a request to create a client entry
	rl.Allow("192.168.1.1")

	// Verify client entry exists
	rl.mu.RLock()
	_, exists := rl.clientLimiter["192.168.1.1"]
	rl.mu.RUnlock()
	assert.True(t, exists)

	// Wait for cleanup to run
	time.Sleep(300 * time.Millisecond)

	// Client entry should be cleaned up
	rl.mu.RLock()
	_, exists = rl.clientLimiter["192.168.1.1"]
	rl.mu.RUnlock()
	assert.False(t, exists)
}

func TestGetClientIP(t *testing.T) {
	tests := []struct {
		name          string
		xForwardedFor string
		xRealIP       string
		remoteAddr    string
		expectedIP    string
	}{
		{
			name:          "X-Forwarded-For single IP",
			xForwardedFor: "192.168.1.1",
			remoteAddr:    "127.0.0.1:8080",
			expectedIP:    "192.168.1.1",
		},
		{
			name:          "X-Forwarded-For multiple IPs",
			xForwardedFor: "192.168.1.1, 10.0.0.1, 172.16.0.1",
			remoteAddr:    "127.0.0.1:8080",
			expectedIP:    "192.168.1.1",
		},
		{
			name:       "X-Real-IP only",
			xRealIP:    "192.168.1.2",
			remoteAddr: "127.0.0.1:8080",
			expectedIP: "192.168.1.2",
		},
		{
			name:       "RemoteAddr fallback",
			remoteAddr: "192.168.1.3:8080",
			expectedIP: "192.168.1.3:8080",
		},
		{
			name:          "X-Forwarded-For takes precedence over X-Real-IP",
			xForwardedFor: "192.168.1.1",
			xRealIP:       "192.168.1.2",
			remoteAddr:    "127.0.0.1:8080",
			expectedIP:    "192.168.1.1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/", nil)
			req.RemoteAddr = tt.remoteAddr
			if tt.xForwardedFor != "" {
				req.Header.Set("X-Forwarded-For", tt.xForwardedFor)
			}
			if tt.xRealIP != "" {
				req.Header.Set("X-Real-IP", tt.xRealIP)
			}

			ip := getClientIP(req)
			assert.Equal(t, tt.expectedIP, ip)
		})
	}
}

func TestRateLimitMiddleware(t *testing.T) {
	logger := zap.New(zap.UseDevMode(true))
	config := RateLimitConfig{
		Enabled:           true,
		RequestsPerSecond: 2.0,
		BurstSize:         2,
		PerClientLimit:    true,
		CleanupInterval:   5 * time.Minute,
	}

	rl := NewRateLimiter(config, logger)
	defer rl.Stop()

	handler := RateLimitMiddleware(rl, logger)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))

	// First requests should succeed
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodGet, "/", nil)
		req.RemoteAddr = "192.168.1.1:8080"
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code)
	}

	// Next request should be rate limited
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.RemoteAddr = "192.168.1.1:8080"
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	assert.Equal(t, http.StatusTooManyRequests, w.Code)
	assert.Equal(t, "1", w.Header().Get("Retry-After"))
}

func TestDefaultRateLimitConfig(t *testing.T) {
	config := DefaultRateLimitConfig()

	assert.False(t, config.Enabled)
	assert.Equal(t, 10.0, config.RequestsPerSecond)
	assert.Equal(t, 20, config.BurstSize)
	assert.True(t, config.PerClientLimit)
	assert.Equal(t, 5*time.Minute, config.CleanupInterval)
}
