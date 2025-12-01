# MCP Server implementation on top of TM Forum Resource Inventory component.
# This script sets up a FastMCP server that interacts with the Resource Inventory API to handle queries and responses.
#
# Transport can be configured via command-line arguments or environment variables:
# - --transport=stdio or MCP_TRANSPORT=stdio for standard input/output (default)
# - --transport=sse or MCP_TRANSPORT=sse for Server-Sent Events
#
# When using SSE transport, port can be specified:
# - --port=8000 or MCP_PORT=8000 (default port is 8000)

# logging and system imports
import logging
import os
import sys
import argparse
from pathlib import Path

# MCP Server imports
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn


# Import API functionality
from resource_inventory_api import get_resource

# Import Helm API functionality
from helm_api import HelmAPI, HelmAPIError

# Additional imports for Helm operations
import json

# ---------------------------------------------------------------------------------------------
# Configure logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("resource-inventory-mcp")
logger.info("Resource Inventory MCP Server")

# ---------------------------------------------------------------------------------------------
# MCP server code

# Initialize FastMCP server
mcp = FastMCP(name="ODACanvas", version="1.0.0")


# ---------------------------------------------------------------------------------------------
# MCP tools
# This section defines the tools for the MCP server to interact with the TM Forum Resource Inventory Management API.
# Note: TMF639 Resource Inventory is read-only, so only GET operations are supported.


@mcp.tool()
async def resource_get(
    resource_id: str = None,
    fields: str = None,
    offset: int = None,
    limit: int = None,
    filter: dict = None,
) -> dict:
    """Retrieve resource information from the TM Forum Resource Inventory Management API.

    This tool provides read-only access to resources in the inventory. Resources can represent
    physical or logical assets that are being managed by the system.

    Args:
        resource_id: Optional ID of a specific resource to retrieve. If not provided, returns all resources.
        fields: Optional comma-separated list of fields to include in the response.
        offset: Optional starting position for paginated results.
        limit: Optional maximum number of results to return.
        filter: Optional dictionary of filter criteria to apply to the search.    Returns:
        A dictionary containing the resource(s) information or an error message.
    """
    if filter:
        logger.info(f"MCP Tool - Getting resources with filter: {filter}")
    else:
        logger.info(
            f"MCP Tool - Getting resource with ID: {resource_id if resource_id else 'ALL'}"
        )
    
    result = await get_resource(
        resource_id=resource_id,
        fields=fields,
        offset=offset,
        limit=limit,
        filter=filter,
    )
    if result == None:
        logger.warning("Failed to retrieve resource data")
        return {"error": "Failed to retrieve resource data"}
    
    return result


# ---------------------------------------------------------------------------------------------
# Helm tools for ODA Component management
# These tools provide Helm chart management capabilities for TM Forum ODA Components


