import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
APISIX_GROUP = "apisix.apache.org"
APISIX_VERSION = "v2"
AR_PLURAL = "apisixroutes"
_APISIX_SEARCH_NAMESPACES = ["apisix", "istio-ingress", "ingress-apisix"]

_ROUTE_NAME_PATTERNS = [
    lambda n: f"apisix-api-route-{n}",
    lambda n: n,
    lambda n: f"{n}-apisixroute",
    lambda n: f"apisixroute-{n}",
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
        logger.info("Falling back to base client for ApisixRoute read access")
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

    return exposedapi_name in meta.get("name", "")


def derive_exposedapi_name(route_name: str) -> str | None:
    patterns = (
        "apisix-api-route-",
        "apisixroute-",
    )
    for prefix in patterns:
        if route_name.startswith(prefix):
            return route_name[len(prefix):]
    if route_name.endswith("-apisixroute"):
        return route_name[: -len("-apisixroute")]
    return None


def _get_apisixroute_by_name(name: str, namespace: str, custom_api) -> dict | None:
    try:
        return custom_api.get_namespaced_custom_object(
            group=APISIX_GROUP, version=APISIX_VERSION,
            namespace=namespace, plural=AR_PLURAL, name=name,
        )
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return None
        raise


def get_apisixroute_for_exposedapi(exposedapi_name: str, user: AuthUser, namespace: str = None) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        search_namespaces: list[str] = []
        if namespace:
            search_namespaces.append(namespace)
        for search_ns in _APISIX_SEARCH_NAMESPACES:
            if search_ns not in search_namespaces:
                search_namespaces.append(search_ns)

        for search_ns in search_namespaces:
            for pattern in _ROUTE_NAME_PATTERNS:
                route = _get_apisixroute_by_name(pattern(exposedapi_name), search_ns, custom_api)
                if route:
                    logger.debug("Found ApisixRoute %r for ExposedAPI %r in namespace %r", route["metadata"]["name"], exposedapi_name, search_ns)
                    return route

        for search_ns in search_namespaces:
            try:
                all_routes = custom_api.list_namespaced_custom_object(
                    group=APISIX_GROUP,
                    version=APISIX_VERSION,
                    namespace=search_ns,
                    plural=AR_PLURAL,
                ).get("items", [])
            except client.exceptions.ApiException:
                continue
            for route in all_routes:
                if _matches_exposedapi(route, exposedapi_name):
                    return route

        logger.debug("No ApisixRoute found for ExposedAPI %r", exposedapi_name)
        return None

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("ApisixRoute read denied for exposedapi=%s namespace=%r", exposedapi_name, namespace)
            return None
        raise


def list_apisixroutes(user: AuthUser, namespace: str = None) -> list[dict]:
    def _list(custom_api: client.CustomObjectsApi) -> list[dict]:
        search_namespaces = [namespace] if namespace else list(_APISIX_SEARCH_NAMESPACES)
        items: list[dict] = []
        seen: set[tuple[str, str]] = set()

        for search_ns in search_namespaces:
            try:
                response = custom_api.list_namespaced_custom_object(
                    group=APISIX_GROUP,
                    version=APISIX_VERSION,
                    namespace=search_ns,
                    plural=AR_PLURAL,
                )
            except client.exceptions.ApiException:
                continue

            for route in response.get("items", []):
                meta = route.get("metadata", {})
                key = (meta.get("namespace", search_ns), meta.get("name", ""))
                if key in seen:
                    continue
                seen.add(key)
                items.append(route)

        return items

    try:
        return _call_with_fallback(user, _list)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("ApisixRoute list denied for namespace=%r", namespace)
            return []
        raise


def extract_plugin_config_names(apisixroute: dict) -> list[str]:
    http_rules = apisixroute.get("spec", {}).get("http", [])
    names: list[str] = []
    for rule in http_rules:
        name = rule.get("plugin_config_name")
        if name and name not in names:
            names.append(name)
    return names


def extract_apisixroute_details(apisixroute: dict) -> dict:
    http_rules = apisixroute.get("spec", {}).get("http", [])
    paths: list[str] = []
    backends: list[str] = []

    for rule in http_rules:
        match = rule.get("match", {})
        for path in match.get("paths", []):
            if isinstance(path, str) and path:
                paths.append(path)

        for backend in rule.get("backends", []):
            service_name = backend.get("serviceName")
            service_port = backend.get("servicePort")
            if service_name:
                backends.append(f"{service_name}:{service_port}" if service_port else service_name)

    return {
        "paths": paths,
        "pluginConfigNames": extract_plugin_config_names(apisixroute),
        "backendRefs": backends,
        "rulesCount": len(http_rules),
    }
