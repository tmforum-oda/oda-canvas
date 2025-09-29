"""
Data models for the Component Registry Service.

This module defines the Pydantic models for ComponentRegistry, ExposedAPI, and Component
following the TM Forum ODA Canvas specification.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ComponentRegistryType(str, Enum):
    """Type of component registry."""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    SELF = "self"


class ComponentRegistry(BaseModel):
    """
    ComponentRegistry model.
    
    Attributes:
        name: Unique name of the component registry
        url: Endpoint for accessing the component registry
        type: Type of registry (upstream/downstream/self)
        labels: Key-value pairs for labeling
    """
    name: str = Field(..., description="Unique name of the component registry")
    url: str = Field(..., description="Endpoint for accessing the component registry")
    type: ComponentRegistryType = Field(..., description="Type of registry")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "production-registry",
                "url": "https://registry.example.com/api",
                "type": "upstream",
                "labels": {
                    "environment": "production",
                    "region": "us-east-1"
                }
            }
        }


class ComponentRegistryCreate(BaseModel):
    """Model for creating a new ComponentRegistry."""
    name: str
    url: str
    type: ComponentRegistryType
    labels: Dict[str, str] = Field(default_factory=dict)


class ComponentRegistryUpdate(BaseModel):
    """Model for updating an existing ComponentRegistry."""
    url: Optional[str] = None
    type: Optional[ComponentRegistryType] = None
    labels: Optional[Dict[str, str]] = None


class ExposedAPI(BaseModel):
    """
    ExposedAPI model.
    
    Attributes:
        name: Name of the exposed API
        oas_specification: URL to OpenAPI specification
        url: Endpoint for accessing the exposed API
        labels: Key-value pairs for labeling
    """
    name: str = Field(..., description="Name of the exposed API")
    oas_specification: str = Field(..., description="URL to OpenAPI specification of this exposed API")
    url: str = Field(..., description="Endpoint for accessing the exposed API")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "product-catalog-api",
                "oas_specification": "https://api.example.com/swagger.json",
                "url": "https://api.example.com/v1/products",
                "labels": {
                    "version": "v1",
                    "category": "catalog"
                }
            }
        }


class ExposedAPICreate(BaseModel):
    """Model for creating a new ExposedAPI."""
    name: str
    oas_specification: str
    url: str
    labels: Dict[str, str] = Field(default_factory=dict)


class ExposedAPIUpdate(BaseModel):
    """Model for updating an existing ExposedAPI."""
    oas_specification: Optional[str] = None
    url: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


class Component(BaseModel):
    """
    Component model.
    
    Attributes:
        component_registry_ref: Reference to ComponentRegistry
        component_name: Unique name together with ComponentRegistry
        exposed_apis: List of ExposedAPI
        labels: Key-value pairs for labeling
    """
    component_registry_ref: str = Field(..., description="Reference to ComponentRegistry")
    component_name: str = Field(..., description="Unique name together with ComponentRegistry")
    exposed_apis: List[ExposedAPI] = Field(default_factory=list, description="List of ExposedAPI")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    class Config:
        json_schema_extra = {
            "example": {
                "component_registry_ref": "production-registry",
                "component_name": "product-catalog-service",
                "exposed_apis": [
                    {
                        "name": "product-catalog-api",
                        "oas_specification": "https://api.example.com/swagger.json",
                        "url": "https://api.example.com/v1/products",
                        "labels": {
                            "version": "v1"
                        }
                    }
                ],
                "labels": {
                    "team": "catalog-team",
                    "environment": "production"
                }
            }
        }


class ComponentCreate(BaseModel):
    """Model for creating a new Component."""
    component_registry_ref: str
    component_name: str
    exposed_apis: List[ExposedAPICreate] = Field(default_factory=list)
    labels: Dict[str, str] = Field(default_factory=dict)


class ComponentUpdate(BaseModel):
    """Model for updating an existing Component."""
    exposed_apis: Optional[List[ExposedAPICreate]] = None
    labels: Optional[Dict[str, str]] = None


class ComponentIdentifier(BaseModel):
    """Unique identifier for a Component."""
    component_registry_ref: str
    component_name: str