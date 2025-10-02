"""
Data models for the Component Registry Service.

This module defines the Pydantic models for ComponentRegistry, ExposedAPI, and Component
following the TM Forum ODA Canvas specification.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
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
    name: str = Field(..., min_length=1, max_length=100, description="Unique name of the component registry")
    url: str = Field(..., description="Endpoint for accessing the component registry")
    type: ComponentRegistryType = Field(..., description="Type of registry")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or contain only whitespace')
        return v.strip()

    @classmethod
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        # Basic URL validation - should start with http/https
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()

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
    name: str = Field(..., min_length=1, max_length=100, description="Unique name of the component registry")
    url: str = Field(..., description="Endpoint for accessing the component registry")
    type: ComponentRegistryType = Field(..., description="Type of registry")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or contain only whitespace')
        return v.strip()

    @classmethod
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        # Basic URL validation - should start with http/https
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()


class ComponentRegistryUpdate(BaseModel):
    """Model for updating an existing ComponentRegistry."""
    url: Optional[str] = Field(None, description="Updated endpoint for accessing the component registry")
    type: Optional[ComponentRegistryType] = Field(None, description="Updated type of registry")
    labels: Optional[Dict[str, str]] = Field(None, description="Updated key-value pairs for labeling")

    @classmethod
    @validator('url')
    def validate_url(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('URL cannot be empty')
            # Basic URL validation - should start with http/https
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            return v.strip()
        return v


class UpstreamRegistryRequest(BaseModel):
    """Request model for creating upstream registry from URL."""
    url: str = Field(..., description="URL of the upstream component registry")


class ExposedAPI(BaseModel):
    """
    ExposedAPI model.
    
    Attributes:
        name: Name of the exposed API
        oas_specification: URL to OpenAPI specification
        url: Endpoint for accessing the exposed API
        labels: Key-value pairs for labeling
    """
    name: str = Field(..., min_length=1, max_length=100, description="Name of the exposed API")
    oas_specification: str = Field(..., description="URL to OpenAPI specification of this exposed API")
    url: str = Field(..., description="Endpoint for accessing the exposed API")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or contain only whitespace')
        return v.strip()

    @classmethod
    @validator('oas_specification', 'url')
    def validate_urls(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        # Basic URL validation - should start with http/https
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()

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
    name: str = Field(..., min_length=1, max_length=100, description="Name of the exposed API")
    oas_specification: str = Field(..., description="URL to OpenAPI specification")
    url: str = Field(..., description="Endpoint for accessing the exposed API")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or contain only whitespace')
        return v.strip()

    @classmethod
    @validator('oas_specification', 'url')
    def validate_urls(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        # Basic URL validation - should start with http/https
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()


class ExposedAPIUpdate(BaseModel):
    """Model for updating an existing ExposedAPI."""
    oas_specification: Optional[str] = Field(None, description="Updated URL to OpenAPI specification")
    url: Optional[str] = Field(None, description="Updated endpoint for accessing the exposed API")
    labels: Optional[Dict[str, str]] = Field(None, description="Updated key-value pairs for labeling")

    @classmethod
    @validator('oas_specification', 'url')
    def validate_urls(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('URL cannot be empty')
            # Basic URL validation - should start with http/https
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            return v.strip()
        return v


class Component(BaseModel):
    """
    Component model.
    
    Attributes:
        component_registry_ref: Reference to the component registry
        component_name: Name of the component
        component_version: Version of the component
        description: Description of the component
        exposed_apis: List of APIs exposed by this component
        labels: Key-value pairs for labeling
    """
    component_registry_ref: str = Field(..., min_length=1, description="Reference to the component registry")
    component_name: str = Field(..., min_length=1, max_length=100, description="Name of the component")
    component_version: str = Field(..., min_length=1, description="Version of the component")
    description: Optional[str] = Field(None, description="Description of the component")
    exposed_apis: List[ExposedAPI] = Field(default_factory=list, description="List of APIs exposed by this component")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('component_registry_ref', 'component_name', 'component_version')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or contain only whitespace')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "component_registry_ref": "production-registry",
                "component_name": "user-service",
                "component_version": "1.0.0",
                "description": "User management service component",
                "exposed_apis": [
                    {
                        "name": "user-management-api",
                        "oas_specification": "https://api.example.com/user-service/swagger.json",
                        "url": "https://api.example.com/user-service/v1",
                        "labels": {"version": "v1"}
                    }
                ],
                "labels": {
                    "team": "platform",
                    "category": "microservice"
                }
            }
        }


class ComponentCreate(BaseModel):
    """Model for creating a new Component."""
    component_registry_ref: str = Field(..., min_length=1, description="Reference to the component registry")
    component_name: str = Field(..., min_length=1, max_length=100, description="Name of the component")
    component_version: str = Field(..., min_length=1, description="Version of the component")
    description: Optional[str] = Field(None, description="Description of the component")
    exposed_apis: List[ExposedAPICreate] = Field(default_factory=list, description="List of APIs exposed by this component")
    labels: Dict[str, str] = Field(default_factory=dict, description="Key-value pairs for labeling")

    @classmethod
    @validator('component_registry_ref', 'component_name', 'component_version')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or contain only whitespace')
        return v.strip()


class ComponentUpdate(BaseModel):
    """Model for updating an existing Component."""
    component_version: Optional[str] = Field(None, min_length=1, description="Updated version of the component")
    description: Optional[str] = Field(None, description="Updated description of the component")
    exposed_apis: Optional[List[ExposedAPICreate]] = Field(None, description="Updated list of APIs exposed by this component")
    labels: Optional[Dict[str, str]] = Field(None, description="Updated key-value pairs for labeling")

    @classmethod
    @validator('component_version')
    def validate_version(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Version cannot be empty or contain only whitespace')
            return v.strip()
        return v