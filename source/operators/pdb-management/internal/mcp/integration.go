package mcp

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/go-logr/logr"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/server"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/tools"
	"github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/internal/mcp/transport"
	"k8s.io/client-go/kubernetes"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// MCPIntegration manages the MCP server integration with the PDB operator
type MCPIntegration struct {
	server     *server.MCPServer
	transport  *transport.HTTPTransport
	httpServer *http.Server
	logger     logr.Logger
	enabled    bool
	address    string
}

// Config contains configuration for MCP integration
type Config struct {
	Enabled    bool
	Address    string
	Logger     logr.Logger
	Client     client.Client
	KubeClient kubernetes.Interface
}

// NewMCPIntegration creates a new MCP integration instance
func NewMCPIntegration(cfg Config) *MCPIntegration {
	if !cfg.Enabled {
		return &MCPIntegration{
			enabled: false,
			logger:  cfg.Logger,
		}
	}

	if cfg.Address == "" {
		cfg.Address = ":8090" // Default MCP server port
	}

	// Create MCP server
	mcpServer := server.NewMCPServer(server.Config{
		Name:       "pdb-management-mcp-server",
		Version:    "v1.0.0",
		Logger:     cfg.Logger.WithName("mcp-server"),
		Client:     cfg.Client,
		KubeClient: cfg.KubeClient,
	})

	// Configure CORS for AI proxy endpoint
	// Allow requests from the web UI (configurable via environment variable)
	allowedOrigins := getConfiguredAllowedOrigins()
	cfg.Logger.Info("Configuring MCP transport with CORS", "allowedOrigins", allowedOrigins)

	// Create HTTP transport with CORS configuration
	transportConfig := transport.DefaultHTTPTransportConfig()
	transportConfig.AllowedOrigins = allowedOrigins

	httpTransport := transport.NewHTTPTransportWithConfig(mcpServer, cfg.Logger.WithName("mcp-transport"), transportConfig)

	return &MCPIntegration{
		server:    mcpServer,
		transport: httpTransport,
		logger:    cfg.Logger.WithName("mcp-integration"),
		enabled:   true,
		address:   cfg.Address,
	}
}

// Start starts the MCP server integration
func (m *MCPIntegration) Start(ctx context.Context) error {
	if !m.enabled {
		m.logger.Info("MCP server disabled, skipping start")
		return nil
	}

	// Register all tools
	if err := m.registerTools(); err != nil {
		return fmt.Errorf("failed to register MCP tools: %w", err)
	}

	// Create HTTP server
	m.httpServer = &http.Server{
		Addr:         m.address,
		Handler:      m.transport,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		m.logger.Info("Starting MCP HTTP server", "address", m.address)

		listener, err := net.Listen("tcp", m.address)
		if err != nil {
			m.logger.Error(err, "Failed to create listener for MCP server")
			return
		}

		if err := m.httpServer.Serve(listener); err != nil && err != http.ErrServerClosed {
			m.logger.Error(err, "MCP HTTP server failed")
		}
	}()

	// Wait for server to be ready
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case <-time.After(1 * time.Second):
				if m.isServerReady() {
					m.logger.Info("MCP server is ready and accepting requests", "address", m.address)
					return
				}
			}
		}
	}()

	return nil
}

// Stop stops the MCP server integration
func (m *MCPIntegration) Stop(ctx context.Context) error {
	if !m.enabled {
		return nil
	}

	m.logger.Info("Stopping MCP server")

	if m.httpServer != nil {
		shutdownCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()

		if err := m.httpServer.Shutdown(shutdownCtx); err != nil {
			m.logger.Error(err, "Failed to gracefully shutdown MCP server")
			return err
		}
	}

	m.logger.Info("MCP server stopped")
	return nil
}

// IsEnabled returns whether MCP integration is enabled
func (m *MCPIntegration) IsEnabled() bool {
	return m.enabled
}

// GetAddress returns the MCP server address
func (m *MCPIntegration) GetAddress() string {
	if !m.enabled {
		return ""
	}
	return m.address
}

