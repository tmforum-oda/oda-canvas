import logging
from typing import Literal
from kubernetes import client
from k8s.client import get_base_api_client

logger = logging.getLogger(__name__)
CanvasType = Literal["istio", "kong", "apisix"]

CANVAS_NAMESPACE = "canvas"

detected_canvas_type: CanvasType | None = None


def list_canvas_deployment_names() -> list[str]:
    apps_api = client.AppsV1Api(get_base_api_client())
    try:
        deployments = apps_api.list_namespaced_deployment(CANVAS_NAMESPACE)
    except client.exceptions.ApiException as exc:
        logger.warning("Unable to list deployments in '%s' namespace: %s", CANVAS_NAMESPACE, exc.reason)
        return []
    return [
        item.metadata.name.lower()
        for item in deployments.items
        if item.metadata and item.metadata.name
    ]


async def detect_canvas_type() -> CanvasType:
    global detected_canvas_type
    if detected_canvas_type is not None:
        return detected_canvas_type
    logger.info("Auto-detecting canvas type from operator deployments in '%s' namespace...", CANVAS_NAMESPACE)
    deployment_names = list_canvas_deployment_names()
    if any("apisix" in name for name in deployment_names):
        detected_canvas_type = "apisix"
    elif any("kong" in name for name in deployment_names):
        detected_canvas_type = "kong"
    else:
        detected_canvas_type = "istio"
    logger.info("Canvas type detected: %s", detected_canvas_type)
    return detected_canvas_type


def get_cached_canvas_type() -> CanvasType | None:
    return detected_canvas_type


def reset_canvas_type_cache():
    global detected_canvas_type
    detected_canvas_type = None
