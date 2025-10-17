"""CRUD operations for TMF639 Resource Inventory v5.0.0."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime
from app import models, schemas


def create_resource(db: Session, resource: dict, base_url: str) -> models.Resource:
    """Create a new resource as a JSON object."""
    resource_id = resource.get("id") or str(uuid.uuid4())
    resource["id"] = resource_id
    db_resource = models.Resource(
        id=resource_id,
        data=resource,
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    # Handle resourceRelationship separately
    for rel in resource.get("resourceRelationship", []):
        rel_type = rel.get("relationshipType")
        related_resource = rel.get("resource", {})
        related_resource_id = related_resource.get("id")
        # Optionally create the related resource if it does not exist
        if related_resource_id and not db.query(models.Resource).filter(models.Resource.id == related_resource_id).first():
            db_related = models.Resource(
                id=related_resource_id,
                data=related_resource,
            )
            db.add(db_related)
            db.commit()
        db_rel = models.ResourceRelationship(
            resource_id=resource_id,
            related_resource_id=related_resource_id,
            relation_type=rel_type
        )
        db.add(db_rel)
    db.commit()
    return db_resource


def get_resource(db: Session, id: str) -> Optional[models.Resource]:
    """Retrieve a resource by ID."""
    return db.query(models.Resource).filter(models.Resource.id == id).first()


def get_resources(
    db: Session, 
    offset: int = 0, 
    limit: int = 100, 
    filter_param: Optional[str] = None, 
    sort: Optional[str] = None
):
    """List resources with pagination."""
    query = db.query(models.Resource)
    total_count = query.count()
    resources = query.offset(offset).limit(limit).all()
    return resources, total_count


def update_resource(db: Session, id: str, resource_update: dict) -> Optional[models.Resource]:
    """Update a resource (replace JSON object)."""
    db_resource = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not db_resource:
        return None
    db_resource.data = resource_update
    db.commit()
    db.refresh(db_resource)
    return db_resource


def delete_resource(db: Session, id: str) -> bool:
    """Delete a resource and its relationships."""
    db_resource = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not db_resource:
        return False
    db.query(models.ResourceRelationship).filter(models.ResourceRelationship.resource_id == id).delete()
    db.delete(db_resource)
    db.commit()
    return True


# Relationship CRUD

def create_resource_relationship(db: Session, resource_id: str, related_resource_id: str, relation_type: str) -> models.ResourceRelationship:
    db_rel = models.ResourceRelationship(resource_id=resource_id, related_resource_id=related_resource_id, relation_type=relation_type)
    db.add(db_rel)
    db.commit()
    db.refresh(db_rel)
    return db_rel

def get_resource_relationships(db: Session, resource_id: str) -> List[models.ResourceRelationship]:
    return db.query(models.ResourceRelationship).filter(models.ResourceRelationship.resource_id == resource_id).all()


# Hub CRUD

def create_hub(db: Session, hub_data: schemas.HubInput) -> schemas.Hub:
    """Create a new event subscription hub."""
    import uuid
    hub_id = str(uuid.uuid4())
    db_hub = models.Resource(
        id=hub_id,
        data={"callback": hub_data.callback, "query": hub_data.query},
    )
    db.add(db_hub)
    db.commit()
    db.refresh(db_hub)
    return schemas.Hub(id=db_hub.id, callback=db_hub.data["callback"], query=db_hub.data.get("query"))


def get_hub(db: Session, id: str) -> schemas.Hub:
    """Retrieve a hub by ID."""
    db_hub = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not db_hub or "callback" not in db_hub.data:
        return None
    return schemas.Hub(id=db_hub.id, callback=db_hub.data["callback"], query=db_hub.data.get("query"))


def delete_hub(db: Session, id: str) -> bool:
    """Delete a hub by ID."""
    db_hub = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not db_hub or "callback" not in db_hub.data:
        return False
    db.delete(db_hub)
    db.commit()
    return True