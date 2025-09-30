#!/usr/bin/env python3
"""
ODA Component Kubernetes to Registry Sync Tool

This command-line application reads ODA Component Custom Resources from Kubernetes
and synchronizes them with the Component Registry Service following TM Forum ODA Canvas specifications.

Usage:
    python k8s_component_sync.py --registry-url http://localhost:8080 --namespace components
    python k8s_component_sync.py --config config.yaml --dry-run
    python k8s_component_sync.py --help

Features:
    - Reads ODA Components from Kubernetes clusters
    - Transforms K8s Component CRDs to Registry Service format
    - Supports dry-run mode for testing
    - Handles multiple namespaces
    - Provides detailed logging and error handling
    - Follows TM Forum ODA Canvas patterns
"""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

import argparse
import logging
import sys
import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os



@dataclass
class RegistryConfig:
    """Configuration for Component Registry Service connection."""
    url: str
    timeout: int = 30
    verify_ssl: bool = True
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }


@dataclass
class SyncConfig:
    """Configuration for the sync operation."""
    registry: RegistryConfig
    namespaces: List[str]
    registry_name: str = "self"
    dry_run: bool = False
    verbose: bool = False


class ComponentTransformer:
    """Transforms Kubernetes ODA Component CRDs to Component Registry Service format."""
    
    @staticmethod
    def transform_component(k8s_component: Dict[str, Any], registry_name: str) -> Dict[str, Any]:
        """
        Transform a Kubernetes ODA Component to Component Registry Service format.
        
        Args:
            k8s_component: Kubernetes Component Custom Resource
            registry_name: Name of the registry to associate with
            
        Returns:
            Dict containing the Component Registry Service format
        """
        metadata = k8s_component.get('metadata', {})
        spec = k8s_component.get('spec', {})
        
        # Extract basic component information
        component_name = metadata.get('name', '')
        component_version = spec.get('version', '1.0.0')
        description = spec.get('description', '')
        
        # Transform exposed APIs from coreFunction
        exposed_apis = []
        core_function = spec.get('coreFunction', {})
        core_exposed_apis = core_function.get('exposedAPIs', [])
        
        for api in core_exposed_apis:
            transformed_api = ComponentTransformer._transform_exposed_api(api, component_name)
            if transformed_api:
                exposed_apis.append(transformed_api)
        
        # Add management APIs if present
        management_function = spec.get('managementFunction', {})
        management_apis = management_function.get('exposedAPIs', [])
        
        for api in management_apis:
            transformed_api = ComponentTransformer._transform_exposed_api(api, component_name, api_type='management')
            if transformed_api:
                exposed_apis.append(transformed_api)
        
        # Add security APIs if present
        security_function = spec.get('securityFunction', {})
        security_apis = security_function.get('exposedAPIs', [])
        
        for api in security_apis:
            transformed_api = ComponentTransformer._transform_exposed_api(api, component_name, api_type='security')
            if transformed_api:
                exposed_apis.append(transformed_api)
        
        # Create labels from metadata and spec
        labels = {}
        labels.update(metadata.get('labels', {}))
        
        # Add ODA-specific labels
        if 'functionalBlock' in spec:
            labels['functionalBlock'] = spec['functionalBlock']
        if 'id' in spec:
            labels['componentId'] = spec['id']
        if 'status' in spec:
            labels['status'] = spec['status']
        
        # Add sync metadata
        labels['syncedFrom'] = 'kubernetes'
        labels['syncedAt'] = datetime.now().isoformat()
        labels['namespace'] = metadata.get('namespace', 'default')
        
        return {
            'component_registry_ref': registry_name,
            'component_name': component_name,
            'component_version': component_version,
            'description': description,
            'exposed_apis': exposed_apis,
            'labels': labels
        }
    
    @staticmethod
    def _transform_exposed_api(api: Dict[str, Any], component_name: str, api_type: str = 'core') -> Optional[Dict[str, Any]]:
        """
        Transform a Kubernetes exposed API to Component Registry Service format.
        
        Args:
            api: Kubernetes API definition
            component_name: Name of the parent component
            api_type: Type of API (core, management, security)
            
        Returns:
            Dict containing the exposed API in Component Registry Service format
        """
        api_name = api.get('name', '')
        if not api_name:
            return None
        
        # Construct the API URL
        path = api.get('path', '')
        port = api.get('port', 80)
        implementation = api.get('implementation', '')
        
        # Try to get URL from status if available, otherwise construct it
        api_url = f"http://{implementation}:{port}{path}"
        
        # Get OpenAPI specification URL
        specifications = api.get('specification', [])
        oas_url = specifications[0] if specifications else f"{api_url}/swagger.json"
        
        # Handle different specification formats
        if isinstance(specifications, list) and specifications:
            if isinstance(specifications[0], dict):
                oas_url = specifications[0].get('url', oas_url)
            else:
                oas_url = specifications[0]
        
        # Create labels for the API
        labels = {
            'apiType': api.get('apiType', 'openapi'),
            'implementation': implementation,
            'componentType': api_type,
            'port': str(port)
        }
        
        if 'developerUI' in api:
            labels['developerUI'] = api['developerUI']
        
        return {
            'name': f"{component_name}-{api_name}",
            'oas_specification': oas_url,
            'url': api_url,
            'labels': labels
        }


