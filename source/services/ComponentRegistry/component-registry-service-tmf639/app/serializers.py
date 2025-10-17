"""Helper functions for converting database models to Pydantic schemas."""

from typing import Optional
from app import models, schemas


def resource_to_schema(db_resource: models.Resource) -> schemas.Resource:
    """Convert a Resource database model to Pydantic schema with all relationships."""
    
    # Convert characteristics
    characteristics = []
    if db_resource.characteristics:
        for char in db_resource.characteristics:
            characteristics.append(schemas.Characteristic(
                name=char.name,
                value=char.value,
                valueType=char.valueType
            ))
    
    # Convert related parties
    related_parties = []
    if db_resource.related_parties:
        for party in db_resource.related_parties:
            related_parties.append(schemas.RelatedPartyRefOrPartyRoleRef(
                id=party.id,
                href=party.href,
                name=party.name,
                role=party.role,
                referredType=party.referredType
            ))
    
    # Convert notes
    notes = []
    if db_resource.notes:
        for note in db_resource.notes:
            notes.append(schemas.Note(
                id=note.id,
                href=note.href,
                author=note.author,
                date=note.date,
                text=note.text
            ))
    
    # Convert attachments
    attachments = []
    if db_resource.attachments:
        for attachment in db_resource.attachments:
            attachments.append(schemas.AttachmentRef(
                id=attachment.id,
                href=attachment.href,
                attachmentType=attachment.attachmentType,
                content=attachment.content,
                description=attachment.description,
                mimeType=attachment.mimeType,
                name=attachment.name,
                url=attachment.url
            ))
    
    # Convert resource relationships
    relationships = []
    if db_resource.resource_relationships:
        for rel in db_resource.resource_relationships:
            relationships.append(schemas.ResourceRelationship(
                id=rel.id,
                href=rel.href,
                relationshipType=rel.relationshipType,
                resource=schemas.ResourceRefOrValue(
                    id=rel.related_resource_id,
                    href=rel.related_resource_href
                )
            ))
    
    # Convert places (v5.0.0 - array)
    places = []
    if db_resource.places:
        for place in db_resource.places:
            places.append(schemas.RelatedPlaceRef(
                id=place.id,
                href=place.href,
                name=place.name,
                role=place.role,
                referredType=place.referredType
            ))
    
    # Convert resource order items (v5.0.0)
    resource_order_items = []
    if db_resource.resource_order_items:
        for item in db_resource.resource_order_items:
            resource_order_items.append(schemas.RelatedResourceOrderItem(
                id=item.id,
                href=item.href,
                resourceOrderId=item.resourceOrderId,
                role=item.role
            ))
    
    # Convert supporting resources (v5.0.0)
    supporting_resources = []
    if db_resource.supporting_resources:
        for supp in db_resource.supporting_resources:
            supporting_resources.append(schemas.ResourceRefOrValue(
                id=supp.supporting_resource_id,
                href=supp.href,
                name=supp.name,
                referredType=supp.referredType
            ))
    
    # Convert activation features (v5.0.0)
    activation_features = []
    if db_resource.activation_features:
        for feature in db_resource.activation_features:
            activation_features.append(schemas.Feature(
                id=feature.id,
                name=feature.name,
                isEnabled=feature.isEnabled,
                isBundle=feature.isBundle
            ))
    
    # Convert external identifiers (v5.0.0)
    external_identifiers = []
    if db_resource.external_identifiers:
        for ext_id in db_resource.external_identifiers:
            external_identifiers.append(schemas.ExternalIdentifier(
                id=ext_id.id,
                owner=ext_id.owner,
                externalIdentifierType=ext_id.externalIdentifierType
            ))
    
    # Build validFor if present
    valid_for = None
    if db_resource.validFor_startDateTime or db_resource.validFor_endDateTime:
        valid_for = schemas.TimePeriod(
            startDateTime=db_resource.validFor_startDateTime,
            endDateTime=db_resource.validFor_endDateTime
        )
    
    # Build intent if present
    intent = None
    if db_resource.intent_id:
        intent = schemas.IntentRef(
            id=db_resource.intent_id,
            href=db_resource.intent_href,
            name=db_resource.intent_name
        )
    
    # Create and return the complete Resource schema
    return schemas.Resource(
        id=db_resource.id,
        href=db_resource.href,
        category=db_resource.category,
        description=db_resource.description,
        endOperatingDate=db_resource.endOperatingDate,
        name=db_resource.name,
        resourceVersion=db_resource.resourceVersion,
        startOperatingDate=db_resource.startOperatingDate,
        administrativeState=db_resource.administrativeState,
        operationalState=db_resource.operationalState,
        resourceStatus=db_resource.resourceStatus,
        usageState=db_resource.usageState,
        baseType=db_resource.baseType,
        schemaLocation=db_resource.schemaLocation,
        type=db_resource.type,
        validFor=valid_for,
        resourceCharacteristic=characteristics if characteristics else None,
        relatedParty=related_parties if related_parties else None,
        note=notes if notes else None,
        attachment=attachments if attachments else None,
        resourceRelationship=relationships if relationships else None,
        place=places if places else None,
        resourceOrderItem=resource_order_items if resource_order_items else None,
        supportingResource=supporting_resources if supporting_resources else None,
        activationFeature=activation_features if activation_features else None,
        intent=intent,
        externalIdentifier=external_identifiers if external_identifiers else None
    )
