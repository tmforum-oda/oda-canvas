"""CRUD operations for TMF639 Resource Inventory."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime

from app import models, schemas


def create_resource(db: Session, resource: schemas.ResourceCreate, base_url: str) -> models.Resource:
    """Create a new resource."""
    # Use provided ID or generate a new one
    resource_id = resource.id if resource.id else str(uuid.uuid4())
    
    # Create resource model
    db_resource = models.Resource(
        id=resource_id,
        href=f"{base_url}/tmf-api/resourceInventoryManagement/v4/resource/{resource_id}",
        category=resource.category,
        description=resource.description,
        endOperatingDate=resource.endOperatingDate,
        name=resource.name,
        resourceVersion=resource.resourceVersion,
        startOperatingDate=resource.startOperatingDate,
        administrativeState=resource.administrativeState.value if resource.administrativeState else None,
        operationalState=resource.operationalState.value if resource.operationalState else None,
        resourceStatus=resource.resourceStatus.value if resource.resourceStatus else None,
        usageState=resource.usageState.value if resource.usageState else None,
    )
    
    # Add characteristics
    if resource.resourceCharacteristic:
        for char in resource.resourceCharacteristic:
            db_char = models.ResourceCharacteristic(
                name=char.name,
                value=str(char.value),
                valueType=char.valueType,
                resource=db_resource
            )
            db_resource.characteristics.append(db_char)
    
    # Add related parties
    if resource.relatedParty:
        for party in resource.relatedParty:
            db_party = models.ResourceRelatedParty(
                id=party.id,
                href=party.href,
                name=party.name,
                role=party.role,
                referredType=party.referredType,
                resource=db_resource
            )
            db_resource.related_parties.append(db_party)
    
    # Add notes
    if resource.note:
        for note in resource.note:
            note_id = note.id or str(uuid.uuid4())
            db_note = models.ResourceNote(
                id=note_id,
                author=note.author,
                date=note.date,
                text=note.text,
                resource=db_resource
            )
            db_resource.notes.append(db_note)
    
    # Add attachments
    if resource.attachment:
        for attachment in resource.attachment:
            attachment_id = attachment.id or str(uuid.uuid4())
            db_attachment = models.ResourceAttachment(
                id=attachment_id,
                attachmentType=attachment.attachmentType,
                content=attachment.content,
                description=attachment.description,
                mimeType=attachment.mimeType,
                name=attachment.name,
                url=attachment.url,
                resource=db_resource
            )
            db_resource.attachments.append(db_attachment)
    
    # Add resource relationships
    if resource.resourceRelationship:
        for rel in resource.resourceRelationship:
            rel_id = rel.id or str(uuid.uuid4())
            db_rel = models.ResourceRelationshipModel(
                id=rel_id,
                relationshipType=rel.relationshipType,
                related_resource_id=rel.resource.id,
                related_resource_href=rel.resource.href,
                resource=db_resource
            )
            db_resource.resource_relationships.append(db_rel)
    
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


def get_resource(db: Session, resource_id: str) -> Optional[models.Resource]:
    """Get a resource by ID."""
    return db.query(models.Resource).filter(models.Resource.id == resource_id).first()


def get_resources(
    db: Session, 
    offset: int = 0, 
    limit: int = 100
) -> tuple[List[models.Resource], int]:
    """Get list of resources with pagination."""
    query = db.query(models.Resource)
    total_count = query.count()
    resources = query.offset(offset).limit(limit).all()
    return resources, total_count


def update_resource(
    db: Session, 
    resource_id: str, 
    resource_update: schemas.ResourceUpdate
) -> Optional[models.Resource]:
    """Update a resource."""
    db_resource = get_resource(db, resource_id)
    if not db_resource:
        return None
    
    # Update basic fields
    update_data = resource_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "resourceCharacteristic":
            # Delete existing characteristics and add new ones
            db.query(models.ResourceCharacteristic).filter(
                models.ResourceCharacteristic.resource_id == resource_id
            ).delete()
            if value:
                for char in value:
                    db_char = models.ResourceCharacteristic(
                        name=char["name"],
                        value=str(char["value"]),
                        valueType=char.get("valueType"),
                        resource_id=resource_id
                    )
                    db.add(db_char)
        elif field == "relatedParty":
            # Delete existing parties and add new ones
            db.query(models.ResourceRelatedParty).filter(
                models.ResourceRelatedParty.resource_id == resource_id
            ).delete()
            if value:
                for party in value:
                    db_party = models.ResourceRelatedParty(
                        id=party["id"],
                        href=party.get("href"),
                        name=party.get("name"),
                        role=party.get("role"),
                        referredType=party.get("@referredType"),
                        resource_id=resource_id
                    )
                    db.add(db_party)
        elif field == "note":
            # Delete existing notes and add new ones
            db.query(models.ResourceNote).filter(
                models.ResourceNote.resource_id == resource_id
            ).delete()
            if value:
                for note in value:
                    note_id = note.get("id") or str(uuid.uuid4())
                    db_note = models.ResourceNote(
                        id=note_id,
                        author=note.get("author"),
                        date=note.get("date"),
                        text=note.get("text"),
                        resource_id=resource_id
                    )
                    db.add(db_note)
        elif field in ["administrativeState", "operationalState", "resourceStatus", "usageState"]:
            # Handle enum fields
            if value:
                setattr(db_resource, field, value.value if hasattr(value, 'value') else value)
        elif field not in ["resourceRelationship", "attachment", "resourceSpecification", "place"]:
            # Update simple fields
            setattr(db_resource, field, value)
    
    db_resource.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_resource)
    return db_resource


def delete_resource(db: Session, resource_id: str) -> bool:
    """Delete a resource."""
    db_resource = get_resource(db, resource_id)
    if not db_resource:
        return False
    
    db.delete(db_resource)
    db.commit()
    return True


def create_event_subscription(
    db: Session, 
    subscription: schemas.EventSubscriptionInput
) -> models.EventSubscription:
    """Create an event subscription."""
    subscription_id = str(uuid.uuid4())
    db_subscription = models.EventSubscription(
        id=subscription_id,
        callback=subscription.callback,
        query=subscription.query
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def get_event_subscription(db: Session, subscription_id: str) -> Optional[models.EventSubscription]:
    """Get an event subscription by ID."""
    return db.query(models.EventSubscription).filter(
        models.EventSubscription.id == subscription_id
    ).first()


def delete_event_subscription(db: Session, subscription_id: str) -> bool:
    """Delete an event subscription."""
    db_subscription = get_event_subscription(db, subscription_id)
    if not db_subscription:
        return False
    
    db.delete(db_subscription)
    db.commit()
    return True