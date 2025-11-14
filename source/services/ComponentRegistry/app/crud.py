"""CRUD operations for TMF639 Resource Inventory v5.0.0."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime
from app import models, schemas
from app.database import RESOURCE_HREF_PREFIX


def create_resource(db: Session, resource: dict, base_url: str) -> models.Resource:
    """Create a new resource as a JSON object, extract and persist relationships separately."""
    resource_id = resource.get("id") or str(uuid.uuid4())
    
    # Extract resourceVersion from the JSON
    resource_version = resource.get("resourceVersion")
    
    # Remove id and href from resource data - they will be generated dynamically
    resource_data = {k: v for k, v in resource.items() if k not in ["id", "href"]}
    
    # Remove resourceRelationship from the resource JSON before persisting
    relationships = resource_data.pop("resourceRelationship", [])
    
    db_resource = models.Resource(
        id=resource_id,
        data=resource_data,
        resource_version=resource_version,
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    # Handle resourceRelationship separately
    for rel in relationships:
        rel_type = rel.get("relationshipType")
        related_resource = rel.get("resource", {})
        related_resource_id = related_resource.get("id")
        # Optionally create the related resource if it does not exist
        if related_resource_id and not db.query(models.Resource).filter(models.Resource.id == related_resource_id).first():
            # Remove id and href from related resource data as well
            related_resource_data = {k: v for k, v in related_resource.items() if k not in ["id", "href"]}
            db_related = models.Resource(
                id=related_resource_id,
                data=related_resource_data,
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


def get_resource(db: Session, id: str, base_url: str = "") -> Optional[models.Resource]:
    """Retrieve a resource by ID and dynamically add resourceRelationship from the relationship table."""
    db_resource = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not db_resource:
        return None
    # Dynamically add resourceRelationship
    relationships = db.query(models.ResourceRelationship).filter(models.ResourceRelationship.resource_id == id).all()
    resource_data = dict(db_resource.data)  # Make a copy
    
    # Dynamically add id and href from the database id column
    resource_data["id"] = db_resource.id
    resource_data["href"] = f"{base_url}{RESOURCE_HREF_PREFIX}{db_resource.id}"
    
    resource_relationships = []
    for rel in relationships:
        # Fetch related resource for href and type if available
        related = db.query(models.Resource).filter(models.Resource.id == rel.related_resource_id).first()
        related_resource = {
            "id": rel.related_resource_id,
            "href": f"{base_url}{RESOURCE_HREF_PREFIX}{rel.related_resource_id}"
        }
        if related and "@type" in related.data:
            related_resource["@type"] = related.data["@type"]
        resource_relationships.append({
            "@type": "ResourceRelationship",
            "relationshipType": rel.relation_type,
            "resource": related_resource
        })
    if resource_relationships:
        resource_data["resourceRelationship"] = resource_relationships
    # Return a Resource object with the dynamic relationships
    return models.Resource(
        id=db_resource.id,
        data=resource_data,
        created_at=db_resource.created_at,
        updated_at=db_resource.updated_at
    )


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
    
    # Extract resourceVersion from the JSON update
    resource_version = resource_update.get("resourceVersion")
    
    # Remove id and href from resource_update before storing - they are generated dynamically
    resource_data = {k: v for k, v in resource_update.items() if k not in ["id", "href"]}
    
    db_resource.data = resource_data
    db_resource.resource_version = resource_version
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
    hub_id = hub_data.id or str(uuid.uuid4())
    db_hub = models.Hub(
        id=hub_id,
        callback=hub_data.callback,
        query=hub_data.query,
    )
    db.add(db_hub)
    db.commit()
    db.refresh(db_hub)
    return schemas.Hub(id=db_hub.id, callback=db_hub.callback, query=db_hub.query)


def get_hub(db: Session, id: str) -> Optional[schemas.Hub]:
    """Retrieve a hub by ID."""
    db_hub = db.query(models.Hub).filter(models.Hub.id == id).first()
    if not db_hub:
        return None
    return schemas.Hub(id=db_hub.id, callback=db_hub.callback, query=db_hub.query)


def delete_hub(db: Session, id: str) -> bool:
    """Delete a hub by ID."""
    db_hub = db.query(models.Hub).filter(models.Hub.id == id).first()
    if not db_hub:
        return False
    db.delete(db_hub)
    db.commit()
    return True


def get_all_hubs(db: Session) -> List[schemas.Hub]:
    """Return all hubs."""
    hubs = db.query(models.Hub).all()
    return [schemas.Hub(id=hub.id, callback=hub.callback, query=hub.query) for hub in hubs]