"""
Component Registry Service - FastAPI REST API

This service provides CRUD operations for managing Component Registries, Components,
and their Exposed APIs following the TM Forum ODA Canvas specification.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

import models, crud, database

# Create database tables
database.create_tables()

app = FastAPI(
    title="Component Registry Service",
    description="REST API for managing ODA Component Registries, Components, and Exposed APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "component-registry-service"}


# ComponentRegistry endpoints
@app.post("/registries", response_model=models.ComponentRegistry, tags=["Component Registries"])
async def create_component_registry(
    registry: models.ComponentRegistryCreate,
    db: Session = Depends(get_db)
):
    """Create a new Component Registry."""
    try:
        # Check if registry already exists
        existing = crud.ComponentRegistryCRUD.get(db, registry.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"ComponentRegistry '{registry.name}' already exists")
        
        return crud.ComponentRegistryCRUD.create(db, registry)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/registries", response_model=List[models.ComponentRegistry], tags=["Component Registries"])
async def get_component_registries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all Component Registries."""
    return crud.ComponentRegistryCRUD.get_all(db, skip=skip, limit=limit)


@app.get("/registries/{name}", response_model=models.ComponentRegistry, tags=["Component Registries"])
async def get_component_registry(name: str, db: Session = Depends(get_db)):
    """Get a Component Registry by name."""
    registry = crud.ComponentRegistryCRUD.get(db, name)
    if not registry:
        raise HTTPException(status_code=404, detail=f"ComponentRegistry '{name}' not found")
    return registry


@app.put("/registries/{name}", response_model=models.ComponentRegistry, tags=["Component Registries"])
async def update_component_registry(
    name: str,
    registry_update: models.ComponentRegistryUpdate,
    db: Session = Depends(get_db)
):
    """Update a Component Registry."""
    registry = crud.ComponentRegistryCRUD.update(db, name, registry_update)
    if not registry:
        raise HTTPException(status_code=404, detail=f"ComponentRegistry '{name}' not found")
    return registry


@app.delete("/registries/{name}", tags=["Component Registries"])
async def delete_component_registry(name: str, db: Session = Depends(get_db)):
    """Delete a Component Registry."""
    success = crud.ComponentRegistryCRUD.delete(db, name)
    if not success:
        raise HTTPException(status_code=404, detail=f"ComponentRegistry '{name}' not found")
    return {"message": f"ComponentRegistry '{name}' deleted successfully"}


# Component endpoints
@app.post("/components", response_model=models.Component, tags=["Components"])
async def create_component(
    component: models.ComponentCreate,
    db: Session = Depends(get_db)
):
    """Create a new Component."""
    try:
        # Check if component already exists
        existing = crud.ComponentCRUD.get(db, component.component_registry_ref, component.component_name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Component '{component.component_name}' already exists in registry '{component.component_registry_ref}'"
            )
        
        return crud.ComponentCRUD.create(db, component)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/components", response_model=List[models.Component], tags=["Components"])
async def get_components(
    registry_ref: Optional[str] = Query(None, description="Filter by component registry reference"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all Components, optionally filtered by registry reference."""
    if registry_ref:
        return crud.ComponentCRUD.get_by_registry(db, registry_ref)
    return crud.ComponentCRUD.get_all(db, skip=skip, limit=limit)


@app.get("/components/{registry_ref}/{component_name}", response_model=models.Component, tags=["Components"])
async def get_component(
    registry_ref: str,
    component_name: str,
    db: Session = Depends(get_db)
):
    """Get a Component by registry reference and component name."""
    component = crud.ComponentCRUD.get(db, registry_ref, component_name)
    if not component:
        raise HTTPException(
            status_code=404,
            detail=f"Component '{component_name}' not found in registry '{registry_ref}'"
        )
    return component


@app.put("/components/{registry_ref}/{component_name}", response_model=models.Component, tags=["Components"])
async def update_component(
    registry_ref: str,
    component_name: str,
    component_update: models.ComponentUpdate,
    db: Session = Depends(get_db)
):
    """Update a Component."""
    component = crud.ComponentCRUD.update(db, registry_ref, component_name, component_update)
    if not component:
        raise HTTPException(
            status_code=404,
            detail=f"Component '{component_name}' not found in registry '{registry_ref}'"
        )
    return component


@app.delete("/components/{registry_ref}/{component_name}", tags=["Components"])
async def delete_component(
    registry_ref: str,
    component_name: str,
    db: Session = Depends(get_db)
):
    """Delete a Component."""
    success = crud.ComponentCRUD.delete(db, registry_ref, component_name)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Component '{component_name}' not found in registry '{registry_ref}'"
        )
    return {"message": f"Component '{component_name}' deleted successfully from registry '{registry_ref}'"}


# Additional utility endpoints
@app.get("/registries/{name}/components", response_model=List[models.Component], tags=["Component Registries"])
async def get_registry_components(name: str, db: Session = Depends(get_db)):
    """Get all Components for a specific registry."""
    # First check if registry exists
    registry = crud.ComponentRegistryCRUD.get(db, name)
    if not registry:
        raise HTTPException(status_code=404, detail=f"ComponentRegistry '{name}' not found")
    
    return crud.ComponentCRUD.get_by_registry(db, name)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Component Registry Service",
        "description": "REST API for managing ODA Component Registries, Components, and Exposed APIs",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)