"""SQLAlchemy models for TMF639 Resource Inventory v5.0.0."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Resource(Base):
    """Resource model representing a physical or logical resource."""
    
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, index=True)
    href = Column(String)
    category = Column(String)
    description = Column(Text)
    endOperatingDate = Column(DateTime, nullable=True)
    name = Column(String)
    resourceVersion = Column(String)
    startOperatingDate = Column(DateTime, nullable=True)
    administrativeState = Column(String)
    operationalState = Column(String)
    resourceStatus = Column(String)
    usageState = Column(String)
    baseType = Column(String)
    schemaLocation = Column(String)
    type = Column(String)
    
    # v5.0.0 new fields
    validFor_startDateTime = Column(DateTime, nullable=True)
    validFor_endDateTime = Column(DateTime, nullable=True)
    intent_id = Column(String, nullable=True)
    intent_href = Column(String, nullable=True)
    intent_name = Column(String, nullable=True)
    
    # Relationships
    characteristics = relationship("ResourceCharacteristic", back_populates="resource", cascade="all, delete-orphan")
    related_parties = relationship("ResourceRelatedParty", back_populates="resource", cascade="all, delete-orphan")
    notes = relationship("ResourceNote", back_populates="resource", cascade="all, delete-orphan")
    attachments = relationship("ResourceAttachment", back_populates="resource", cascade="all, delete-orphan")
    resource_relationships = relationship("ResourceRelationshipModel", back_populates="resource", cascade="all, delete-orphan")
    places = relationship("ResourcePlace", back_populates="resource", cascade="all, delete-orphan")
    resource_order_items = relationship("ResourceOrderItem", back_populates="resource", cascade="all, delete-orphan")
    supporting_resources = relationship("SupportingResource", back_populates="resource", cascade="all, delete-orphan")
    activation_features = relationship("ActivationFeature", back_populates="resource", cascade="all, delete-orphan")
    external_identifiers = relationship("ResourceExternalIdentifier", back_populates="resource", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResourceCharacteristic(Base):
    """Characteristic of a resource."""
    
    __tablename__ = "resource_characteristics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    name = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    valueType = Column(String)
    
    resource = relationship("Resource", back_populates="characteristics")


class ResourceRelatedParty(Base):
    """Related party for a resource."""
    
    __tablename__ = "resource_related_parties"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    name = Column(String)
    role = Column(String, nullable=False)
    referredType = Column(String)
    
    resource = relationship("Resource", back_populates="related_parties")


class ResourceNote(Base):
    """Note attached to a resource."""
    
    __tablename__ = "resource_notes"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    author = Column(String)
    date = Column(DateTime)
    text = Column(Text)
    
    resource = relationship("Resource", back_populates="notes")


class ResourceAttachment(Base):
    """Attachment for a resource."""
    
    __tablename__ = "resource_attachments"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    attachmentType = Column(String)
    content = Column(Text)
    description = Column(Text)
    mimeType = Column(String)
    name = Column(String)
    url = Column(String)
    
    resource = relationship("Resource", back_populates="attachments")


class ResourceRelationshipModel(Base):
    """Relationship between resources."""
    
    __tablename__ = "resource_relationships"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    relationshipType = Column(String, nullable=False)
    related_resource_id = Column(String)
    related_resource_href = Column(String)
    
    resource = relationship("Resource", back_populates="resource_relationships")


class ResourcePlace(Base):
    """Place reference for a resource (v5.0.0 - now array)."""
    
    __tablename__ = "resource_places"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    name = Column(String)
    role = Column(String)
    referredType = Column(String)
    
    resource = relationship("Resource", back_populates="places")


class ResourceOrderItem(Base):
    """Related resource order item (v5.0.0 new)."""
    
    __tablename__ = "resource_order_items"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    href = Column(String)
    resourceOrderId = Column(String)
    role = Column(String)
    
    resource = relationship("Resource", back_populates="resource_order_items")


class SupportingResource(Base):
    """Supporting resource reference (v5.0.0 new)."""
    
    __tablename__ = "supporting_resources"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    supporting_resource_id = Column(String, nullable=False)
    href = Column(String)
    name = Column(String)
    referredType = Column(String)
    
    resource = relationship("Resource", back_populates="supporting_resources")


class ActivationFeature(Base):
    """Activation feature (v5.0.0 new)."""
    
    __tablename__ = "activation_features"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    name = Column(String)
    isEnabled = Column(Boolean, default=True)
    isBundle = Column(Boolean, default=False)
    
    resource = relationship("Resource", back_populates="activation_features")


class ResourceExternalIdentifier(Base):
    """External identifier (v5.0.0 new)."""
    
    __tablename__ = "resource_external_identifiers"
    
    id = Column(String, primary_key=True, index=True)
    resource_id = Column(String, ForeignKey("resources.id"))
    owner = Column(String)
    externalIdentifierType = Column(String)
    
    resource = relationship("Resource", back_populates="external_identifiers")


class EventSubscription(Base):
    """Event subscription for notifications."""
    
    __tablename__ = "event_subscriptions"
    
    id = Column(String, primary_key=True, index=True)
    callback = Column(String, nullable=False)
    query = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)