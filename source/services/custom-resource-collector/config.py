"""
Configuration management for the Custom-Resource Collector.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class KubernetesConfig(BaseModel):
    """Kubernetes connection configuration"""
    k8s_proxy: str = Field(default="", description="Proxy to be used for Kubernetes connection")
    namespace: str = Field(default="default", description="Kubernetes namespace to monitor")
    config_path: Optional[str] = Field(default=None, description="Path to kubeconfig file")
    in_cluster: bool = Field(default=False, description="Whether running inside Kubernetes cluster")
    watch_timeout: int = Field(default=300, description="Timeout for watch operations in seconds")


class ComponentRegistryConfig(BaseModel):
    """Component Registry microservice configuration"""
    base_url: str = Field(..., description="Base URL of the Component Registry microservice")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class MonitoringConfig(BaseModel):
    """Monitoring and metrics configuration"""
    enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    port: int = Field(default=8080, description="Metrics server port")
    endpoint: str = Field(default="/metrics", description="Metrics endpoint path")


class CollectorConfig(BaseModel):
    """Main collector configuration"""
    kubernetes: KubernetesConfig = Field(default_factory=KubernetesConfig)
    component_registry: ComponentRegistryConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # ODA Component specific settings
    component_group: str = Field(default="oda.tmforum.org", description="ODA Component API group")
    component_version: str = Field(default="v1beta3", description="ODA Component API version")
    component_plural: str = Field(default="components", description="ODA Component resource plural name")
    
    # Sync settings
    sync_interval: int = Field(default=60, description="Full sync interval in seconds")
    batch_size: int = Field(default=10, description="Number of resources to process in batch")


def load_config() -> CollectorConfig:
    """Load configuration from environment variables and defaults"""
    
    # Component Registry configuration (required)
    registry_base_url = os.getenv("COMPONENT_REGISTRY_URL", "https://localhost:8000")
    
    component_registry_config = ComponentRegistryConfig(
        base_url=registry_base_url,
        api_key=os.getenv("COMPONENT_REGISTRY_API_KEY"),
        timeout=int(os.getenv("COMPONENT_REGISTRY_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("COMPONENT_REGISTRY_RETRY_ATTEMPTS", "3")),
        retry_delay=int(os.getenv("COMPONENT_REGISTRY_RETRY_DELAY", "5"))
    )
    
    # Kubernetes configuration
    kubernetes_config = KubernetesConfig(
        k8s_proxy=os.getenv("K8S_PROXY", ""),
        namespace=os.getenv("KUBERNETES_NAMESPACE", "default"),
        config_path=os.getenv("KUBECONFIG"),
        in_cluster=os.getenv("KUBERNETES_IN_CLUSTER", "false").lower() == "true",
        watch_timeout=int(os.getenv("KUBERNETES_WATCH_TIMEOUT", "300"))
    )
    
    # Logging configuration
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    
    # Monitoring configuration
    monitoring_config = MonitoringConfig(
        enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        port=int(os.getenv("MONITORING_PORT", "8080")),
        endpoint=os.getenv("MONITORING_ENDPOINT", "/metrics")
    )
    
    return CollectorConfig(
        kubernetes=kubernetes_config,
        component_registry=component_registry_config,
        logging=logging_config,
        monitoring=monitoring_config,
        component_group=os.getenv("ODA_COMPONENT_GROUP", "oda.tmforum.org"),
        component_version=os.getenv("ODA_COMPONENT_VERSION", "v1beta3"),
        component_plural=os.getenv("ODA_COMPONENT_PLURAL", "components"),
        sync_interval=int(os.getenv("SYNC_INTERVAL", "60")),
        batch_size=int(os.getenv("BATCH_SIZE", "10"))
    )