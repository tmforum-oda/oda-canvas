"""Main FastAPI application for TMF639 Resource Inventory Management v5.0.0."""

from dotenv import load_dotenv
# load_dotenv()  # take environment variables
load_dotenv(".env2")  # take environment variables

import os
import httpx
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from multiprocessing import Process
import asyncio

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jsonpath import findall

from app import models, schemas, crud
from app.database import engine, get_db, Base
from app.global_lock import GlobalLock
from app.validators import TMF639ResourceValidator


# Filter to suppress health check logging
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/health") == -1


# Configure logging to suppress health endpoint
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

CANVAS_RESOURCE_INVENTORY = os.getenv("CANVAS_RESOURCE_INVENTORY", None)
WATCHED_NAMESPACES_STR = os.getenv("WATCHED_NAMESPACES", "")
WATCHED_NAMESPACES = WATCHED_NAMESPACES_STR.split(",") if WATCHED_NAMESPACES_STR else []
OWN_REGISTRY_NAME = os.getenv("OWN_REGISTRY_NAME", "self")

print(f"OWN_REGISTRY_NAME: {OWN_REGISTRY_NAME}")

global_lock = GlobalLock("GlobalLock.ResourceInventoryApp")


#===============================================================================
# # see https://www.nashruddinamin.com/blog/running-scheduled-jobs-in-fastapi
# scheduler = AsyncIOScheduler()
# @scheduler.scheduled_job('interval', seconds=10)  # ('cron', hour=13, minute=05)
# async def process_events():
#     print(f"scheduled on worker {ipc._process_num} (pid={os.getpid()}), PROCESSES: {ipc.get_process_ids()} {'LEADER' if ipc.is_leader() else ''}")
#     ipc.alive()
#     ipc.cleanup()
#===============================================================================

class ResourceSyncer:
    def __init__(self, downstream_url: str, upstream_url: str, upstream_repo_name:str="self"):
        self._downstream_url = downstream_url
        self._upstream_url = upstream_url
        self._repo_name = upstream_repo_name
        self._initialized = False
        self._resource_versions = {}  # resource_id -> version

    def initialize(self):
        """Fetch initial resource versions from upstream."""
        # For simplicity, we assume upstream provides an endpoint to list resources with their versions
        if self._initialized:
            return
        print(f"CANVAS_RESOURCE_INVENTORY: {CANVAS_RESOURCE_INVENTORY}")
        print(f"WATCHED_NAMESPACES: {WATCHED_NAMESPACES}")
        async def fetch_versions():
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{self._upstream_url}/resource", params={"fields": "resourceVersion"}, timeout=10)
                    response.raise_for_status()
                    resources = response.json()
                    for res in resources:
                        resource_id = res.get("id")
                        resourceVersion = res.get("resourceVersion")
                        self._resource_versions[resource_id] = resourceVersion
                    self._initialized = True
                except Exception as e:
                    print(f"Failed to initialize ResourceSyncer: {e}")

        asyncio.run(fetch_versions())


    def k8s_resource_to_downstream_id(self, kind, namespace, name):
        return f"{name}"
    
    def k8s_resource_to_upstream_id(self, kind, namespace, name):
        return f"{self._repo_name}:{name}"

    async def k8s_resource_changed_event(self, kind, namespace, name, rv, old_rv):
        print(f"[PID{os.getpid()}]: Callback received event for {kind} {namespace}:{name}: new version {rv} was ({old_rv})")
        up_id = self.k8s_resource_to_upstream_id(kind, namespace, name)
        if rv == self._resource_versions.get(up_id, None):
            print(f"[PID{os.getpid()}]: No version change detected for {up_id}, skipping sync.")
            return
        if rv is None:
            await self.delete_upstream(up_id)
            self._resource_versions[up_id] = rv
        else:
            down_id = self.k8s_resource_to_downstream_id(kind, namespace, name)
            resource_data = await self.fetch_from_downstream(down_id, namespace)
            resource_data = self.patch_resource_data(resource_data, self._repo_name)
            await self.send_to_upstream(up_id, resource_data)
            self._resource_versions[up_id] = rv
        
    def patch_resource_data(self, resource_data: dict, repo_name: str) -> dict:
        """Patch resource data to replace 'self:' prefixes with the repo_name prefix."""
        res_id = resource_data.get("id", None)
        up_res_id = f"{repo_name}:{res_id}"
        resource_data["id"] = up_res_id
        category = resource_data.get("category", None)
        if category == "ODAComponent":  # only maintain exposedBy relations in ExposedAPIs
            resource_data.pop("resourceRelationship", None)
        if "resourceRelationship" in resource_data:
            for rr in resource_data["resourceRelationship"]:
                rel_id = rr.get("resource",{}).get("id", None)
                up_rel_id = f"{repo_name}:{rel_id}"
                rr.get("resource",{})["id"] = up_rel_id
                rr.get("resource",{})["href"] = f"{self._upstream_url}/resource/{up_rel_id}"
        return resource_data
    
    async def delete_upstream(self, resource_id: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self._upstream_url}/resource/{resource_id}", timeout=5)
                response.raise_for_status()
            except Exception as e:
                raise RuntimeError(f"Failed to delete resource {resource_id} from upstream: {e}")
    
    async def fetch_from_downstream(self, resource_id: str, namespace: str = None) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self._downstream_url}/resource/{resource_id}"
                if namespace:
                    url += f"?namespace={namespace}"
                response = await client.get(url, timeout=5)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch resource {resource_id} from downstream: {e}")

    async def send_to_upstream(self, resource_id: str, resource_data: dict):
        if resource_id in self._resource_versions:
            try:
                return await self.update_upstream(resource_id, resource_data)
            except Exception as e:
                if "404" in str(e):
                    return await self.create_upstream(resource_id, resource_data)
                raise e
        else:
            try:
                return await self.create_upstream(resource_id, resource_data)
            except RuntimeError as e:
                if "409" in str(e):
                    return await self.update_upstream(resource_id, resource_data)
                raise e

    async def create_upstream(self, resource_id: str, resource_data: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self._upstream_url}/resource", json=resource_data, timeout=5)
                response.raise_for_status()
            except Exception as e:
                raise RuntimeError(f"Failed to send resource {resource_id} to upstream: {e}")
                    
    async def update_upstream(self, resource_id: str, resource_data: dict):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(f"{self._upstream_url}/resource/{resource_id}", json=resource_data, timeout=5)
                response.raise_for_status()
            except Exception as e:
                raise RuntimeError(f"Failed to send resource {resource_id} to upstream: {e}")
                        
                
    async def send_event(self, event_type: str, event_id: str, resource_data: dict):
        event_payload = {
            "eventType": event_type,
            "eventTime": datetime.utcnow().isoformat() + "Z",
            "id": event_id,
            "resource": resource_data,
        }
        if self.query:
            event_payload["query"] = self.query
        async with httpx.AsyncClient() as client:
            try:
                await client.post(self.callback_url, json=event_payload, timeout=5)
            except Exception as e:
                print(f"Failed to send event to {self.callback_url}: {e}")


