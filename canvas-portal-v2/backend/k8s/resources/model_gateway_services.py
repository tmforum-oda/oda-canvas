import json
from typing import Any

from kubernetes import client
from kubernetes.client.exceptions import ApiException

from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

MGS_GROUP = "oda.tmforum.org"
MGS_VERSION = "v1alpha1"
MGS_PLURAL = "modelgatewayservices"
MGS_CRD_NAME = "modelgatewayservices.oda.tmforum.org"


def model_gateway_services_available() -> bool:
    api_client = get_base_api_client()
    api = client.ApiextensionsV1Api(api_client)
    try:
        api.read_custom_resource_definition(MGS_CRD_NAME)
        return True
    except client.exceptions.ApiException as exc:
        if exc.status == 404:
            return False
        if exc.status == 403:
            return _model_gateway_resource_listable(api_client)
        raise


def _custom_api(api_client) -> client.CustomObjectsApi:
    return client.CustomObjectsApi(api_client)


def _crd_api(api_client) -> client.ApiextensionsV1Api:
    return client.ApiextensionsV1Api(api_client)


def _model_gateway_resource_listable(api_client) -> bool:
    try:
        _custom_api(api_client).list_cluster_custom_object(
            group=MGS_GROUP,
            version=MGS_VERSION,
            plural=MGS_PLURAL,
            limit=1,
        )
        return True
    except client.exceptions.ApiException as exc:
        if exc.status == 404:
            return False
        raise


def get_model_gateway_service_schema() -> dict[str, Any]:
    api_client = get_base_api_client()
    raw = api_client.sanitize_for_serialization(_crd_api(api_client).read_custom_resource_definition(MGS_CRD_NAME))
    versions = raw.get("spec", {}).get("versions", []) or []
    version = next((item for item in versions if item.get("name") == MGS_VERSION), None)
    if version is None:
        version = next((item for item in versions if item.get("storage")), None)
    if version is None and versions:
        version = versions[0]

    schema = (version or {}).get("schema", {}).get("openAPIV3Schema", {}) or {}
    spec_schema = schema.get("properties", {}).get("spec", {}) or {}
    return {
        "apiVersion": f"{MGS_GROUP}/{MGS_VERSION}",
        "kind": "ModelGatewayService",
        "version": (version or {}).get("name", MGS_VERSION),
        "scope": raw.get("spec", {}).get("scope", "Namespaced"),
        "schema": schema,
        "specSchema": spec_schema,
    }


def format_k8s_api_exception(exc: ApiException) -> str:
    if not exc.body:
        return exc.reason or "Kubernetes API error"
    try:
        body = json.loads(exc.body)
    except (TypeError, json.JSONDecodeError):
        return exc.body

    causes = body.get("details", {}).get("causes", []) or []
    cause_messages = []
    for cause in causes:
        field = cause.get("field")
        message = cause.get("message")
        if field and message:
            cause_messages.append(f"{field}: {message}")
        elif message:
            cause_messages.append(str(message))
    if cause_messages:
        return "; ".join(cause_messages)
    return body.get("message") or exc.reason or "Kubernetes API error"


def _model_names_from_spec(spec: dict[str, Any]) -> list[str]:
    models = spec.get("dependentAIModels", [])
    if not isinstance(models, list):
        return []
    names: list[str] = []
    for model in models:
        if not isinstance(model, dict):
            continue
        name = str(model.get("name", "")).strip()
        if name:
            names.append(name)
    return names


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _format_http_endpoint(host: str, port: Any, port_name: str = "") -> str:
    try:
        port_number = int(port)
    except (TypeError, ValueError):
        port_number = 80

    scheme = "https" if port_number == 443 or "https" in port_name.lower() else "http"
    default_port = (scheme == "http" and port_number == 80) or (scheme == "https" and port_number == 443)
    port_suffix = "" if default_port else f":{port_number}"
    return f"{scheme}://{host}{port_suffix}"


