"""
CRUD operations for ODA Canvas entities.
Contains Create, Read, Update, Delete functions for Label, Registry, Component, and ExposedAPI entities.
"""

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import models
import schemas
from sqlalchemy import func

# ODA Canvas CRUD operations

class LabelCRUD:
    """CRUD operations for Label entity"""
    
    @staticmethod
    def create(db: Session, label: schemas.LabelCreate) -> models.Label:
        """Create a new label"""
        db_label = models.Label(**label.dict())
        db.add(db_label)
        db.commit()
        db.refresh(db_label)
        return db_label
    
    @staticmethod
    def get(db: Session, label_id: int) -> Optional[models.Label]:
        """Get label by ID"""
        return db.query(models.Label).filter(models.Label.id == label_id).first()
    
    @staticmethod
    def get_by_key_value(db: Session, key: str, value: str) -> Optional[models.Label]:
        """Get label by key and value"""
        return db.query(models.Label).filter(
            models.Label.key == key, 
            models.Label.value == value
        ).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.Label]:
        """Get all labels with pagination"""
        return db.query(models.Label).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, label_id: int, label_update: schemas.LabelUpdate) -> Optional[models.Label]:
        """Update label"""
        db_label = db.query(models.Label).filter(models.Label.id == label_id).first()
        if db_label:
            update_data = label_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_label, field, value)
            db.commit()
            db.refresh(db_label)
        return db_label
    
    @staticmethod
    def delete(db: Session, label_id: int) -> bool:
        """Delete label"""
        db_label = db.query(models.Label).filter(models.Label.id == label_id).first()
        if db_label:
            db.delete(db_label)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """Count total labels"""
        return db.query(func.count(models.Label.id)).scalar()

class RegistryCRUD:
    """CRUD operations for Registry entity"""
    
    @staticmethod
    def create(db: Session, registry: schemas.RegistryCreate) -> models.Registry:
        """Create a new registry with labels"""
        # Create registry
        registry_data = registry.dict(exclude={'label_ids'})
        db_registry = models.Registry(**registry_data)
        db.add(db_registry)
        db.flush()  # Get the registry ID
        
        # Add labels
        for label_id in registry.label_ids:
            registry_label = models.RegistryLabel(
                registry_id=db_registry.id,
                label_id=label_id
            )
            db.add(registry_label)
        
        db.commit()
        db.refresh(db_registry)
        return db_registry
    
    @staticmethod
    def get(db: Session, registry_id: int) -> Optional[models.Registry]:
        """Get registry by ID with labels"""
        return db.query(models.Registry).options(
            joinedload(models.Registry.registry_labels).joinedload(models.RegistryLabel.label)
        ).filter(models.Registry.id == registry_id).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[models.Registry]:
        """Get registry by name"""
        return db.query(models.Registry).options(
            joinedload(models.Registry.registry_labels).joinedload(models.RegistryLabel.label)
        ).filter(models.Registry.name == name).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.Registry]:
        """Get all registries with pagination"""
        return db.query(models.Registry).options(
            joinedload(models.Registry.registry_labels).joinedload(models.RegistryLabel.label)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, registry_id: int, registry_update: schemas.RegistryUpdate) -> Optional[models.Registry]:
        """Update registry"""
        db_registry = db.query(models.Registry).filter(models.Registry.id == registry_id).first()
        if db_registry:
            update_data = registry_update.dict(exclude_unset=True, exclude={'label_ids'})
            for field, value in update_data.items():
                setattr(db_registry, field, value)
            
            # Update labels if provided
            if registry_update.label_ids is not None:
                # Remove existing labels
                db.query(models.RegistryLabel).filter(
                    models.RegistryLabel.registry_id == registry_id
                ).delete()
                
                # Add new labels
                for label_id in registry_update.label_ids:
                    registry_label = models.RegistryLabel(
                        registry_id=registry_id,
                        label_id=label_id
                    )
                    db.add(registry_label)
            
            db.commit()
            db.refresh(db_registry)
        return db_registry
    
    @staticmethod
    def delete(db: Session, registry_id: int) -> bool:
        """Delete registry"""
        db_registry = db.query(models.Registry).filter(models.Registry.id == registry_id).first()
        if db_registry:
            db.delete(db_registry)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """Count total registries"""
        return db.query(func.count(models.Registry.id)).scalar()

