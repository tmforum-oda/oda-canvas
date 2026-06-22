"""
Data models for CarbonManagement CRD

"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class CarbonIntensityConfig:
    """Configuration for scaling based on carbon intensity"""
    carbon_intensity_threshold: int
    max_replicas: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CarbonIntensityConfig':
        return cls(
            carbon_intensity_threshold=data['carbonIntensityThreshold'],
            max_replicas=data['maxReplicas']
        )


@dataclass
class TMF628ApiConfig:
    """Configuration for TMF628 Performance Management API"""
    url: str
    region: Optional[str] = None
    timeout: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TMF628ApiConfig':
        return cls(
            url=data['url'],
            region=data.get('region'),
            timeout=data.get('timeout', 10)
        )


@dataclass
class CarbonIntensityForecastDataSource:
    """Data source for carbon intensity forecast via TMF628 API"""
    tmf628_api: TMF628ApiConfig
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CarbonIntensityForecastDataSource':
        if 'tmf628Api' not in data:
            raise ValueError(
                "carbonIntensityForecastDataSource must specify 'tmf628Api' configuration"
            )
        
        tmf628_api = TMF628ApiConfig.from_dict(data['tmf628Api'])
        
        return cls(
            tmf628_api=tmf628_api
        )


@dataclass
class ScaledObjectTemplate:
    """Template for creating ScaledObjects automatically"""
    triggers: List[Dict[str, Any]]
    polling_interval: int = 30
    cooldown_period: int = 300
    min_replica_count: int = 1
    max_replica_count: int = 10
    fallback: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScaledObjectTemplate':
        return cls(
            triggers=data['triggers'],
            polling_interval=data.get('pollingInterval', 30),
            cooldown_period=data.get('cooldownPeriod', 300),
            min_replica_count=data.get('minReplicaCount', 1),
            max_replica_count=data.get('maxReplicaCount', 10),
            fallback=data.get('fallback')
        )


@dataclass
class DeploymentSelector:
    """Selector for discovering deployments by label matching"""
    match_labels: Dict[str, str]
    namespace: Optional[str] = None
    deployment_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeploymentSelector':
        return cls(
            match_labels=data['matchLabels'],
            namespace=data.get('namespace'),
            deployment_overrides=data.get('deploymentOverrides')
        )


@dataclass
class CarbonManagementSpec:
    """
    Specification for CarbonManagement
    
    Discovers deployments using deploymentSelector and creates/manages ScaledObjects
    automatically using scaledObjectTemplate. The maxReplicaCount in ScaledObjects
    is dynamically adjusted based on carbon intensity thresholds.
    """
    carbon_intensity_forecast_data_source: CarbonIntensityForecastDataSource
    default_max_replicas: int
    max_replicas_by_carbon_intensity: List[CarbonIntensityConfig]
    deployment_selector: DeploymentSelector
    scaled_object_template: ScaledObjectTemplate
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CarbonManagementSpec':
        deployment_selector = DeploymentSelector.from_dict(data['deploymentSelector'])
        scaled_object_template = ScaledObjectTemplate.from_dict(data['scaledObjectTemplate'])
        
        return cls(
            carbon_intensity_forecast_data_source=CarbonIntensityForecastDataSource.from_dict(
                data['carbonIntensityForecastDataSource']
            ),
            default_max_replicas=data['defaultMaxReplicas'],
            deployment_selector=deployment_selector,
            scaled_object_template=scaled_object_template,
            max_replicas_by_carbon_intensity=[
                CarbonIntensityConfig.from_dict(c) 
                for c in data['maxReplicasByCarbonIntensity']
            ]
        )