// registerTools registers all MCP tools with the server
func (m *MCPIntegration) registerTools() error {
	client := m.server

	// Create tool instances
	analysisTools := tools.NewAnalysisTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("analysis-tools"),
	)

	recommendationTools := tools.NewRecommendationTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("recommendation-tools"),
	)

	managementTools := tools.NewManagementTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("management-tools"),
	)

	complianceTools := tools.NewComplianceTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("compliance-tools"),
	)

	backupTools := tools.NewBackupTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("backup-tools"),
	)

	monitoringTools := tools.NewMonitoringTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("monitoring-tools"),
	)

	optimizationTools := tools.NewOptimizationTools(
		client.GetClient(),
		client.GetKubeClient(),
		m.logger.WithName("optimization-tools"),
	)

	// Register analysis tools
	if err := tools.RegisterAnalysisTools(m.server, analysisTools); err != nil {
		return fmt.Errorf("failed to register analysis tools: %w", err)
	}
	m.logger.Info("Registered analysis tools")

	// Register recommendation tools
	if err := tools.RegisterRecommendationTools(m.server, recommendationTools); err != nil {
		return fmt.Errorf("failed to register recommendation tools: %w", err)
	}
	m.logger.Info("Registered recommendation tools")

	// Register management tools
	if err := tools.RegisterManagementTools(m.server, managementTools); err != nil {
		return fmt.Errorf("failed to register management tools: %w", err)
	}
	m.logger.Info("Registered management tools")

	// Register compliance tools
	if err := tools.RegisterComplianceTools(m.server, complianceTools); err != nil {
		return fmt.Errorf("failed to register compliance tools: %w", err)
	}
	m.logger.Info("Registered compliance tools")

	// Register backup tools
	if err := tools.RegisterBackupTools(m.server, backupTools); err != nil {
		return fmt.Errorf("failed to register backup tools: %w", err)
	}
	m.logger.Info("Registered backup tools")

	// Register monitoring tools
	if err := tools.RegisterMonitoringTools(m.server, monitoringTools); err != nil {
		return fmt.Errorf("failed to register monitoring tools: %w", err)
	}
	m.logger.Info("Registered monitoring tools")

	// Register optimization tools
	if err := tools.RegisterOptimizationTools(m.server, optimizationTools); err != nil {
		return fmt.Errorf("failed to register optimization tools: %w", err)
	}
	m.logger.Info("Registered optimization tools")

	m.logger.Info("All MCP tools registered successfully")
	return nil
}

// isServerReady checks if the MCP server is ready to accept requests
func (m *MCPIntegration) isServerReady() bool {
	if m.httpServer == nil {
		return false
	}

	// Determine the correct address for health check
	// If address is ":port" or "0.0.0.0:port", use 127.0.0.1:port for the check
	healthAddr := m.address
	if len(healthAddr) > 0 && healthAddr[0] == ':' {
		healthAddr = "127.0.0.1" + healthAddr
	} else {
		host, port, err := net.SplitHostPort(healthAddr)
		if err == nil && (host == "" || host == "0.0.0.0") {
			healthAddr = "127.0.0.1:" + port
		}
	}

	// Try to connect to the health endpoint
	client := &http.Client{Timeout: 1 * time.Second}
	resp, err := client.Get(fmt.Sprintf("http://%s/health", healthAddr))
	if err != nil {
		return false
	}
	defer func() { _ = resp.Body.Close() }()

	return resp.StatusCode == http.StatusOK
}

// getConfiguredAllowedOrigins returns the list of allowed CORS origins
// for the AI proxy endpoint. This is configurable via environment variables.
func getConfiguredAllowedOrigins() []string {
	// Check for environment variable configuration
	// MCP_CORS_ALLOWED_ORIGINS can be comma-separated list of origins
	// e.g., "http://localhost:8080,https://myapp.example.com"
	envOrigins := os.Getenv("MCP_CORS_ALLOWED_ORIGINS")
	if envOrigins != "" {
		origins := strings.Split(envOrigins, ",")
		for i, origin := range origins {
			origins[i] = strings.TrimSpace(origin)
		}
		return origins
	}

	// Default allowed origins for development and common scenarios
	return []string{
		"http://localhost:8080", // Local web UI development
		"http://localhost:3000", // Common React dev server port
		"http://127.0.0.1:8080", // Alternative localhost
		"http://127.0.0.1:3000", // Alternative localhost for React
		"http://localhost:5173", // Vite dev server
		"http://127.0.0.1:5173", // Alternative for Vite
	}
}
