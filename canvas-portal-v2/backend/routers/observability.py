from fastapi import APIRouter, Depends, HTTPException
from kubernetes.client.exceptions import ApiException

from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.observability import get_observability_summary

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("")
def get_observability(_: AuthUser = Depends(get_current_user)):
    try:
        return get_observability_summary()
    except ApiException as exc:
        status_code = exc.status if exc.status in (400, 401, 403, 404) else 500
        raise HTTPException(status_code=status_code, detail=exc.reason or "Kubernetes API error")
