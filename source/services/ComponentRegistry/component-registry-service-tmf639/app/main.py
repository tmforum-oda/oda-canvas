"""Main FastAPI application for TMF639 Resource Inventory Management v5.0.0."""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
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


async def notify_hubs(event_type: str, resource: schemas.Resource, db: Session):
    """Send event notification to all registered hubs."""
    hubs = crud.get_all_hubs(db)
    event_payload = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "resource": resource.json(),  # Use JSON string to avoid datetime serialization issues
    }
    async with httpx.AsyncClient() as client:
        for hub in hubs:
            try:
                event_payload_q = {**event_payload, "query": hub.query} if hub.query else event_payload
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
    # Notify hubs
    result = schemas.Resource(id=db_resource.id, data=db_resource.data, created_at=db_resource.created_at, updated_at=db_resource.updated_at)
    await notify_hubs("ResourceCreated", result, db)
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
    # Notify hubs
    result = schemas.Resource(id=db_resource.id, data=db_resource.data, created_at=db_resource.created_at, updated_at=db_resource.updated_at)
    await notify_hubs("ResourceChanged", result, db)
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
    # Notify hubs (send minimal event)
    event_payload = schemas.Resource(id=id, data={}, created_at=None, updated_at=None)
    await notify_hubs("ResourceDeleted", event_payload, db)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )