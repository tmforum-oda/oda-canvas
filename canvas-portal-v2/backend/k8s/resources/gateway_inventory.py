import logging
from collections import defaultdict

from kubernetes import client

from auth.models import AuthUser
from k8s.canvas_detector import get_cached_canvas_type
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client
from k8s.resources.apisix_plugin_configs import (
    get_apisix_plugin_config_for_exposedapi,
    summarize_apisix_plugins,
)
from k8s.resources.apisixroutes import (
    derive_exposedapi_name as derive_apisix_exposedapi_name,
    extract_apisixroute_details,
    extract_plugin_config_names,
    get_apisixroute_for_exposedapi,
    list_apisixroutes,
)
from k8s.resources.httproutes import (
    derive_exposedapi_name as derive_httproute_exposedapi_name,
    extract_httproute_details,
    extract_plugin_names_from_httproute,
    get_httproute_for_exposedapi,
    list_httproutes,
)
from k8s.resources.kong_plugins import get_kong_plugin, summarize_kong_plugin
from k8s.resources.virtualservices import (
    extract_virtualservice_details,
    get_virtualservice_for_exposedapi,
    list_virtualservices,
)

logger = logging.getLogger(__name__)

ODA_GROUP = "oda.tmforum.org"
ODA_VERSION = "v1beta3"
EXPOSEDAPIS_PLURAL = "exposedapis"

_CANVAS_TYPE_PRIORITY = {
    "kong": 0,
    "apisix": 1,
    "istio": 2,
}

_RESOURCE_KIND_PRIORITY = {
    "HTTPRoute": 0,
    "ApisixRoute": 1,
    "VirtualService": 2,
}


def _list_exposedapis(user: AuthUser, namespace: str | None = None) -> list[dict]:
    def _list(custom_api: client.CustomObjectsApi):
        if namespace:
            return custom_api.list_namespaced_custom_object(
                group=ODA_GROUP,
                version=ODA_VERSION,
                namespace=namespace,
                plural=EXPOSEDAPIS_PLURAL,
            )
        return custom_api.list_cluster_custom_object(
            group=ODA_GROUP,
            version=ODA_VERSION,
            plural=EXPOSEDAPIS_PLURAL,
        )

    try:
        response = _list(client.CustomObjectsApi(get_impersonated_client(user)))
    except client.exceptions.ApiException as e:
        if e.status != 403:
            raise
        logger.info("Falling back to base client for ExposedAPI read access")
        response = _list(client.CustomObjectsApi(get_base_api_client()))
    return response.get("items", [])


def _build_exposedapi_index(items: list[dict]) -> tuple[dict[tuple[str, str], dict], dict[str, list[dict]]]:
    by_ref: dict[tuple[str, str], dict] = {}
    by_name: dict[str, list[dict]] = defaultdict(list)

    for item in items:
        metadata = item.get("metadata", {})
        status = item.get("status", {})
        api_status = status.get("apiStatus", {})
        impl_status = status.get("implementation", {})
        summary = {
            "name": metadata.get("name", ""),
            "namespace": metadata.get("namespace", ""),
            "url": api_status.get("url"),
            "status": "ready" if impl_status.get("ready") else "notReady",
        }
        by_ref[(summary["namespace"], summary["name"])] = summary
        by_name[summary["name"]].append(summary)

    return by_ref, by_name


def _resource_ref(resource: dict) -> tuple[str, str]:
    metadata = resource.get("metadata", {})
    return metadata.get("namespace", ""), metadata.get("name", "")


def _resolve_related_exposedapi(
    resource: dict,
    derived_name: str | None,
    by_ref: dict[tuple[str, str], dict],
    by_name: dict[str, list[dict]],
) -> dict | None:
    metadata = resource.get("metadata", {})
    namespace = metadata.get("namespace", "")
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})

    candidate_names: list[str] = []
    candidate_pairs: list[tuple[str | None, str]] = []

    for owner in metadata.get("ownerReferences", []):
        if owner.get("kind") == "ExposedAPI" and owner.get("name"):
            candidate_pairs.append((namespace, owner["name"]))

    for key in (
        "oda.tmforum.org/exposedapi",
        "app.kubernetes.io/name",
    ):
        value = labels.get(key) or annotations.get(key)
        if value:
            candidate_pairs.append((namespace, value))
            candidate_names.append(value)

    if derived_name:
        candidate_pairs.append((namespace, derived_name))
        candidate_names.append(derived_name)

    for candidate_ns, candidate_name in candidate_pairs:
        if candidate_ns and (candidate_ns, candidate_name) in by_ref:
            return by_ref[(candidate_ns, candidate_name)]

    for candidate_name in candidate_names:
        matches = by_name.get(candidate_name, [])
        if len(matches) == 1:
            return matches[0]

    return None


