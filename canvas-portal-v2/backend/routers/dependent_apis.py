from fastapi import APIRouter, Depends, Query

from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.dependent_apis import list_full_dependent_apis, get_full_dependent_api

router = APIRouter(prefix="/api/dependentapis", tags=["dependentapis"])


@router.get("")
async def get_dependent_apis(namespace: str | None = Query(None), user: AuthUser = Depends(get_current_user)):
    return await list_full_dependent_apis(user, namespace)


@router.get("/{namespace}/{name}")
async def get_dependent_api_detail(namespace: str, name: str, user: AuthUser = Depends(get_current_user)):
    return await get_full_dependent_api(name, namespace, user)