class RegistryClient:
    """Client for interacting with the Component Registry Service."""
    
    def __init__(self, config: RegistryConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        
    def create_registry(self, registry_name: str, description: str = "") -> bool:
        """
        Create or ensure a component registry exists.
        
        Args:
            registry_name: Name of the registry
            description: Description of the registry
            
        Returns:
            True if successful, False otherwise
        """
        registry_data = {
            "name": registry_name,
            "url": self.config.url,
            "type": "self",
            "labels": {
                "description": f"Registry {registry_name} for Kubernetes ODA Components",
                "regName": "local",
                "createdAt": datetime.now().isoformat()
            }
        }
        
        try:
            # Check if registry already exists
            response = self.session.get(
                f"{self.config.url}/registries/{registry_name}",
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if response.status_code == 200:
                logging.info(f"Registry '{registry_name}' already exists")
                return True
            elif response.status_code == 404:
                # Registry doesn't exist, create it
                response = self.session.post(
                    f"{self.config.url}/registries",
                    json=registry_data,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code == 200:
                    logging.info(f"Created registry '{registry_name}'")
                    return True
                else:
                    logging.error(f"Failed to create registry: {response.status_code} - {response.text}")
                    return False
            else:
                logging.error(f"Unexpected response checking registry: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Error creating/checking registry: {e}")
            return False
    
    def sync_component(self, component_data: Dict[str, Any]) -> bool:
        """
        Sync a component to the registry service.
        
        Args:
            component_data: Component data in Registry Service format
            
        Returns:
            True if successful, False otherwise
        """
        component_name = component_data['component_name']
        registry_name = component_data['component_registry_ref']
        
        try:
            # Check if component already exists
            response = self.session.get(
                f"{self.config.url}/components/{registry_name}/{component_name}",
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if response.status_code == 200:
                # Component exists, update it
                update_data = {
                    'component_version': component_data['component_version'],
                    'description': component_data['description'],
                    'exposed_apis': component_data['exposed_apis'],
                    'labels': component_data['labels']
                }
                
                response = self.session.put(
                    f"{self.config.url}/components/{registry_name}/{component_name}",
                    json=update_data,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code == 200:
                    logging.info(f"Updated component '{component_name}'")
                    return True
                else:
                    logging.error(f"Failed to update component: {response.status_code} - {response.text}")
                    return False
                    
            elif response.status_code == 404:
                # Component doesn't exist, create it
                response = self.session.post(
                    f"{self.config.url}/components",
                    json=component_data,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code == 200:
                    logging.info(f"Created component '{component_name}'")
                    return True
                else:
                    logging.error(f"Failed to create component: {response.status_code} - {response.text}")
                    return False
            else:
                logging.error(f"Unexpected response checking component: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logging.error(f"Error syncing component '{component_name}': {e}")
            return False


class KubernetesComponentReader:
    """Reads ODA Component Custom Resources from Kubernetes."""
    
    def __init__(self):
        try:
            # Try to load in-cluster config first, then kubeconfig
            try:
                config.load_incluster_config()
                logging.info("Using in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config()
                logging.info("Using kubeconfig for Kubernetes configuration")
            k8s_proxy = os.getenv('K8S_PROXY')
            if k8s_proxy:
                client.Configuration._default.proxy = k8s_proxy
                print(f"set proxy to {k8s_proxy}")
                
            self.custom_api = client.CustomObjectsApi()
            
        except Exception as e:
            logging.error(f"Failed to configure Kubernetes client: {e}")
            raise

    
    def get_components(self, namespaces: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve ODA Components from specified namespaces.
        
        Args:
            namespaces: List of namespaces to search
            
        Returns:
            List of ODA Component Custom Resources
        """
        components = []
        
        for namespace in namespaces:
            try:
                logging.info(f"Reading components from namespace: {namespace}")
                
                response = self.custom_api.list_namespaced_custom_object(
                    group="oda.tmforum.org",
                    version="v1beta3",
                    namespace=namespace,
                    plural="components"
                )
                
                namespace_components = response.get('items', [])
                logging.info(f"Found {len(namespace_components)} components in namespace '{namespace}'")
                
                components.extend(namespace_components)
                
            except ApiException as e:
                if e.status == 404:
                    logging.warning(f"ODA Components CRD not found in namespace '{namespace}' or namespace doesn't exist")
                else:
                    logging.error(f"Error reading components from namespace '{namespace}': {e}")
            except Exception as e:
                logging.error(f"Unexpected error reading components from namespace '{namespace}': {e}")
        
        return components


class ComponentSyncTool:
    """Main orchestrator for the K8s Component to Registry sync process."""
    
    def __init__(self, sync_config: SyncConfig):
        self.config = sync_config
        self.k8s_reader = KubernetesComponentReader()
        self.registry_client = RegistryClient(sync_config.registry)
        self.transformer = ComponentTransformer()
    
    def sync(self) -> bool:
        """
        Perform the complete sync operation.
        
        Returns:
            True if successful, False otherwise
        """
        logging.info("Starting ODA Component synchronization...")
        
        try:
            # Step 1: Ensure registry exists
            if not self.config.dry_run:
                if not self.registry_client.create_registry(
                    self.config.registry_name,
                    "Kubernetes ODA Components Registry"
                ):
                    logging.error("Failed to create/verify registry")
                    return False
            else:
                logging.info(f"[DRY RUN] Would create/verify registry '{self.config.registry_name}'")
            
            # Step 2: Read components from Kubernetes
            components = self.k8s_reader.get_components(self.config.namespaces)
            logging.info(f"Found {len(components)} ODA Components across all namespaces")
            
            if not components:
                logging.info("No components found to sync")
                return True
            
            # Step 3: Transform and sync each component
            success_count = 0
            error_count = 0
            
            for k8s_component in components:
                try:
                    # Transform component
                    registry_component = self.transformer.transform_component(
                        k8s_component, 
                        self.config.registry_name
                    )
                    
                    if self.config.verbose:
                        logging.info(f"Transformed component: {json.dumps(registry_component, indent=2)}")
                    
                    # Sync to registry
                    if not self.config.dry_run:
                        if self.registry_client.sync_component(registry_component):
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        logging.info(f"[DRY RUN] Would sync component '{registry_component['component_name']}'")
                        success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    component_name = k8s_component.get('metadata', {}).get('name', 'unknown')
                    logging.error(f"Failed to process component '{component_name}': {e}")
            
            # Step 4: Report results
            logging.info(f"Sync completed: {success_count} successful, {error_count} errors")
            
            if error_count > 0:
                logging.warning(f"{error_count} components failed to sync")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Sync operation failed: {e}")
            return False


def load_config_file(config_path: str) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config file '{config_path}': {e}")
        return None


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    """Main entry point for the command-line application."""
    parser = argparse.ArgumentParser(
        description="Sync ODA Components from Kubernetes to Component Registry Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python k8s_component_sync.py --registry-url http://localhost:8080 --namespace components
  python k8s_component_sync.py --config config.yaml --dry-run --verbose
  python k8s_component_sync.py --registry-url https://registry.company.com --namespace prod --namespace staging
        """
    )
    
    parser.add_argument(
        '--registry-url',
        type=str,
        help='URL of the Component Registry Service (e.g., http://localhost:8080)',
        default=os.getenv('REGISTRY_URL', None)
    )
    
    parser.add_argument(
        '--namespace', '-n',
        action='append',
        dest='namespaces',
        help='Kubernetes namespace to read components from (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--registry-name',
        type=str,
        default='self',
        help='Name for the registry in the Component Registry Service (default: self)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making changes to the registry'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='HTTP timeout for registry requests (default: 30 seconds)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load configuration
    config_data = {}
    if args.config:
        config_data = load_config_file(args.config) or {}
    
    # Determine registry URL
    registry_url = args.registry_url or config_data.get('registry', {}).get('url')
    if not registry_url:
        logging.error("Registry URL must be specified via --registry-url, config file or env variable REGISTRY_URL")
        return 1
    
    # Determine namespaces
    namespaces = args.namespaces or config_data.get('namespaces', ['components'])
    if not namespaces:
        logging.error("At least one namespace must be specified")
        return 1
    
    # Create configuration objects
    registry_config = RegistryConfig(
        url=registry_url,
        timeout=args.timeout
    )
    
    sync_config = SyncConfig(
        registry=registry_config,
        namespaces=namespaces,
        registry_name=args.registry_name or config_data.get('registry_name', 'kubernetes-registry'),
        dry_run=args.dry_run or config_data.get('dry_run', False),
        verbose=args.verbose or config_data.get('verbose', False)
    )
    
    logging.info(f"Configuration: Registry={registry_config.url}, Namespaces={namespaces}, DryRun={sync_config.dry_run}")
    
    # Run synchronization
    sync_tool = ComponentSyncTool(sync_config)
    success = sync_tool.sync()
    
    return 0 if success else 1


if __name__ == '__main__':
    #if len(sys.argv) == 1:
    #    sys.argv = ["k8s_component_sync.py", "--registry-url=http://localhost:8080", "--namespace=components"]
    sys.exit(main())
