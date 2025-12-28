package transport

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/logging"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/ai"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/server"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/types"
)

// HTTPTransportConfig holds configuration for HTTPTransport
type HTTPTransportConfig struct {
	// AllowedOrigins specifies which origins are allowed for CORS.
	// Use "*" for development only. In production, specify exact origins.
	AllowedOrigins []string
	// RateLimit configures rate limiting
	RateLimit RateLimitConfig
	// EnableAuditLog enables audit logging
	EnableAuditLog bool
	// APIKey is the API key required for /mcp endpoint authentication.
	// If empty, authentication is disabled (not recommended for production).
	APIKey string
	// MaxRequestBodySize is the maximum allowed request body size in bytes.
	// Default is 1MB (1048576 bytes). Set to 0 to use default.
	MaxRequestBodySize int64
}

// DefaultMaxRequestBodySize is 1MB
const DefaultMaxRequestBodySize int64 = 1 << 20 // 1MB

// DefaultHTTPTransportConfig returns the default configuration
func DefaultHTTPTransportConfig() HTTPTransportConfig {
	return HTTPTransportConfig{
		AllowedOrigins:     []string{}, // Empty means no CORS headers (same-origin only)
		RateLimit:          DefaultRateLimitConfig(),
		EnableAuditLog:     true,
		APIKey:             "", // Empty means no authentication (not recommended)
		MaxRequestBodySize: DefaultMaxRequestBodySize,
	}
}

// HTTPTransport handles HTTP-based MCP communication
type HTTPTransport struct {
	server             *server.MCPServer
	aiClient           *ai.Client
	logger             logr.Logger
	mux                *http.ServeMux
	allowedOrigins     map[string]bool
	rateLimiter        *RateLimiter
	auditLogger        *AuditLogger
	apiKey             string
	maxRequestBodySize int64
}

// NewHTTPTransport creates a new HTTP transport for MCP
func NewHTTPTransport(mcpServer *server.MCPServer, logger logr.Logger) *HTTPTransport {
	return NewHTTPTransportWithConfig(mcpServer, logger, DefaultHTTPTransportConfig())
}

// NewHTTPTransportWithConfig creates a new HTTP transport with configuration
func NewHTTPTransportWithConfig(mcpServer *server.MCPServer, logger logr.Logger, config HTTPTransportConfig) *HTTPTransport {
	allowedOrigins := make(map[string]bool)
	for _, origin := range config.AllowedOrigins {
		allowedOrigins[origin] = true
	}

	// Use default max body size if not specified
	maxBodySize := config.MaxRequestBodySize
	if maxBodySize <= 0 {
		maxBodySize = DefaultMaxRequestBodySize
	}

	// Log warning if authentication is disabled
	if config.APIKey == "" {
		logger.Info("WARNING: MCP endpoint authentication is disabled. This is not recommended for production.")
	}

	t := &HTTPTransport{
		server:             mcpServer,
		aiClient:           ai.NewClient(logger.WithName("ai-client")),
		logger:             logger,
		mux:                http.NewServeMux(),
		allowedOrigins:     allowedOrigins,
		rateLimiter:        NewRateLimiter(config.RateLimit, logger.WithName("rate-limiter")),
		auditLogger:        NewAuditLogger(logger, config.EnableAuditLog),
		apiKey:             config.APIKey,
		maxRequestBodySize: maxBodySize,
	}

	// Register handlers
	t.mux.HandleFunc("/mcp", t.handleMCPRequest)
	t.mux.HandleFunc("/health", t.handleHealth)
	t.mux.HandleFunc("/ai/proxy", t.handleAIProxy)

	return t
}

// Stop cleans up resources
func (t *HTTPTransport) Stop() {
	if t.rateLimiter != nil {
		t.rateLimiter.Stop()
	}
}

// ServeHTTP implements the http.Handler interface
func (t *HTTPTransport) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	t.mux.ServeHTTP(w, r)
}

