import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
KONG_GROUP = "configuration.konghq.com"
KONG_VERSION = "v1"
KP_PLURAL = "kongplugins"


def _get_custom_api(user: AuthUser, use_base_client: bool = False) -> client.CustomObjectsApi:
    api_client = get_base_api_client() if use_base_client else get_impersonated_client(user)
    return client.CustomObjectsApi(api_client)


def _call_with_fallback(user: AuthUser, operation):
    try:
        return operation(_get_custom_api(user))
    except client.exceptions.ApiException as e:
        if e.status != 403:
            raise
        logger.info("Falling back to base client for KongPlugin read access")
        return operation(_get_custom_api(user, use_base_client=True))


def get_kong_plugin(plugin_name: str, namespace: str, user: AuthUser) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        try:
            return custom_api.get_namespaced_custom_object(
                group=KONG_GROUP,
                version=KONG_VERSION,
                namespace=namespace,
                plural=KP_PLURAL,
                name=plugin_name,
            )
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return None
            raise

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("KongPlugin read denied for %s/%s", namespace, plugin_name)
            return None
        raise


def list_kong_plugins_for_exposedapi(plugin_names: list[str], namespace: str, user: AuthUser) -> list[dict]:
    return [p for name in plugin_names if (p := get_kong_plugin(name, namespace, user))]


def summarize_kong_plugin(plugin: dict) -> dict:
    metadata = plugin.get("metadata", {})
    return {
        "name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "pluginType": plugin.get("plugin", ""),
        "config": plugin.get("config", {}),
    }
