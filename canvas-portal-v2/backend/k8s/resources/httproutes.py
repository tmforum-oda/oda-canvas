import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
GATEWAY_GROUP = "gateway.networking.k8s.io"
GATEWAY_VERSION = "v1"
HR_PLURAL = "httproutes"

_ROUTE_NAME_PATTERNS = [
    lambda n: f"kong-api-route-{n}",
    lambda n: n,
    lambda n: f"{n}-httproute",
    lambda n: f"httproute-{n}",
]


def _get_custom_api(user: AuthUser, use_base_client: bool = False) -> client.CustomObjectsApi:
    api_client = get_base_api_client() if use_base_client else get_impersonated_client(user)
    return client.CustomObjectsApi(api_client)


def _call_with_fallback(user: AuthUser, operation):
    try:
        return operation(_get_custom_api(user))
    except client.exceptions.ApiException as e:
        if e.status != 403:
            raise
        logger.info("Falling back to base client for HTTPRoute read access")
        return operation(_get_custom_api(user, use_base_client=True))


def _matches_exposedapi(route: dict, exposedapi_name: str) -> bool:
    meta = route.get("metadata", {})
    labels = meta.get("labels", {})
    annotations = meta.get("annotations", {})

    for owner in meta.get("ownerReferences", []):
        if owner.get("kind") == "ExposedAPI" and owner.get("name") == exposedapi_name:
            return True

    if labels.get("oda.tmforum.org/exposedapi") == exposedapi_name:
        return True
    if labels.get("app.kubernetes.io/name") == exposedapi_name:
        return True
    if annotations.get("oda.tmforum.org/exposedapi") == exposedapi_name:
        return True

    route_name: str = meta.get("name", "")
    if exposedapi_name in route_name:
        return True

    tags_str = annotations.get("konghq.com/tags", "")
    return exposedapi_name in tags_str


def derive_exposedapi_name(route_name: str) -> str | None:
    patterns = (
        "kong-api-route-",
        "httproute-",
    )
    for prefix in patterns:
        if route_name.startswith(prefix):
            return route_name[len(prefix):]
    if route_name.endswith("-httproute"):
        return route_name[: -len("-httproute")]
    return None


def _get_httproute_by_name(name: str, namespace: str, custom_api) -> dict | None:
    try:
        return custom_api.get_namespaced_custom_object(
            group=GATEWAY_GROUP, version=GATEWAY_VERSION,
            namespace=namespace, plural=HR_PLURAL, name=name,
        )
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return None
        raise


def get_httproute_for_exposedapi(exposedapi_name: str, namespace: str, user: AuthUser) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        for pattern in _ROUTE_NAME_PATTERNS:
            route = _get_httproute_by_name(pattern(exposedapi_name), namespace, custom_api)
            if route:
                logger.debug("Found HTTPRoute %r for ExposedAPI %r via name pattern", route["metadata"]["name"], exposedapi_name)
                return route

        try:
            all_routes = custom_api.list_namespaced_custom_object(
                group=GATEWAY_GROUP,
                version=GATEWAY_VERSION,
                namespace=namespace,
                plural=HR_PLURAL,
            ).get("items", [])
        except client.exceptions.ApiException:
            return None

        for route in all_routes:
            if _matches_exposedapi(route, exposedapi_name):
                return route

        logger.debug("No HTTPRoute found for ExposedAPI %r in namespace %r", exposedapi_name, namespace)
        return None

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("HTTPRoute read denied for %s/%s", namespace, exposedapi_name)
            return None
        raise


def list_httproutes(namespace: str | None, user: AuthUser) -> list[dict]:
    def _list(custom_api: client.CustomObjectsApi):
        if namespace:
            return custom_api.list_namespaced_custom_object(
                group=GATEWAY_GROUP,
                version=GATEWAY_VERSION,
                namespace=namespace,
                plural=HR_PLURAL,
            )
        return custom_api.list_cluster_custom_object(
            group=GATEWAY_GROUP,
            version=GATEWAY_VERSION,
            plural=HR_PLURAL,
        )

    try:
        response = _call_with_fallback(user, _list)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("HTTPRoute list denied for namespace=%r", namespace)
            return []
        raise
    return response.get("items", [])


def extract_plugin_names_from_httproute(httproute: dict) -> list[str]:
    annotations = httproute.get("metadata", {}).get("annotations", {})
    plugins_str = annotations.get("konghq.com/plugins", "")
    if not plugins_str:
        return []
    return [p.strip() for p in plugins_str.split(",") if p.strip()]


def extract_httproute_details(httproute: dict) -> dict:
    spec = httproute.get("spec", {})
    rules = spec.get("rules", [])
    hostnames = spec.get("hostnames", [])
    plugin_names = extract_plugin_names_from_httproute(httproute)
    paths = []
    parent_refs = []
    backends = []

    for parent_ref in spec.get("parentRefs", []):
        parent_ns = parent_ref.get("namespace") or httproute.get("metadata", {}).get("namespace", "")
        parent_name = parent_ref.get("name", "")
        if parent_name:
            parent_refs.append(f"{parent_ns}/{parent_name}" if parent_ns else parent_name)

    for rule in rules:
        for match in rule.get("matches", []):
            path_obj = match.get("path", {})
            if path_obj.get("value"):
                paths.append(path_obj["value"])
        for backend in rule.get("backendRefs", []):
            name = backend.get("name")
            namespace = backend.get("namespace") or httproute.get("metadata", {}).get("namespace", "")
            port = backend.get("port")
            if name:
                identifier = f"{namespace}/{name}" if namespace else name
                backends.append(f"{identifier}:{port}" if port else identifier)

    return {
        "hostnames": hostnames,
        "paths": paths,
        "gateways": parent_refs,
        "backendRefs": backends,
        "pluginNames": plugin_names,
        "rulesCount": len(rules),
    }
