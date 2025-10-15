"""Pydantic schemas for TMF639 Resource Inventory API."""

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


class ResourceUsageStateType(str, Enum):
    """Resource usage state enumeration."""
    idle = "idle"
    active = "active"
    busy = "busy"


class CharacteristicBase(BaseModel):
    """Base schema for Characteristic."""
    name: str
    value: Any
    valueType: Optional[str] = None


class Characteristic(CharacteristicBase):
    """Characteristic schema."""
    id: Optional[str] = None


class RelatedPartyBase(BaseModel):
    """Base schema for RelatedParty."""
    name: Optional[str] = None
    role: Optional[str] = None


class RelatedParty(RelatedPartyBase):
    """Related party schema."""
    id: str
    href: Optional[str] = None
    referredType: str = Field(..., alias="@referredType")

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


class AttachmentRefOrValueBase(BaseModel):
    """Base schema for Attachment."""
    attachmentType: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None


class AttachmentRefOrValue(AttachmentRefOrValueBase):
    """Attachment schema."""
    id: Optional[str] = None
    href: Optional[str] = None


class ResourceSpecificationRef(BaseModel):
    """Resource specification reference."""
    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None


class RelatedPlaceRefOrValue(BaseModel):
    """Related place reference or value."""
    id: Optional[str] = None
    href: Optional[str] = None
    name: Optional[str] = None
    role: str


class ResourceRefOrValue(BaseModel):
    """Resource reference or value."""
    id: str
    href: str
    name: Optional[str] = None


class ResourceRelationship(BaseModel):
    """Resource relationship schema."""
    id: Optional[str] = None
    href: Optional[str] = None
    relationshipType: str
    resource: ResourceRefOrValue


class ResourceBase(BaseModel):
    """Base schema for Resource."""
    category: Optional[str] = None
    description: Optional[str] = None
    endOperatingDate: Optional[datetime] = None
    name: Optional[str] = None
    resourceVersion: Optional[str] = None
    startOperatingDate: Optional[datetime] = None
    administrativeState: Optional[ResourceAdministrativeStateType] = None
    operationalState: Optional[ResourceOperationalStateType] = None
    resourceStatus: Optional[ResourceStatusType] = None
    usageState: Optional[ResourceUsageStateType] = None
    resourceCharacteristic: Optional[List[Characteristic]] = None
    relatedParty: Optional[List[RelatedParty]] = None
    note: Optional[List[Note]] = None
    attachment: Optional[List[AttachmentRefOrValue]] = None
    resourceRelationship: Optional[List[ResourceRelationship]] = None
    resourceSpecification: Optional[ResourceSpecificationRef] = None
    place: Optional[RelatedPlaceRefOrValue] = None


class ResourceCreate(ResourceBase):
    """Schema for creating a Resource."""
    id: Optional[str] = None
    name: str


class ResourceUpdate(ResourceBase):
    """Schema for updating a Resource."""
    pass


class Resource(ResourceBase):
    """Full Resource schema."""
    id: str
    href: str
    baseType: Optional[str] = Field(None, alias="@baseType")
    schemaLocation: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")

    class Config:
        from_attributes = True
        populate_by_name = True


class EventSubscriptionInput(BaseModel):
    """Schema for event subscription input."""
    callback: str
    query: Optional[str] = None


class EventSubscription(BaseModel):
    """Schema for event subscription."""
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