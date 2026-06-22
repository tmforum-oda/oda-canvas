import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
ISTIO_GROUP = "networking.istio.io"
ISTIO_VERSION = "v1alpha3"
VS_PLURAL = "virtualservices"


def _get_custom_api(user: AuthUser, use_base_client: bool = False) -> client.CustomObjectsApi:
    api_client = get_base_api_client() if use_base_client else get_impersonated_client(user)
    return client.CustomObjectsApi(api_client)


def _call_with_fallback(user: AuthUser, operation):
    try:
        return operation(_get_custom_api(user))
    except client.exceptions.ApiException as e:
        if e.status != 403:
            raise
        logger.info("Falling back to base client for VirtualService read access")
        return operation(_get_custom_api(user, use_base_client=True))


def _matches_exposedapi(virtualservice: dict, exposedapi_name: str) -> bool:
    metadata = virtualservice.get("metadata", {})
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})

    for owner in metadata.get("ownerReferences", []):
        if owner.get("kind") == "ExposedAPI" and owner.get("name") == exposedapi_name:
            return True

    if labels.get("oda.tmforum.org/exposedapi") == exposedapi_name:
        return True
    if labels.get("app.kubernetes.io/name") == exposedapi_name:
        return True
    if annotations.get("oda.tmforum.org/exposedapi") == exposedapi_name:
        return True

    return metadata.get("name") == exposedapi_name


def get_virtualservice_for_exposedapi(exposedapi_name: str, namespace: str, user: AuthUser) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        try:
            return custom_api.get_namespaced_custom_object(
                group=ISTIO_GROUP,
                version=ISTIO_VERSION,
                namespace=namespace,
                plural=VS_PLURAL,
                name=exposedapi_name,
            )
        except client.exceptions.ApiException as e:
            if e.status == 404:
                response = custom_api.list_namespaced_custom_object(
                    group=ISTIO_GROUP,
                    version=ISTIO_VERSION,
                    namespace=namespace,
                    plural=VS_PLURAL,
                )
                for virtualservice in response.get("items", []):
                    if _matches_exposedapi(virtualservice, exposedapi_name):
                        return virtualservice
                return None
            raise

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("VirtualService read denied for %s/%s", namespace, exposedapi_name)
            return None
        raise


def list_virtualservices(namespace: str | None, user: AuthUser) -> list[dict]:
    def _list(custom_api: client.CustomObjectsApi):
        if namespace:
            return custom_api.list_namespaced_custom_object(
                group=ISTIO_GROUP,
                version=ISTIO_VERSION,
                namespace=namespace,
                plural=VS_PLURAL,
            )
        return custom_api.list_cluster_custom_object(
            group=ISTIO_GROUP,
            version=ISTIO_VERSION,
            plural=VS_PLURAL,
        )

    try:
        response = _call_with_fallback(user, _list)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("VirtualService list denied for namespace=%r", namespace)
            return []
        raise
    return response.get("items", [])


def extract_virtualservice_details(virtualservice: dict) -> dict:
    spec = virtualservice.get("spec", {})
    paths: list[str] = []
    destinations: list[str] = []

    for http_rule in spec.get("http", []):
        for match in http_rule.get("match", []):
            uri = match.get("uri", {})
            for key in ("prefix", "exact", "regex"):
                value = uri.get(key)
                if value:
                    paths.append(value)
                    break

        for route in http_rule.get("route", []):
            destination = route.get("destination", {})
            host = destination.get("host")
            port = destination.get("port", {}).get("number")
            if host:
                destinations.append(f"{host}:{port}" if port else host)

    return {
        "hosts": spec.get("hosts", []),
        "gateways": spec.get("gateways", []),
        "paths": paths,
        "backendRefs": destinations,
        "rulesCount": len(spec.get("http", [])),
    }
