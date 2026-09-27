from fastapi import APIRouter, Depends, Query
from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.canvas_detector import detect_canvas_type
from k8s.resources.gateway_inventory import list_gateway_inventory

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


@router.get("/type")
async def get_canvas_type(user: AuthUser = Depends(get_current_user)):
    return {"canvasType": await detect_canvas_type()}


@router.get("/resources")
async def get_gateway_resources(namespace: str | None = Query(None), user: AuthUser = Depends(get_current_user)):
    resources = list_gateway_inventory(user, namespace)
    canvas_types = sorted({resource.get("canvasType") for resource in resources if resource.get("canvasType")})
    return {
        "canvasType": await detect_canvas_type(),
        "availableCanvasTypes": canvas_types,
        "resources": resources,
    }
