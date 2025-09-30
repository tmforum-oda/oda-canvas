"""
Kubernetes client for monitoring ODA Component Custom Resources.
Handles watching, listing, and processing ODA Components.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import yaml
import os

from config import KubernetesConfig
from models import ODAComponentResource, ComponentCollectorMetrics


logger = logging.getLogger(__name__)


class KubernetesClient:
    """Kubernetes client for ODA Component Custom Resources"""
    
    def __init__(self, k8s_config: KubernetesConfig):
        self.config = k8s_config
        self.api_client = None
        self.custom_objects_api = None
        self.metrics = ComponentCollectorMetrics()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Kubernetes client"""
        try:
            if self.config.in_cluster:
                logger.info("Loading in-cluster Kubernetes configuration")
                config.load_incluster_config()
            else:
                logger.info("Loading Kubernetes configuration from file")
                config.load_kube_config(config_file=self.config.config_path)
            if self.config.k8s_proxy:
                client.Configuration._default.proxy = self.config.k8s_proxy
                print(f"set proxy to {self.config.k8s_proxy}")
            
            self.api_client = client.ApiClient()
            self.custom_objects_api = client.CustomObjectsApi(self.api_client)
            logger.info("Kubernetes client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Kubernetes API connection"""
        try:
            # Try to list namespaces as a connectivity test
            v1 = client.CoreV1Api(self.api_client)
            v1.list_namespace(limit=1)
            logger.info("Kubernetes API connectivity test successful")
            return True
        except Exception as e:
            logger.error(f"Kubernetes API connectivity test failed: {e}")
            return False
    
    def list_oda_components(
        self,
        namespace: Optional[str] = None,
        group: str = "oda.tmforum.org",
        version: str = "v1beta3",
        plural: str = "components"
    ) -> List[ODAComponentResource]:
        """List all ODA Components in the specified namespace"""
        try:
            target_namespace = namespace or self.config.namespace
            logger.info(f"Listing ODA Components in namespace: {target_namespace}")
            
            if target_namespace == "all":
                # List across all namespaces
                response = self.custom_objects_api.list_cluster_custom_object(
                    group=group,
                    version=version,
                    plural=plural
                )
            else:
                # List in specific namespace
                response = self.custom_objects_api.list_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=target_namespace,
                    plural=plural
                )
            
            components = []
            for item in response.get("items", []):
                try:
                    component = ODAComponentResource(**item)
                    components.append(component)
                except Exception as e:
                    logger.warning(f"Failed to parse ODA Component {item.get('metadata', {}).get('name', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(components)} ODA Components")
            self.metrics.components_watched = len(components)
            return components
            
        except ApiException as e:
            logger.error(f"Failed to list ODA Components: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing ODA Components: {e}")
            raise
    
    def get_oda_component(
        self,
        name: str,
        namespace: Optional[str] = None,
        group: str = "oda.tmforum.org",
        version: str = "v1beta3",
        plural: str = "components"
    ) -> Optional[ODAComponentResource]:
        """Get a specific ODA Component by name"""
        try:
            target_namespace = namespace or self.config.namespace
            logger.debug(f"Getting ODA Component {name} in namespace {target_namespace}")
            
            response = self.custom_objects_api.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=target_namespace,
                plural=plural,
                name=name
            )
            
            return ODAComponentResource(**response)
            
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"ODA Component {name} not found in namespace {target_namespace}")
                return None
            else:
                logger.error(f"Failed to get ODA Component {name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error getting ODA Component {name}: {e}")
            raise
    
    async def watch_oda_components(
        self,
        callback: Callable[[str, ODAComponentResource], None],
        namespace: Optional[str] = None,
        group: str = "oda.tmforum.org",
        version: str = "v1beta3",
        plural: str = "components"
    ):
        """Watch for changes to ODA Components and call callback function"""
        target_namespace = namespace or self.config.namespace
        logger.info(f"Starting to watch ODA Components in namespace: {target_namespace}")
        
        while True:
            try:
                w = watch.Watch()
                
                if target_namespace == "all":
                    stream = w.stream(
                        self.custom_objects_api.list_cluster_custom_object,
                        group=group,
                        version=version,
                        plural=plural,
                        timeout_seconds=self.config.watch_timeout
                    )
                else:
                    stream = w.stream(
                        self.custom_objects_api.list_namespaced_custom_object,
                        group=group,
                        version=version,
                        namespace=target_namespace,
                        plural=plural,
                        timeout_seconds=self.config.watch_timeout
                    )
                
                for event in stream:
                    try:
                        event_type = event['type']  # ADDED, MODIFIED, DELETED
                        resource_data = event['object']
                        
                        # Parse the ODA Component resource
                        component = ODAComponentResource(**resource_data)
                        
                        logger.debug(f"Received {event_type} event for component {component.metadata['name']}")
                        
                        # Call the callback function
                        await callback(event_type, component)
                        
                        self.metrics.kubernetes_events_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing watch event: {e}")
                        continue
                
                logger.warning("Watch stream ended, restarting...")
                
            except ApiException as e:
                logger.error(f"API error during watch: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Unexpected error during watch: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def check_crd_exists(
        self,
        group: str = "oda.tmforum.org",
        version: str = "v1beta3",
        plural: str = "components"
    ) -> bool:
        """Check if the ODA Component CRD exists in the cluster"""
        try:
            # Try to get the CRD
            extensions_v1 = client.ApiextensionsV1Api(self.api_client)
            crd_name = f"{plural}.{group}"
            
            try:
                extensions_v1.read_custom_resource_definition(name=crd_name)
                logger.info(f"ODA Component CRD {crd_name} found")
                return True
            except ApiException as e:
                if e.status == 404:
                    logger.warning(f"ODA Component CRD {crd_name} not found")
                    return False
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Error checking for ODA Component CRD: {e}")
            return False
    
    def get_resource_status(self, component: ODAComponentResource) -> Dict[str, Any]:
        """Extract status information from ODA Component"""
        status = {
            "name": component.metadata.get("name"),
            "namespace": component.metadata.get("namespace"),
            "uid": component.metadata.get("uid"),
            "resource_version": component.metadata.get("resourceVersion"),
            "creation_timestamp": component.metadata.get("creationTimestamp"),
            "labels": component.metadata.get("labels", {}),
            "annotations": component.metadata.get("annotations", {}),
            "spec_type": component.spec.type,
            "spec_version": component.spec.version,
            "exposed_apis_count": len(component.spec.exposedAPIs or []),
            "dependent_apis_count": len(component.spec.dependentAPIs or []),
            "deployment_status": None,
            "summary_status": None
        }
        
        if component.status:
            status["deployment_status"] = component.status.deployment_status
            status["summary_status"] = component.status.summary_status
            if component.status.exposed_apis:
                status["ready_apis_count"] = len([
                    api for api in component.status.exposed_apis 
                    if api.get("ready", False)
                ])
        
        return status
    
    def close(self):
        """Close the Kubernetes client"""
        if self.api_client:
            self.api_client.close()
            logger.info("Kubernetes client closed")


class ComponentWatcher:
    """High-level watcher for ODA Components"""
    
    def __init__(self, k8s_client: KubernetesClient):
        self.k8s_client = k8s_client
        self.component_cache: Dict[str, ODAComponentResource] = {}
        self.event_handlers: List[Callable] = []
    
    def add_event_handler(self, handler: Callable[[str, ODAComponentResource], None]):
        """Add an event handler function"""
        self.event_handlers.append(handler)
    
    async def handle_component_event(self, event_type: str, component: ODAComponentResource):
        """Handle a component event and notify all registered handlers"""
        component_key = f"{component.metadata.get('namespace', 'default')}/{component.metadata['name']}"
        
        # Update cache
        if event_type == "DELETED":
            self.component_cache.pop(component_key, None)
        else:
            self.component_cache[component_key] = component
        
        # Notify all handlers
        for handler in self.event_handlers:
            try:
                await handler(event_type, component)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def start_watching(self, namespace: Optional[str] = None):
        """Start watching for ODA Component changes"""
        await self.k8s_client.watch_oda_components(
            callback=self.handle_component_event,
            namespace=namespace
        )
    
    def get_cached_components(self) -> List[ODAComponentResource]:
        """Get all cached components"""
        return list(self.component_cache.values())