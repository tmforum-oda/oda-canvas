"""
Component Registry Service - FastAPI REST API

This service provides CRUD operations for managing Component Registries, Components,
and their Exposed APIs following the TM Forum ODA Canvas specification.
"""

from dotenv import load_dotenv
load_dotenv()  # take environment variables

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db, init_db
import models, crud
from typing import List, Optional
import uvicorn
import os
import httpx
import logging



OWN_REGISTRY_URL = os.getenv("OWN_REGISTRY_URL")
OWN_REGISTRY_EXTERNAL_NAME = os.getenv("OWN_REGISTRY_EXTERNAL_NAME")

if not OWN_REGISTRY_URL or not OWN_REGISTRY_EXTERNAL_NAME:
    raise ValueError("Environment variables OWN_REGISTRY_URL and OWN_REGISTRY_EXTERNAL_NAME must be set")


def initialize_own_registry_entry(db: Session):
    """Ensure the 'self' ComponentRegistry exists in the database."""
    existing = crud.ComponentRegistryCRUD.get(db, "self")
    if not existing:
        self_registry = models.ComponentRegistryCreate(
            name="self",
            url=OWN_REGISTRY_URL,
            type="self",
            labels={"externalName": OWN_REGISTRY_EXTERNAL_NAME}
        )
        try:
            crud.ComponentRegistryCRUD.create(db, self_registry)
            logging.info("Initialized 'self' ComponentRegistry in the database.")
        except ValueError as e:
            logging.error(f"Error initializing 'self' ComponentRegistry: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_db()
    initialize_own_registry_entry(next(get_db()))
    yield
    # shutdown


app = FastAPI(
    lifespan=lifespan,
    title=f"Component Registry {OWN_REGISTRY_EXTERNAL_NAME}",
    description="REST API for managing ODA Components and Exposed APIs",
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

    

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "component-registry-service"}


# ROOT ENDPOINT (COMPONENT REGISTRY OVERVIEW GUI)
@app.get("/", response_class=HTMLResponse, tags=["Component Registries", "Components"])
def root(request: Request, db: Session = Depends(get_db)):
    """GUI page to display all component registries and their components"""
    # Get all component registries
    registries = crud.ComponentRegistryCRUD.get_all(db)
    
    # Get all components
    components = crud.ComponentCRUD.get_all(db)
    
    # Get self registry info for title
    selfCompReg = crud.ComponentRegistryCRUD.get(db, "self")
    selfname = "Component Registry Service"
    if selfCompReg and selfCompReg.labels and "externalName" in selfCompReg.labels:
        selfname = selfCompReg.labels["externalName"]
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "registries": registries, 
        "components": components, 
        "selfname": selfname
    })


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


@app.get("/registries/{name}", response_model=models.ComponentRegistry, tags=["Component Registries"])
async def get_component_registry(name: str, db: Session = Depends(get_db)):
    """Get a ComponentRegistry by name."""
    registry = crud.ComponentRegistryCRUD.get(db, name)
    if not registry:
        raise HTTPException(status_code=404, detail=f"ComponentRegistry '{name}' not found")
    return registry