@mcp.tool()
async def search_component_repositories(
    search_term: str = None,
    repository: str = None
) -> dict:
    """Search for component helm charts in configured repositories.
    
    This tool searches for Helm charts that can be installed as ODA Components.
    
    Args:
        search_term: Search term to find charts (e.g., "productcatalog")
        repository: Specific repository to search (default: searches all)
        
    Returns:
        A dictionary containing search results or error information.
    """    
    logger.info(f"MCP Tool - Searching Helm charts with term: {search_term}")
    
    try:
        helm = HelmAPI()
        

        
        logger.info(f"Helm API - Calling search_charts with term: '{search_term}', repository: {repository}")
        results = await helm.search_charts(
            search_term=search_term,
            repository=repository
        )
        logger.info(f"Helm API - search_charts returned {len(results)} results")
        
        return {
            "search_term": search_term,
            "charts": results,
            "count": len(results)
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm search error: {e}")
        return {"error": f"Helm search failed: {str(e)}"}


@mcp.tool()
async def list_component_releases(
    namespace: str = None
) -> dict:
    """List installed Component releases (installed components).
    
    This tool lists all Component releases that are currently installed, which represent
    deployed ODA Components in the canvas environment.
    
    Args:
        namespace: Kubernetes namespace to list releases from
        
    Returns:
        A dictionary containing the list of releases or error information.
    """    
    logger.info(f"MCP Tool - Listing Helm releases in namespace: {namespace or 'components'}")
    
    try:
        helm = HelmAPI()
        
        logger.info(f"Helm API - Calling list_releases with namespace: {namespace}")
        releases = await helm.list_releases(
            namespace=namespace
        )
          
        logger.info(f"Helm API - list_releases returned {len(releases)} releases")
        
        return {
            "releases": [vars(release) if hasattr(release, '__dict__') else release for release in releases],
            "count": len(releases),
            "namespace": namespace or "components"
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm list error: {e}")
        return {"error": f"Failed to list Helm releases: {str(e)}"}


@mcp.tool()
async def install_component(
    release_name: str,
    chart_name: str,
    chart_version: str = None,
    namespace: str = "components",
    values: dict = None,
    repository: str = "oda-components"
) -> dict:
    """Install a Helm chart as an ODA Component.
    
    This tool installs Helm charts from the TM Forum ODA repository or other
    configured repositories. The installed chart becomes an ODA Component.
    
    Args:
        release_name: Name for the Helm release (ODA Component instance)
        chart_name: Name of the chart to install
        chart_version: Specific version of the chart to install
        namespace: Kubernetes namespace for installation
        values: Dictionary of values to override chart defaults
        repository: Repository to install from (default: oda-components)
        
    Returns:
        A dictionary containing installation results or error information.
    """    
    logger.info(f"MCP Tool - Installing Helm chart {chart_name} as {release_name}")
    
    try:
        helm = HelmAPI()
        
        logger.info(f"Helm API - Calling install_chart with release_name: {release_name}, chart_name: {chart_name}, chart_version: {chart_version}, namespace: {namespace}")
        result = await helm.install_chart(
            release_name=release_name,
            chart_name=chart_name,
            chart_version=chart_version,
            namespace=namespace,
            values=values,
            repository=repository
        )
        logger.info(f"Helm API - install_chart completed successfully for release: {release_name}")
        
        return {
            "status": "success",
            "release_name": release_name,
            "chart_name": chart_name,
            "chart_version": chart_version,
            "namespace": namespace or "components",
            "output": result
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm install error: {e}")
        return {"error": f"Failed to install chart {chart_name}: {str(e)}"}


@mcp.tool()
async def upgrade_component(
    release_name: str,
    chart_name: str = None,
    chart_version: str = None,
    namespace: str = None,
    values: dict = None,
    repository: str = None
) -> dict:
    """Upgrade an existing Helm release (ODA Component).
    
    This tool upgrades an existing ODA Component to a new version or with
    new configuration values.
    
    Args:
        release_name: Name of the existing release to upgrade
        chart_name: Chart name (if changing from current chart)
        chart_version: New version to upgrade to
        namespace: Kubernetes namespace of the release
        values: Dictionary of values to override
        repository: Repository to upgrade from (default: oda-components)
        
    Returns:
        A dictionary containing upgrade results or error information.
    """    
    logger.info(f"MCP Tool - Upgrading Helm release {release_name}")
    
    try:
        helm = HelmAPI()
        
        logger.info(f"Helm API - Calling upgrade_chart with release_name: {release_name}, chart_name: {chart_name}, chart_version: {chart_version}, namespace: {namespace}")
        result = await helm.upgrade_chart(
            release_name=release_name,
            chart_name=chart_name,
            chart_version=chart_version,
            namespace=namespace,
            values=values,
            repository=repository
        )
        logger.info(f"Helm API - upgrade_release completed successfully for release: {release_name}")
        
        return {
            "status": "success",
            "release_name": release_name,
            "chart_version": chart_version,
            "namespace": namespace or "components",
            "output": result
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm upgrade error: {e}")
        return {"error": f"Failed to upgrade release {release_name}: {str(e)}"}


@mcp.tool()
async def uninstall_component(
    release_name: str,
    namespace: str = "components"
) -> dict:
    """Uninstall an ODA Component (Helm release).
    
    This tool removes an ODA Component by uninstalling its Helm release.
    Use with caution as this will delete the component and its resources.
    
    Args:
        release_name: Name of the release to uninstall
        namespace: Kubernetes namespace of the release
        
    Returns:
        A dictionary containing uninstallation results or error information.
    """    
    logger.info(f"MCP Tool - Uninstalling Helm release {release_name}")
    
    try:
        helm = HelmAPI()
        
        logger.info(f"Helm API - Calling uninstall_release with release_name: {release_name}, namespace: {namespace}")
        result = await helm.uninstall_release(
            release_name=release_name,
            namespace=namespace
        )
        logger.info(f"Helm API - uninstall_release completed successfully for release: {release_name}")
        
        return {
            "status": "success",
            "release_name": release_name,
            "namespace": namespace or "components",
            "output": result
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm uninstall error: {e}")
        return {"error": f"Failed to uninstall release {release_name}: {str(e)}"}


@mcp.tool()
async def get_component_release_status(
    release_name: str,
    namespace: str = "components"
) -> dict:
    """Get detailed status of an ODA Component Helm release.
    
    This tool provides detailed information about an installed ODA Component,
    including its current status, values, and Kubernetes resources.
    
    Args:
        release_name: Name of the release to check
        namespace: Kubernetes namespace of the release
        
    Returns:
        A dictionary containing detailed release information or error.
    """    
    print(f"MCP Tool - Getting status for Helm release {release_name}")
    
    try:
        helm = HelmAPI()
        
        logger.info(f"Helm API - Calling get_release_status with release_name: {release_name}, namespace: {namespace}")
        status = await helm.get_release_status(
            release_name=release_name,
            namespace=namespace
        )
        logger.info(f"Helm API - get_release_status completed successfully for release: {release_name}")
        
        return {
            "release_name": release_name,
            "namespace": namespace or "components",
            "status": status
        }
        
    except HelmAPIError as e:
        logger.error(f"Helm status error: {e}")
        return {"error": f"Failed to get status for release {release_name}: {str(e)}"}


@mcp.tool()
async def helm_manage_repositories(
    action: str,
    repository_name: str = None,
    repository_url: str = None
) -> dict:
    """Manage Helm repositories for ODA Components.
    
    This tool allows you to add, update, list, or remove Helm repositories.
    The TM Forum ODA repository is automatically configured.
    
    Args:
        action: Action to perform (list, add, update, remove)
        repository_name: Name of the repository (required for add/remove)
        repository_url: URL of the repository (required for add)
        
    Returns:
        A dictionary containing repository management results or error.
    """
    logger.info(f"MCP Tool - Managing Helm repository: {action}")
    
    try:
        helm = HelmAPI()
        if action == "list":
            logger.info("Helm API - Calling list_repositories")
            repos = await helm.list_repositories()
            logger.info(f"Helm API - list_repositories returned {len(repos)} repositories")
            return {
                "action": "list",
                "repositories": repos,
                "count": len(repos)
            }
        elif action == "add":
            if not repository_name or not repository_url:
                return {"error": "Repository name and URL are required for add action"}
                
            logger.info(f"Helm API - Calling add_repository with name: {repository_name}, url: {repository_url}")
            await helm.add_repository(repository_name, repository_url)
            logger.info(f"Helm API - add_repository completed successfully")
            return {
                "action": "add",
                "repository_name": repository_name,
                "repository_url": repository_url,
                "status": "success"
            }
        elif action == "update":
            logger.info("Helm API - Calling update_repositories")
            await helm.update_repositories()
            logger.info("Helm API - update_repositories completed successfully")
            return {
                "action": "update",
                "status": "success",
                "message": "All repositories updated"
            }
            
        elif action == "remove":
            if not repository_name:
                return {"error": "Repository name is required for remove action"}
                
            logger.info(f"Helm API - Calling remove_repository with name: {repository_name}")
            await helm.remove_repository(repository_name)
            logger.info(f"Helm API - remove_repository completed successfully")
            return {
                "action": "remove",
                "repository_name": repository_name,
                "status": "success"
            }
            
        else:
            return {"error": f"Unknown action: {action}. Supported actions: list, add, update, remove"}
        
    except HelmAPIError as e:
        logger.error(f"Helm repository management error: {e}")
        return {"error": f"Repository operation failed: {str(e)}"}




# ---------------------------------------------------------------------------------------------
# MCP resources
# These provides examples of how to define resources and their schemas for the TM Forum Resource Inventory Management API.


@mcp.resource("resource://tmf639/resource/{resource_id}")
async def resource_resource(resource_id: str = None) -> dict:
    """Retrieve resource information as a resource from the TM Forum Resource Inventory Management API.

    This resource represents a Resource in the inventory, which can be a physical or logical asset.
    Resources are read-only entities that describe the current state of inventory items.

    Args:
        resource_id: Optional ID of a specific resource to retrieve. If not provided, returns all resources.

    Returns:
        A structured representation of the resource(s) following the TMF639 specification.
    """
    logger.info(
        f"MCP Resource - Getting resource with ID: {resource_id if resource_id else 'ALL'}"
    )
    result = await get_resource(resource_id=resource_id)
    if result is None:
        logger.warning("Failed to retrieve resource data")
        return {"error": "Failed to retrieve resource data"}
    return result


@mcp.resource("schema://tmf639/resource")
async def resource_schema() -> dict:
    """Provide the schema definition for TMF639 Resource entities.

    Returns:
        A dictionary containing the complete schema definition for Resource entities,
        including all properties, relationships, and constraints as defined in the TMF639 specification.
    """
    return {
        "name": "Resource",
        "description": "Resource Inventory Management API schema for TMF639 Resource entities",
        "version": "5.0.0",
        "schema": {
            "type": "object",
            "description": "Resource is an abstract entity that describes the common set of attributes shared by all concrete resources (e.g. TPE, EQUIPMENT) in the inventory.",
            "properties": {
                "@baseType": {
                    "type": "string",
                    "description": "When sub-classing, this defines the super-class",
                },
                "@schemaLocation": {
                    "type": "string",
                    "format": "uri",
                    "description": "A URI to a JSON-Schema file that defines additional attributes and relationships",
                },
                "@type": {
                    "type": "string",
                    "description": "When sub-classing, this defines the sub-class entity name",
                },
                "id": {
                    "type": "string",
                    "description": "Unique identifier of the resource",
                },
                "href": {
                    "type": "string",
                    "description": "Reference of the resource",
                },
                "name": {
                    "type": "string",
                    "description": "The name of the resource",
                },
                "description": {
                    "type": "string",
                    "description": "Free-text description of the resource",
                },
                "category": {
                    "type": "string",
                    "description": "Category of the concrete resource. e.g Gold, Silver for MSISDN concrete resource",
                },
                "administrativeState": {
                    "type": "string",
                    "enum": ["locked", "unlocked", "shutdown"],
                    "description": "The administrative state of the resource",
                },
                "operationalState": {
                    "type": "string",
                    "enum": ["enable", "disable"],
                    "description": "The operational state of the resource",
                },
                "resourceStatus": {
                    "type": "string",
                    "enum": ["standby", "alarm", "available", "reserved", "unknown", "suspended"],
                    "description": "The status of the resource",
                },
                "usageState": {
                    "type": "string",
                    "enum": ["idle", "active", "busy"],
                    "description": "The usage state of the resource",
                },
                "startOperatingDate": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The date from which the resource is operating",
                },
                "endOperatingDate": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The date till the resource is operating",
                },
                "resourceVersion": {
                    "type": "string",
                    "description": "A field that identifies the specific version of an instance of a resource",
                },
                "validFor": {
                    "type": "object",
                    "description": "The period for which the resource is valid",
                    "properties": {
                        "startDateTime": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start date and time of the validity period",
                        },
                        "endDateTime": {
                            "type": "string",
                            "format": "date-time", 
                            "description": "End date and time of the validity period",
                        }
                    }
                },
                "resourceCharacteristic": {
                    "type": "array",
                    "description": "List of characteristics that describe the resource",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                            "valueType": {"type": "string"}
                        }
                    }
                },
                "supportingResource": {
                    "type": "array",
                    "description": "A collection of resources that support this resource",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "href": {"type": "string"},
                            "name": {"type": "string"},
                            "@referredType": {"type": "string"}
                        }
                    }
                },
                "resourceRelationship": {
                    "type": "array",
                    "description": "List of relationships this resource has with other resources",
                    "items": {
                        "type": "object",
                        "properties": {
                            "relationshipType": {"type": "string"},
                            "resource": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "href": {"type": "string"},
                                    "name": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "resourceSpecification": {
                    "type": "object",
                    "description": "Reference to the specification that defines this resource",
                    "properties": {
                        "id": {"type": "string"},
                        "href": {"type": "string"},
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "@referredType": {"type": "string"}
                    }
                },
                "place": {
                    "type": "array",
                    "description": "List of places where this resource is located",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "href": {"type": "string"},
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "@referredType": {"type": "string"}
                        }
                    }
                },
                "relatedParty": {
                    "type": "array",
                    "description": "List of parties related to this resource",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "href": {"type": "string"},
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "@referredType": {"type": "string"}
                        }
                    }
                },
                "note": {
                    "type": "array",
                    "description": "List of notes associated with this resource",
                    "items": {
                        "type": "object",
                        "properties": {
                            "author": {"type": "string"},
                            "date": {"type": "string", "format": "date-time"},
                            "text": {"type": "string"}
                        }
                    }
                },
                "attachment": {
                    "type": "array",
                    "description": "List of attachments related to this resource",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "href": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "mimeType": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    }
                }
            },
        },
        "operations": [
            {
                "name": "get",
                "description": "Retrieve resource information",
                "tool": "resource_get",
            },
        ],
        "examples": [
            {
                "name": "Firewall Device",
                "description": "Enterprise firewall appliance in the data center",
                "category": "Network Security",
                "administrativeState": "unlocked",
                "operationalState": "enable",
                "resourceStatus": "available",
                "usageState": "active",
                "@type": "PhysicalResource",
            },
            {
                "name": "Virtual Router Instance",
                "description": "Software-defined routing instance for customer network",
                "category": "Virtual Network Function",
                "administrativeState": "unlocked",
                "operationalState": "enable",
                "resourceStatus": "reserved",
                "usageState": "active",
                "@type": "LogicalResource",
            },
            {
                "name": "ODA Component - Product Catalog",
                "description": "Product Catalog microservice component",
                "category": "ODA Component",
                "administrativeState": "unlocked",
                "operationalState": "enable",
                "resourceStatus": "available",
                "usageState": "active",
                "@type": "LogicalResource",
            },
        ],
    }


