"""SQLAlchemy models for TMF639 Resource Inventory v5.0.0."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.types import JSON


class Resource(Base):
    """Resource model storing the entire resource as a JSON object."""
    
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, index=True)
    data = Column(JSON)
    resource_version = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResourceRelationship(Base):
    """Table mapping resource relationships with type."""
    
    __tablename__ = "resource_relationships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(String, ForeignKey("resources.id"), index=True)
    related_resource_id = Column(String, ForeignKey("resources.id"), index=True)
    relation_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resource = relationship("Resource", foreign_keys=[resource_id], backref="outgoing_relationships")
    related_resource = relationship("Resource", foreign_keys=[related_resource_id], backref="incoming_relationships")


class Hub(Base):
    """Hub model for event subscriptions."""
    
    __tablename__ = "hubs"
    
    id = Column(String, primary_key=True, index=True)
    callback = Column(String, nullable=False)
    query = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)