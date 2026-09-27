import asyncio
import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client
from k8s.canvas_detector import detect_canvas_type
from k8s.resources.gateway_inventory import (
    find_related_gateway_bindings_for_exposedapi,
    merge_policies,
    select_primary_binding,
)

logger = logging.getLogger(__name__)
ODA_GROUP = "oda.tmforum.org"
ODA_VERSION = "v1beta3"
EXPOSEDAPIS_PLURAL = "exposedapis"


def list_exposed_apis(user: AuthUser, namespace: str = None) -> list[dict]:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    if namespace:
        response = custom_api.list_namespaced_custom_object(group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=EXPOSEDAPIS_PLURAL)
    else:
        response = custom_api.list_cluster_custom_object(group=ODA_GROUP, version=ODA_VERSION, plural=EXPOSEDAPIS_PLURAL)
    return response.get("items", [])


def get_exposed_api(name: str, namespace: str, user: AuthUser) -> dict:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    return custom_api.get_namespaced_custom_object(group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=EXPOSEDAPIS_PLURAL, name=name)


def _enrich_exposed_api(raw: dict, fallback_canvas_type: str, user: AuthUser) -> dict:
    name = raw["metadata"]["name"]
    namespace = raw["metadata"]["namespace"]
    metadata = raw.get("metadata", {})
    spec = raw.get("spec", {})
    status = raw.get("status", {})
    api_status = status.get("apiStatus", {})
    impl_status = status.get("implementation", {})
    gateway_bindings = find_related_gateway_bindings_for_exposedapi(name, namespace, user)
    primary_binding = select_primary_binding(gateway_bindings)
    policies = merge_policies(gateway_bindings)
    canvas_type = primary_binding.get("canvasType") if primary_binding else fallback_canvas_type

    result = {
        "apiVersion": raw.get("apiVersion", ""),
        "name": metadata.get("name", name),
        "namespace": namespace,
        "url": api_status.get("url"),
        "status": "ready" if impl_status.get("ready") else "notReady",
        "apiType": spec.get("apiType", "openapi"),
        "implementation": spec.get("implementation", ""),
        "port": spec.get("port", ""),
        "version": spec.get("version") or metadata.get("labels", {}).get("oda.tmforum.org/componentVersion"),
        "canvasType": canvas_type,
        "gatewayResource": None,
        "gatewayDetails": None,
        "gatewayResources": gateway_bindings,
        "policies": policies,
    }

    if primary_binding:
        result["gatewayResource"] = {
            "kind": primary_binding.get("kind", ""),
            "name": primary_binding.get("name", ""),
            "namespace": primary_binding.get("namespace", namespace),
            "group": primary_binding.get("group", ""),
            "apiVersion": primary_binding.get("apiVersion", ""),
        }
        result["gatewayDetails"] = primary_binding.get("details")

    return result


async def get_full_exposed_api(name: str, namespace: str, user: AuthUser) -> dict:
    fallback_canvas_type = await detect_canvas_type()
    raw = get_exposed_api(name, namespace, user)
    return await asyncio.to_thread(_enrich_exposed_api, raw, fallback_canvas_type, user)


async def list_full_exposed_apis(user: AuthUser, namespace: str = None) -> list[dict]:
    fallback_canvas_type = await detect_canvas_type()
    raw_list = await asyncio.to_thread(list_exposed_apis, user, namespace)

    async def _safe_enrich(raw: dict) -> dict:
        name = raw["metadata"]["name"]
        namespace = raw["metadata"]["namespace"]
        try:
            return await asyncio.to_thread(_enrich_exposed_api, raw, fallback_canvas_type, user)
        except Exception as e:
            logger.error("Failed to enrich ExposedAPI %r: %s", name, e)
            return {"name": name, "namespace": namespace, "error": str(e), "gatewayResource": None, "policies": []}

    return list(await asyncio.gather(*[_safe_enrich(raw) for raw in raw_list]))