# ---------------------------------------------------------------------------------------------
# MCP prompt examples
# These prompts provide templates for common operations with the Resource Inventory Management API

import datetime
import json


@mcp.prompt()
def list_resources_prompt(
    limit: int = 10,
    category: str = None,
    resource_status: str = None,
) -> str:
    """Generate a prompt for listing resources from the Resource Inventory.

    Args:
        limit: Maximum number of resources to retrieve (default: 10)
        category: Optional category filter (e.g., "Network Security", "ODA Component")
        resource_status: Optional status filter (e.g., "available", "reserved", "suspended")

    Returns:
        A formatted prompt string for listing resources.
    """
    
    filter_params = {}
    if category:
        filter_params["category"] = category
    if resource_status:
        filter_params["resourceStatus"] = resource_status
    
    filter_text = ""
    if filter_params:
        filter_text = f"with filters: {json.dumps(filter_params, indent=2)}"
    
    return f"""
I want to retrieve a list of resources from the Resource Inventory Management system.

Request details:
- Maximum results: {limit}
{f"- Filters: {filter_text}" if filter_text else "- No filters applied"}

The Resource Inventory contains information about physical and logical resources such as:
* Network equipment (firewalls, routers, switches)
* Virtual network functions and services
* ODA Components (microservices)
* Storage systems and devices
* Infrastructure resources

Each resource includes details about:
* Current operational and administrative states
* Resource characteristics and specifications
* Relationships with other resources
* Location and ownership information
* Status and usage information

Please retrieve the resources and provide a summary of what's available in the inventory.
"""