def _service_endpoint_url(raw_service: dict[str, Any]) -> str:
    spec = _as_dict(raw_service.get("spec"))
    status = _as_dict(raw_service.get("status"))
    ports = _as_list(spec.get("ports"))
    first_port = _as_dict(ports[0]) if ports else {}
    service_port = first_port.get("port", 80)
    port_name = str(first_port.get("name", ""))

    load_balancer = _as_dict(status.get("loadBalancer"))
    for ingress in _as_list(load_balancer.get("ingress")):
        ingress_data = _as_dict(ingress)
        host = _first_string(ingress_data.get("ip"), ingress_data.get("hostname"))
        if host:
            return _format_http_endpoint(host, service_port, port_name)

    for host in _as_list(spec.get("externalIPs")):
        if isinstance(host, str) and host.strip():
            return _format_http_endpoint(host.strip(), service_port, port_name)

    cluster_ip = _first_string(spec.get("clusterIP"))
    if cluster_ip and cluster_ip.lower() != "none":
        return _format_http_endpoint(cluster_ip, service_port, port_name)

    return ""


def _candidate_service_names(name: str, spec: dict[str, Any], status: dict[str, Any]) -> list[str]:
    gateway = _as_dict(spec.get("gateway"))
    candidates = [
        status.get("proxyServiceName"),
        status.get("gatewayServiceName"),
        status.get("serviceName"),
        gateway.get("proxyServiceName"),
        gateway.get("serviceName"),
        f"{name}-proxy",
    ]
    result: list[str] = []
    for candidate in candidates:
        value = _first_string(candidate)
        if value and value not in result:
            result.append(value)
    return result


def _proxy_service_endpoint_url(api_client, namespace: str, name: str, spec: dict[str, Any], status: dict[str, Any]) -> str:
    if not api_client or not namespace or not name:
        return ""

    api = client.CoreV1Api(api_client)
    for service_name in _candidate_service_names(name, spec, status):
        try:
            raw_service = api_client.sanitize_for_serialization(api.read_namespaced_service(service_name, namespace))
        except client.exceptions.ApiException:
            continue

        endpoint = _service_endpoint_url(raw_service)
        if endpoint:
            return endpoint

    return ""


def _endpoint_from_status_or_spec(spec: dict[str, Any], status: dict[str, Any]) -> str:
    gateway = _as_dict(spec.get("gateway"))
    endpoint = _first_string(
        status.get("gatewayEndpoint"),
        status.get("endpointUrl"),
        status.get("endpointURL"),
        status.get("endpoint"),
        status.get("url"),
        status.get("serviceEndpoint"),
        status.get("proxyUrl"),
        status.get("proxyURL"),
        gateway.get("endpointUrl"),
        gateway.get("endpointURL"),
        gateway.get("endpoint"),
        gateway.get("baseUrl"),
        gateway.get("baseURL"),
        gateway.get("url"),
        gateway.get("externalUrl"),
        gateway.get("externalURL"),
    )
    if endpoint:
        return endpoint

    endpoints = status.get("endpoints")
    if isinstance(endpoints, dict):
        return _first_string(endpoints.get("url"), endpoints.get("endpointUrl"), endpoints.get("endpoint"), endpoints.get("address"))
    if isinstance(endpoints, list):
        for item in endpoints:
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                endpoint = _first_string(item.get("url"), item.get("endpointUrl"), item.get("endpoint"), item.get("address"))
                if endpoint:
                    return endpoint

    return ""


