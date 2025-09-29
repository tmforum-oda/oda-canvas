"""
CRUD operations for the Component Registry Service.

This module provides database operations for ComponentRegistry, ExposedAPI, and Component models.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import models, database


class ComponentRegistryCRUD:
    """CRUD operations for ComponentRegistry."""

    @staticmethod
    def create(db: Session, registry: models.ComponentRegistryCreate) -> models.ComponentRegistry:
        """Create a new ComponentRegistry."""
        db_registry = database.ComponentRegistryDB(
            name=registry.name,
            url=registry.url,
            type=registry.type.value,
            labels=registry.labels
        )
        db.add(db_registry)
        db.commit()
        db.refresh(db_registry)
        return models.ComponentRegistry(
            name=db_registry.name,
            url=db_registry.url,
            type=db_registry.type,
            labels=db_registry.labels or {}
        )

    @staticmethod
    def get(db: Session, name: str) -> Optional[models.ComponentRegistry]:
        """Get a ComponentRegistry by name."""
        db_registry = db.query(database.ComponentRegistryDB).filter(
            database.ComponentRegistryDB.name == name
        ).first()
        if db_registry:
            return models.ComponentRegistry(
                name=db_registry.name,
                url=db_registry.url,
                type=db_registry.type,
                labels=db_registry.labels or {}
            )
        return None

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.ComponentRegistry]:
        """Get all ComponentRegistries."""
        db_registries = db.query(database.ComponentRegistryDB).offset(skip).limit(limit).all()
        return [
            models.ComponentRegistry(
                name=db_registry.name,
                url=db_registry.url,
                type=db_registry.type,
                labels=db_registry.labels or {}
            )
            for db_registry in db_registries
        ]

    @staticmethod
    def update(db: Session, name: str, registry_update: models.ComponentRegistryUpdate) -> Optional[models.ComponentRegistry]:
        """Update a ComponentRegistry."""
        db_registry = db.query(database.ComponentRegistryDB).filter(
            database.ComponentRegistryDB.name == name
        ).first()
        if not db_registry:
            return None

        update_data = registry_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "type" and value:
                setattr(db_registry, field, value.value)
            else:
                setattr(db_registry, field, value)

        db.commit()
        db.refresh(db_registry)
        return models.ComponentRegistry(
            name=db_registry.name,
            url=db_registry.url,
            type=db_registry.type,
            labels=db_registry.labels or {}
        )

    @staticmethod
    def delete(db: Session, name: str) -> bool:
        """Delete a ComponentRegistry."""
        db_registry = db.query(database.ComponentRegistryDB).filter(
            database.ComponentRegistryDB.name == name
        ).first()
        if db_registry:
            db.delete(db_registry)
            db.commit()
            return True
        return False


class ComponentCRUD:
    """CRUD operations for Component."""

    @staticmethod
    def _create_component_id(registry_ref: str, component_name: str) -> str:
        """Create composite ID for component."""
        return f"{registry_ref}:{component_name}"

    @staticmethod
    def _create_api_id(registry_ref: str, component_name: str, api_name: str) -> str:
        """Create composite ID for exposed API."""
        return f"{registry_ref}:{component_name}:{api_name}"

    @staticmethod
    def create(db: Session, component: models.ComponentCreate) -> models.Component:
        """Create a new Component."""
        # Check if registry exists
        registry = db.query(database.ComponentRegistryDB).filter(
            database.ComponentRegistryDB.name == component.component_registry_ref
        ).first()
        if not registry:
            raise ValueError(f"ComponentRegistry '{component.component_registry_ref}' not found")

        component_id = ComponentCRUD._create_component_id(
            component.component_registry_ref, component.component_name
        )

        db_component = database.ComponentDB(
            id=component_id,
            component_registry_ref=component.component_registry_ref,
            component_name=component.component_name,
            labels=component.labels
        )
        db.add(db_component)
        db.flush()  # Flush to get the component ID

        # Create exposed APIs
        exposed_apis = []
        for api in component.exposed_apis:
            api_id = ComponentCRUD._create_api_id(
                component.component_registry_ref, component.component_name, api.name
            )
            db_api = database.ExposedAPIDB(
                id=api_id,
                name=api.name,
                oas_specification=api.oas_specification,
                url=api.url,
                labels=api.labels,
                component_id=component_id
            )
            db.add(db_api)
            exposed_apis.append(models.ExposedAPI(
                name=api.name,
                oas_specification=api.oas_specification,
                url=api.url,
                labels=api.labels
            ))

        db.commit()
        db.refresh(db_component)

        return models.Component(
            component_registry_ref=db_component.component_registry_ref,
            component_name=db_component.component_name,
            exposed_apis=exposed_apis,
            labels=db_component.labels or {}
        )

    @staticmethod
    def get(db: Session, registry_ref: str, component_name: str) -> Optional[models.Component]:
        """Get a Component by registry reference and component name."""
        component_id = ComponentCRUD._create_component_id(registry_ref, component_name)
        db_component = db.query(database.ComponentDB).filter(
            database.ComponentDB.id == component_id
        ).first()
        
        if not db_component:
            return None

        exposed_apis = [
            models.ExposedAPI(
                name=api.name,
                oas_specification=api.oas_specification,
                url=api.url,
                labels=api.labels or {}
            )
            for api in db_component.exposed_apis
        ]

        return models.Component(
            component_registry_ref=db_component.component_registry_ref,
            component_name=db_component.component_name,
            exposed_apis=exposed_apis,
            labels=db_component.labels or {}
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.Component]:
        """Get all Components."""
        db_components = db.query(database.ComponentDB).offset(skip).limit(limit).all()
        
        components = []
        for db_component in db_components:
            exposed_apis = [
                models.ExposedAPI(
                    name=api.name,
                    oas_specification=api.oas_specification,
                    url=api.url,
                    labels=api.labels or {}
                )
                for api in db_component.exposed_apis
            ]
            
            components.append(models.Component(
                component_registry_ref=db_component.component_registry_ref,
                component_name=db_component.component_name,
                exposed_apis=exposed_apis,
                labels=db_component.labels or {}
            ))
        
        return components

    @staticmethod
    def get_by_registry(db: Session, registry_ref: str) -> List[models.Component]:
        """Get all Components for a specific registry."""
        db_components = db.query(database.ComponentDB).filter(
            database.ComponentDB.component_registry_ref == registry_ref
        ).all()
        
        components = []
        for db_component in db_components:
            exposed_apis = [
                models.ExposedAPI(
                    name=api.name,
                    oas_specification=api.oas_specification,
                    url=api.url,
                    labels=api.labels or {}
                )
                for api in db_component.exposed_apis
            ]
            
            components.append(models.Component(
                component_registry_ref=db_component.component_registry_ref,
                component_name=db_component.component_name,
                exposed_apis=exposed_apis,
                labels=db_component.labels or {}
            ))
        
        return components

    @staticmethod
    def update(db: Session, registry_ref: str, component_name: str, component_update: models.ComponentUpdate) -> Optional[models.Component]:
        """Update a Component."""
        component_id = ComponentCRUD._create_component_id(registry_ref, component_name)
        db_component = db.query(database.ComponentDB).filter(
            database.ComponentDB.id == component_id
        ).first()
        
        if not db_component:
            return None

        # Update component fields
        if component_update.labels is not None:
            db_component.labels = component_update.labels

        # Update exposed APIs if provided
        if component_update.exposed_apis is not None:
            # Delete existing APIs
            db.query(database.ExposedAPIDB).filter(
                database.ExposedAPIDB.component_id == component_id
            ).delete()
            
            # Create new APIs
            for api in component_update.exposed_apis:
                api_id = ComponentCRUD._create_api_id(registry_ref, component_name, api.name)
                db_api = database.ExposedAPIDB(
                    id=api_id,
                    name=api.name,
                    oas_specification=api.oas_specification,
                    url=api.url,
                    labels=api.labels,
                    component_id=component_id
                )
                db.add(db_api)

        db.commit()
        db.refresh(db_component)

        # Fetch updated component
        return ComponentCRUD.get(db, registry_ref, component_name)

    @staticmethod
    def delete(db: Session, registry_ref: str, component_name: str) -> bool:
        """Delete a Component."""
        component_id = ComponentCRUD._create_component_id(registry_ref, component_name)
        db_component = db.query(database.ComponentDB).filter(
            database.ComponentDB.id == component_id
        ).first()
        
        if db_component:
            db.delete(db_component)
            db.commit()
            return True
        return False