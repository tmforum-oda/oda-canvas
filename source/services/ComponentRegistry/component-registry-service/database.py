"""
Database models and configuration for the Component Registry Service.

This module defines SQLAlchemy models for persisting ComponentRegistry, ExposedAPI,
and Component data.
"""

from sqlalchemy import create_engine, Column, String, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
import os

# Database configuration
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./data/component_registry.db")
print(f"Using database URL: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ComponentRegistryDB(Base):
    """SQLAlchemy model for ComponentRegistry."""
    __tablename__ = "component_registries"

    name = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False)
    type = Column(String, nullable=False)
    labels = Column(JSON, default=dict)

    # Relationship to components
    components = relationship("ComponentDB", back_populates="registry", cascade="all, delete-orphan")


class ExposedAPIDB(Base):
    """SQLAlchemy model for ExposedAPI."""
    __tablename__ = "exposed_apis"

    id = Column(String, primary_key=True, index=True)  # Composite key: component_registry_ref:component_name:api_name
    name = Column(String, nullable=False)
    oas_specification = Column(String, nullable=False)
    url = Column(String, nullable=False)
    labels = Column(JSON, default=dict)
    
    # Foreign key to component
    component_id = Column(String, ForeignKey("components.id"), nullable=False)
    component = relationship("ComponentDB", back_populates="exposed_apis")


class ComponentDB(Base):
    """SQLAlchemy model for Component."""
    __tablename__ = "components"

    id = Column(String, primary_key=True, index=True)  # Composite key: component_registry_ref:component_name
    component_registry_ref = Column(String, ForeignKey("component_registries.name"), nullable=False)
    component_name = Column(String, nullable=False)
    component_version = Column(String, nullable=False, default="1.0.0")
    description = Column(String, nullable=True)
    labels = Column(JSON, default=dict)

    # Relationships
    registry = relationship("ComponentRegistryDB", back_populates="components")
    exposed_apis = relationship("ExposedAPIDB", back_populates="component", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('component_registry_ref', 'component_name', name='unique_component'),
    )


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Initialize database
def init_db():
    """Initialize database with tables"""
    create_tables()