def summarize_model_gateway_service(raw: dict[str, Any], api_client=None) -> dict[str, Any]:
    metadata = raw.get("metadata", {}) or {}
    spec = raw.get("spec", {}) or {}
    status = raw.get("status", {}) or {}
    spec_model_names = _model_names_from_spec(spec)
    status_model_names = status.get("modelNames", "")
    endpoint_url = _endpoint_from_status_or_spec(spec, status) or _proxy_service_endpoint_url(
        api_client,
        metadata.get("namespace", ""),
        metadata.get("name", ""),
        spec,
        status,
    )
    return {
        "apiVersion": raw.get("apiVersion", f"{MGS_GROUP}/{MGS_VERSION}"),
        "kind": raw.get("kind", "ModelGatewayService"),
        "name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "createdAt": metadata.get("creationTimestamp") or metadata.get("creation_timestamp") or "",
        "resourceVersion": metadata.get("resourceVersion", ""),
        "environmentalFunction": spec.get("environmentalFunction", {}) or {},
        "dependentAIModels": spec.get("dependentAIModels", []) or [],
        "modelNames": status_model_names or ", ".join(spec_model_names),
        "trafficSplitStrategy": spec.get("trafficSplitStrategy", ""),
        "gateway": spec.get("gateway", {}) or {},
        "guardrails": spec.get("guardrails", {}) or {},
        "jwtAuth": spec.get("jwtAuth", {}) or {},
        "mcpServers": spec.get("mcpServers", []) or [],
        "endpointUrl": endpoint_url,
        "status": status,
        "spec": spec,
    }


def list_model_gateway_services() -> dict[str, Any]:
    if not model_gateway_services_available():
        return {"available": False, "items": []}
    api_client = get_base_api_client()
    response = _custom_api(api_client).list_cluster_custom_object(
        group=MGS_GROUP,
        version=MGS_VERSION,
        plural=MGS_PLURAL,
    )
    return {
        "available": True,
        "items": [summarize_model_gateway_service(item, api_client) for item in response.get("items", [])],
    }


def get_model_gateway_service(namespace: str, name: str) -> dict[str, Any] | None:
    if not model_gateway_services_available():
        return None
    api_client = get_base_api_client()
    try:
        raw = _custom_api(api_client).get_namespaced_custom_object(
            group=MGS_GROUP,
            version=MGS_VERSION,
            namespace=namespace,
            plural=MGS_PLURAL,
            name=name,
        )
    except client.exceptions.ApiException as exc:
        if exc.status == 404:
            return None
        raise
    return summarize_model_gateway_service(raw, api_client)


def create_model_gateway_service(user: AuthUser, namespace: str, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    body = _model_gateway_service_body(namespace, name, spec)
    raw = _custom_api(get_impersonated_client(user)).create_namespaced_custom_object(
        group=MGS_GROUP,
        version=MGS_VERSION,
        namespace=namespace,
        plural=MGS_PLURAL,
        body=body,
    )
    return summarize_model_gateway_service(raw, get_base_api_client())


def _model_gateway_service_body(namespace: str, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": f"{MGS_GROUP}/{MGS_VERSION}",
        "kind": "ModelGatewayService",
        "metadata": {"name": name, "namespace": namespace},
        "spec": spec,
    }


def validate_model_gateway_service(
    user: AuthUser,
    namespace: str,
    name: str,
    spec: dict[str, Any],
    mode: str,
) -> None:
    api = _custom_api(get_impersonated_client(user))
    if mode == "update":
        api.patch_namespaced_custom_object(
            group=MGS_GROUP,
            version=MGS_VERSION,
            namespace=namespace,
            plural=MGS_PLURAL,
            name=name,
            body={"spec": spec},
            dry_run="All",
        )
        return

    api.create_namespaced_custom_object(
        group=MGS_GROUP,
        version=MGS_VERSION,
        namespace=namespace,
        plural=MGS_PLURAL,
        body=_model_gateway_service_body(namespace, name, spec),
        dry_run="All",
    )


def update_model_gateway_service(user: AuthUser, namespace: str, name: str, spec: dict[str, Any]) -> dict[str, Any]:
    raw = _custom_api(get_impersonated_client(user)).patch_namespaced_custom_object(
        group=MGS_GROUP,
        version=MGS_VERSION,
        namespace=namespace,
        plural=MGS_PLURAL,
        name=name,
        body={"spec": spec},
    )
    return summarize_model_gateway_service(raw, get_base_api_client())


def delete_model_gateway_service(user: AuthUser, namespace: str, name: str) -> None:
    _custom_api(get_impersonated_client(user)).delete_namespaced_custom_object(
        group=MGS_GROUP,
        version=MGS_VERSION,
        namespace=namespace,
        plural=MGS_PLURAL,
        name=name,
    )
