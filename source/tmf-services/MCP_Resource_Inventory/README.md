# TMF639 Resource Inventory MCP Server with Helm Integration

This microservice implements a Model Context Protocol (MCP) server that provides a standardized interface to access the TM Forum Resource Inventory API (TMF639) with integrated Helm management capabilities for TM Forum ODA Components. It allows AI agents to interact with both the Resource Inventory component and manage ODA Component lifecycles through the MCP standard.

## What is MCP?

Model Context Protocol (MCP) is a standard designed to enable AI agents to interact with tools and services in a consistent way. It allows AI agents to discover and use your API's capabilities without requiring custom integration for each service. For more information, see:

- [Model Context Protocol Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [MCP Specification](https://modelcontextprotocol.io/quickstart/server)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

## TMF639 Resource Inventory Management

The TMF639 Resource Inventory Management API provides read-only access to information about resources in the system inventory. Resources can be physical devices (servers, network equipment) or logical entities (software components, ODA Components, virtual resources).

### Key Features

- **Read-only Access**: TMF639 is designed for inventory queries and monitoring
- **Resource Discovery**: Find and list resources by various criteria
- **State Monitoring**: Check administrative, operational, and usage states
- **Relationship Mapping**: Understand dependencies and hierarchies
- **ODA Component Integration**: Discover deployed microservices and APIs
- **Helm Management**: Complete lifecycle management of ODA Components using Helm
- **TM Forum Repository Integration**: Direct access to TM Forum reference components

## Helm Integration for ODA Components

This server includes comprehensive Helm integration providing the following capabilities:

### Helm Tools Available
- **helm_search_charts**: Search for Helm charts in configured repositories
- **helm_list_releases**: List installed Helm releases (ODA Components)
- **helm_install_chart**: Install a Helm chart as an ODA Component
- **helm_upgrade_release**: Upgrade an existing Helm release
- **helm_uninstall_release**: Uninstall a Helm release (remove ODA Component)
- **helm_get_release_status**: Get detailed status of a Helm release
- **helm_manage_repositories**: Manage Helm repositories
- **helm_install_tmforum_component**: Install TM Forum ODA Components from reference repository

### TM Forum ODA Repository
Pre-configured with the official TM Forum ODA reference components repository:
- **Repository URL**: https://tmforum-oda.github.io/reference-example-components
- **Repository Name**: oda-components

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Access to TMF639 Resource Inventory API endpoint
- Helm 3.x installed and accessible in PATH (for Helm integration)
- Kubernetes cluster access (for ODA Component management)

## Installation and Setup

### Using uv (Recommended)

1. **Install uv** (if not already installed):
   ```powershell
   # On Windows using PowerShell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Alternative: Using pip
   pip install uv
   ```

2. **Navigate to the project directory**:
   ```powershell
   cd "c:\Dev\tmforum-oda\oda-canvas\source\tmf-services\TMF639_Resource_Inventory\MCPServerMicroservice"
   ```

3. **Install dependencies using uv**:
   ```powershell
   # Install production dependencies
   uv sync
   
   # Install with development dependencies
   uv sync --dev
   ```

4. **Activate the virtual environment** (optional, uv handles this automatically):
   ```powershell
   # uv automatically manages the virtual environment
   # But if you want to activate it manually:
   .venv\Scripts\Activate.ps1
   ```

### Using pip (Alternative)

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

Copy the example environment file and customize:

```powershell
# Copy example configuration
Copy-Item .env.example .env

# Edit configuration
notepad .env
```

Example `.env` configuration:
```env
# TMF639 API endpoint
TMF639_BASE_URL=http://localhost:8639/tmf-api/resourceInventoryManagement/v5

# MCP Server configuration  
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3001
LOG_LEVEL=INFO

# Optional: Enable debug mode
# DEBUG=true
```

### API Endpoint Configuration

The Resource Inventory API endpoint can be configured for different environments:

- **Local development**: `http://localhost:8639/tmf-api/resourceInventoryManagement/v5`
- **Kubernetes cluster**: `http://tmf639-resource-inventory:8080/tmf-api/resourceInventoryManagement/v5`

## Running the MCP Server

### Standard I/O Transport (Default - for AI clients)

```powershell
# Using uv (recommended)
uv run resource_inventory_mcp_server.py

# Alternative: Direct Python execution
uv run python resource_inventory_mcp_server.py
```

### Server-Sent Events (SSE) Transport (for web clients)

```powershell
# Using uv with arguments
uv run resource_inventory_mcp_server.py --transport=sse --port=3001

# Using environment variables
$env:MCP_TRANSPORT="sse"
$env:MCP_SERVER_PORT="3001"
uv run resource_inventory_mcp_server.py
```

### Development Mode (with auto-reload)

```powershell
# Install with development dependencies
uv sync --dev

# Run with development tools
uv run python -m uvicorn resource_inventory_mcp_server:app --reload --port 3001
```

## Testing

### Run API Tests

```powershell
# Run API connectivity tests
uv run test_resource_inventory_api.py

# Run with verbose output
uv run python test_resource_inventory_api.py --verbose
```

### Run Unit Tests with pytest

```powershell
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
uv run pytest test_resource_inventory_api.py

# Run with verbose output
uv run pytest -v
```

### Development Testing Commands

```powershell
# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .

# Linting
uv run flake8 .

# Run all quality checks
uv run black . && uv run isort . && uv run flake8 . && uv run mypy . && uv run pytest
```

### Manual API Testing

```powershell
# Test the API wrapper directly
uv run python -c "
import asyncio
from resource_inventory_api import get_resource
print(asyncio.run(get_resource()))
"
```

## MCP Tools Reference

### Resource Inventory Tools

#### `resource_get`
Retrieve resource information from the TMF639 Resource Inventory API.

**Parameters:**
- `resource_id` (optional): ID of specific resource to retrieve
- `fields` (optional): Comma-separated list of fields to include in response
- `offset` (optional): Starting position for paginated results
- `limit` (optional): Maximum number of results to return
- `filter` (optional): Filter criteria dictionary

**Example usage:**
```javascript
// Get all resources
await resource_get()

// Get specific resource
await resource_get({resource_id: "resource-123"})

// Get resources with pagination
await resource_get({offset: 0, limit: 10})
```

### Helm Tools for ODA Components

#### `helm_search_charts`
Search for Helm charts in configured repositories.

**Parameters:**
- `search_term`: Search term (e.g., "productcatalog", "component")
- `repository` (optional): Specific repository to search
- `version` (optional): Chart version filter
- `app_version` (optional): Application version filter

#### `helm_list_releases`
List installed Helm releases (ODA Components).

**Parameters:**
- `namespace` (optional): Kubernetes namespace filter
- `status_filter` (optional): Release status filter (deployed, failed, etc.)
- `chart_filter` (optional): Chart name filter

#### `helm_install_chart`
Install a Helm chart as an ODA Component.

**Parameters:**
- `release_name`: Name for the release
- `chart_reference`: Chart reference (repo/chart or URL)
- `namespace` (optional): Target namespace (default: components)
- `values` (optional): Values to override (JSON object)
- `version` (optional): Chart version to install
- `create_namespace` (optional): Create namespace if it doesn't exist

#### `helm_upgrade_release`
Upgrade an existing Helm release.

**Parameters:**
- `release_name`: Name of the release to upgrade
- `chart_reference` (optional): New chart reference
- `namespace` (optional): Release namespace
- `values` (optional): Values to override
- `version` (optional): Chart version

#### `helm_uninstall_release`
Uninstall a Helm release (remove ODA Component).

**Parameters:**
- `release_name`: Name of the release to uninstall
- `namespace` (optional): Release namespace
- `keep_history` (optional): Keep release history after uninstall

#### `helm_get_release_status`
Get detailed status of a Helm release.

**Parameters:**
- `release_name`: Name of the release
- `namespace` (optional): Release namespace

#### `helm_manage_repositories`
Manage Helm repositories.

**Parameters:**
- `action`: Action to perform ("add", "update", "remove", "list")
- `repo_name` (optional): Repository name (required for add/remove)
- `repo_url` (optional): Repository URL (required for add)

#### `helm_install_tmforum_component`
Install a TM Forum ODA Component from the reference repository.

**Parameters:**
- `component_name`: Name of the TM Forum component (e.g., "productcatalogmanagement")
- `release_name` (optional): Custom release name
- `namespace` (optional): Target namespace
- `values` (optional): Custom values to override
- `version` (optional): Component version

**Example usage:**
```javascript
// Search for TM Forum components
await helm_search_charts({search_term: "productcatalog"})

// Install a TM Forum component
await helm_install_tmforum_component({
  component_name: "productcatalogmanagement",
  namespace: "components"
})

// List all installed components
await helm_list_releases()
```

### Integration Verification

You can verify the integration is working properly:

```powershell
# Run the verification script
uv run verify_integration.py
```

## MCP Client Integration

### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "resource-inventory": {
      "command": "uv",
      "args": [
        "run", 
        "c:/Dev/tmforum-oda/oda-canvas/source/tmf-services/TMF639_Resource_Inventory/MCPServerMicroservice/resource_inventory_mcp_server.py"
      ],
      "cwd": "c:/Dev/tmforum-oda/oda-canvas/source/tmf-services/TMF639_Resource_Inventory/MCPServerMicroservice"
    }
  }
}
```

### Using Other MCP Clients

For SSE transport, connect to:
```
http://localhost:8000/
```

## MCP Tools

The MCP server exposes the following Resource Inventory operations as tools:

- `resource_get`: Retrieve resource information (with filtering, pagination)

## MCP Resources

The MCP protocol also allows a server to expose resources to a client:

- `resource://tmf639/resource/{resource_id}`: Access resource data directly
- `schema://tmf639/resource`: Access the resource schema definition

