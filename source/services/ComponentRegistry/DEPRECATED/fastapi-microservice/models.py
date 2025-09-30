"""
Database models for the FastAPI microservice.
Defines ODA Canvas entities (Registry, Component, ExposedAPI, Label) with relationships.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# ODA Canvas data models

class RegistryTypeEnum(enum.Enum):
    """Registry type enumeration"""
    upstream = "upstream"
    downstream = "downstream"
    self = "self"

class APIStatusEnum(enum.Enum):
    """ExposedAPI status enumeration"""
    pending = "pending"
    ready = "ready"

class Label(Base):
    """Label entity representing key-value pairs for tagging"""
    __tablename__ = "labels"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships to registries, components, and exposed APIs
    registry_labels = relationship("RegistryLabel", back_populates="label")
    component_labels = relationship("ComponentLabel", back_populates="label")
    exposed_api_labels = relationship("ExposedAPILabel", back_populates="label")

class Registry(Base):
    """Registry entity representing component registries"""
    __tablename__ = "registries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(Enum(RegistryTypeEnum), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    components = relationship("Component", back_populates="registry")
    registry_labels = relationship("RegistryLabel", back_populates="registry", cascade="all, delete-orphan")

class ExposedAPI(Base):
    """ExposedAPI entity representing APIs exposed by components"""
    __tablename__ = "exposed_apis"
    
    id = Column(Integer, primary_key=True, index=True)
    registry_name = Column(String(100), ForeignKey("registries.name"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    oas_specification = Column(Text)  # OpenAPI Specification
    status = Column(Enum(APIStatusEnum), default=APIStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    registry = relationship("Registry")
    exposed_api_labels = relationship("ExposedAPILabel", back_populates="exposed_api", cascade="all, delete-orphan")

class Component(Base):
    """Component entity representing ODA components"""
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    registry_name = Column(String(100), ForeignKey("registries.name"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    registry = relationship("Registry", back_populates="components")
    component_labels = relationship("ComponentLabel", back_populates="component", cascade="all, delete-orphan")

# Association tables for many-to-many relationships with labels

class RegistryLabel(Base):
    """Association table for Registry-Label many-to-many relationship"""
    __tablename__ = "registry_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    registry_id = Column(Integer, ForeignKey("registries.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)
    
    # Relationships
    registry = relationship("Registry", back_populates="registry_labels")
    label = relationship("Label", back_populates="registry_labels")

class ComponentLabel(Base):
    """Association table for Component-Label many-to-many relationship"""
    __tablename__ = "component_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)
    
    # Relationships
    component = relationship("Component", back_populates="component_labels")
    label = relationship("Label", back_populates="component_labels")

class ExposedAPILabel(Base):
    """Association table for ExposedAPI-Label many-to-many relationship"""
    __tablename__ = "exposed_api_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    exposed_api_id = Column(Integer, ForeignKey("exposed_apis.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)
    
    # Relationships
    exposed_api = relationship("ExposedAPI", back_populates="exposed_api_labels")
    label = relationship("Label", back_populates="exposed_api_labels")