"""
Data models for ODA Components and Component Registry entities.
Handles the mapping between Kubernetes Custom Resources and Registry API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ComponentStatus(str, Enum):
    """ODA Component status enumeration"""
    PENDING = "pending"
    READY = "ready"
    ERROR = "error"
    UNKNOWN = "unknown"


class APIStatus(str, Enum):
    """Exposed API status enumeration"""
    PENDING = "pending" 
    READY = "ready"


class RegistryType(str, Enum):
    """Registry type enumeration"""
    SELF = "self"
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"


# ODA Component models (from Kubernetes Custom Resources)

class ODAExposedAPI(BaseModel):
    """ODA Component Exposed API specification"""
    name: str
    specification: List[str]
    implementation: Optional[str] = None
    path: Optional[str] = None
    developerUI: Optional[str] = None
    port: Optional[int] = None
    
    
class ODACoreFunction(BaseModel):
    """Core functions of an ODA Component"""
    exposedAPIs: Optional[List[ODAExposedAPI]] = None
    dependentAPIs: Optional[List[Dict[str, Any]]] = None
    


class ODAComponentSpec(BaseModel):
    """ODA Component specification from Custom Resource"""
    version: str
    description: Optional[str] = None
    maintainers: Optional[List[Dict[str, str]]] = None
    owners: Optional[List[Dict[str, str]]] = None
    coreFunction: Optional[ODACoreFunction] = None
    securityFunction: Optional[Dict[str, Any]] = None
    managementFunction: Optional[Dict[str, Any]] = None
    eventNotification: Optional[Dict[str, Any]] = None


class ODAComponentStatus(BaseModel):
    """ODA Component status from Custom Resource"""
    deployment_status: Optional[str] = None
    summary_status: Optional[Dict[str, Any]] = None
    exposed_apis: Optional[List[Dict[str, Any]]] = None


class ODAComponentResource(BaseModel):
    """Complete ODA Component Custom Resource"""
    apiVersion: str
    kind: str
    metadata: Dict[str, Any]
    spec: ODAComponentSpec
    status: Optional[ODAComponentStatus] = None


# Component Registry models (for API calls)

class RegistryLabel(BaseModel):
    """Registry API Label model"""
    key: str
    value: str


class RegistryComponent(BaseModel):
    """Registry API Component model"""
    registry_name: str
    name: str
    label_ids: List[int] = Field(default_factory=list)


class RegistryExposedAPI(BaseModel):
    """Registry API ExposedAPI model"""
    registry_name: str
    component_name: str
    name: str
    url: str
    oas_specification: Optional[str] = None
    status: APIStatus = APIStatus.PENDING
    label_ids: List[int] = Field(default_factory=list)


class RegistryRegistry(BaseModel):
    """Registry API Registry model"""
    name: str
    type: RegistryType
    url: str
    label_ids: List[int] = Field(default_factory=list)


# Mapping and synchronization models

class ComponentMapping(BaseModel):
    """Maps ODA Component to Registry entities"""
    kubernetes_name: str
    kubernetes_namespace: str
    kubernetes_uid: str
    registry_name: str
    component_name: str
    last_sync: datetime
    resource_version: str
    labels: Dict[str, str] = Field(default_factory=dict)
    exposed_apis: List[str] = Field(default_factory=list)


class SyncOperation(BaseModel):
    """Represents a synchronization operation"""
    operation_type: str  # CREATE, UPDATE, DELETE
    resource_type: str   # component, exposed_api, label
    kubernetes_resource: Optional[Dict[str, Any]] = None
    registry_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class SyncResult(BaseModel):
    """Result of a synchronization operation"""
    success: bool
    operation: SyncOperation
    registry_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class ComponentCollectorMetrics(BaseModel):
    """Metrics for the collector operation"""
    components_watched: int = 0
    components_synced: int = 0
    components_failed: int = 0
    apis_synced: int = 0
    apis_failed: int = 0
    labels_created: int = 0
    last_sync_time: Optional[datetime] = None
    sync_duration_seconds: float = 0.0
    kubernetes_events_processed: int = 0
    registry_api_calls: int = 0
    registry_api_errors: int = 0


def extract_labels_from_component(component: ODAComponentResource) -> Dict[str, str]:
    """Extract relevant labels from ODA Component for Registry"""
    labels = {}
    
    # Add metadata labels
    if component.metadata.get("labels"):
        for key, value in component.metadata["labels"].items():
            # Filter ODA-specific labels
            if key.startswith("oda.tmforum.org/") or key in ["version", "team", "domain"]:
                clean_key = key.replace("oda.tmforum.org/", "")
                labels[clean_key] = str(value)
    
    # Add spec-based labels
    if component.spec.version:
        labels["component-version"] = component.spec.version
        
    # Add maintainer information as labels
    if component.spec.maintainers:
        for i, maintainer in enumerate(component.spec.maintainers[:3]):  # Limit to 3
            if maintainer.get("name"):
                labels[f"maintainer-{i+1}"] = maintainer["name"]
                
    return labels


def map_component_to_registry(
    component: ODAComponentResource,
    registry_name: str = "local-registry"
) -> ComponentMapping:
    """Map ODA Component to Registry Component format"""
    
    component_name = component.metadata["name"]
    namespace = component.metadata.get("namespace", "default")
    uid = component.metadata.get("uid", "")
    resource_version = component.metadata.get("resourceVersion", "")
    
    labels = extract_labels_from_component(component)
    
    # Extract exposed API names
    exposed_apis = []
    if component.spec.coreFunction.exposedAPIs:
        exposed_apis = [api.name for api in component.spec.coreFunction.exposedAPIs]
    
    return ComponentMapping(
        kubernetes_name=component_name,
        kubernetes_namespace=namespace,
        kubernetes_uid=uid,
        registry_name=registry_name,
        component_name=component_name,
        last_sync=datetime.utcnow(),
        resource_version=resource_version,
        labels=labels,
        exposed_apis=exposed_apis
    )


def create_registry_exposed_apis(
    component: ODAComponentResource,
    registry_name: str = "local-registry"
) -> List[RegistryExposedAPI]:
    """Create Registry ExposedAPI objects from ODA Component"""
    apis = []
    
    if not component.spec.coreFunction.exposedAPIs:
        return apis
        
    component_name = component.metadata["name"]
    
    for api in component.spec.coreFunction.exposedAPIs:
        # Determine API URL - try to construct from available information
        api_url = api.implementation or f"http://{component_name}:8080{api.path or '/api'}"
        
        # Determine status based on component status
        api_status = APIStatus.PENDING
        if component.status and component.status.exposed_apis:
            # Check if this API is ready in the component status
            for status_api in component.status.exposed_apis:
                if status_api.get("name") == api.name and status_api.get("ready"):
                    api_status = APIStatus.READY
                    break
        
        registry_api = RegistryExposedAPI(
            registry_name=registry_name,
            component_name=component_name,
            name=api.name,
            url=api_url,
            oas_specification=api.specification[0],
            status=api_status,
            label_ids=[]  # Will be populated after labels are created
        )
        apis.append(registry_api)
    
    return apis