"""SQLAlchemy models for TMF639 Resource Inventory."""

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
    
    # Relationships
    characteristics = relationship("ResourceCharacteristic", back_populates="resource", cascade="all, delete-orphan")
    related_parties = relationship("ResourceRelatedParty", back_populates="resource", cascade="all, delete-orphan")
    notes = relationship("ResourceNote", back_populates="resource", cascade="all, delete-orphan")
    attachments = relationship("ResourceAttachment", back_populates="resource", cascade="all, delete-orphan")
    resource_relationships = relationship("ResourceRelationshipModel", back_populates="resource", cascade="all, delete-orphan")
    
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
    role = Column(String)
    referredType = Column(String, nullable=False)
    
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


class EventSubscription(Base):
    """Event subscription for notifications."""
    
    __tablename__ = "event_subscriptions"
    
    id = Column(String, primary_key=True, index=True)
    callback = Column(String, nullable=False)
    query = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
