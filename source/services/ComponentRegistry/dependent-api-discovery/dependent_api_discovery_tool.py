"""
Dependent API Discovery Tool

This tool takes an oas_specification and a local ComponentRegistry endpoint as input, searches for ExposedAPIs implementing the given oas_specification in the local registry, and if not found, recursively queries upstream registries until matches are found or the top level is reached.
"""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

import os
import sys
import argparse
import requests
from typing import List, Dict, Any, Set

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
            url = f"{self.base_url}/components/by-oas-specification"
            response = requests.get(url, params={"oas_specification": oas_specification}, timeout=10)
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
            url = f"{self.base_url}/registries/by-type/upstream"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            registries = response.json()  # List of ComponentRegistry objects
            return [reg["url"] for reg in registries if "url" in reg]
        except Exception as e:
            print(f"Error fetching upstream registries from {self.base_url}: {e}", file=sys.stderr)
            return []


def recursive_api_discovery(component_registry_url: str, oas_specification: str, visited: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Recursively search for ExposedAPIs implementing the oas_specification, starting from the given registry.
    Returns a list of matching ExposedAPIs (with their parent Component info).
    """
    if visited is None:
        visited = set()
    if component_registry_url in visited:
        return []  # Prevent cycles
    visited.add(component_registry_url)

    client = ComponentRegistryClient(component_registry_url)
    # 1. Search local registry
    matches = client.find_exposed_apis(oas_specification)
    if matches:
        return matches

    # 2. Query upstream registries recursively
    upstreams = client.get_upstream_registries()
    for upstream_url in upstreams:
        result = recursive_api_discovery(upstream_url, oas_specification, visited)
        if result:
            return result
    return []  # No matches found at any level


def main():
    parser = argparse.ArgumentParser(description="Dependent API Discovery Tool")
    parser.add_argument(
        "--oas_specification", "-s", 
        type=str, 
        help="OAS specification string to search for",
        default=os.getenv('OAS_SPECIFICATION', "?"),
    )
    parser.add_argument(
        "--component_registry_url", "-u", 
        type=str, 
        help="URL of the local ComponentRegistry endpoint",
        default=os.getenv('LOCAL_COMPREG_URL', "?"),
    )
    args = parser.parse_args()

    if not args.oas_specification or not args.component_registry_url:
        print("Both oas_specification and component_registry_url are required.", file=sys.stderr)
        sys.exit(1)

    print(f"Searching for ExposedAPIs implementing '{args.oas_specification}' starting from {args.component_registry_url} ...")
    matches = recursive_api_discovery(args.component_registry_url, args.oas_specification)
    if matches:
        print("Found matching ExposedAPIs:")
        for comp in matches:
            print(f"Component: {comp.get('component_name')} (Registry: {comp.get('component_registry_ref')})")
            for api in comp.get('exposed_apis', []):
                print(f"  - API: {api.get('name')}, OAS: {api.get('oas_specification')}, URL: {api.get('url')}")
    else:
        print("No matching ExposedAPIs found in any registry.")

if __name__ == "__main__":
    main()