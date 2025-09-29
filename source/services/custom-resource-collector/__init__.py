"""
Custom-Resource Collector for ODA Canvas Components.

A Python application that monitors Kubernetes ODA Component Custom Resources
and synchronizes them with the Component Registry microservice.
"""

__version__ = "1.0.0"
__author__ = "ODA Canvas Team"
__description__ = "Custom-Resource Collector for ODA Canvas Components"

from config import load_config, CollectorConfig
from main import CustomResourceCollector, main
from models import (
    ODAComponentResource, ComponentMapping, RegistryLabel,
    RegistryComponent, RegistryExposedAPI, SyncResult
)

__all__ = [
    "load_config",
    "CollectorConfig", 
    "CustomResourceCollector",
    "main",
    "ODAComponentResource",
    "ComponentMapping",
    "RegistryLabel",
    "RegistryComponent", 
    "RegistryExposedAPI",
    "SyncResult"
]