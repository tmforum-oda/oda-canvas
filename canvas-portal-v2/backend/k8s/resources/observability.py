import json
import logging
import os
from typing import Any

import httpx
from kubernetes import client
from kubernetes.client.exceptions import ApiException

from k8s.client import get_base_api_client


logger = logging.getLogger(__name__)


COMMON_NAMESPACES = ["default", "monitoring", "observability", "prometheus", "grafana", "canvas"]


OBSERVABILITY_TOOLS: list[dict[str, Any]] = [
    {
        "id": "langfuse",
        "name": "Langfuse",
        "description": "LLM traces, prompts, evaluations, and application observability.",
        "serviceNames": ["langfuse-web", "langfuse"],
        "healthPath": "/api/public/health",
    },
    {
        "id": "grafana",
        "name": "Grafana",
        "description": "Dashboards for cluster, application, and platform telemetry.",
        "serviceNames": ["monitoring-grafana", "grafana", "prometheus-grafana", "kube-prometheus-stack-grafana"],
        "healthPath": "/api/health",
    },
    {
        "id": "prometheus",
        "name": "Prometheus",
        "description": "Metrics collection, PromQL query, and target health.",
        "serviceNames": [
            "monitoring-kube-prometheus-prometheus",
            "prometheus",
            "prometheus-server",
            "prometheus-operated",
            "kube-prometheus-stack-prometheus",
        ],
        "healthPath": "/-/healthy",
    },
]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _scheme_for_port(port: Any, port_name: str = "") -> str:
    try:
        port_number = int(port)
    except (TypeError, ValueError):
        port_number = 80
    return "https" if port_number == 443 or "https" in port_name.lower() else "http"


def _format_endpoint(host: str, port: Any, port_name: str = "") -> str:
    try:
        port_number = int(port)
    except (TypeError, ValueError):
        port_number = 80

    scheme = _scheme_for_port(port_number, port_name)
    default_port = (scheme == "http" and port_number == 80) or (scheme == "https" and port_number == 443)
    return f"{scheme}://{host}{'' if default_port else f':{port_number}'}"


def _service_ports(raw_service: dict[str, Any]) -> tuple[Any, str]:
    spec = _as_dict(raw_service.get("spec"))
    ports = _as_list(spec.get("ports"))
    first_port = _as_dict(ports[0]) if ports else {}
    return first_port.get("port", 80), str(first_port.get("name", ""))


def _public_url(raw_service: dict[str, Any]) -> str:
    spec = _as_dict(raw_service.get("spec"))
    status = _as_dict(raw_service.get("status"))
    service_port, port_name = _service_ports(raw_service)

    for ingress in _as_list(_as_dict(status.get("loadBalancer")).get("ingress")):
        host = _first_string(_as_dict(ingress).get("ip"), _as_dict(ingress).get("hostname"))
        if host:
            return _format_endpoint(host, service_port, port_name)

    for host in _as_list(spec.get("externalIPs")):
        if isinstance(host, str) and host.strip():
            return _format_endpoint(host.strip(), service_port, port_name)

    return ""


def _internal_url(raw_service: dict[str, Any]) -> str:
    metadata = _as_dict(raw_service.get("metadata"))
    namespace = _first_string(metadata.get("namespace"))
    name = _first_string(metadata.get("name"))
    service_port, port_name = _service_ports(raw_service)
    if not namespace or not name:
        return ""
    return _format_endpoint(f"{name}.{namespace}.svc.cluster.local", service_port, port_name)


def _find_service(api_client, service_names: list[str]) -> dict[str, Any] | None:
    core = client.CoreV1Api(api_client)
    for namespace in COMMON_NAMESPACES:
        for service_name in service_names:
            try:
                raw = core.read_namespaced_service(service_name, namespace)
                return api_client.sanitize_for_serialization(raw)
            except ApiException as exc:
                if exc.status == 404:
                    continue
                raise
    return None


def _health_check(url: str, path: str) -> tuple[str, str]:
    if not url:
        return "not_found", "Service was not found"

    target = f"{url.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=4.0, follow_redirects=False) as http:
            response = http.get(target)
    except httpx.HTTPError as exc:
        return "unhealthy", str(exc)

    if 200 <= response.status_code < 400:
        return "healthy", f"HTTP {response.status_code}"
    return "unhealthy", f"HTTP {response.status_code}"


def _load_declared_providers() -> dict[str, dict[str, Any]]:
    raw = os.environ.get("OBSERVABILITY_PROVIDERS_JSON", "").strip()
    if not raw or raw in ("null", "[]"):
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid OBSERVABILITY_PROVIDERS_JSON: %s", exc)
        return {}
    if not isinstance(parsed, list):
        return {}

    by_id: dict[str, dict[str, Any]] = {}
    allowed = {tool["id"] for tool in OBSERVABILITY_TOOLS}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider", "")).strip().lower()
        url = str(entry.get("url", "")).strip()
        if not provider or provider not in allowed or not url:
            continue
        by_id[provider] = {"url": url, "label": str(entry.get("label", "")).strip()}
    return by_id


def _tool_summary(api_client, definition: dict[str, Any], declared: dict[str, Any] | None) -> dict[str, Any]:
    if declared:
        return {
            "id": definition["id"],
            "name": declared.get("label") or definition["name"],
            "description": definition["description"],
            "available": True,
            "status": "declared",
            "source": "chart",
            "healthMessage": "Declared in Helm chart values",
            "namespace": "",
            "serviceName": "",
            "publicUrl": declared["url"],
            "internalUrl": "",
        }

    raw_service = _find_service(api_client, definition["serviceNames"])
    if raw_service is None:
        return {
            "id": definition["id"],
            "name": definition["name"],
            "description": definition["description"],
            "available": False,
            "status": "not_found",
            "source": "cluster",
            "healthMessage": "Service was not found",
            "namespace": "",
            "serviceName": "",
            "publicUrl": "",
            "internalUrl": "",
        }

    metadata = _as_dict(raw_service.get("metadata"))
    internal_url = _internal_url(raw_service)
    status, health_message = _health_check(internal_url, definition["healthPath"])

    return {
        "id": definition["id"],
        "name": definition["name"],
        "description": definition["description"],
        "available": True,
        "status": status,
        "source": "cluster",
        "healthMessage": health_message,
        "namespace": metadata.get("namespace", ""),
        "serviceName": metadata.get("name", ""),
        "publicUrl": _public_url(raw_service),
        "internalUrl": internal_url,
    }


def get_observability_summary() -> dict[str, Any]:
    api_client = get_base_api_client()
    declared = _load_declared_providers()
    tools = [
        _tool_summary(api_client, definition, declared.get(definition["id"]))
        for definition in OBSERVABILITY_TOOLS
    ]
    return {"tools": tools}