// handleMCPRequest handles incoming MCP requests over HTTP
func (t *HTTPTransport) handleMCPRequest(w http.ResponseWriter, r *http.Request) {
	clientIP := getClientIP(r)

	// Check API key authentication if configured
	if t.apiKey != "" {
		authHeader := r.Header.Get("Authorization")
		apiKeyHeader := r.Header.Get("X-API-Key")

		authenticated := false
		if authHeader != "" && authHeader == "Bearer "+t.apiKey {
			authenticated = true
		} else if apiKeyHeader != "" && apiKeyHeader == t.apiKey {
			authenticated = true
		}

		if !authenticated {
			t.logger.Info("Authentication failed for MCP request", "client", clientIP)
			t.auditLogger.LogAuthFailure(r.Context(), clientIP, r.URL.Path, "invalid or missing API key")
			http.Error(w, "Unauthorized: invalid or missing API key", http.StatusUnauthorized)
			return
		}
	}

	// Check rate limit
	if !t.rateLimiter.Allow(clientIP) {
		t.logger.Info("Rate limit exceeded for MCP request", "client", clientIP)
		t.auditLogger.LogRateLimitExceeded(r.Context(), clientIP, r.URL.Path, r.Method)
		w.Header().Set("Retry-After", "1")
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Read request body with size limit to prevent DoS
	limitedReader := io.LimitReader(r.Body, t.maxRequestBodySize+1)
	body, err := io.ReadAll(limitedReader)
	if err != nil {
		t.logger.Error(err, "Failed to read request body")
		http.Error(w, "Failed to read request", http.StatusBadRequest)
		return
	}
	defer func() { _ = r.Body.Close() }()

	// Check if body exceeded the limit
	if int64(len(body)) > t.maxRequestBodySize {
		t.logger.Info("Request body too large", "client", clientIP, "size", len(body), "maxSize", t.maxRequestBodySize)
		http.Error(w, fmt.Sprintf("Request body too large (max %d bytes)", t.maxRequestBodySize), http.StatusRequestEntityTooLarge)
		return
	}

	// Parse MCP request
	var mcpReq types.Request
	if err := json.Unmarshal(body, &mcpReq); err != nil {
		t.logger.Error(err, "Failed to parse MCP request")
		http.Error(w, "Invalid request format", http.StatusBadRequest)
		return
	}

	// Add timestamp if not present
	if mcpReq.Created.IsZero() {
		mcpReq.Created = time.Now()
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	// Create MCP logger with request context
	startTime := time.Now()
	mcpLogger := logging.NewLogger(ctx).
		WithName("mcp").
		WithMCPRequest(mcpReq.Method, mcpReq.ID).
		WithValues("source", clientIP)

	mcpLogger.Info("Received MCP request")

	// Handle the request
	response, err := t.server.HandleRequest(ctx, &mcpReq)
	duration := time.Since(startTime)

	if err != nil {
		mcpLogger.Error(err, "Failed to handle MCP request")
		mcpLogger.AuditMCPRequest(mcpReq.Method, mcpReq.ID, clientIP, duration, logging.AuditResultFailure, err)
		t.auditLogger.LogMCPRequest(ctx, mcpReq.Method, mcpReq.ID, clientIP, r.UserAgent(), duration, err)
		response = &types.Response{
			ID: mcpReq.ID,
			Error: &types.Error{
				Code:    -32603,
				Message: fmt.Sprintf("Internal error: %v", err),
			},
			Created: time.Now(),
		}
	} else {
		// Log successful request
		mcpLogger.Info("MCP request completed successfully",
			"duration", duration.String(),
			"durationMs", duration.Milliseconds())
		mcpLogger.AuditMCPRequest(mcpReq.Method, mcpReq.ID, clientIP, duration, logging.AuditResultSuccess, nil)
		t.auditLogger.LogMCPRequest(ctx, mcpReq.Method, mcpReq.ID, clientIP, r.UserAgent(), duration, nil)
	}

	// Send response
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		mcpLogger.Error(err, "Failed to send response")
	}
}

// handleHealth handles health check requests
func (t *HTTPTransport) handleHealth(w http.ResponseWriter, r *http.Request) {
	// Check Kubernetes connectivity
	kubeConnected := false
	if kubeClient := t.server.GetKubeClient(); kubeClient != nil {
		// Try to get server version as a connectivity check
		_, err := kubeClient.Discovery().ServerVersion()
		kubeConnected = err == nil
	}

	status := map[string]interface{}{
		"status":      "healthy",
		"initialized": t.server.IsInitialized(),
		"timestamp":   time.Now().Unix(),
		"checks": map[string]bool{
			"mcp":        true,
			"kubernetes": kubeConnected,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(status)
}

// handleAIProxy handles AI provider proxy requests
func (t *HTTPTransport) handleAIProxy(w http.ResponseWriter, r *http.Request) {
	clientIP := getClientIP(r)

	// Check rate limit
	if !t.rateLimiter.Allow(clientIP) {
		t.logger.Info("Rate limit exceeded for AI proxy request", "client", clientIP)
		t.auditLogger.LogRateLimitExceeded(r.Context(), clientIP, r.URL.Path, r.Method)
		w.Header().Set("Retry-After", "1")
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	// Set CORS headers based on configuration
	origin := r.Header.Get("Origin")
	if t.isOriginAllowed(origin) {
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.Header().Set("Access-Control-Max-Age", "86400")
	} else if origin != "" {
		// Log CORS rejection
		t.auditLogger.LogCORSRejected(r.Context(), clientIP, origin, r.URL.Path)
	}

	// Handle preflight request
	if r.Method == "OPTIONS" {
		if origin == "" || !t.isOriginAllowed(origin) {
			w.WriteHeader(http.StatusForbidden)
			return
		}
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Read request body with size limit to prevent DoS
	limitedReader := io.LimitReader(r.Body, t.maxRequestBodySize+1)
	body, err := io.ReadAll(limitedReader)
	if err != nil {
		t.logger.Error(err, "Failed to read AI proxy request body")
		http.Error(w, "Failed to read request", http.StatusBadRequest)
		return
	}
	defer func() { _ = r.Body.Close() }()

	// Check if body exceeded the limit
	if int64(len(body)) > t.maxRequestBodySize {
		t.logger.Info("AI proxy request body too large", "client", clientIP, "size", len(body), "maxSize", t.maxRequestBodySize)
		http.Error(w, fmt.Sprintf("Request body too large (max %d bytes)", t.maxRequestBodySize), http.StatusRequestEntityTooLarge)
		return
	}

	// Parse AI proxy request
	var proxyReq struct {
		Config  ai.Config      `json:"config"`
		Request ai.ChatRequest `json:"request"`
	}

	if err := json.Unmarshal(body, &proxyReq); err != nil {
		t.logger.Error(err, "Failed to parse AI proxy request")
		http.Error(w, "Invalid request format", http.StatusBadRequest)
		return
	}

	// Validate provider and API key
	if proxyReq.Config.Provider == "" {
		http.Error(w, "Provider is required", http.StatusBadRequest)
		return
	}
	if proxyReq.Config.APIKey == "" {
		http.Error(w, "API key is required", http.StatusBadRequest)
		return
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(r.Context(), 120*time.Second)
	defer cancel()

	// Create logger with request context
	startTime := time.Now()
	proxyLogger := t.logger.WithValues(
		"provider", proxyReq.Config.Provider,
		"messageCount", len(proxyReq.Request.Messages),
		"source", r.RemoteAddr,
	)

	proxyLogger.Info("Received AI proxy request")

	// Make the AI provider request
	response, err := t.aiClient.Chat(ctx, proxyReq.Config, proxyReq.Request)
	duration := time.Since(startTime)

	if err != nil {
		proxyLogger.Error(err, "AI proxy request failed", "duration", duration.String())
		t.auditLogger.LogAIProxy(ctx, string(proxyReq.Config.Provider), clientIP, r.UserAgent(), origin, len(proxyReq.Request.Messages), duration, err)

		// Return structured error response
		errorResponse := map[string]interface{}{
			"success": false,
			"error":   err.Error(),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(errorResponse)
		return
	}

	// Log successful request
	proxyLogger.Info("AI proxy request completed successfully",
		"duration", duration.String(),
		"durationMs", duration.Milliseconds(),
		"responseLength", len(response.Message.Content))
	t.auditLogger.LogAIProxy(ctx, string(proxyReq.Config.Provider), clientIP, r.UserAgent(), origin, len(proxyReq.Request.Messages), duration, nil)

	// Return successful response
	successResponse := map[string]interface{}{
		"success": true,
		"data":    response,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(successResponse); err != nil {
		proxyLogger.Error(err, "Failed to send AI proxy response")
	}
}

// isOriginAllowed checks if the given origin is allowed for CORS
func (t *HTTPTransport) isOriginAllowed(origin string) bool {
	if origin == "" {
		return false
	}

	// Check for wildcard (only for development)
	if t.allowedOrigins["*"] {
		return true
	}

	// Check if origin is in the allowed list
	return t.allowedOrigins[origin]
}

// StartHTTPServer starts the HTTP server for MCP
func StartHTTPServer(addr string, transport *HTTPTransport, logger logr.Logger) error {
	logger.Info("Starting MCP HTTP server", "address", addr)

	server := &http.Server{
		Addr:         addr,
		Handler:      transport,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	return server.ListenAndServe()
}