## MCP Prompt Templates

The MCP server provides several pre-built prompt templates:

- `list_resources_prompt`: Template for listing resources with filters
- `get_resource_details_prompt`: Template for getting detailed resource information
- `search_resources_by_type_prompt`: Template for searching by resource type/category
- `get_usage_help_prompt`: General help for using the TMF639 API

## Development

### Code Formatting

```powershell
# Format code with black
uv run black .

# Sort imports with isort
uv run isort .

# Lint with flake8
uv run flake8 .

# Type checking with mypy
uv run mypy .
```

### Development Workflow

1. **Make changes to the code**
2. **Format and lint**:
   ```powershell
   uv run black . && uv run isort . && uv run flake8 .
   ```
3. **Run tests**:
   ```powershell
   uv run pytest
   ```
4. **Test API integration**:
   ```powershell
   uv run test_resource_inventory_api.py
   ```

## Project Structure

```
TMF639_Resource_Inventory/MCPServerMicroservice/
├── resource_inventory_api.py          # API wrapper for TMF639
├── resource_inventory_mcp_server.py   # MCP Server implementation
├── test_resource_inventory_api.py     # Test suite
├── pyproject.toml                     # Project configuration
├── .python-version                    # Python version specification
├── .env                              # Environment variables
└── README.md                         # This file
```

