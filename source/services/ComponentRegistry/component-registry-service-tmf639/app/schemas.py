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
    """Resource relationship schema."""
    id: Optional[str] = None
    href: Optional[str] = None
    relationshipType: str
    resource: ResourceRefOrValue
    resourceRelationshipCharacteristic: Optional[List[Characteristic]] = None


class RelatedResourceOrderItem(BaseModel):
    """Related resource order item."""
    id: str
    href: Optional[str] = None
    resourceOrderId: Optional[str] = None
    role: Optional[str] = None


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
    validFor: Optional[TimePeriod] = None
    resourceCharacteristic: Optional[List[Characteristic]] = None
    relatedParty: Optional[List[RelatedPartyRefOrPartyRoleRef]] = None
    note: Optional[List[Note]] = None
    attachment: Optional[List[AttachmentRef]] = None
    resourceRelationship: Optional[List[ResourceRelationship]] = None
    resourceSpecification: Optional[ResourceSpecificationRef] = None
    place: Optional[List[RelatedPlaceRef]] = None
    resourceOrderItem: Optional[List[RelatedResourceOrderItem]] = None
    supportingResource: Optional[List[ResourceRefOrValue]] = None
    activationFeature: Optional[List[Feature]] = None
    intent: Optional[IntentRef] = None
    externalIdentifier: Optional[List[ExternalIdentifier]] = None


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
