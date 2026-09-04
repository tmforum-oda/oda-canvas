import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from kubernetes.client.exceptions import ApiException
from pydantic import BaseModel

from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.model_gateway_services import (
    create_model_gateway_service,
    delete_model_gateway_service,
    format_k8s_api_exception,
    get_model_gateway_service,
    get_model_gateway_service_schema,
    list_model_gateway_services,
    model_gateway_services_available,
    update_model_gateway_service,
    validate_model_gateway_service,
)
from models.model_gateway import (
    ModelGatewayServiceCreate,
    ModelGatewayServiceUpdate,
    ModelGatewayServiceValidate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model-gateway-services", tags=["model-gateway-services"])


@router.get("/availability")
def get_availability(_: AuthUser = Depends(get_current_user)):
    return {"available": model_gateway_services_available()}


@router.get("")
def list_services(_: AuthUser = Depends(get_current_user)):
    return list_model_gateway_services()


@router.get("/schema")
def get_schema(_: AuthUser = Depends(get_current_user)):
    if not model_gateway_services_available():
        raise HTTPException(status_code=404, detail="ModelGatewayService CRD is not installed")
    try:
        return get_model_gateway_service_schema()
    except ApiException as exc:
        status_code = exc.status if exc.status in (400, 401, 403, 404) else 500
        raise HTTPException(status_code=status_code, detail=format_k8s_api_exception(exc))


@router.get("/{namespace}/{name}")
def get_service(namespace: str, name: str, _: AuthUser = Depends(get_current_user)):
    result = get_model_gateway_service(namespace, name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"ModelGatewayService {namespace}/{name} not found")
    return result


@router.post("", status_code=201)
def create_service(payload: ModelGatewayServiceCreate, user: AuthUser = Depends(get_current_user)):
    if not model_gateway_services_available():
        raise HTTPException(status_code=404, detail="ModelGatewayService CRD is not installed")
    try:
        spec = payload.resolved_spec()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        return create_model_gateway_service(user, payload.namespace, payload.name, spec)
    except ApiException as exc:
        status_code = exc.status if exc.status in (400, 401, 403, 404, 409, 422) else 500
        raise HTTPException(status_code=status_code, detail=format_k8s_api_exception(exc))


@router.post("/validate")
def validate_service(payload: ModelGatewayServiceValidate, user: AuthUser = Depends(get_current_user)):
    if not model_gateway_services_available():
        raise HTTPException(status_code=404, detail="ModelGatewayService CRD is not installed")
    try:
        spec = payload.resolved_spec()
        validate_model_gateway_service(user, payload.namespace, payload.name, spec, payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ApiException as exc:
        status_code = exc.status if exc.status in (400, 401, 403, 404, 409, 422) else 422
        raise HTTPException(status_code=status_code, detail=format_k8s_api_exception(exc))
    return {"valid": True, "spec": spec}


@router.put("/{namespace}/{name}")
def update_service(
    namespace: str,
    name: str,
    payload: ModelGatewayServiceUpdate,
    user: AuthUser = Depends(get_current_user),
):
    if not model_gateway_services_available():
        raise HTTPException(status_code=404, detail="ModelGatewayService CRD is not installed")
    try:
        spec = payload.resolved_spec()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        return update_model_gateway_service(user, namespace, name, spec)
    except ApiException as exc:
        status_code = exc.status if exc.status in (400, 401, 403, 404, 409, 422) else 500
        raise HTTPException(status_code=status_code, detail=format_k8s_api_exception(exc))


@router.delete("/{namespace}/{name}", status_code=204)
def delete_service(namespace: str, name: str, user: AuthUser = Depends(get_current_user)):
    if not model_gateway_services_available():
        raise HTTPException(status_code=404, detail="ModelGatewayService CRD is not installed")
    try:
        delete_model_gateway_service(user, namespace, name)
    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(status_code=404, detail=f"ModelGatewayService {namespace}/{name} not found")
        status_code = exc.status if exc.status in (400, 401, 403, 404) else 500
        raise HTTPException(status_code=status_code, detail=format_k8s_api_exception(exc))


class ProxyTokenRequest(BaseModel):
    token_url: str
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"


class ProxyModelsRequest(BaseModel):
    gateway_url: str
    token: str


class ProxyChatRequest(BaseModel):
    gateway_url: str
    token: str
    model: str
    message: str


def _response_body(resp: httpx.Response) -> dict:
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text or f"HTTP {resp.status_code}"}
    return body if isinstance(body, dict) else {"data": body}


@router.post("/proxy/token")
def proxy_token(payload: ProxyTokenRequest, _: AuthUser = Depends(get_current_user)):
    token_url = payload.token_url.strip()
    client_id = payload.client_id.strip()
    client_secret = payload.client_secret.strip()
    grant_type = (payload.grant_type or "client_credentials").strip() or "client_credentials"
    if not token_url or not client_id or not client_secret:
        raise HTTPException(status_code=422, detail="token_url, client_id, and client_secret are required")
    try:
        resp = httpx.post(
            token_url,
            data={
                "grant_type": grant_type,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
            verify=False,
        )
        return JSONResponse(status_code=resp.status_code, content=_response_body(resp))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Token request failed: {exc}")


@router.post("/proxy/models")
def proxy_models(payload: ProxyModelsRequest, _: AuthUser = Depends(get_current_user)):
    gateway_url = payload.gateway_url.strip().rstrip("/")
    token = payload.token.strip()
    if not gateway_url or not token:
        raise HTTPException(status_code=422, detail="gateway_url and token are required")
    try:
        resp = httpx.get(
            f"{gateway_url}/v1/models",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
            verify=False,
        )
        return JSONResponse(status_code=resp.status_code, content=_response_body(resp))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Models request failed: {exc}")


@router.post("/proxy/chat")
def proxy_chat(payload: ProxyChatRequest, _: AuthUser = Depends(get_current_user)):
    gateway_url = payload.gateway_url.strip().rstrip("/")
    token = payload.token.strip()
    model = payload.model.strip()
    message = payload.message.strip()
    if not gateway_url or not token or not model or not message:
        raise HTTPException(status_code=422, detail="gateway_url, token, model, and message are required")
    try:
        resp = httpx.post(
            f"{gateway_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=30,
            verify=False,
        )
        return JSONResponse(status_code=resp.status_code, content=_response_body(resp))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Chat request failed: {exc}")