started_processes = []

def event_callback(kind, namespace, name, rv, old_rv):
    print(f"[PID{os.getpid()}]: Callback received event for {kind} {namespace}:{name}: new version {rv} was ({old_rv})")

def bgprocess_run():
    rsync = ResourceSyncer(downstream_url=CANVAS_RESOURCE_INVENTORY, upstream_url="http://localhost:8080", upstream_repo_name="self")
    rsync.initialize();
    from app.k8s_watcher import K8SWatcher
    k8sWatcher = K8SWatcher(rsync.k8s_resource_changed_event)
    k8sWatcher.add_watch(api_version="v1", group="oda.tmforum.org", kind="Component", namespaces=WATCHED_NAMESPACES)
    k8sWatcher.add_watch(api_version="v1", group="oda.tmforum.org", kind="ExposedAPI", namespaces=WATCHED_NAMESPACES)
    k8sWatcher.start()

def start_k8s_watcher_process():
    print(f"[PID{os.getpid()}]: Starting K8s watcher background process...")
    p = Process(target=bgprocess_run, args=())
    p.start()
    started_processes.append(p)


def stop_k8s_watcher_process():
    for p in started_processes:
        p.terminate()
    started_processes.clear()
    

def initialize_database():
    """Initialize the database with required tables."""
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    if CANVAS_RESOURCE_INVENTORY:
        if global_lock.acquire(block=False):
            start_k8s_watcher_process()
    yield
    if CANVAS_RESOURCE_INVENTORY:
        stop_k8s_watcher_process()
    
    


