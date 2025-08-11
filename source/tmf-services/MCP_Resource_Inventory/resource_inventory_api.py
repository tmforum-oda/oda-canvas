# Resource Inventory API module for making requests to Resource Inventory Component
import logging
from pathlib import Path
import json
import httpx
from httpx import Timeout
from typing import Any, List, Dict
from dotenv import load_dotenv
import os
import datetime
import uuid
import warnings

# Suppress SSL warnings since we're using verify=False
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
VALIDATE_SSL = False

# Load environment variables
load_dotenv()

RELEASE_NAME = os.environ.get("RELEASE_NAME", "local")

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("resource-inventory-api")

# Constants
if RELEASE_NAME == "local":
    API_URL = "http://localhost:8639/tmf-api/resourceInventoryManagement/v5"
else:
    API_URL = f"http://{RELEASE_NAME}-resinv:8639/tmf-api/resourceInventoryManagement/v5"
logger.info(f"API URL: {API_URL}")


async def get_resource(
    resource_id: str = None,
    fields: str = None,
    offset: int = None,
    limit: int = None,
    filter: dict = None,
) -> dict[str, Any] | None:
    """
    Get resource(s) from the Resource Inventory Management API.
    
    Args:
        resource_id: Specific resource ID to retrieve. If None, lists all resources.
        fields: Comma-separated list of fields to return
        offset: Pagination offset
        limit: Maximum number of items to return
        filter: Filter parameters as a dictionary
        
    Returns:
        Dictionary containing the resource(s) or None if error
    """
    base_url = f"{API_URL}/resource"
    
    if resource_id:
        url = f"{base_url}/{resource_id}"
        logger.info(f"Getting resource with ID: {resource_id}")
    else:
        url = base_url
        logger.info("Listing resources")

    # Add query parameters if provided
    params = {}
    if fields:
        params["fields"] = fields
    if offset is not None:
        params["offset"] = offset
    if limit is not None:
        params["limit"] = limit

    # Apply filters if provided
    if filter:
        for key, value in filter.items():
            # Format as per TMF API filtering convention
            params[key] = value
        logger.info(f"Applied filters: {filter}")

    if params:
        logger.info(f"With parameters: {params}")

    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json;charset=utf-8",
    }
    
    # Configure timeouts (in seconds)
    timeout = Timeout(
        connect=10.0,  # connection timeout
        read=30.0,  # read timeout
        write=10.0,  # write timeout
        pool=5.0,  # pool timeout
    )

    # Make the request
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            verify=VALIDATE_SSL,  # SSL certificate verification
        ) as client:
            try:
                logger.info(f"Sending GET request to: {url}")
                logger.info(f"Headers: {headers}")

                response = await client.get(url, headers=headers, params=params)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()

                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        logger.info("Response received successfully")
                        return response_json
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON response: {e}")
                        return None
                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")
                    return None

            except httpx.TimeoutException as e:
                logger.error(
                    f"Timeout Error: Request timed out after {timeout.read} seconds"
                )
                return None
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP Status Error: {e.response.status_code} - {e.response.text}"
                )
                return None
            except httpx.HTTPError as e:
                logger.error(f"HTTP Error: {e}")
                return None

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception("Stack trace:")
        return None


async def main():
    """Main function to demonstrate getting resources using example parameters."""
    logger.info("Starting Resource Inventory API demonstration")
    
    try:
        # Example 1: List all resources
        logger.info("Example 1: Listing all resources")
        all_resources = await get_resource()
        if all_resources:
            logger.info(f"Retrieved {len(all_resources) if isinstance(all_resources, list) else 1} resources")
        else:
            logger.error("Failed to retrieve resources")

        # Example 2: Get a specific resource (if any exist)
        if all_resources and isinstance(all_resources, list) and len(all_resources) > 0:
            first_resource_id = all_resources[0].get("id")
            if first_resource_id:
                logger.info(f"Example 2: Getting specific resource with ID: {first_resource_id}")
                specific_resource = await get_resource(resource_id=first_resource_id)
                if specific_resource:
                    logger.info(f"Retrieved resource: {specific_resource.get('name', 'Unnamed')}")
                else:
                    logger.error("Failed to retrieve specific resource")

        # Example 3: Filter resources by category (if supported)
        logger.info("Example 3: Filtering resources by category 'Component'")
        filtered_resources = await get_resource(filter={"category": "Component"})
        if filtered_resources:
            logger.info(f"Retrieved {len(filtered_resources) if isinstance(filtered_resources, list) else 1} filtered resources")
        else:
            logger.error("Failed to retrieve filtered resources")

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.exception("Stack trace:")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
