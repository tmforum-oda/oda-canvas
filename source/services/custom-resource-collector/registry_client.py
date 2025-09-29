"""
Component Registry client for synchronizing ODA Components.
Handles all API calls to the Component Registry microservice.
"""

import logging
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

from config import ComponentRegistryConfig
from models import (
    RegistryLabel, RegistryComponent, RegistryExposedAPI, RegistryRegistry,
    ComponentCollectorMetrics, SyncResult, SyncOperation
)


logger = logging.getLogger(__name__)


class RegistryAPIError(Exception):
    """Custom exception for Registry API errors"""
    pass


class ComponentRegistryClient:
    """Client for the Component Registry microservice API"""
    
    def __init__(self, config: ComponentRegistryConfig):
        print(f"Initializing Component Registry client for {config.base_url}")
        self.config = config
        self.session = self._create_session()
        self.metrics = ComponentCollectorMetrics()
        self._test_connection()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ODA-CustomResourceCollector/1.0"
        })
        
        # Add API key if configured
        if self.config.api_key:
            session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}"
            })
        
        return session
    
    def _test_connection(self):
        """Test connection to the Component Registry"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            logger.info("Component Registry connection test successful")
        except Exception as e:
            logger.error(f"Component Registry connection test failed: {e}")
            raise RegistryAPIError(f"Cannot connect to Component Registry: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request to the Component Registry API with error handling"""
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            self.metrics.registry_api_calls += 1
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            self.metrics.registry_api_errors += 1
            logger.error(f"Registry API request failed: {method} {url} - {e}")
            raise RegistryAPIError(f"API request failed: {e}")
    
    # Label operations
    
    def create_label(self, label: RegistryLabel) -> int:
        """Create a new label and return its ID"""
        try:
            response = self._make_request("POST", "/labels/", json=label.dict())
            created_label = response.json()
            logger.debug(f"Created label: {label.key}={label.value} (ID: {created_label['id']})")
            return created_label["id"]
        except RegistryAPIError as e:
            if "already exists" in str(e):
                # Try to find existing label
                existing_label = self.get_label_by_key_value(label.key, label.value)
                if existing_label:
                    return existing_label["id"]
            raise
    
    def get_label_by_key_value(self, key: str, value: str) -> Optional[Dict]:
        """Get label by key and value"""
        try:
            response = self._make_request("GET", "/labels/")
            labels = response.json()
            
            for label in labels:
                if label["key"] == key and label["value"] == value:
                    return label
            return None
        except RegistryAPIError:
            return None
    
    def get_labels(self) -> List[Dict]:
        """Get all labels"""
        response = self._make_request("GET", "/labels/")
        return response.json()
    
    def delete_label(self, label_id: int) -> bool:
        """Delete a label"""
        try:
            self._make_request("DELETE", f"/labels/{label_id}")
            logger.debug(f"Deleted label ID: {label_id}")
            return True
        except RegistryAPIError:
            return False
    
    # Registry operations
    
    def create_registry(self, registry: RegistryRegistry) -> int:
        """Create a new registry and return its ID"""
        response = self._make_request("POST", "/registries/", json=registry.dict())
        created_registry = response.json()
        logger.info(f"Created registry: {registry.name} (ID: {created_registry['id']})")
        return created_registry["id"]
    
    def get_registry_by_name(self, name: str) -> Optional[Dict]:
        """Get registry by name"""
        try:
            response = self._make_request("GET", "/registries/")
            registries = response.json()
            
            for registry in registries:
                if registry["name"] == name:
                    return registry
            return None
        except RegistryAPIError:
            return None
    
    def ensure_registry_exists(self, registry_name: str, registry_type: str = "self") -> int:
        """Ensure a registry exists, create if not found"""
        existing = self.get_registry_by_name(registry_name)
        if existing:
            return existing["id"]
        
        # Create new registry
        registry = RegistryRegistry(
            name=registry_name,
            type=registry_type,
            url=f"http://{registry_name}:8080",
            label_ids=[]
        )
        return self.create_registry(registry)
    
    # Component operations
    
    def create_component(self, component: RegistryComponent) -> int:
        """Create a new component and return its ID"""
        response = self._make_request("POST", "/components/", json=component.dict())
        created_component = response.json()
        logger.info(f"Created component: {component.name} in registry {component.registry_name} (ID: {created_component['id']})")
        self.metrics.components_synced += 1
        return created_component["id"]
    
    def get_component_by_registry_and_name(self, registry_name: str, name: str) -> Optional[Dict]:
        """Get component by registry name and component name"""
        try:
            response = self._make_request("GET", f"/components/?registry_name={registry_name}")
            components = response.json()
            
            for component in components:
                if component["name"] == name:
                    return component
            return None
        except RegistryAPIError:
            return None
    
    def update_component(self, component_id: int, component: RegistryComponent) -> bool:
        """Update an existing component"""
        try:
            self._make_request("PUT", f"/components/{component_id}", json=component.dict())
            logger.info(f"Updated component ID: {component_id}")
            return True
        except RegistryAPIError:
            self.metrics.components_failed += 1
            return False
    
    def delete_component(self, component_id: int) -> bool:
        """Delete a component"""
        try:
            self._make_request("DELETE", f"/components/{component_id}")
            logger.info(f"Deleted component ID: {component_id}")
            return True
        except RegistryAPIError:
            return False
    
    # Exposed API operations
    
    def create_exposed_api(self, api: RegistryExposedAPI) -> int:
        """Create a new exposed API and return its ID"""
        response = self._make_request("POST", "/exposed-apis/", json=api.dict())
        created_api = response.json()
        logger.info(f"Created exposed API: {api.name} for component {api.component_name} (ID: {created_api['id']})")
        self.metrics.apis_synced += 1
        return created_api["id"]
    
    def get_exposed_apis_by_component(self, registry_name: str, component_name: str) -> List[Dict]:
        """Get all exposed APIs for a component"""
        try:
            response = self._make_request(
                "GET", 
                f"/exposed-apis/?registry_name={registry_name}&component_name={component_name}"
            )
            return response.json()
        except RegistryAPIError:
            return []
    
    def update_exposed_api(self, api_id: int, api: RegistryExposedAPI) -> bool:
        """Update an existing exposed API"""
        try:
            self._make_request("PUT", f"/exposed-apis/{api_id}", json=api.dict())
            logger.info(f"Updated exposed API ID: {api_id}")
            return True
        except RegistryAPIError:
            self.metrics.apis_failed += 1
            return False
    
    def update_exposed_api_status(self, api_id: int, status: str) -> bool:
        """Update exposed API status"""
        try:
            self._make_request("PATCH", f"/exposed-apis/{api_id}/status", json={"status": status})
            logger.debug(f"Updated exposed API {api_id} status to {status}")
            return True
        except RegistryAPIError:
            return False
    
    def delete_exposed_api(self, api_id: int) -> bool:
        """Delete an exposed API"""
        try:
            self._make_request("DELETE", f"/exposed-apis/{api_id}")
            logger.info(f"Deleted exposed API ID: {api_id}")
            return True
        except RegistryAPIError:
            return False
    
    # Batch operations
    
    def create_labels_batch(self, labels: List[RegistryLabel]) -> Dict[str, int]:
        """Create multiple labels and return mapping of key=value to ID"""
        label_map = {}
        
        for label in labels:
            try:
                label_id = self.create_label(label)
                label_map[f"{label.key}={label.value}"] = label_id
                self.metrics.labels_created += 1
            except Exception as e:
                logger.error(f"Failed to create label {label.key}={label.value}: {e}")
        
        return label_map
    
    def sync_component_full(
        self,
        component: RegistryComponent,
        exposed_apis: List[RegistryExposedAPI],
        registry_name: str = "local-registry"
    ) -> SyncResult:
        """Perform full synchronization of a component and its APIs"""
        start_time = time.time()
        
        try:
            # Ensure registry exists
            self.ensure_registry_exists(registry_name)
            
            # Check if component already exists
            existing_component = self.get_component_by_registry_and_name(
                component.registry_name, component.name
            )
            
            component_id = None
            if existing_component:
                # Update existing component
                component_id = existing_component["id"]
                success = self.update_component(component_id, component)
                operation_type = "UPDATE"
            else:
                # Create new component
                component_id = self.create_component(component)
                success = component_id is not None
                operation_type = "CREATE"
            
            if not success:
                raise RegistryAPIError("Failed to sync component")
            
            # Sync exposed APIs
            for api in exposed_apis:
                try:
                    existing_apis = self.get_exposed_apis_by_component(
                        api.registry_name, api.component_name
                    )
                    
                    existing_api = None
                    for existing in existing_apis:
                        if existing["name"] == api.name:
                            existing_api = existing
                            break
                    
                    if existing_api:
                        self.update_exposed_api(existing_api["id"], api)
                    else:
                        self.create_exposed_api(api)
                        
                except Exception as e:
                    logger.error(f"Failed to sync exposed API {api.name}: {e}")
                    self.metrics.apis_failed += 1
            
            sync_duration = time.time() - start_time
            self.metrics.sync_duration_seconds += sync_duration
            
            return SyncResult(
                success=True,
                operation=SyncOperation(
                    operation_type=operation_type,
                    resource_type="component"
                ),
                registry_id=component_id
            )
            
        except Exception as e:
            self.metrics.components_failed += 1
            return SyncResult(
                success=False,
                operation=SyncOperation(
                    operation_type="CREATE",
                    resource_type="component"
                ),
                error_message=str(e)
            )
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        try:
            response = self._make_request("GET", "/stats")
            return response.json()
        except RegistryAPIError:
            return {}
    
    def health_check(self) -> bool:
        """Check if the registry is healthy"""
        try:
            response = self._make_request("GET", "/health")
            return response.json().get("status") == "healthy"
        except RegistryAPIError:
            return False