class ComponentCRUD:
    """CRUD operations for Component entity"""
    
    @staticmethod
    def create(db: Session, component: schemas.ComponentCreate) -> models.Component:
        """Create a new component with labels"""
        # Create component
        component_data = component.dict(exclude={'label_ids'})
        db_component = models.Component(**component_data)
        db.add(db_component)
        db.flush()  # Get the component ID
        
        # Add labels
        for label_id in component.label_ids:
            component_label = models.ComponentLabel(
                component_id=db_component.id,
                label_id=label_id
            )
            db.add(component_label)
        
        db.commit()
        db.refresh(db_component)
        return db_component
    
    @staticmethod
    def get(db: Session, component_id: int) -> Optional[models.Component]:
        """Get component by ID with related data"""
        return db.query(models.Component).options(
            joinedload(models.Component.registry),
            joinedload(models.Component.component_labels).joinedload(models.ComponentLabel.label)
        ).filter(models.Component.id == component_id).first()
    
    @staticmethod
    def get_by_registry_and_name(db: Session, registry_name: str, name: str) -> Optional[models.Component]:
        """Get component by registry name and component name"""
        return db.query(models.Component).options(
            joinedload(models.Component.registry),
            joinedload(models.Component.component_labels).joinedload(models.ComponentLabel.label)
        ).filter(
            models.Component.registry_name == registry_name,
            models.Component.name == name
        ).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.Component]:
        """Get all components with pagination"""
        return db.query(models.Component).options(
            joinedload(models.Component.registry),
            joinedload(models.Component.component_labels).joinedload(models.ComponentLabel.label)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_registry(db: Session, registry_name: str, skip: int = 0, limit: int = 100) -> List[models.Component]:
        """Get components by registry"""
        return db.query(models.Component).options(
            joinedload(models.Component.registry),
            joinedload(models.Component.component_labels).joinedload(models.ComponentLabel.label)
        ).filter(models.Component.registry_name == registry_name).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, component_id: int, component_update: schemas.ComponentUpdate) -> Optional[models.Component]:
        """Update component"""
        db_component = db.query(models.Component).filter(models.Component.id == component_id).first()
        if db_component:
            update_data = component_update.dict(exclude_unset=True, exclude={'label_ids'})
            for field, value in update_data.items():
                setattr(db_component, field, value)
            
            # Update labels if provided
            if component_update.label_ids is not None:
                # Remove existing labels
                db.query(models.ComponentLabel).filter(
                    models.ComponentLabel.component_id == component_id
                ).delete()
                
                # Add new labels
                for label_id in component_update.label_ids:
                    component_label = models.ComponentLabel(
                        component_id=component_id,
                        label_id=label_id
                    )
                    db.add(component_label)
            
            db.commit()
            db.refresh(db_component)
        return db_component
    
    @staticmethod
    def delete(db: Session, component_id: int) -> bool:
        """Delete component"""
        db_component = db.query(models.Component).filter(models.Component.id == component_id).first()
        if db_component:
            db.delete(db_component)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """Count total components"""
        return db.query(func.count(models.Component.id)).scalar()

