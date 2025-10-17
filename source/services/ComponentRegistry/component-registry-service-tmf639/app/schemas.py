"""Pydantic schemas for TMF639 Resource Inventory API v5.0.0."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class ResourceAdministrativeStateType(str, Enum):
    """Resource administrative state enumeration."""
    locked = "locked"
    unlocked = "unlocked"
    shutdown = "shutdown"


class ResourceOperationalStateType(str, Enum):
    """Resource operational state enumeration."""
    enable = "enable"
    disable = "disable"


class ResourceStatusType(str, Enum):
    """Resource status enumeration."""
    standby = "standby"
    alarm = "alarm"
    available = "available"
    reserved = "reserved"
    unknown = "unknown"
    suspended = "suspended"
    installed = "installed"
    not_exists = "not exists"
    pendingRemoval = "pendingRemoval"
    planned = "planned"


class ResourceUsageStateType(str, Enum):
    """Resource usage state enumeration."""
    idle = "idle"
    active = "active"
    busy = "busy"


class TimePeriod(BaseModel):
    """Time period schema."""
    startDateTime: Optional[datetime] = None
    endDateTime: Optional[datetime] = None


class CharacteristicBase(BaseModel):
    """Base schema for Characteristic."""
    name: str
    value: Any
    valueType: Optional[str] = None


class Characteristic(CharacteristicBase):
    """Characteristic schema."""
    id: Optional[str] = None


class RelatedPartyRefOrPartyRoleRef(BaseModel):
    """Related party reference or party role reference."""
    role: str
    id: Optional[str] = None
    href: Optional[str] = None
    name: Optional[str] = None
    referredType: Optional[str] = Field(None, alias="@referredType")

    class Config:
        populate_by_name = True


class NoteBase(BaseModel):
    """Base schema for Note."""
    author: Optional[str] = None
    date: Optional[datetime] = None
    text: Optional[str] = None


class Note(NoteBase):
    """Note schema."""
    id: Optional[str] = None
    href: Optional[str] = None


class AttachmentRefBase(BaseModel):
    """Base schema for Attachment."""
    attachmentType: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class AttachmentRef(AttachmentRefBase):
    """Attachment schema."""
    id: Optional[str] = None
    href: Optional[str] = None


class ResourceSpecificationRef(BaseModel):
    """Resource specification reference."""
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None


class RelatedPlaceRef(BaseModel):
    """Related place reference."""
    id: Optional[str] = None
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referredType: Optional[str] = Field(None, alias="@referredType")

    class Config:
        populate_by_name = True


class ResourceRefOrValue(BaseModel):
    """Resource reference or value."""
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    referredType: Optional[str] = Field(None, alias="@referredType")

    class Config:
        populate_by_name = True


class ResourceRelationship(BaseModel):
    """ResourceRelationship schema."""
    id: Optional[int]
    resource_id: str
    related_resource_id: str
    relation_type: str
    created_at: Optional[datetime]


class ExternalIdentifier(BaseModel):
    """External identifier from other systems."""
    id: str
    owner: Optional[str] = None
    externalIdentifierType: Optional[str] = None


class Feature(BaseModel):
    """Configuration feature."""
    id: Optional[str] = None
    name: Optional[str] = None
    isEnabled: Optional[bool] = True
    isBundle: Optional[bool] = False
    featureCharacteristic: Optional[List[Characteristic]] = None


class IntentRef(BaseModel):
    """Intent reference."""
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Resource(BaseModel):
    """Resource schema as a generic JSON object."""
    id: str
    data: dict
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ResourceCreate(BaseModel):
    """Resource creation schema as a generic dict."""
    class Config:
        extra = "allow"


class ResourceUpdate(BaseModel):
    """Resource update schema as a generic dict."""
    class Config:
        extra = "allow"


class HubInput(BaseModel):
    """Schema for hub/event subscription input."""
    callback: str
    query: Optional[str] = None


class Hub(BaseModel):
    """Schema for hub/event subscription."""
    id: str
    callback: str
    query: Optional[str] = None

    class Config:
        from_attributes = True


class Error(BaseModel):
    """Error response schema."""
    code: str
    reason: str
    message: Optional[str] = None
    status: Optional[str] = None
    referenceError: Optional[str] = None
    baseType: Optional[str] = Field(None, alias="@baseType")
    schemaLocation: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")

    class Config:
        populate_by_name = True