@app.get("/registries", response_model=List[models.ComponentRegistry], tags=["Component Registries"])
async def get_all_component_registries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all ComponentRegistries."""
    return crud.ComponentRegistryCRUD.get_all(db, skip=skip, limit=limit)


@app.post("/registries/upstream-from-url", response_model=models.ComponentRegistry, tags=["Component Registries"])
async def create_upstream_registry_from_url(
    request: models.UpstreamRegistryRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new upstream ComponentRegistry by fetching data from the upstream's 'self' registry.
    
    This endpoint takes only a URL and fetches the registry information from the upstream's
    'self' ComponentRegistry to populate name, labels, and other metadata.
    """
    try:
        # Fetch the 'self' registry from the upstream URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream_url = request.url.rstrip('/')
            
            try:
                response = await client.get(f"{upstream_url}/registries/self")
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not fetch 'self' registry from upstream URL. Status: {response.status_code}"
                    )
                
                upstream_self_data = response.json()
                
            except httpx.RequestError as req_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error connecting to upstream registry: {str(req_error)}"
                )
            except Exception as parse_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing response from upstream registry: {str(parse_error)}"
                )
        
        # Extract data from the upstream's self registry
        upstream_name = upstream_self_data.get("name")
        upstream_labels = upstream_self_data.get("labels", {})
        
        # Use externalName from labels if available, otherwise use the name
        registry_name = upstream_labels.get("externalName", upstream_name)
        
        if not registry_name:
            raise HTTPException(
                status_code=400,
                detail="Upstream 'self' registry does not have a valid name or externalName"
            )
        
        # Check if registry with this name already exists
        existing = crud.ComponentRegistryCRUD.get(db, registry_name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"ComponentRegistry '{registry_name}' already exists"
            )
        
        # Create the upstream registry
        upstream_registry = models.ComponentRegistryCreate(
            name=registry_name,
            url=request.url,
            type="upstream",
            labels=upstream_labels
        )
        
        created_registry = crud.ComponentRegistryCRUD.create(db, upstream_registry)
        
        logging.info(f"Successfully created upstream registry '{registry_name}' from URL '{request.url}'")
        
        return created_registry
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error creating upstream registry from URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


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
    Synchronize all local component registries and their components to all upstream ComponentRegistries.
    
    This endpoint:
    1. Finds all upstream ComponentRegistries
    2. Gets all local component registries (self, downstream) 
    3. Registers each local registry with upstream registries if needed
    4. Gets all components and syncs them to upstream registries
    5. Returns a comprehensive summary of the synchronization results
    """
    try:
        own_registry = crud.ComponentRegistryCRUD.get(db, "self")
        if not own_registry is None:
            external_name = own_registry.labels.get("externalName", None) if own_registry.labels else None
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
                "registries_synced": 0,
                "components_synced": 0,
                "sync_results": []
            }
        
        # Get all local registries (self and downstream) to sync
        self_registries = crud.ComponentRegistryCRUD.get_by_type(db, "self")
        downstream_registries = crud.ComponentRegistryCRUD.get_by_type(db, "downstream")
        local_registries = self_registries + downstream_registries
        
        # Get all components from all registries
        all_components = crud.ComponentCRUD.get_all(db)
        
        if not all_components:
            return {
                "message": "No components found in any registry to sync",
                "upstream_registries": len(upstream_registries),
                "registries_synced": len(local_registries),
                "components_synced": 0,
                "sync_results": []
            }
        
        sync_results = []
        total_success = 0
        total_failed = 0
        total_registries_registered = 0
        
        # Sync to each upstream registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            for upstream_registry in upstream_registries:
                registry_results = {
                    "registry_name": upstream_registry.name,
                    "registry_url": upstream_registry.url,
                    "local_registries_registered": 0,
                    "components_sent": 0,
                    "components_success": 0,
                    "components_failed": 0,
                    "errors": []
                }
                
                # First, register all local registries with this upstream
                for local_registry in local_registries:
                    try:
                        # Determine the external name for this registry
                        if local_registry.name == "self":
                            registry_external_name = external_name
                        else:
                            # For downstream registries, use their externalName label or fallback to name
                            registry_external_name = local_registry.labels.get("externalName", local_registry.name) if local_registry.labels else local_registry.name
                        
                        # Register this local registry with upstream
                        registration_success = await register_upstream(upstream_registry, local_registry, registry_external_name)
                        if registration_success:
                            registry_results["local_registries_registered"] += 1
                            total_registries_registered += 1
                            logging.info(f"Successfully registered registry '{registry_external_name}' with upstream '{upstream_registry.name}'")
                        
                    except Exception as reg_error:
                        error_msg = f"Error registering registry '{local_registry.name}': {str(reg_error)}"
                        registry_results["errors"].append(error_msg)
                        logging.error(error_msg)
                
                # Now sync all components to this upstream registry
                for component in all_components:
                    registry_results["components_sent"] += 1
                    
                    try:
                        # Determine the correct registry reference name for this component
                        comp_reg_name = component.component_registry_ref
                        
                        # Map registry names to their external names
                        if comp_reg_name == 'self':
                            comp_reg_name = external_name
                        else:
                            # For other registries, try to get their external name
                            source_registry = crud.ComponentRegistryCRUD.get(db, comp_reg_name)
                            if source_registry and source_registry.labels and "externalName" in source_registry.labels:
                                comp_reg_name = source_registry.labels["externalName"]
                            # Otherwise keep the original name
                        
                        # Prepare component data for upstream registry
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
                                f"from registry '{component.component_registry_ref}' to upstream '{upstream_registry.name}'"
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
                                        f"from registry '{component.component_registry_ref}' in upstream '{upstream_registry.name}'"
                                    )
                                else:
                                    registry_results["components_failed"] += 1
                                    total_failed += 1
                                    error_msg = f"Failed to update component '{component.component_name}' from registry '{component.component_registry_ref}': {update_response.status_code} - {update_response.text}"
                                    registry_results["errors"].append(error_msg)
                                    logging.error(error_msg)
                            except Exception as update_error:
                                registry_results["components_failed"] += 1
                                total_failed += 1
                                error_msg = f"Error updating component '{component.component_name}' from registry '{component.component_registry_ref}': {str(update_error)}"
                                registry_results["errors"].append(error_msg)
                                logging.error(error_msg)
                        else:
                            registry_results["components_failed"] += 1
                            total_failed += 1
                            error_msg = f"Failed to sync component '{component.component_name}' from registry '{component.component_registry_ref}': {response.status_code} - {response.text}"
                            registry_results["errors"].append(error_msg)
                            logging.error(error_msg)
                            
                    except httpx.RequestError as req_error:
                        registry_results["components_failed"] += 1
                        total_failed += 1
                        error_msg = f"Request error for component '{component.component_name}' from registry '{component.component_registry_ref}': {str(req_error)}"
                        registry_results["errors"].append(error_msg)
                        logging.error(error_msg)
                    except Exception as sync_error:
                        registry_results["components_failed"] += 1
                        total_failed += 1
                        error_msg = f"Unexpected error syncing component '{component.component_name}' from registry '{component.component_registry_ref}': {str(sync_error)}"
                        registry_results["errors"].append(error_msg)
                        logging.error(error_msg)
                
                sync_results.append(registry_results)
        
        return {
            "message": f"Synchronization completed. {total_registries_registered} registries registered, {total_success} components synced successfully, {total_failed} failed.",
            "upstream_registries": len(upstream_registries),
            "local_registries_synced": len(local_registries),
            "components_synced": len(all_components),
            "total_registries_registered": total_registries_registered,
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)