# Create FastAPI app
app = FastAPI(
    title="Resource Inventory Management",
    description="TMF639 - Resource Inventory Management API v5.0.0",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


async def notify_hubs(event_type: str, event_id: str, resource_data: dict, db: Session):
    """Send event notification to all registered hubs."""
    hubs = crud.get_all_hubs(db)
    event_payload = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "id": event_id,
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
    fields: Optional[str] = None,
    filter: Optional[str] = None,
    request: Request = None,
    response: Response = None,
    db: Session = Depends(get_db)
):
    base_url = f"{request.url.scheme}://{request.url.netloc}" if request else ""
    resources, total_count = crud.get_resources(db, offset=offset, limit=limit)
    
    
    # Check if fields parameter requests only resourceVersion
    if fields and fields.strip() == "resourceVersion":
        # Optimized query: return only id, resourceVersion, href without accessing data column
        result = []
        for r in resources:
            result.append({
                "id": r.id,
                "resourceVersion": r.resource_version,
                "href": f"{base_url}/resource/{r.id}",
                "@type": "LogicalResource",
                "@baseType": "Resource"
            })
        
        # Apply JSONPath filter if provided
        if filter:
            try:
                result = findall(filter, result)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSONPath filter: {str(e)}"
                )
        
        response.headers["X-Result-Count"] = str(len(result))
        response.headers["X-Total-Count"] = str(total_count)
        return result
    
    # Default behavior: return full resource data
    result = []
    for r in resources:
        db_resource = crud.get_resource(db, r.id, base_url)
        result.append(db_resource.data)  # Return only the data content
    
    # Apply JSONPath filter if provided
    if filter:
        try:
            result = findall(filter, result)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSONPath filter: {str(e)}"
            )
    
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

    # Validate resource against TMF639 v5.0.0 specification
    validated_resource = TMF639ResourceValidator.validate_resource_create(resource)

    # Check if resource with same ID already exists
    resource_id = validated_resource.get("id")
    if resource_id:
        existing_resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
        if existing_resource:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Resource with id {resource_id} already exists"
            )

    db_resource = crud.create_resource(db, validated_resource, base_url)
    # Get the resource with dynamically generated href
    db_resource = crud.get_resource(db, db_resource.id, base_url)
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
    fields: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    base_url = f"{request.url.scheme}://{request.url.netloc}" if request else ""
    
    # Check if fields parameter requests only resourceVersion
    if fields and fields.strip() == "resourceVersion":
        # Optimized query: fetch only id and resource_version from database
        db_resource = db.query(models.Resource).filter(models.Resource.id == id).first()
        if db_resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource with id {id} not found"
            )
        return {
            "id": db_resource.id,
            "resourceVersion": db_resource.resource_version,
            "href": f"{base_url}/resource/{db_resource.id}",
            "@type": "LogicalResource",
            "@baseType": "Resource"
        }
    
    # Default behavior: return full resource data
    db_resource = crud.get_resource(db, id, base_url)
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
    request: Request = None,
    db: Session = Depends(get_db)
):
    base_url = f"{request.url.scheme}://{request.url.netloc}" if request else ""
    db_resource = crud.update_resource(db, id, resource)
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {id} not found"
        )
    # Get the resource with dynamically generated href
    db_resource = crud.get_resource(db, id, base_url)
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


def guess_id(url: str) -> Optional[str]:
    if url.endswith("/sync"):
        health_url = url[:-5] + "/health"
        try:
            print(f"calling health url: {health_url}")
            response = httpx.get(health_url, timeout=5)
            response.raise_for_status()
            health_data = response.json()
            print(f"got response: {health_data}")
            return health_data.get("Name", None)
        except Exception as e:
            print(f"exception: {str(e)}")
            return None


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
    if data.id is None:
        data.id = guess_id(data.callback)
    """Register an event listener."""
    db_hub = crud.create_hub(db, data)
    return db_hub


@app.get(
    "/hub",
    response_model=List[schemas.Hub],
    tags=["events subscription"],
    summary="List all subscriptions (hubs)",
    description="This operation retrieves all subscriptions to receive Events."
)
async def list_hubs(
    db: Session = Depends(get_db)
):
    """Retrieve all event listeners."""
    hubs = crud.get_all_hubs(db)
    return hubs


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
    return {"status": "healthy", "version": "5.0.0", "Name": OWN_REGISTRY_NAME, "worker_pid": os.getpid()}