@mcp.prompt()
def get_resource_details_prompt(
    resource_id: str,
    include_relationships: bool = True,
    include_characteristics: bool = True,
) -> str:
    """Generate a prompt for retrieving detailed information about a specific resource.

    Args:
        resource_id: The ID of the resource to retrieve details for
        include_relationships: Whether to include related resources information (default: True)
        include_characteristics: Whether to include resource characteristics (default: True)

    Returns:
        A formatted prompt string for getting resource details.
    """
    
    fields_list = ["id", "name", "description", "category", "administrativeState", 
                   "operationalState", "resourceStatus", "usageState"]
    
    if include_relationships:
        fields_list.extend(["supportingResource", "resourceRelationship"])
    
    if include_characteristics:
        fields_list.append("resourceCharacteristic")
    
    fields_text = ", ".join(fields_list)
    
    return f"""
I want to retrieve detailed information about a specific resource from the Resource Inventory Management system.

Resource ID: {resource_id}

Please include the following information:
* Basic resource details (name, description, category)
* Current states (administrative, operational, resource status, usage)
{f"* Resource relationships and supporting resources" if include_relationships else ""}
{f"* Resource characteristics and properties" if include_characteristics else ""}
* Resource specification reference
* Location and party information if available

This will help me understand the current state and configuration of the resource, including how it relates to other resources in the inventory.
"""