def _collect_kong_policies(route: dict, api_namespace: str | None, user: AuthUser) -> list[dict]:
    metadata = route.get("metadata", {})
    namespaces = [metadata.get("namespace", "")]
    if api_namespace and api_namespace not in namespaces:
        namespaces.append(api_namespace)

    policies: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for plugin_name in extract_plugin_names_from_httproute(route):
        for namespace in namespaces:
            if not namespace:
                continue
            plugin = get_kong_plugin(plugin_name, namespace, user)
            if not plugin:
                continue
            summary = summarize_kong_plugin(plugin)
            key = (
                summary.get("namespace", ""),
                summary.get("name", ""),
                summary.get("pluginType", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            policies.append(summary)
            break

    return policies


def _collect_apisix_policies(route: dict, api_namespace: str | None, exposedapi_name: str, user: AuthUser) -> list[dict]:
    plugin_config = get_apisix_plugin_config_for_exposedapi(
        exposedapi_name,
        user,
        namespace=api_namespace,
        plugin_config_names=extract_plugin_config_names(route),
    )
    if not plugin_config:
        return []
    return summarize_apisix_plugins(plugin_config)


def _build_binding(
    *,
    kind: str,
    group: str,
    canvas_type: str,
    resource: dict,
    details: dict,
    related_exposed_api: dict | None,
    policies: list[dict] | None = None,
) -> dict:
    metadata = resource.get("metadata", {})
    return {
        "kind": kind,
        "name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "group": group,
        "apiVersion": resource.get("apiVersion", ""),
        "canvasType": canvas_type,
        "details": details,
        "relatedExposedApi": related_exposed_api,
        "policies": policies or [],
    }


def build_binding_from_virtualservice(virtualservice: dict, related_exposed_api: dict | None = None) -> dict:
    return _build_binding(
        kind="VirtualService",
        group="networking.istio.io",
        canvas_type="istio",
        resource=virtualservice,
        details=extract_virtualservice_details(virtualservice),
        related_exposed_api=related_exposed_api,
    )


def build_binding_from_httproute(route: dict, user: AuthUser, related_exposed_api: dict | None = None) -> dict:
    return _build_binding(
        kind="HTTPRoute",
        group="gateway.networking.k8s.io",
        canvas_type="kong",
        resource=route,
        details=extract_httproute_details(route),
        related_exposed_api=related_exposed_api,
        policies=_collect_kong_policies(route, related_exposed_api.get("namespace") if related_exposed_api else None, user),
    )


def build_binding_from_apisixroute(route: dict, user: AuthUser, related_exposed_api: dict | None = None) -> dict:
    exposedapi_name = related_exposed_api.get("name") if related_exposed_api else derive_apisix_exposedapi_name(route.get("metadata", {}).get("name", ""))
    return _build_binding(
        kind="ApisixRoute",
        group="apisix.apache.org",
        canvas_type="apisix",
        resource=route,
        details=extract_apisixroute_details(route),
        related_exposed_api=related_exposed_api,
        policies=_collect_apisix_policies(
            route,
            related_exposed_api.get("namespace") if related_exposed_api else None,
            exposedapi_name or "",
            user,
        ) if exposedapi_name else [],
    )


def select_primary_binding(bindings: list[dict]) -> dict | None:
    if not bindings:
        return None

    preferred_canvas_type = get_cached_canvas_type()

    def binding_sort_key(binding: dict) -> tuple[int, int, str, str]:
        canvas_type = binding.get("canvasType")
        if preferred_canvas_type and canvas_type == preferred_canvas_type:
            preferred_rank = -1
        else:
            preferred_rank = _CANVAS_TYPE_PRIORITY.get(canvas_type, 99)

        return (
            preferred_rank,
            _RESOURCE_KIND_PRIORITY.get(binding.get("kind"), 99),
            binding.get("namespace", ""),
            binding.get("name", ""),
        )

    return sorted(bindings, key=binding_sort_key)[0]


def merge_policies(bindings: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for binding in bindings:
        for policy in binding.get("policies", []):
            key = (
                policy.get("namespace", ""),
                policy.get("name", ""),
                policy.get("pluginType", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(policy)

    return merged


def find_related_gateway_bindings_for_exposedapi(exposedapi_name: str, namespace: str, user: AuthUser) -> list[dict]:
    related_api = {"name": exposedapi_name, "namespace": namespace}
    bindings: list[dict] = []

    if virtualservice := get_virtualservice_for_exposedapi(exposedapi_name, namespace, user):
        bindings.append(build_binding_from_virtualservice(virtualservice, related_api))

    if httproute := get_httproute_for_exposedapi(exposedapi_name, namespace, user):
        bindings.append(build_binding_from_httproute(httproute, user, related_api))

    if apisix_route := get_apisixroute_for_exposedapi(exposedapi_name, user, namespace=namespace):
        bindings.append(build_binding_from_apisixroute(apisix_route, user, related_api))

    return sorted(
        bindings,
        key=lambda binding: (
            _RESOURCE_KIND_PRIORITY.get(binding.get("kind"), 99),
            binding.get("namespace", ""),
            binding.get("name", ""),
        ),
    )


def list_gateway_inventory(user: AuthUser, namespace: str | None = None) -> list[dict]:
    exposedapis = _list_exposedapis(user, namespace)
    by_ref, by_name = _build_exposedapi_index(exposedapis)

    items: list[dict] = []

    for virtualservice in list_virtualservices(namespace, user):
        related = _resolve_related_exposedapi(
            virtualservice,
            virtualservice.get("metadata", {}).get("name", ""),
            by_ref,
            by_name,
        )
        items.append(build_binding_from_virtualservice(virtualservice, related))

    for route in list_httproutes(namespace, user):
        related = _resolve_related_exposedapi(
            route,
            derive_httproute_exposedapi_name(route.get("metadata", {}).get("name", "")),
            by_ref,
            by_name,
        )
        items.append(build_binding_from_httproute(route, user, related))

    for route in list_apisixroutes(user, namespace):
        related = _resolve_related_exposedapi(
            route,
            derive_apisix_exposedapi_name(route.get("metadata", {}).get("name", "")),
            by_ref,
            by_name,
        )
        items.append(build_binding_from_apisixroute(route, user, related))

    return sorted(
        items,
        key=lambda item: (
            _CANVAS_TYPE_PRIORITY.get(item.get("canvasType"), 99),
            item.get("namespace", ""),
            item.get("name", ""),
        ),
    )