@app.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    tags=["synchronization"],
    summary="Synchronization callback endpoint",
    description="Receives events from other instances to keep resources synchronized."
)
async def sync_callback(
    event: dict,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for synchronization via hub subscriptions.
    Processes ResourceCreated, ResourceChanged, and ResourceDeleted events.
    """
    base_url = f"{request.url.scheme}://{request.url.netloc}" if request else ""
    event_type = event.get("eventType")
    # event_time = event.get("eventTime")
    resource_data = event.get("resource", {})
    # ID can be at event level or in resource data
    resource_id = event.get("id") or resource_data.get("id")
    
    # Parse query parameter for source mapping
    query = event.get("query", "")
    source_prefix = None
    if query and "source=" in query:
        # Extract source value from query string (e.g., "source=localdev82")
        for param in query.split("&"):
            if param.startswith("source="):
                source_value = param.split("=", 1)[1]
                source_prefix = f"{source_value}:"
                break
    
    # Helper function to replace "self:" prefix with source prefix in IDs
    def replace_self_prefix(value, source_prefix):
        """Recursively replace 'self:' prefix with source prefix in dict/list structures."""
        if not source_prefix:
            return value
        
        if isinstance(value, str):
            if value.startswith("self:"):
                return value.replace("self:", source_prefix, 1)
            return value
        elif isinstance(value, dict):
            return {k: replace_self_prefix(v, source_prefix) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_self_prefix(item, source_prefix) for item in value]
        else:
            return value
    
    # Apply source prefix replacement to resource_id and resource_data
    if source_prefix:
        if resource_id and resource_id.startswith("self:"):
            resource_id = resource_id.replace("self:", source_prefix, 1)
        resource_data = replace_self_prefix(resource_data, source_prefix)
        # Ensure the id in resource_data matches the transformed resource_id
        if "id" in resource_data:
            resource_data["id"] = resource_id
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing eventType in event payload"
        )
    
    try:
        if event_type == "ResourceCreated":
            # Check if resource already exists
            existing_resource = crud.get_resource(db, resource_id, base_url)
            if existing_resource:
                # Update if it already exists (to handle race conditions)
                crud.update_resource(db, resource_id, resource_data)
                db_resource = crud.get_resource(db, resource_id, base_url)
                await notify_hubs("ResourceChanged", resource_id, db_resource.data, db)
            else:
                # Ensure id is in resource_data for create
                resource_data_with_id = {**resource_data, "id": resource_id}
                crud.create_resource(db, resource_data_with_id, base_url="")
                db_resource = crud.get_resource(db, resource_id, base_url)
                await notify_hubs("ResourceCreated", resource_id, db_resource.data, db)
            
            return {
                "status": "synchronized",
                "eventType": event_type,
                "resourceId": resource_id,
                "action": "created"
            }
        
        elif event_type == "ResourceChanged":
            # Update the resource
            existing_resource = crud.get_resource(db, resource_id, base_url)
            if existing_resource:
                crud.update_resource(db, resource_id, resource_data)
                db_resource = crud.get_resource(db, resource_id, base_url)
                await notify_hubs("ResourceChanged", resource_id, db_resource.data, db)
                return {
                    "status": "synchronized",
                    "eventType": event_type,
                    "resourceId": resource_id,
                    "action": "updated"
                }
            else:
                # Create if it doesn't exist (to handle missing resources)
                resource_data_with_id = {**resource_data, "id": resource_id}
                crud.create_resource(db, resource_data_with_id, base_url="")
                db_resource = crud.get_resource(db, resource_id, base_url)
                await notify_hubs("ResourceCreated", resource_id, db_resource.data, db)
                return {
                    "status": "synchronized",
                    "eventType": event_type,
                    "resourceId": resource_id,
                    "action": "created_from_update"
                }
        
        elif event_type == "ResourceDeleted":
            # Delete the resource
            success = crud.delete_resource(db, resource_id)
            await notify_hubs("ResourceDeleted", resource_id, {}, db)
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
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    # Get all resources
    resources, _ = crud.get_resources(db)
    resources_with_data = []
    for r in resources:
        db_resource = crud.get_resource(db, r.id, base_url)
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
                            
                            status = potential_api.data.get('resourceStatus', "?")
                            
                            # This API is exposed by this component
                            oda_component_apis[component_id].append({
                                'id': potential_api.id,
                                'name': potential_api.data.get('name', '-'),
                                'type': potential_api.data.get('@type', 'API'),
                                'category': potential_api.data.get('category', '-'),
                                'apiType': api_type,
                                'url': url,
                                'apiDocs': api_docs,
                                'specifications': specifications,
                                'status': status
                            })
    namespaces = WATCHED_NAMESPACES_STR if CANVAS_RESOURCE_INVENTORY else "N/A"
    if not namespaces:
        namespaces = "ALL"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "own_registry_name": OWN_REGISTRY_NAME,
            "namespaces": namespaces,
            "resources": resources_with_data,
            "hubs": hubs,
            "relationships": relationships,
            "oda_component_apis": oda_component_apis
        }
    )

print(f"THIS IS WORKER {os.getpid()}")

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        #reload=True,
        workers=2,
    )