"""Main FastAPI application for TMF639 Resource Inventory Management v5.0.0."""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from app import models, schemas, crud
from app.database import engine, get_db, Base
import httpx
from datetime import datetime

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Resource Inventory Management",
    description="TMF639 - Resource Inventory Management API v5.0.0",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


async def notify_hubs(event_type: str, id: str, resource_data: dict, db: Session):
    """Send event notification to all registered hubs."""
    hubs = crud.get_all_hubs(db)
    event_payload = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "id": id,
        "resource": resource_data,  # Send only the resource data without wrapper
    }
    async with httpx.AsyncClient() as client:
        for hub in hubs:
            try:
                event_payload_q = {"query": hub.query, **event_payload} if hub.query else event_payload
                await client.post(hub.callback, json=event_payload_q, timeout=5)
            except Exception as e:
                # Log error, but do not block main operation
                print(f"Failed to notify hub {hub.callback}: {e}")


@app.get(
    "/resource",
    tags=["resource"],
    summary="List or find Resource objects",
    description="List or find Resource objects"
)
async def list_resources(
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    response: Response = None,
    db: Session = Depends(get_db)
):
    resources, total_count = crud.get_resources(db, offset=offset, limit=limit)
    # For each resource, dynamically add resourceRelationship from the relationship table
    result = []
    for r in resources:
        db_resource = crud.get_resource(db, r.id)
        result.append(db_resource.data)  # Return only the data content
    response.headers["X-Result-Count"] = str(len(result))
    response.headers["X-Total-Count"] = str(total_count)
    return result


@app.post(
    "/resource",
    status_code=status.HTTP_201_CREATED,
    tags=["resource"],
    summary="Creates a Resource",
    description="This operation creates a Resource entity."
)
async def create_resource(
    resource: dict,  # Accept arbitrary JSON directly
    request: Request = None,
    db: Session = Depends(get_db)
):
    base_url = f"{request.url.scheme}://{request.url.netloc}" if request else ""
    db_resource = crud.create_resource(db, resource, base_url)
    # Notify hubs with resource data only
    await notify_hubs("ResourceCreated", db_resource.id, db_resource.data, db)
    return db_resource.data  # Return only the data content


@app.get(
    "/resource/{id}",
    tags=["resource"],
    summary="Retrieves a Resource by ID",
    description="This operation retrieves a Resource entity. Attribute selection enabled for all first level attributes."
)
async def retrieve_resource(
    id: str,
    db: Session = Depends(get_db)
):
    db_resource = crud.get_resource(db, id)
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    return db_resource.data  # Return only the data content


@app.patch(
    "/resource/{id}",
    tags=["resource"],
    summary="Updates partially a Resource",
    description="This operation updates partially a Resource entity."
)
async def patch_resource(
    id: str,
    resource: dict,  # Accept arbitrary JSON directly
    db: Session = Depends(get_db)
):
    db_resource = crud.update_resource(db, id, resource)
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    # Notify hubs with resource data only
    await notify_hubs("ResourceChanged", id, db_resource.data, db)
    return db_resource.data  # Return only the data content


@app.delete(
    "/resource/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["resource"],
    summary="Deletes a Resource",
    description="This operation deletes a Resource entity."
)
async def delete_resource(
    id: str,
    db: Session = Depends(get_db)
):
    success = crud.delete_resource(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    # Notify hubs with minimal event data (just the id)
    await notify_hubs("ResourceDeleted", id, {}, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/hub",
    response_model=schemas.Hub,
    status_code=status.HTTP_201_CREATED,
    tags=["events subscription"],
    summary="Create a subscription (hub) to receive Events",
    description="Sets the communication endpoint to receive Events."
)
async def create_hub(
    data: schemas.HubInput,
    db: Session = Depends(get_db)
):
    """Register an event listener."""
    db_hub = crud.create_hub(db, data)
    return db_hub


@app.get(
    "/hub/{id}",
    response_model=schemas.Hub,
    tags=["events subscription"],
    summary="Retrieve a subscription (hub)",
    description="This operation retrieves the subscription to receive Events."
)
async def get_hub(
    id: str,
    db: Session = Depends(get_db)
):
    """Retrieve an event listener by ID."""
    db_hub = crud.get_hub(db, id)
    if not db_hub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hub with id {id} not found"
        )
    return db_hub


@app.delete(
    "/hub/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["events subscription"],
    summary="Remove a subscription (hub) to receive Events",
    description="This operation removes the subscription to receive Events."
)
async def delete_hub(
    id: str,
    db: Session = Depends(get_db)
):
    """Unregister an event listener."""
    success = crud.delete_hub(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hub with id {id} not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "5.0.0"}


