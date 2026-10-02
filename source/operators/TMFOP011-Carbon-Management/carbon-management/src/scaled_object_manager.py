"""
ScaledObject Manager Module

Manages lifecycle of KEDA ScaledObjects as child resources of CarbonManagement.
Enables automatic creation, updates, and cleanup of ScaledObjects for discovered deployments.

"""

from typing import List, Dict, Any, Optional, Tuple
from kubernetes import client
import logging

logger = logging.getLogger(__name__)

# KEDA constants
KEDA_GROUP = "keda.sh"
KEDA_VERSION = "v1alpha1"
KEDA_SCALEDOBJECTS_PLURAL = "scaledobjects"


class ScaledObjectManager:
    """
    Manages ScaledObject lifecycle for deployments
    
    This manager:
    - Discovers deployments based on label selectors
    - Creates ScaledObjects automatically for each deployment
    - Updates maxReplicaCount based on carbon intensity
    - Cleans up orphaned ScaledObjects
    - Sets owner references for automatic cascade deletion
    """
    
    def __init__(self, apps_v1: client.AppsV1Api, custom_objects_api: client.CustomObjectsApi):
        """
        Initialize the ScaledObject manager
        
        Args:
            apps_v1: Kubernetes Apps V1 API client
            custom_objects_api: Kubernetes Custom Objects API client
        """
        self.apps_v1 = apps_v1
        self.custom_objects_api = custom_objects_api
        self._keda_available = None  # Cache for KEDA availability check
    
    def is_keda_available(self) -> Tuple[bool, str]:
        """
        Check if KEDA is installed and ScaledObject CRD is available.
        Uses caching to avoid repeated API calls.
        
        Returns:
            Tuple of (is_available: bool, message: str)
        """
        # Return cached result if already checked
        if self._keda_available is not None:
            if self._keda_available:
                return True, "KEDA is available"
            else:
                return False, "KEDA ScaledObject CRD is not registered. Please install KEDA: https://keda.sh/docs/deploy/"
        
        try:
            # Try to list ScaledObjects in any namespace to verify KEDA is installed
            # We use a simple API call to check if the resource group exists
            apis = client.ApisApi()
            api_groups = apis.get_api_versions()
            
            # Check if keda.sh API group exists
            for group in api_groups.groups:
                if group.name == KEDA_GROUP:
                    logger.info("KEDA is installed and available")
                    self._keda_available = True
                    return True, "KEDA is available"
            
            logger.error(f"KEDA API group '{KEDA_GROUP}' not found. KEDA may not be installed.")
            self._keda_available = False
            return False, "KEDA ScaledObject CRD is not registered. Please install KEDA: https://keda.sh/docs/deploy/"
            
        except Exception as e:
            logger.error(f"Error checking KEDA availability: {e}")
            self._keda_available = False
            return False, f"Failed to verify KEDA installation: {str(e)}"
    
    def discover_deployments(
        self, 
        match_labels: Dict[str, str],
        namespace: str
    ) -> List[Dict[str, str]]:
        """
        Discover deployments by matching labels
        
        Args:
            match_labels: Dictionary of labels to match (e.g., {"oda.tmforum.org/componentName": "ocv1-productordercaptureandvalidation", "carbon-aware": "enabled"})
            namespace: Namespace to search in
        
        Returns:
            List of dicts with 'name' and 'namespace' keys
        """
        try:
            if not match_labels:
                logger.warning("No match labels provided, skipping discovery")
                return []
            
            # Build label selector from match_labels dictionary
            label_selector = ",".join([f"{k}={v}" for k, v in match_labels.items()])
            
            logger.info(f"Discovering deployments with labels: {label_selector} in namespace: {namespace}")
            
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
            
            discovered = []
            for dep in deployments.items:
                discovered.append({
                    'name': dep.metadata.name,
                    'namespace': dep.metadata.namespace
                })
                logger.info(f"Discovered deployment: {dep.metadata.namespace}/{dep.metadata.name}")
            
            logger.info(f"Total deployments discovered: {len(discovered)}")
            return discovered
            
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to discover deployments: {e}")
            raise
    
    def ensure_scaled_object(
        self,
        deployment_name: str,
        deployment_namespace: str,
        triggers: List[Dict[str, Any]],
        max_replica_count: int,
        owner_references: List[Dict[str, Any]],
        min_replica_count: int = 1,
        polling_interval: int = 30,
        cooldown_period: int = 300,
        fallback: Optional[Dict[str, Any]] = None,
        deployment_overrides: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Create or update KEDA ScaledObject for a deployment
        
        Args:
            deployment_name: Name of the target deployment
            deployment_namespace: Namespace of the target deployment
            triggers: KEDA triggers configuration
            max_replica_count: Maximum replica count based on carbon intensity
            owner_references: Owner references (CarbonManagement)
            min_replica_count: Minimum replica count (default: 1)
            polling_interval: Polling interval in seconds (default: 30)
            cooldown_period: Cooldown period in seconds (default: 300)
            fallback: Optional fallback configuration
            deployment_overrides: Optional per-deployment overrides
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check KEDA availability first
        keda_available, keda_msg = self.is_keda_available()
        if not keda_available:
            logger.error(f"Cannot ensure ScaledObject: {keda_msg}")
            return False, keda_msg
        
        # Always use ScaledObjects
        plural = "scaledobjects"
        kind = "ScaledObject"
        
        scaled_object_name = f"{deployment_name}-carbon-scaled"
        
        # Apply deployment-specific overrides if present
        if deployment_overrides:
            min_replica_count = deployment_overrides.get('minReplicaCount', min_replica_count)
            polling_interval = deployment_overrides.get('pollingInterval', polling_interval)
            cooldown_period = deployment_overrides.get('cooldownPeriod', cooldown_period)
        
        # Build spec
        spec = {
            "scaleTargetRef": {
                "name": deployment_name
            },
            "pollingInterval": polling_interval,
            "cooldownPeriod": cooldown_period,
            "minReplicaCount": min_replica_count,
            "maxReplicaCount": max_replica_count,
            "triggers": triggers if triggers else []
        }
        
        # Add fallback if provided
        if fallback:
            spec["fallback"] = fallback
        
        # Build ScaledObject/ScaledJob
        scaled_object = {
            "apiVersion": "keda.sh/v1alpha1",
            "kind": kind,
            "metadata": {
                "name": scaled_object_name,
                "namespace": deployment_namespace,
                "labels": {
                    "carbon-aware.kubernetes.io/managed": "true",
                    "carbon-aware.kubernetes.io/deployment": deployment_name
                },
                "ownerReferences": owner_references
            },
            "spec": spec
        }
        
        try:
            # Try to get existing resource
            try:
                existing = self.custom_objects_api.get_namespaced_custom_object(
                    group=KEDA_GROUP,
                    version=KEDA_VERSION,
                    namespace=deployment_namespace,
                    plural=plural,
                    name=scaled_object_name
                )
                
                # Update existing resource
                # Preserve existing spec but update critical fields
                existing["spec"]["maxReplicaCount"] = max_replica_count
                existing["spec"]["minReplicaCount"] = min_replica_count
                existing["spec"]["pollingInterval"] = polling_interval
                existing["spec"]["cooldownPeriod"] = cooldown_period
                
                # Update triggers if provided
                if triggers:
                    existing["spec"]["triggers"] = triggers
                
                # Update fallback if provided
                if fallback:
                    existing["spec"]["fallback"] = fallback
                
                self.custom_objects_api.patch_namespaced_custom_object(
                    group=KEDA_GROUP,
                    version=KEDA_VERSION,
                    namespace=deployment_namespace,
                    plural=plural,
                    name=scaled_object_name,
                    body=existing
                )
                
                msg = f"Updated {kind}: {deployment_namespace}/{scaled_object_name} (maxReplicas={max_replica_count})"
                logger.info(msg)
                return True, msg
                
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create new resource
                    self.custom_objects_api.create_namespaced_custom_object(
                        group=KEDA_GROUP,
                        version=KEDA_VERSION,
                        namespace=deployment_namespace,
                        plural=plural,
                        body=scaled_object
                    )
                    msg = f"Created {kind}: {deployment_namespace}/{scaled_object_name} (maxReplicas={max_replica_count})"
                    logger.info(msg)
                    return True, msg
                else:
                    raise
            
        except client.exceptions.ApiException as e:
            error_msg = f"Failed to ensure {kind} {scaled_object_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error ensuring {kind} {scaled_object_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def cleanup_orphaned_scaled_objects(
        self,
        namespace: str,
        active_deployments: List[str],
        owner_uid: str
    ) -> int:
        """
        Remove ScaledObjects for deployments that no longer match selector
        
        Args:
            namespace: Namespace to search in
            active_deployments: List of deployment names that should have ScaledObjects
            owner_uid: UID of the CarbonManagement owner
        
        Returns:
            Number of ScaledObjects deleted
        """
        # Check KEDA availability first
        keda_available, _ = self.is_keda_available()
        if not keda_available:
            logger.warning("Skipping cleanup: KEDA is not available")
            return 0
        
        deleted_count = 0
        
        try:
            # List all ScaledObjects in the namespace
            scaled_objects = self.custom_objects_api.list_namespaced_custom_object(
                group=KEDA_GROUP,
                version=KEDA_VERSION,
                namespace=namespace,
                plural=KEDA_SCALEDOBJECTS_PLURAL
            )
            
            for so in scaled_objects.get('items', []):
                metadata = so.get('metadata', {})
                name = metadata.get('name')
                owner_refs = metadata.get('ownerReferences', [])
                labels = metadata.get('labels', {})
                
                # Check if owned by this CarbonManagement
                is_owned = any(
                    ref.get('uid') == owner_uid and 
                    ref.get('kind') == 'CarbonManagement'
                    for ref in owner_refs
                )
                
                if is_owned:
                    # Extract deployment name from label
                    deployment_name = labels.get('carbon-aware.kubernetes.io/deployment')
                    
                    # Delete if deployment no longer in active list
                    if deployment_name and deployment_name not in active_deployments:
                        self.custom_objects_api.delete_namespaced_custom_object(
                            group=KEDA_GROUP,
                            version=KEDA_VERSION,
                            namespace=namespace,
                            plural=KEDA_SCALEDOBJECTS_PLURAL,
                            name=name
                        )
                        logger.info(f"Deleted orphaned ScaledObject: {namespace}/{name} (deployment removed)")
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} orphaned ScaledObjects")
                
            return deleted_count
            
        except client.exceptions.ApiException as e:
            logger.error(f"Failed to cleanup orphaned ScaledObjects: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")
            return 0
