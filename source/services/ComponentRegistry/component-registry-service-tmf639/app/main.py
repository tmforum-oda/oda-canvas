"""Main FastAPI application for TMF639 Resource Inventory Management."""

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app import models, schemas, crud
from app.database import engine, get_db, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="API Resource Inventory Management",
    description="TMF639 - Resource Inventory Management API v4.0.0",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Base path for API
BASE_PATH = "/tmf-api/resourceInventoryManagement/v4"


def get_base_url(request: Request) -> str:
    """Get base URL for href generation."""
    return f"{request.url.scheme}://{request.url.netloc}"


@app.get(
    f"{BASE_PATH}/resource",
    response_model=List[schemas.Resource],
    tags=["resource"],
    summary="List or find Resource objects",
    description="This operation list or find Resource entities"
)
async def list_resources(
    fields: Optional[str] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 100,
    response: Response = None,
    db: Session = Depends(get_db)
):
    """List resources with pagination."""
    resources, total_count = crud.get_resources(db, offset=offset, limit=limit)
    
    # Add pagination headers
    response.headers["X-Result-Count"] = str(len(resources))
    response.headers["X-Total-Count"] = str(total_count)
    
    return resources


@app.post(
    f"{BASE_PATH}/resource",
    response_model=schemas.Resource,
    status_code=status.HTTP_201_CREATED,
    tags=["resource"],
    summary="Creates a Resource",
    description="This operation creates a Resource entity."
)
async def create_resource(
    resource: schemas.ResourceCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new resource."""
    base_url = get_base_url(request)
    db_resource = crud.create_resource(db, resource, base_url)
    return db_resource


@app.get(
    f"{BASE_PATH}/resource/{{id}}",
    response_model=schemas.Resource,
    tags=["resource"],
    summary="Retrieves a Resource by ID",
    description="This operation retrieves a Resource entity. Attribute selection is enabled for all first level attributes."
)
async def retrieve_resource(
    id: str,
    fields: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve a resource by ID."""
    db_resource = crud.get_resource(db, id)
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    return db_resource


@app.patch(
    f"{BASE_PATH}/resource/{{id}}",
    response_model=schemas.Resource,
    tags=["resource"],
    summary="Updates partially a Resource",
    description="This operation updates partially a Resource entity."
)
async def patch_resource(
    id: str,
    resource: schemas.ResourceUpdate,
    db: Session = Depends(get_db)
):
    """Partially update a resource."""
    db_resource = crud.update_resource(db, id, resource)
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    return db_resource


@app.delete(
    f"{BASE_PATH}/resource/{{id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["resource"],
    summary="Deletes a Resource",
    description="This operation deletes a Resource entity."
)
async def delete_resource(
    id: str,
    db: Session = Depends(get_db)
):
    """Delete a resource."""
    success = crud.delete_resource(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    f"{BASE_PATH}/hub",
    response_model=schemas.EventSubscription,
    status_code=status.HTTP_201_CREATED,
    tags=["events subscription"],
    summary="Register a listener",
    description="Sets the communication endpoint address the service instance must use to deliver information about its health state, execution state, failures and metrics."
)
async def register_listener(
    data: schemas.EventSubscriptionInput,
    db: Session = Depends(get_db)
):
    """Register an event listener."""
    db_subscription = crud.create_event_subscription(db, data)
    return db_subscription


@app.delete(
    f"{BASE_PATH}/hub/{{id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["events subscription"],
    summary="Unregister a listener",
    description="Resets the communication endpoint address the service instance must use to deliver information about its health state, execution state, failures and metrics."
)
async def unregister_listener(
    id: str,
    db: Session = Depends(get_db)
):
    """Unregister an event listener."""
    success = crud.delete_event_subscription(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with id {id} not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )
