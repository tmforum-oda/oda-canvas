"""
ComponentRegistryClient

A helper class to communicate with a ComponentRegistry endpoint.
"""
from dotenv import load_dotenv
load_dotenv()  # take environment variables

import sys
import requests
from typing import List, Dict, Any
import asyncio
import threading

from app.oauth2_httpx_async import auth_client


class ComponentRegistryClient:
    
    """
    Helper class to communicate with a ComponentRegistry endpoint.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    async def find_exposed_apis(self, oas_specification: str) -> List[Dict[str, Any]]:
        """
        Query the ComponentRegistry for ExposedAPIs matching the oas_specification.
        Returns a list of matching ExposedAPIs (with their parent Component info).
        """
        try:
            filter_str = f"$[?(@.resourceCharacteristic[?(@.name=='specification' && @.value[?(@.url=='{oas_specification}')])])]"
            url = f"{self.base_url}/resource"
            response = await auth_client.get(url, params={"filter": filter_str}, timeout=10)
            response.raise_for_status()
            return response.json()  # List of Components, each with filtered ExposedAPIs
        except Exception as e:
            print(f"Error querying {self.base_url}: {e}", file=sys.stderr)
            return []

    async def get_upstream_registries(self) -> List[str]:
        """
        Query the ComponentRegistry for its upstream registries.
        Returns a list of upstream registry URLs.
        """
        try:
            url = f"{self.base_url}/hub"
            response = await auth_client.get(url, timeout=10)
            response.raise_for_status()
            registries = response.json()  # List of ComponentRegistry objects
            return [reg["callback"].replace("/sync", "") for reg in registries if "callback" in reg]
        except Exception as e:
            print(f"Error fetching upstream registries from {self.base_url}: {e}", file=sys.stderr)
            return []
        
        
    async def get_resources(self) -> List[str]:
        """
        Query the ComponentRegistry for resources.
        Returns a list of resources.
        """
        try:
            url = f"{self.base_url}/resource"
            response = await auth_client.get(url, timeout=10)
            response.raise_for_status()
            resources = response.json()  # List of resources
            return resources
        except Exception as e:
            print(f"Error fetching resources from {self.base_url}: {e}", file=sys.stderr)
            return []

            
if __name__ == "__main__":
    # cr = ComponentRegistryClient("https://canvas-compreg.ihc-dt.cluster-2.de/")
    cr = ComponentRegistryClient("http://localhost:8080/")
    result = asyncio.run(cr.get_resources())
    print(result)
    