"""
Component Registry Service - FastAPI REST API

This service provides CRUD operations for managing Component Registries, Components,
and their Exposed APIs following the TM Forum ODA Canvas specification.
"""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

from fastapi import FastAPI, HTTPException, Depends, Query, Request

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os
import models, crud, database
import httpx
import asyncio
import logging


# Create database tables
database.create_tables()

app = FastAPI(
    title="Component Registry Service",
    description="REST API for managing ODA Component Registries, Components, and Exposed APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Set up Jinja2 templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


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


# ROOT ENDPOINT
@app.get("/", response_class=HTMLResponse, tags=["Root"])
def root(request: Request):
    """Root page with links to OpenAPI docs and Component GUI"""
    return templates.TemplateResponse("index.html", {"request": request})


# COMPONENTS GUI ENDPOINT
@app.get("/components-gui", response_class=HTMLResponse, tags=["Components"])
def components_gui(request: Request, db: Session = Depends(get_db)):
    """GUI page to display all registered components"""
    components = crud.ComponentCRUD.get_all(db)
    selfCompReg = crud.ComponentRegistryCRUD.get(db, "self")
    selfname = "?"
    if selfCompReg and selfCompReg.labels and "externalName" in selfCompReg.labels:
        selfname = selfCompReg.labels["externalName"]
    # Attach labels for each component (as in API response)
    return templates.TemplateResponse("components.html", {"request": request, "components": components, "selfname": selfname})


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


async def check_registry_exists(upstream_registry, external_name) -> bool:
    """Check if a registry exists in the upstream registry."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{upstream_registry.url.rstrip('/')}/registries/{external_name}",
            )
            return response.status_code == 200
    except Exception:
        return False
            

async def register_upstream(upstream_registry: models.ComponentRegistry, own_registry: models.ComponentRegistry, external_name: str):
    """
    Register this registry with an upstream registry if not already registered.
    
    This function checks if the upstream registry has a label indicating that
    this registry is already registered. If not, it sends a registration request.
    """
    try:
        if not await check_registry_exists(upstream_registry, external_name):
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{upstream_registry.url.rstrip('/')}/registries",
                    json={
                        "name": external_name,
                        "url": own_registry.url,
                        "type": "downstream",
                        "labels": own_registry.labels or {}
                    },
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code in [200, 201]
    except Exception as e:
        logging.error(f"Error during registration with upstream registry '{upstream_registry.name}': {str(e)}")
        return False


@app.post("/sync-upstream", tags=["Synchronization"])
async def sync_upstream(db: Session = Depends(get_db)):
    """
    Synchronize local component data to all upstream ComponentRegistries.
    
    This endpoint:
    1. Finds all upstream ComponentRegistries
    2. Gets all components from the 'self' registry
    3. Sends each component to all upstream registries
    4. Returns a summary of the synchronization results
    """
    try:


        own_registry = crud.ComponentRegistryCRUD.get(db, "self")
        external_name = own_registry.labels.get("externalName", None) if own_registry and own_registry.labels else None
        
        if not external_name:
            raise HTTPException(
                status_code=400,
                detail="The 'self' ComponentRegistry must have an 'externalName' label to identify this registry to upstreams."
            )
    
        # Get all upstream registries
        upstream_registries = crud.ComponentRegistryCRUD.get_by_type(db, "upstream")
        
        if not upstream_registries:
            return {
                "message": "No upstream registries found",
                "upstream_registries": 0,
                "components_synced": 0,
                "sync_results": []
            }
        
        # Get all components from the 'self' registry
        self_components = crud.ComponentCRUD.get_all(db)
        
        if not self_components:
            return {
                "message": "No components found in own registry to sync",
                "upstream_registries": len(upstream_registries),
                "components_synced": 0,
                "sync_results": []
            }
        
        sync_results = []
        total_success = 0
        total_failed = 0
        
        # Sync each component to each upstream registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            for upstream_registry in upstream_registries:
                await register_upstream(upstream_registry, own_registry, external_name)
                registry_results = {
                    "registry_name": upstream_registry.name,
                    "registry_url": upstream_registry.url,
                    "components_sent": 0,
                    "components_success": 0,
                    "components_failed": 0,
                    "errors": []
                }
                
                for component in self_components:
                    registry_results["components_sent"] += 1
                    
                    try:
                        
                        comp_reg_name = component.component_registry_ref
                        if comp_reg_name == 'self':
                            comp_reg_name = external_name
                            
                        # Prepare component data for upstream registry
                        # Convert ExposedAPI objects to dictionaries for JSON serialization
                        component_data = {
                            "component_registry_ref": comp_reg_name,
                            "component_name": component.component_name,
                            "component_version": component.component_version,
                            "description": component.description,
                            "exposed_apis": [
                                {
                                    "name": api.name,
                                    "oas_specification": api.oas_specification,
                                    "url": api.url,
                                    "labels": api.labels
                                }
                                for api in component.exposed_apis
                            ],
                            "labels": component.labels
                        }
                        
                        # Send POST request to upstream registry
                        upstream_url = upstream_registry.url.rstrip('/')
                        response = await client.post(
                            f"{upstream_url}/components",
                            json=component_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if response.status_code in [200, 201]:
                            registry_results["components_success"] += 1
                            total_success += 1
                            logging.info(
                                f"Successfully synced component '{component.component_name}' "
                                f"to upstream registry '{upstream_registry.name}'"
                            )
                        elif response.status_code == 400 and "already exists" in response.text:
                            # Component already exists, try to update it instead
                            try:
                                update_data = {
                                    "component_version": component.component_version,
                                    "description": component.description,
                                    "exposed_apis": [
                                        {
                                            "name": api.name,
                                            "oas_specification": api.oas_specification,
                                            "url": api.url,
                                            "labels": api.labels
                                        }
                                        for api in component.exposed_apis
                                    ],
                                    "labels": component.labels
                                }
                                
                                update_response = await client.put(
                                    f"{upstream_url}/components/{comp_reg_name}/{component.component_name}",
                                    json=update_data,
                                    headers={"Content-Type": "application/json"}
                                )
                                
                                if update_response.status_code == 200:
                                    registry_results["components_success"] += 1
                                    total_success += 1
                                    logging.info(
                                        f"Successfully updated component '{component.component_name}' "
                                        f"in upstream registry '{upstream_registry.name}'"
                                    )
                                else:
                                    registry_results["components_failed"] += 1
                                    total_failed += 1
                                    error_msg = f"Failed to update component '{component.component_name}': {update_response.status_code} - {update_response.text}"
                                    registry_results["errors"].append(error_msg)
                                    logging.error(error_msg)
                            except Exception as update_error:
                                registry_results["components_failed"] += 1
                                total_failed += 1
                                error_msg = f"Error updating component '{component.component_name}': {str(update_error)}"
                                registry_results["errors"].append(error_msg)
                                logging.error(error_msg)
                        else:
                            registry_results["components_failed"] += 1
                            total_failed += 1
                            error_msg = f"Failed to sync component '{component.component_name}': {response.status_code} - {response.text}"
                            registry_results["errors"].append(error_msg)
                            logging.error(error_msg)
                            
                    except httpx.RequestError as req_error:
                        registry_results["components_failed"] += 1
                        total_failed += 1
                        error_msg = f"Request error for component '{component.component_name}': {str(req_error)}"
                        registry_results["errors"].append(error_msg)
                        logging.error(error_msg)
                    except Exception as sync_error:
                        registry_results["components_failed"] += 1
                        total_failed += 1
                        error_msg = f"Unexpected error syncing component '{component.component_name}': {str(sync_error)}"
                        registry_results["errors"].append(error_msg)
                        logging.error(error_msg)
                
                sync_results.append(registry_results)
        
        return {
            "message": f"Synchronization completed. {total_success} components synced successfully, {total_failed} failed.",
            "upstream_registries": len(upstream_registries),
            "components_synced": len(self_components),
            "total_success": total_success,
            "total_failed": total_failed,
            "sync_results": sync_results
        }
        
    except Exception as e:
        logging.error(f"Error during upstream synchronization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during synchronization: {str(e)}"
        )


@app.get("/desc", tags=["Description"])
async def description():
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