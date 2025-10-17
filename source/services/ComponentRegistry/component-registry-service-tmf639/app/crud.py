"""CRUD operations for TMF639 Resource Inventory v5.0.0."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime

from app import models, schemas


def _create_embedded_resource(db: Session, embedded_resource: dict, base_url: str) -> models.Resource:
    """Create an embedded resource from resourceRelationship."""
    # Extract ID or generate new one
    resource_id = embedded_resource.get("id") or str(uuid.uuid4())
    
    # Create the embedded resource
    db_embedded = models.Resource(
        id=resource_id,
        href=embedded_resource.get("href") or f"{base_url}/resourceInventory/v5/resource/{resource_id}",
        category=embedded_resource.get("category"),
        description=embedded_resource.get("description"),
        name=embedded_resource.get("name"),
        resourceVersion=embedded_resource.get("resourceVersion"),
        startOperatingDate=embedded_resource.get("startOperatingDate"),
        endOperatingDate=embedded_resource.get("endOperatingDate"),
        administrativeState=embedded_resource.get("administrativeState"),
        operationalState=embedded_resource.get("operationalState"),
        resourceStatus=embedded_resource.get("resourceStatus"),
        usageState=embedded_resource.get("usageState"),
        baseType=embedded_resource.get("@baseType"),
        schemaLocation=embedded_resource.get("@schemaLocation"),
        type=embedded_resource.get("@type")
    )
    
    # Add characteristics if present
    if "resourceCharacteristic" in embedded_resource:
        for char in embedded_resource["resourceCharacteristic"]:
            db_char = models.ResourceCharacteristic(
                name=char["name"],
                value=str(char["value"]),
                valueType=char.get("valueType"),
                resource=db_embedded
            )
            db_embedded.characteristics.append(db_char)
    
    # Add resource specification if present
    # Note: Currently stored in relationship, could be extended if needed
    
    # Add to database
    db.add(db_embedded)
    db.flush()  # Flush to get the ID without committing
    
    return db_embedded


def create_resource(db: Session, resource: schemas.ResourceCreate, base_url: str) -> models.Resource:
    """Create a new resource."""
    # Use provided ID or generate a new one
    resource_id = resource.id if resource.id else str(uuid.uuid4())
    
    # Create resource model
    db_resource = models.Resource(
        id=resource_id,
        href=f"{base_url}/resourceInventory/v5/resource/{resource_id}",
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
        validFor_startDateTime=resource.validFor.startDateTime if resource.validFor else None,
        validFor_endDateTime=resource.validFor.endDateTime if resource.validFor else None,
        intent_id=resource.intent.id if resource.intent else None,
        intent_href=resource.intent.href if resource.intent else None,
        intent_name=resource.intent.name if resource.intent else None,
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
            party_id = party.id or str(uuid.uuid4())
            db_party = models.ResourceRelatedParty(
                id=party_id,
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
    
    # Add resource relationships - WITH embedded resource creation
    if resource.resourceRelationship:
        for rel in resource.resourceRelationship:
            rel_id = rel.id or str(uuid.uuid4())
            
            # Check if resource is embedded (has more than just id and href)
            resource_dict = rel.resource.model_dump(exclude_unset=True)
            is_embedded = len(resource_dict) > 2 or "name" in resource_dict or "category" in resource_dict
            
            if is_embedded:
                # Create the embedded resource as a separate resource
                embedded_resource = _create_embedded_resource(db, resource_dict, base_url)
                related_resource_id = embedded_resource.id
                related_resource_href = embedded_resource.href
            else:
                # Just a reference
                related_resource_id = rel.resource.id
                related_resource_href = rel.resource.href
            
            db_rel = models.ResourceRelationshipModel(
                id=rel_id,
                relationshipType=rel.relationshipType,
                related_resource_id=related_resource_id,
                related_resource_href=related_resource_href,
                resource=db_resource
            )
            db_resource.resource_relationships.append(db_rel)
    
    # Add places (v5.0.0 - now array)
    if resource.place:
        for place in resource.place:
            place_id = place.id or str(uuid.uuid4())
            db_place = models.ResourcePlace(
                id=place_id,
                href=place.href,
                name=place.name,
                role=place.role,
                referredType=place.referredType,
                resource=db_resource
            )
            db_resource.places.append(db_place)
    
    # Add resource order items (v5.0.0)
    if resource.resourceOrderItem:
        for item in resource.resourceOrderItem:
            db_item = models.ResourceOrderItem(
                id=item.id,
                href=item.href,
                resourceOrderId=item.resourceOrderId,
                role=item.role,
                resource=db_resource
            )
            db_resource.resource_order_items.append(db_item)
    
    # Add supporting resources (v5.0.0)
    if resource.supportingResource:
        for supp_res in resource.supportingResource:
            supp_id = str(uuid.uuid4())
            db_supp = models.SupportingResource(
                id=supp_id,
                supporting_resource_id=supp_res.id,
                href=supp_res.href,
                name=supp_res.name,
                referredType=supp_res.referredType,
                resource=db_resource
            )
            db_resource.supporting_resources.append(db_supp)
    
    # Add activation features (v5.0.0)
    if resource.activationFeature:
        for feature in resource.activationFeature:
            feature_id = feature.id or str(uuid.uuid4())
            db_feature = models.ActivationFeature(
                id=feature_id,
                name=feature.name,
                isEnabled=feature.isEnabled,
                isBundle=feature.isBundle,
                resource=db_resource
            )
            db_resource.activation_features.append(db_feature)
    
    # Add external identifiers (v5.0.0)
    if resource.externalIdentifier:
        for ext_id in resource.externalIdentifier:
            db_ext = models.ResourceExternalIdentifier(
                id=ext_id.id,
                owner=ext_id.owner,
                externalIdentifierType=ext_id.externalIdentifierType,
                resource=db_resource
            )
            db_resource.external_identifiers.append(db_ext)
    
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
    limit: int = 100,
    filter_param: Optional[str] = None,
    sort: Optional[str] = None
) -> tuple[List[models.Resource], int]:
    """Get list of resources with pagination and filtering."""
    query = db.query(models.Resource)
    
    # Apply filtering if provided
    if filter_param:
        # Simple filter implementation - can be extended
        pass
    
    # Apply sorting if provided
    if sort:
        # Simple sort implementation - can be extended
        pass
    
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
            # Delete existing and add new
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
            db.query(models.ResourceRelatedParty).filter(
                models.ResourceRelatedParty.resource_id == resource_id
            ).delete()
            if value:
                for party in value:
                    party_id = party.get("id") or str(uuid.uuid4())
                    db_party = models.ResourceRelatedParty(
                        id=party_id,
                        href=party.get("href"),
                        name=party.get("name"),
                        role=party["role"],
                        referredType=party.get("@referredType"),
                        resource_id=resource_id
                    )
                    db.add(db_party)
        elif field == "place":
            db.query(models.ResourcePlace).filter(
                models.ResourcePlace.resource_id == resource_id
            ).delete()
            if value:
                for place in value:
                    place_id = place.get("id") or str(uuid.uuid4())
                    db_place = models.ResourcePlace(
                        id=place_id,
                        href=place.get("href"),
                        name=place.get("name"),
                        role=place.get("role"),
                        referredType=place.get("@referredType"),
                        resource_id=resource_id
                    )
                    db.add(db_place)
        elif field == "validFor":
            if value:
                db_resource.validFor_startDateTime = value.get("startDateTime")
                db_resource.validFor_endDateTime = value.get("endDateTime")
        elif field == "intent":
            if value:
                db_resource.intent_id = value.get("id")
                db_resource.intent_href = value.get("href")
                db_resource.intent_name = value.get("name")
        elif field in ["administrativeState", "operationalState", "resourceStatus", "usageState"]:
            if value:
                setattr(db_resource, field, value.value if hasattr(value, 'value') else value)
        elif field not in ["resourceRelationship", "attachment", "resourceSpecification", "note",
                          "resourceOrderItem", "supportingResource", "activationFeature", "externalIdentifier"]:
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


def create_hub(db: Session, hub: schemas.HubInput) -> models.EventSubscription:
    """Create a hub/event subscription."""
    hub_id = str(uuid.uuid4())
    db_hub = models.EventSubscription(
        id=hub_id,
        callback=hub.callback,
        query=hub.query
    )
    db.add(db_hub)
    db.commit()
    db.refresh(db_hub)
    return db_hub


def get_hub(db: Session, hub_id: str) -> Optional[models.EventSubscription]:
    """Get a hub/event subscription by ID."""
    return db.query(models.EventSubscription).filter(
        models.EventSubscription.id == hub_id
    ).first()


def delete_hub(db: Session, hub_id: str) -> bool:
    """Delete a hub/event subscription."""
    db_hub = get_hub(db, hub_id)
    if not db_hub:
        return False
    
    db.delete(db_hub)
    db.commit()
    return True
