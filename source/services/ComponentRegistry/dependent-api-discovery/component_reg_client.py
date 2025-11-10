"""
ComponentRegistryClient

A helper class to communicate with a ComponentRegistry endpoint.
"""

import sys
import requests
from typing import List, Dict, Any


class ComponentRegistryClient:
    """
    Helper class to communicate with a ComponentRegistry endpoint.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def find_exposed_apis(self, oas_specification: str) -> List[Dict[str, Any]]:
        """
        Query the ComponentRegistry for ExposedAPIs matching the oas_specification.
        Returns a list of matching ExposedAPIs (with their parent Component info).
        """
        try:
            filter_str = f"$[?(@.resourceCharacteristic[?(@.name=='specification' && @.value[?(@.url=='{oas_specification}')])])]"
            url = f"{self.base_url}/resource"
            response = requests.get(url, params={"filter": filter_str}, timeout=10)
            response.raise_for_status()
            return response.json()  # List of Components, each with filtered ExposedAPIs
        except Exception as e:
            print(f"Error querying {self.base_url}: {e}", file=sys.stderr)
            return []

    def get_upstream_registries(self) -> List[str]:
        """
        Query the ComponentRegistry for its upstream registries.
        Returns a list of upstream registry URLs.
        """
        try:
            url = f"{self.base_url}/hub"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            registries = response.json()  # List of ComponentRegistry objects
            return [reg["callback"].replace("/sync", "") for reg in registries if "callback" in reg]
        except Exception as e:
            print(f"Error fetching upstream registries from {self.base_url}: {e}", file=sys.stderr)
            return []