@mcp.prompt()
def search_resources_by_type_prompt(
    resource_type: str,
    state_filter: str = None,
) -> str:
    """Generate a prompt for searching resources by type or category.

    Args:
        resource_type: The type or category of resources to search for
        state_filter: Optional state filter (e.g., "available", "active")

    Returns:
        A formatted prompt string for searching resources by type.
    """
    
    filter_params = {"category": resource_type}
    if state_filter:
        if state_filter in ["available", "reserved", "suspended", "alarm", "standby", "unknown"]:
            filter_params["resourceStatus"] = state_filter
        elif state_filter in ["active", "idle", "busy"]:
            filter_params["usageState"] = state_filter
        elif state_filter in ["enable", "disable"]:
            filter_params["operationalState"] = state_filter
    
    return f"""
I want to search for resources of a specific type in the Resource Inventory Management system.

Search criteria:
- Resource type/category: {resource_type}
{f"- State filter: {state_filter}" if state_filter else "- No state filter applied"}

Common resource types in the inventory include:
* "Network Security" - Firewalls, intrusion detection systems
* "ODA Component" - Microservice components and APIs
* "Virtual Network Function" - Software-defined network services  
* "Physical Infrastructure" - Servers, storage, network hardware
* "Cloud Resource" - Virtual machines, containers, cloud services

Please search for resources matching these criteria and provide:
* Total count of matching resources
* Summary of their current states
* Key characteristics and capabilities
* Any relationships between the resources

This will help me understand what resources of this type are available and their current status.

Filter parameters: {json.dumps(filter_params, indent=2)}
"""