## API Reference

### Resource States

Resources have multiple state dimensions:

- **Administrative State**: `locked`, `unlocked`, `shutdown`
- **Operational State**: `enable`, `disable`
- **Resource Status**: `available`, `reserved`, `suspended`, `alarm`, `standby`, `unknown`
- **Usage State**: `idle`, `active`, `busy`

### Resource Types

- **Physical Resources**: Hardware devices, equipment
- **Logical Resources**: Software components, virtual resources, ODA Components
- **Resource Collections**: Groups of related resources

### Common Use Cases

1. **Inventory Monitoring**: Check current status of all resources
2. **Capacity Planning**: Find available resources for allocation
3. **Dependency Analysis**: Understand resource relationships
4. **State Tracking**: Monitor operational and administrative states
5. **ODA Component Discovery**: Find deployed microservices and APIs

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the TMF639 API service is running on the expected port
2. **SSL Certificate Errors**: The API wrapper disables SSL verification for development
3. **Import Errors**: Ensure all dependencies are installed with `uv pip install -e .`

### Logs

Check the `logs/` directory for detailed API interaction logs.

### Debug Mode

Enable verbose logging:
```powershell
uv run test_resource_inventory_api.py --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Quick Start with uv

For the fastest setup experience, use `uv` (the modern Python package manager):

```powershell
# 1. Install uv if you haven't already
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Navigate to project directory
cd "c:\Dev\tmforum-oda\oda-canvas\source\tmf-services\TMF639_Resource_Inventory\MCPServerMicroservice"

# 3. Install dependencies
uv sync

# 4. Copy configuration template
Copy-Item ".env.example" ".env"

# 5. Run API tests
uv run python test_resource_inventory_api.py

# 6. Start the MCP server
uv run python resource_inventory_mcp_server.py
```

## Development Scripts

Use the provided PowerShell development script for common tasks:

```powershell
# Show available commands
.\dev.ps1 help

# Setup development environment
.\dev.ps1 setup

# Run tests
.\dev.ps1 test

# Start MCP server
.\dev.ps1 run

# Format and lint code
.\dev.ps1 check
```

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## Related Projects

- [TM Forum ODA Canvas](https://github.com/tmforum-oda/oda-canvas)
- [Product Catalog MCP Server](../../../reference-example-components/source/ProductCatalog/MCPServerMicroservice/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
