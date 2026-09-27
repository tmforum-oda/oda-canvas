import asyncio
import logging
from kubernetes import client

from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
ODA_GROUP = "oda.tmforum.org"
ODA_VERSION = "v1"
DEPENDENT_APIS_PLURAL = "dependentapis"


def _list_raw(user: AuthUser, namespace: str | None) -> list[dict]:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    if namespace:
        resp = custom_api.list_namespaced_custom_object(
            group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=DEPENDENT_APIS_PLURAL
        )
    else:
        resp = custom_api.list_cluster_custom_object(
            group=ODA_GROUP, version=ODA_VERSION, plural=DEPENDENT_APIS_PLURAL
        )
    return resp.get("items", []) or []


def _get_raw(name: str, namespace: str, user: AuthUser) -> dict:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    return custom_api.get_namespaced_custom_object(
        group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=DEPENDENT_APIS_PLURAL, name=name
    )


def _shape(raw: dict) -> dict:
    metadata = raw.get("metadata") or {}
    spec = raw.get("spec") or {}
    status = raw.get("status") or {}
    impl = status.get("implementation") or {}
    depapi_status = status.get("depapiStatus") or {}
    specification = spec.get("specification") or {}
    labels = metadata.get("labels") or {}

    return {
        "apiVersion": raw.get("apiVersion", ""),
        "name": metadata.get("name"),
        "namespace": metadata.get("namespace"),
        "apiName": spec.get("name"),
        "apiType": spec.get("apiType", "openapi"),
        "segment": spec.get("segment"),
        "componentName": labels.get("oda.tmforum.org/componentName"),
        "specificationUrl": specification.get("url"),
        "version": specification.get("version"),
        "ready": bool(impl.get("ready", False)),
        "resolvedUrl": depapi_status.get("url"),
        "svcInvID": depapi_status.get("svcInvID"),
        "createdAt": metadata.get("creationTimestamp"),
    }


async def list_full_dependent_apis(user: AuthUser, namespace: str | None = None) -> list[dict]:
    raw_list = await asyncio.to_thread(_list_raw, user, namespace)
    return [_shape(raw) for raw in raw_list]


async def get_full_dependent_api(name: str, namespace: str, user: AuthUser) -> dict:
    raw = await asyncio.to_thread(_get_raw, name, namespace, user)
    return _shape(raw)
