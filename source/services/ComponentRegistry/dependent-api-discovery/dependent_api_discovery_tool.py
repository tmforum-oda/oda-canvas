"""
Dependent API Discovery Tool

This tool takes an oas_specification and a local ComponentRegistry endpoint as input, searches for ExposedAPIs implementing the given oas_specification in the local registry, and if not found, recursively queries upstream registries until matches are found or the top level is reached.
"""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

import os
import sys
import argparse
from typing import List, Dict, Any

from component_reg_client import ComponentRegistryClient


def recursive_api_discovery(component_registry_url: str, oas_specification: str) -> List[Dict[str, Any]]:
    """
    Recursively search for ExposedAPIs implementing the oas_specification, starting from the given registry.
    Returns a list of matching ExposedAPIs (with their parent Component info).
    """
    component_registry_urls = [component_registry_url]
    visited = set()
    while (component_registry_urls):
        current_url = component_registry_urls.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        client = ComponentRegistryClient(current_url)
        # 1. Search local registry
        matches = client.find_exposed_apis(oas_specification)
        if matches:
            return matches

        # 2. Query upstream registries
        upstreams = client.get_upstream_registries()
        component_registry_urls.extend(upstreams)

    return []  # No matches found in any registryreturn


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