@app.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    tags=["synchronization"],
    summary="Synchronization callback endpoint",
    description="Receives events from other instances to keep resources synchronized."
)
async def sync_callback(
    event: dict,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for synchronization via hub subscriptions.
    Processes ResourceCreated, ResourceChanged, and ResourceDeleted events.
    """
    event_type = event.get("eventType")
    event_time = event.get("eventTime")
    resource_data = event.get("resource", {})
    resource_id = event.get("id") or resource_data.get("id")
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing eventType in event payload"
        )
    
    try:
        if event_type == "ResourceCreated":
            # Check if resource already exists
            existing_resource = crud.get_resource(db, resource_id)
            if existing_resource:
                # Update if it already exists (to handle race conditions)
                crud.update_resource(db, resource_id, resource_data)
            else:
                # Create new resource
                crud.create_resource(db, resource_data, base_url="")
            
            return {
                "status": "synchronized",
                "eventType": event_type,
                "resourceId": resource_id,
                "action": "created"
            }
        
        elif event_type == "ResourceChanged":
            # Update the resource
            existing_resource = crud.get_resource(db, resource_id)
            if existing_resource:
                crud.update_resource(db, resource_id, resource_data)
                return {
                    "status": "synchronized",
                    "eventType": event_type,
                    "resourceId": resource_id,
                    "action": "updated"
                }
            else:
                # Create if it doesn't exist (to handle missing resources)
                crud.create_resource(db, resource_data, base_url="")
                return {
                    "status": "synchronized",
                    "eventType": event_type,
                    "resourceId": resource_id,
                    "action": "created_from_update"
                }
        
        elif event_type == "ResourceDeleted":
            # Delete the resource
            success = crud.delete_resource(db, resource_id)
            return {
                "status": "synchronized",
                "eventType": event_type,
                "resourceId": resource_id,
                "action": "deleted" if success else "already_deleted"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown eventType: {event_type}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing sync event: {str(e)}"
        )


@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Display dashboard with resources, hubs, and relationships."""
    # Get all resources
    resources, _ = crud.get_resources(db)
    resources_with_data = []
    for r in resources:
        db_resource = crud.get_resource(db, r.id)
        resources_with_data.append(db_resource)
    
    # Get all hubs
    hubs = crud.get_all_hubs(db)
    
    # Get all relationships
    relationships = db.query(models.ResourceRelationship).all()
    
    # Build a map of ODA Components to their exposed APIs
    # Find APIs that have "exposedBy" relationship to ODA Components
    oda_component_apis = {}
    for resource in resources_with_data:
        if resource.data.get('category') == 'ODAComponent':
            component_id = resource.id
            oda_component_apis[component_id] = []
            
            # Find all resources that have an "exposedBy" relationship to this component
            for potential_api in resources_with_data:
                api_relationships = potential_api.data.get('resourceRelationship', [])
                for rel in api_relationships:
                    if rel.get('relationshipType') == 'exposedBy':
                        related_resource = rel.get('resource', {})
                        if related_resource.get('id') == component_id:
                            # Extract apiType, url, apiDocs from resourceCharacteristic
                            api_type = '-'
                            url = None
                            api_docs = None
                            # OAS specifications
                            specifications = []
                            for char in potential_api.data.get('resourceCharacteristic', []):
                                if char.get('name') == 'apiType':
                                    api_type = char.get('value', '-')
                                elif char.get('name') == 'url':
                                    url = char.get('value')
                                elif char.get('name') == 'apiDocs':
                                    api_docs = char.get('value')
                                elif char.get('name') == 'specification':
                                    specs = char.get('value', [])
                                    for spec in specs:
                                        spec_url = spec.get('url')
                                        if spec_url:
                                            specifications.append(spec_url)
                            
                            # This API is exposed by this component
                            oda_component_apis[component_id].append({
                                'id': potential_api.id,
                                'name': potential_api.data.get('name', '-'),
                                'type': potential_api.data.get('@type', 'API'),
                                'category': potential_api.data.get('category', '-'),
                                'apiType': api_type,
                                'url': url,
                                'apiDocs': api_docs,
                                'specifications': specifications
                            })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "service_name": os.getenv("SERVICE_NAME", "Resource Inventory Service"),
            "resources": resources_with_data,
            "hubs": hubs,
            "relationships": relationships,
            "oda_component_apis": oda_component_apis
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )