"""
FastAPI microservice for ODA Canvas entities.
Provides comprehensive REST API endpoints for Registry, Component, ExposedAPI, and Label management.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

import models
import schemas
import crud
from database import get_db, init_db

# Initialize FastAPI app
app = FastAPI(
    title="ODA Canvas Microservice",
    description="A comprehensive microservice for managing ODA Canvas entities: Registries, Components, Exposed APIs, and Labels",
    version="1.0.0"
)

# Set up Jinja2 templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ODA Canvas Microservice"}

# LABEL ENDPOINTS
@app.post("/labels/", response_model=schemas.Label, status_code=status.HTTP_201_CREATED, tags=["Labels"])
def create_label(label: schemas.LabelCreate, db: Session = Depends(get_db)):
    """Create a new label"""
    # Check if label with same key-value pair already exists
    existing_label = crud.label_crud.get_by_key_value(db, label.key, label.value)
    if existing_label:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Label with key '{label.key}' and value '{label.value}' already exists"
        )
    
    return crud.label_crud.create(db=db, label=label)

@app.get("/labels/{label_id}", response_model=schemas.Label, tags=["Labels"])
def get_label(label_id: int, db: Session = Depends(get_db)):
    """Get label by ID"""
    db_label = crud.label_crud.get(db, label_id=label_id)
    if db_label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    return db_label

@app.get("/labels/", response_model=List[schemas.Label], tags=["Labels"])
def get_labels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all labels with pagination"""
    labels = crud.label_crud.get_all(db, skip=skip, limit=limit)
    return labels

@app.put("/labels/{label_id}", response_model=schemas.Label, tags=["Labels"])
def update_label(label_id: int, label_update: schemas.LabelUpdate, db: Session = Depends(get_db)):
    """Update label"""
    updated_label = crud.label_crud.update(db=db, label_id=label_id, label_update=label_update)
    if not updated_label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    return updated_label

@app.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Labels"])
def delete_label(label_id: int, db: Session = Depends(get_db)):
    """Delete label"""
    success = crud.label_crud.delete(db=db, label_id=label_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )

# REGISTRY ENDPOINTS
@app.post("/registries/", response_model=schemas.Registry, status_code=status.HTTP_201_CREATED, tags=["Registries"])
def create_registry(registry: schemas.RegistryCreate, db: Session = Depends(get_db)):
    """Create a new registry"""
    # Check if registry name already exists
    existing_registry = crud.registry_crud.get_by_name(db, registry.name)
    if existing_registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registry name already exists"
        )
    
    # Validate that all label IDs exist
    for label_id in registry.label_ids:
        if not crud.label_crud.get(db, label_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with ID {label_id} not found"
            )
    
    return crud.registry_crud.create(db=db, registry=registry)

@app.get("/registries/{registry_id}", response_model=schemas.Registry, tags=["Registries"])
def get_registry(registry_id: int, db: Session = Depends(get_db)):
    """Get registry by ID"""
    db_registry = crud.registry_crud.get(db, registry_id=registry_id)
    if db_registry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registry not found"
        )
    
    # Convert labels from association objects to Label objects
    db_registry.labels = [rl.label for rl in db_registry.registry_labels]
    return db_registry

@app.get("/registries/", response_model=List[schemas.Registry], tags=["Registries"])
def get_registries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all registries with pagination"""
    registries = crud.registry_crud.get_all(db, skip=skip, limit=limit)
    
    # Convert labels for each registry
    for registry in registries:
        registry.labels = [rl.label for rl in registry.registry_labels]
    
    return registries

@app.put("/registries/{registry_id}", response_model=schemas.Registry, tags=["Registries"])
def update_registry(registry_id: int, registry_update: schemas.RegistryUpdate, db: Session = Depends(get_db)):
    """Update registry"""
    # Validate that all label IDs exist if provided
    if registry_update.label_ids is not None:
        for label_id in registry_update.label_ids:
            if not crud.label_crud.get(db, label_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with ID {label_id} not found"
                )
    
    updated_registry = crud.registry_crud.update(db=db, registry_id=registry_id, registry_update=registry_update)
    if not updated_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registry not found"
        )
    
    # Reload with labels
    updated_registry = crud.registry_crud.get(db, registry_id)
    updated_registry.labels = [rl.label for rl in updated_registry.registry_labels]
    return updated_registry

@app.delete("/registries/{registry_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Registries"])
def delete_registry(registry_id: int, db: Session = Depends(get_db)):
    """Delete registry"""
    success = crud.registry_crud.delete(db=db, registry_id=registry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registry not found"
        )

# COMPONENT ENDPOINTS
@app.post("/components/", response_model=schemas.Component, status_code=status.HTTP_201_CREATED, tags=["Components"])
def create_component(component: schemas.ComponentCreate, db: Session = Depends(get_db)):
    """Create a new component"""
    # Check if registry exists
    registry = crud.registry_crud.get_by_name(db, component.registry_name)
    if not registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registry not found"
        )
    
    # Check if component already exists in this registry
    existing_component = crud.component_crud.get_by_registry_and_name(db, component.registry_name, component.name)
    if existing_component:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Component '{component.name}' already exists in registry '{component.registry_name}'"
        )
    
    # Validate that all label IDs exist
    for label_id in component.label_ids:
        if not crud.label_crud.get(db, label_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with ID {label_id} not found"
            )
    
    return crud.component_crud.create(db=db, component=component)

@app.get("/components/{component_id}", response_model=schemas.Component, tags=["Components"])
def get_component(component_id: int, db: Session = Depends(get_db)):
    """Get component by ID"""
    db_component = crud.component_crud.get(db, component_id=component_id)
    if db_component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Convert labels from association objects to Label objects
    db_component.labels = [cl.label for cl in db_component.component_labels]
    return db_component

@app.get("/components/", response_model=List[schemas.Component], tags=["Components"])
def get_components(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    registry_name: str = Query(None, description="Filter components by registry name"),
    db: Session = Depends(get_db)
):
    """Get all components with pagination and optional registry filter"""
    if registry_name:
        components = crud.component_crud.get_by_registry(db, registry_name=registry_name, skip=skip, limit=limit)
    else:
        components = crud.component_crud.get_all(db, skip=skip, limit=limit)
    
    # Convert labels for each component
    for component in components:
        component.labels = [cl.label for cl in component.component_labels]
    
    return components

@app.put("/components/{component_id}", response_model=schemas.Component, tags=["Components"])
def update_component(component_id: int, component_update: schemas.ComponentUpdate, db: Session = Depends(get_db)):
    """Update component"""
    # Validate that all label IDs exist if provided
    if component_update.label_ids is not None:
        for label_id in component_update.label_ids:
            if not crud.label_crud.get(db, label_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with ID {label_id} not found"
                )
    
    updated_component = crud.component_crud.update(db=db, component_id=component_id, component_update=component_update)
    if not updated_component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Reload with labels
    updated_component = crud.component_crud.get(db, component_id)
    updated_component.labels = [cl.label for cl in updated_component.component_labels]
    return updated_component

@app.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Components"])
def delete_component(component_id: int, db: Session = Depends(get_db)):
    """Delete component"""
    success = crud.component_crud.delete(db=db, component_id=component_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )

# EXPOSED API ENDPOINTS
@app.post("/exposed-apis/", response_model=schemas.ExposedAPI, status_code=status.HTTP_201_CREATED, tags=["Exposed APIs"])
def create_exposed_api(exposed_api: schemas.ExposedAPICreate, db: Session = Depends(get_db)):
    """Create a new exposed API"""
    # Check if registry exists
    registry = crud.registry_crud.get_by_name(db, exposed_api.registry_name)
    if not registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registry not found"
        )
    
    # Check if component exists
    component = crud.component_crud.get_by_registry_and_name(db, exposed_api.registry_name, exposed_api.component_name)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    # Validate that all label IDs exist
    for label_id in exposed_api.label_ids:
        if not crud.label_crud.get(db, label_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label with ID {label_id} not found"
            )
    
    return crud.exposed_api_crud.create(db=db, exposed_api=exposed_api)

@app.get("/exposed-apis/{api_id}", response_model=schemas.ExposedAPI, tags=["Exposed APIs"])
def get_exposed_api(api_id: int, db: Session = Depends(get_db)):
    """Get exposed API by ID"""
    db_api = crud.exposed_api_crud.get(db, api_id=api_id)
    if db_api is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exposed API not found"
        )
    
    # Convert labels from association objects to Label objects
    db_api.labels = [al.label for al in db_api.exposed_api_labels]
    return db_api

@app.get("/exposed-apis/", response_model=List[schemas.ExposedAPI], tags=["Exposed APIs"])
def get_exposed_apis(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    registry_name: str = Query(None, description="Filter by registry name"),
    component_name: str = Query(None, description="Filter by component name (requires registry_name)"),
    status: str = Query(None, description="Filter by status (pending/ready)"),
    db: Session = Depends(get_db)
):
    """Get all exposed APIs with pagination and optional filters"""
    if registry_name and component_name:
        apis = crud.exposed_api_crud.get_by_component(db, registry_name=registry_name, component_name=component_name, skip=skip, limit=limit)
    elif status:
        apis = crud.exposed_api_crud.get_by_status(db, status=status, skip=skip, limit=limit)
    else:
        apis = crud.exposed_api_crud.get_all(db, skip=skip, limit=limit)
    
    # Convert labels for each API
    for api in apis:
        api.labels = [al.label for al in api.exposed_api_labels]
    
    return apis

@app.patch("/exposed-apis/{api_id}/status", response_model=schemas.ExposedAPI, tags=["Exposed APIs"])
def update_exposed_api_status(api_id: int, status_update: schemas.ExposedAPIUpdate, db: Session = Depends(get_db)):
    """Update exposed API status"""
    if status_update.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    updated_api = crud.exposed_api_crud.update_status(db=db, api_id=api_id, status=status_update.status.value)
    if not updated_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exposed API not found"
        )
    
    # Reload with labels
    updated_api = crud.exposed_api_crud.get(db, api_id)
    updated_api.labels = [al.label for al in updated_api.exposed_api_labels]
    return updated_api

@app.put("/exposed-apis/{api_id}", response_model=schemas.ExposedAPI, tags=["Exposed APIs"])
def update_exposed_api(api_id: int, api_update: schemas.ExposedAPIUpdate, db: Session = Depends(get_db)):
    """Update exposed API"""
    # Validate that all label IDs exist if provided
    if api_update.label_ids is not None:
        for label_id in api_update.label_ids:
            if not crud.label_crud.get(db, label_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Label with ID {label_id} not found"
                )
    
    updated_api = crud.exposed_api_crud.update(db=db, api_id=api_id, api_update=api_update)
    if not updated_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exposed API not found"
        )
    
    # Reload with labels
    updated_api = crud.exposed_api_crud.get(db, api_id)
    updated_api.labels = [al.label for al in updated_api.exposed_api_labels]
    return updated_api

@app.delete("/exposed-apis/{api_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Exposed APIs"])
def delete_exposed_api(api_id: int, db: Session = Depends(get_db)):
    """Delete exposed API"""
    success = crud.exposed_api_crud.delete(db=db, api_id=api_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exposed API not found"
        )

# COMPONENTS GUI ENDPOINT
@app.get("/components-gui", response_class=HTMLResponse, tags=["Components"])
def components_gui(request: Request, db: Session = Depends(get_db)):
    """GUI page to display all registered components"""
    components = crud.component_crud.get_all(db)
    # Attach labels for each component (as in API response)
    for component in components:
        component.labels = [cl.label for cl in getattr(component, 'component_labels', [])]
    return templates.TemplateResponse("components.html", {"request": request, "components": components})

# STATISTICS ENDPOINT
@app.get("/stats", tags=["Statistics"])
def get_statistics(db: Session = Depends(get_db)):
    """Get ODA Canvas statistics"""
    return {
        "oda_canvas": {
            "total_labels": crud.label_crud.count(db),
            "total_registries": crud.registry_crud.count(db),
            "total_components": crud.component_crud.count(db),
            "total_exposed_apis": crud.exposed_api_crud.count(db)
        },
        "service_info": {
            "name": "ODA Canvas Microservice",
            "version": "1.0.0",
            "description": "Microservice for managing ODA Canvas entities"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)