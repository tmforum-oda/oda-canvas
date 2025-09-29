"""
Synchronization engine for ODA Components.
Orchestrates the mapping and synchronization between Kubernetes and Component Registry.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import time

from config import CollectorConfig
from models import (
    ODAComponentResource, ComponentMapping, RegistryLabel, RegistryComponent,
    RegistryExposedAPI, SyncResult, ComponentCollectorMetrics,
    map_component_to_registry, create_registry_exposed_apis, extract_labels_from_component
)
from kubernetes_client import KubernetesClient
from registry_client import ComponentRegistryClient


logger = logging.getLogger(__name__)


class ComponentSynchronizer:
    """Handles synchronization of ODA Components with Component Registry"""
    
    def __init__(self, config: CollectorConfig, k8s_client: KubernetesClient, registry_client: ComponentRegistryClient):
        self.config = config
        self.k8s_client = k8s_client
        self.registry_client = registry_client
        self.metrics = ComponentCollectorMetrics()
        
        # Cache for mappings and labels
        self.component_mappings: Dict[str, ComponentMapping] = {}
        self.label_cache: Dict[str, int] = {}  # key=value -> label_id
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        
        # Tracking sets
        self.processed_components: Set[str] = set()
        self.failed_components: Set[str] = set()
        
    def _get_component_key(self, component: ODAComponentResource) -> str:
        """Generate unique key for component"""
        namespace = component.metadata.get("namespace", "default")
        name = component.metadata["name"]
        return f"{namespace}/{name}"
    
    async def _ensure_labels_exist(self, labels: Dict[str, str]) -> List[int]:
        """Ensure all labels exist in registry and return their IDs"""
        label_ids = []
        
        for key, value in labels.items():
            label_key = f"{key}={value}"
            
            # Check cache first
            if label_key in self.label_cache:
                label_ids.append(self.label_cache[label_key])
                continue
            
            # Check if label exists in registry
            existing_label = self.registry_client.get_label_by_key_value(key, value)
            if existing_label:
                label_id = existing_label["id"]
                self.label_cache[label_key] = label_id
                label_ids.append(label_id)
                continue
            
            # Create new label
            try:
                registry_label = RegistryLabel(key=key, value=value)
                label_id = self.registry_client.create_label(registry_label)
                self.label_cache[label_key] = label_id
                label_ids.append(label_id)
                self.metrics.labels_created += 1
                logger.debug(f"Created new label: {key}={value} (ID: {label_id})")
            except Exception as e:
                logger.error(f"Failed to create label {key}={value}: {e}")
                continue
        
        return label_ids
    
    async def _sync_component_to_registry(self, component: ODAComponentResource) -> SyncResult:
        """Synchronize a single ODA Component to the Component Registry"""
        component_key = self._get_component_key(component)
        
        try:
            logger.info(f"Syncing component: {component_key}")
            
            # Map component to registry format
            mapping = map_component_to_registry(component, self.config.component_group)
            
            # Ensure labels exist and get their IDs
            label_ids = await self._ensure_labels_exist(mapping.labels)
            
            # Create registry component
            registry_component = RegistryComponent(
                registry_name=mapping.registry_name,
                name=mapping.component_name,
                label_ids=label_ids
            )
            
            # Create exposed APIs
            registry_apis = create_registry_exposed_apis(component, mapping.registry_name)
            
            # Update API label IDs
            for api in registry_apis:
                # Add component-specific labels to APIs
                api_labels = mapping.labels.copy()
                api_labels["api-name"] = api.name
                api_label_ids = await self._ensure_labels_exist(api_labels)
                api.label_ids = api_label_ids
            
            # Perform full sync with registry
            result = self.registry_client.sync_component_full(
                registry_component, registry_apis, mapping.registry_name
            )
            
            if result.success:
                # Update mapping cache
                mapping.last_sync = datetime.utcnow()
                mapping.resource_version = component.metadata.get("resourceVersion", "")
                self.component_mappings[component_key] = mapping
                
                self.processed_components.add(component_key)
                self.failed_components.discard(component_key)
                self.metrics.components_synced += 1
                
                logger.info(f"Successfully synced component: {component_key}")
            else:
                self.failed_components.add(component_key)
                self.metrics.components_failed += 1
                logger.error(f"Failed to sync component {component_key}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.failed_components.add(component_key)
            self.metrics.components_failed += 1
            logger.error(f"Error syncing component {component_key}: {e}")
            
            return SyncResult(
                success=False,
                operation=None,
                error_message=str(e)
            )
    
    async def _delete_component_from_registry(self, component: ODAComponentResource) -> bool:
        """Delete component and its APIs from the Component Registry"""
        component_key = self._get_component_key(component)
        
        try:
            logger.info(f"Deleting component from registry: {component_key}")
            
            mapping = self.component_mappings.get(component_key)
            if not mapping:
                logger.warning(f"No mapping found for component {component_key}, cannot delete")
                return False
            
            # Find component in registry
            existing_component = self.registry_client.get_component_by_registry_and_name(
                mapping.registry_name, mapping.component_name
            )
            
            if existing_component:
                component_id = existing_component["id"]
                
                # Delete associated exposed APIs first
                existing_apis = self.registry_client.get_exposed_apis_by_component(
                    mapping.registry_name, mapping.component_name
                )
                
                for api in existing_apis:
                    self.registry_client.delete_exposed_api(api["id"])
                
                # Delete component
                success = self.registry_client.delete_component(component_id)
                
                if success:
                    # Remove from cache
                    self.component_mappings.pop(component_key, None)
                    self.processed_components.discard(component_key)
                    logger.info(f"Successfully deleted component: {component_key}")
                    return True
                else:
                    logger.error(f"Failed to delete component {component_key} from registry")
                    return False
            else:
                logger.warning(f"Component {component_key} not found in registry")
                # Clean up mapping anyway
                self.component_mappings.pop(component_key, None)
                return True
                
        except Exception as e:
            logger.error(f"Error deleting component {component_key}: {e}")
            return False
    
    async def handle_component_event(self, event_type: str, component: ODAComponentResource):
        """Handle a Kubernetes event for an ODA Component"""
        component_key = self._get_component_key(component)
        
        logger.debug(f"Handling {event_type} event for component: {component_key}")
        
        try:
            if event_type in ["ADDED", "MODIFIED"]:
                # Check if we need to sync (resource version changed)
                existing_mapping = self.component_mappings.get(component_key)
                current_version = component.metadata.get("resourceVersion", "")
                
                if (not existing_mapping or 
                    existing_mapping.resource_version != current_version or
                    component_key in self.failed_components):
                    
                    # Add to processing queue
                    await self.processing_queue.put(("SYNC", component))
                    self.metrics.kubernetes_events_processed += 1
                else:
                    logger.debug(f"Component {component_key} already up to date")
                    
            elif event_type == "DELETED":
                # Add to processing queue for deletion
                await self.processing_queue.put(("DELETE", component))
                self.metrics.kubernetes_events_processed += 1
            
        except Exception as e:
            logger.error(f"Error handling event {event_type} for component {component_key}: {e}")
    
    async def _process_queue(self):
        """Process the synchronization queue"""
        logger.info("Starting queue processor")
        
        while True:
            try:
                # Get next item from queue (with timeout)
                operation, component = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                if operation == "SYNC":
                    await self._sync_component_to_registry(component)
                elif operation == "DELETE":
                    await self._delete_component_from_registry(component)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                # No items in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing queue item: {e}")
                continue
    
    async def perform_full_sync(self):
        """Perform full synchronization of all ODA Components"""
        logger.info("Starting full synchronization")
        start_time = time.time()
        
        try:
            # Get all ODA Components from Kubernetes
            components = self.k8s_client.list_oda_components(
                namespace=self.config.kubernetes.namespace,
                group=self.config.component_group,
                version=self.config.component_version,
                plural=self.config.component_plural
            )
            
            logger.info(f"Found {len(components)} ODA Components for full sync")
            
            # Process components in batches
            batch_size = self.config.batch_size
            for i in range(0, len(components), batch_size):
                batch = components[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [self._sync_component_to_registry(comp) for comp in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log batch results
                successful = sum(1 for r in results if isinstance(r, SyncResult) and r.success)
                logger.info(f"Batch {i//batch_size + 1}: {successful}/{len(batch)} components synced successfully")
                
                # Small delay between batches to avoid overwhelming the registry
                if i + batch_size < len(components):
                    await asyncio.sleep(0.1)
            
            # Update metrics
            sync_duration = time.time() - start_time
            self.metrics.sync_duration_seconds += sync_duration
            self.metrics.last_sync_time = datetime.utcnow()
            
            logger.info(f"Full synchronization completed in {sync_duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during full synchronization: {e}")
    
    async def cleanup_orphaned_resources(self):
        """Clean up resources in registry that no longer exist in Kubernetes"""
        logger.info("Starting cleanup of orphaned resources")
        
        try:
            # Get all components from Kubernetes
            k8s_components = self.k8s_client.list_oda_components(
                namespace=self.config.kubernetes.namespace,
                group=self.config.component_group,
                version=self.config.component_version,
                plural=self.config.component_plural
            )
            
            # Create set of existing component keys
            existing_keys = set()
            for component in k8s_components:
                key = self._get_component_key(component)
                existing_keys.add(key)
            
            # Find orphaned mappings
            orphaned_keys = set(self.component_mappings.keys()) - existing_keys
            
            if orphaned_keys:
                logger.info(f"Found {len(orphaned_keys)} orphaned components to clean up")
                
                for orphaned_key in orphaned_keys:
                    mapping = self.component_mappings[orphaned_key]
                    
                    # Try to delete from registry
                    existing_component = self.registry_client.get_component_by_registry_and_name(
                        mapping.registry_name, mapping.component_name
                    )
                    
                    if existing_component:
                        component_id = existing_component["id"]
                        
                        # Delete associated APIs
                        apis = self.registry_client.get_exposed_apis_by_component(
                            mapping.registry_name, mapping.component_name
                        )
                        for api in apis:
                            self.registry_client.delete_exposed_api(api["id"])
                        
                        # Delete component
                        self.registry_client.delete_component(component_id)
                        logger.info(f"Cleaned up orphaned component: {orphaned_key}")
                    
                    # Remove from cache
                    self.component_mappings.pop(orphaned_key, None)
            else:
                logger.info("No orphaned resources found")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_sync_status(self) -> Dict:
        """Get current synchronization status"""
        return {
            "total_components": len(self.component_mappings),
            "processed_components": len(self.processed_components),
            "failed_components": len(self.failed_components),
            "queue_size": self.processing_queue.qsize(),
            "last_sync_time": self.metrics.last_sync_time.isoformat() if self.metrics.last_sync_time else None,
            "metrics": {
                "components_synced": self.metrics.components_synced,
                "components_failed": self.metrics.components_failed,
                "apis_synced": self.metrics.apis_synced,
                "apis_failed": self.metrics.apis_failed,
                "labels_created": self.metrics.labels_created,
                "kubernetes_events_processed": self.metrics.kubernetes_events_processed,
                "registry_api_calls": self.metrics.registry_api_calls,
                "registry_api_errors": self.metrics.registry_api_errors,
                "sync_duration_seconds": self.metrics.sync_duration_seconds
            }
        }
    
    async def start_processing(self):
        """Start the background processing tasks"""
        logger.info("Starting component synchronization processing")
        
        # Start queue processor
        processor_task = asyncio.create_task(self._process_queue())
        
        # Start periodic full sync
        async def periodic_full_sync():
            while True:
                try:
                    await asyncio.sleep(self.config.sync_interval)
                    await self.perform_full_sync()
                except Exception as e:
                    logger.error(f"Error in periodic full sync: {e}")
        
        full_sync_task = asyncio.create_task(periodic_full_sync())
        
        # Start periodic cleanup
        async def periodic_cleanup():
            while True:
                try:
                    # Run cleanup every 10 minutes
                    await asyncio.sleep(600)
                    await self.cleanup_orphaned_resources()
                except Exception as e:
                    logger.error(f"Error in periodic cleanup: {e}")
        
        cleanup_task = asyncio.create_task(periodic_cleanup())
        
        return [processor_task, full_sync_task, cleanup_task]