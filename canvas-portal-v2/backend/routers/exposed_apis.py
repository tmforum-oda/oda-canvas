from fastapi import APIRouter, Depends, Query
from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.exposed_apis import list_full_exposed_apis, get_full_exposed_api

router = APIRouter(prefix="/api/exposedapis", tags=["exposedapis"])


@router.get("")
async def get_exposed_apis(namespace: str | None = Query(None), user: AuthUser = Depends(get_current_user)):
    return await list_full_exposed_apis(user, namespace)


@router.get("/{namespace}/{name}")
async def get_exposed_api_detail(namespace: str, name: str, user: AuthUser = Depends(get_current_user)):
    return await get_full_exposed_api(name, namespace, user)
