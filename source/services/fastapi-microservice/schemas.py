"""
Pydantic schemas for request/response validation and serialization.
Contains ODA Canvas entities only.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Enums for ODA Canvas
class RegistryTypeEnum(str, Enum):
    upstream = "upstream"
    downstream = "downstream"
    self = "self"

class APIStatusEnum(str, Enum):
    pending = "pending"
    ready = "ready"

# ODA Canvas schemas

# Label schemas
class LabelBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=200)

class LabelCreate(LabelBase):
    pass

class LabelUpdate(BaseModel):
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = Field(None, min_length=1, max_length=200)

class Label(LabelBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Registry schemas
class RegistryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: RegistryTypeEnum
    url: str = Field(..., min_length=1, max_length=500)

class RegistryCreate(RegistryBase):
    label_ids: List[int] = Field(default_factory=list)

class RegistryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[RegistryTypeEnum] = None
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    label_ids: Optional[List[int]] = None

class Registry(RegistryBase):
    id: int
    created_at: datetime
    labels: List[Label] = []
    
    class Config:
        from_attributes = True

# Component schemas
class ComponentBase(BaseModel):
    registry_name: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)

class ComponentCreate(ComponentBase):
    label_ids: List[int] = Field(default_factory=list)

class ComponentUpdate(BaseModel):
    registry_name: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    label_ids: Optional[List[int]] = None

class Component(ComponentBase):
    id: int
    created_at: datetime
    registry: Optional[Registry] = None
    labels: List[Label] = []
    
    class Config:
        from_attributes = True

# ExposedAPI schemas
class ExposedAPIBase(BaseModel):
    registry_name: str = Field(..., min_length=1, max_length=100)
    component_name: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    oas_specification: Optional[str] = None
    status: APIStatusEnum = APIStatusEnum.pending

class ExposedAPICreate(ExposedAPIBase):
    label_ids: List[int] = Field(default_factory=list)

class ExposedAPIUpdate(BaseModel):
    registry_name: Optional[str] = Field(None, min_length=1, max_length=100)
    component_name: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    oas_specification: Optional[str] = None
    status: Optional[APIStatusEnum] = None
    label_ids: Optional[List[int]] = None

class ExposedAPI(ExposedAPIBase):
    id: int
    created_at: datetime
    registry: Optional[Registry] = None
    component: Optional[Component] = None
    labels: List[Label] = []
    
    class Config:
        from_attributes = True

# Response schemas with pagination
class PaginatedResponse(BaseModel):
    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int