@mcp.prompt()
def get_usage_help_prompt() -> str:
    """Generate a prompt providing general help for using the TMF639 Resource Inventory Management API.

    Returns:
        A formatted help prompt string.
    """
    return """
I need help understanding how to use the TMF639 Resource Inventory Management API effectively.

The Resource Inventory Management API (TMF639) provides read-only access to information about resources in the system inventory. Here's what you can do:

## Available Operations:

1. **List All Resources**
   - Get a complete or filtered list of all resources
   - Apply pagination with offset and limit parameters
   - Filter by category, status, or other attributes

2. **Get Specific Resource**
   - Retrieve detailed information about a resource by its ID
   - Include related resources and characteristics
   - View current operational and administrative states

## Key Resource Information:

* **States**: Resources have multiple state dimensions:
  - Administrative State: locked, unlocked, shutdown
  - Operational State: enable, disable  
  - Resource Status: available, reserved, suspended, alarm, standby, unknown
  - Usage State: idle, active, busy

* **Types**: Resources can be physical or logical:
  - Physical: Hardware devices, equipment
  - Logical: Software components, virtual resources, ODA Components

* **Relationships**: Resources can have complex relationships:
  - Supporting resources (dependencies)
  - Resource hierarchies (contains/contained-by)
  - Associations and references

## Common Use Cases:

1. **Inventory Monitoring**: Check current status of all resources
2. **Capacity Planning**: Find available resources for allocation
3. **Dependency Analysis**: Understand resource relationships
4. **State Tracking**: Monitor operational and administrative states
5. **ODA Component Discovery**: Find deployed microservices and APIs

## Example Filters:

* Find available network security resources
* List all ODA Components that are currently active
* Get physical resources in a specific location
* Find resources with specific characteristics

Would you like help with any specific operation or use case?
"""


# ---------------------------------------------------------------------------------------------
# Server configuration and startup

def parse_args():
    """Parse command line arguments for the MCP server."""
    parser = argparse.ArgumentParser(description="Resource Inventory MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport mechanism (stdio or sse)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port for SSE transport (default: 8000)",
    )
    return parser.parse_args()


def main():
    """Main entry point for the ODACanvas MCP Server."""
    args = parse_args()
    
    if args.transport == "stdio":
        logger.info("Starting ODACanvas MCP Server with stdio transport")
        mcp.run()
    elif args.transport == "sse":

        # Get the transport from command-line argument or environment variable
        transport = "sse"
        port = args.port

        logger.info(
            f"Starting ODACanvas MCP Server with {transport} transport on port {port}"
        )

        try:
            # Create a main FastAPI app
            main_app = FastAPI(title="ODACanvas MCP Server")

            # Create the SSE app using the MCP server's built-in method
            mcp_app = mcp.sse_app()

            # Mount the MCP server app at the url endpoint
            main_app.mount( "/mcp", mcp_app)

            # Run the ASGI app with uvicorn
            uvicorn.run(main_app, host="0.0.0.0", port=port)
        except KeyboardInterrupt:
            logger.info("Server shutting down")
        except Exception as e:
            logger.exception("Server error")
            sys.exit(1)
        else:
            logger.error(f"Unsupported transport: {args.transport}")
            sys.exit(1)


if __name__ == "__main__":
    main()