class ExposedAPICRUD:
    """CRUD operations for ExposedAPI entity"""
    
    @staticmethod
    def create(db: Session, exposed_api: schemas.ExposedAPICreate) -> models.ExposedAPI:
        """Create a new exposed API with labels"""
        # Create exposed API
        api_data = exposed_api.dict(exclude={'label_ids'})
        db_api = models.ExposedAPI(**api_data)
        db.add(db_api)
        db.flush()  # Get the API ID
        
        # Add labels
        for label_id in exposed_api.label_ids:
            api_label = models.ExposedAPILabel(
                exposed_api_id=db_api.id,
                label_id=label_id
            )
            db.add(api_label)
        
        db.commit()
        db.refresh(db_api)
        return db_api
    
    @staticmethod
    def get(db: Session, api_id: int) -> Optional[models.ExposedAPI]:
        """Get exposed API by ID with related data"""
        return db.query(models.ExposedAPI).options(
            joinedload(models.ExposedAPI.registry),
            joinedload(models.ExposedAPI.exposed_api_labels).joinedload(models.ExposedAPILabel.label)
        ).filter(models.ExposedAPI.id == api_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.ExposedAPI]:
        """Get all exposed APIs with pagination"""
        return db.query(models.ExposedAPI).options(
            joinedload(models.ExposedAPI.registry),
            joinedload(models.ExposedAPI.exposed_api_labels).joinedload(models.ExposedAPILabel.label)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_component(db: Session, registry_name: str, component_name: str, skip: int = 0, limit: int = 100) -> List[models.ExposedAPI]:
        """Get exposed APIs by component"""
        return db.query(models.ExposedAPI).options(
            joinedload(models.ExposedAPI.registry),
            joinedload(models.ExposedAPI.exposed_api_labels).joinedload(models.ExposedAPILabel.label)
        ).filter(
            models.ExposedAPI.registry_name == registry_name,
            models.ExposedAPI.component_name == component_name
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[models.ExposedAPI]:
        """Get exposed APIs by status"""
        return db.query(models.ExposedAPI).options(
            joinedload(models.ExposedAPI.registry),
            joinedload(models.ExposedAPI.exposed_api_labels).joinedload(models.ExposedAPILabel.label)
        ).filter(models.ExposedAPI.status == status).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, api_id: int, api_update: schemas.ExposedAPIUpdate) -> Optional[models.ExposedAPI]:
        """Update exposed API"""
        db_api = db.query(models.ExposedAPI).filter(models.ExposedAPI.id == api_id).first()
        if db_api:
            update_data = api_update.dict(exclude_unset=True, exclude={'label_ids'})
            for field, value in update_data.items():
                setattr(db_api, field, value)
            
            # Update labels if provided
            if api_update.label_ids is not None:
                # Remove existing labels
                db.query(models.ExposedAPILabel).filter(
                    models.ExposedAPILabel.exposed_api_id == api_id
                ).delete()
                
                # Add new labels
                for label_id in api_update.label_ids:
                    api_label = models.ExposedAPILabel(
                        exposed_api_id=api_id,
                        label_id=label_id
                    )
                    db.add(api_label)
            
            db.commit()
            db.refresh(db_api)
        return db_api
    
    @staticmethod
    def update_status(db: Session, api_id: int, status: str) -> Optional[models.ExposedAPI]:
        """Update exposed API status"""
        db_api = db.query(models.ExposedAPI).filter(models.ExposedAPI.id == api_id).first()
        if db_api:
            db_api.status = status
            db.commit()
            db.refresh(db_api)
        return db_api
    
    @staticmethod
    def delete(db: Session, api_id: int) -> bool:
        """Delete exposed API"""
        db_api = db.query(models.ExposedAPI).filter(models.ExposedAPI.id == api_id).first()
        if db_api:
            db.delete(db_api)
            db.commit()
            return True
        return False
    
    @staticmethod
    def count(db: Session) -> int:
        """Count total exposed APIs"""
        return db.query(func.count(models.ExposedAPI.id)).scalar()

# Instantiate CRUD classes
label_crud = LabelCRUD()
registry_crud = RegistryCRUD()
component_crud = ComponentCRUD()
exposed_api_crud = ExposedAPICRUD()