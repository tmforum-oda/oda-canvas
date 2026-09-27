import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.client import get_base_api_client
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)
APISIX_GROUP = "apisix.apache.org"
APISIX_VERSION = "v2"
APC_PLURAL = "apisixpluginconfigs"
_APISIX_SEARCH_NAMESPACES = ["apisix", "istio-ingress", "ingress-apisix"]

_CONFIG_NAME_PATTERNS = [
    lambda n: f"combined-apisixpluginconfig-{n}",
    lambda n: f"apisixpluginconfig-{n}",
    lambda n: n,
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
        logger.info("Falling back to base client for ApisixPluginConfig read access")
        return operation(_get_custom_api(user, use_base_client=True))


def get_apisix_plugin_config(config_name: str, user: AuthUser, namespace: str) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        try:
            return custom_api.get_namespaced_custom_object(
                group=APISIX_GROUP,
                version=APISIX_VERSION,
                namespace=namespace,
                plural=APC_PLURAL,
                name=config_name,
            )
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return None
            raise

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("ApisixPluginConfig read denied for %s/%s", namespace, config_name)
            return None
        raise


def get_apisix_plugin_config_for_exposedapi(
    exposedapi_name: str,
    user: AuthUser,
    namespace: str = None,
    plugin_config_names: list[str] | None = None,
) -> dict | None:
    def _lookup(custom_api: client.CustomObjectsApi) -> dict | None:
        search_namespaces: list[str] = []
        if namespace:
            search_namespaces.append(namespace)
        for search_ns in _APISIX_SEARCH_NAMESPACES:
            if search_ns not in search_namespaces:
                search_namespaces.append(search_ns)

        for search_ns in search_namespaces:
            for config_name in plugin_config_names or []:
                try:
                    result = custom_api.get_namespaced_custom_object(
                        group=APISIX_GROUP,
                        version=APISIX_VERSION,
                        namespace=search_ns,
                        plural=APC_PLURAL,
                        name=config_name,
                    )
                    logger.debug(
                        "Found ApisixPluginConfig %r for ExposedAPI %r via explicit route reference in namespace %r",
                        config_name,
                        exposedapi_name,
                        search_ns,
                    )
                    return result
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        continue
                    raise

        for search_ns in search_namespaces:
            for pattern in _CONFIG_NAME_PATTERNS:
                config_name = pattern(exposedapi_name)
                try:
                    result = custom_api.get_namespaced_custom_object(
                        group=APISIX_GROUP,
                        version=APISIX_VERSION,
                        namespace=search_ns,
                        plural=APC_PLURAL,
                        name=config_name,
                    )
                    logger.debug("Found ApisixPluginConfig %r for ExposedAPI %r in namespace %r", config_name, exposedapi_name, search_ns)
                    return result
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        continue
                    raise

        logger.debug("No ApisixPluginConfig found for ExposedAPI %r", exposedapi_name)
        return None

    try:
        return _call_with_fallback(user, _lookup)
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("ApisixPluginConfig read denied for exposedapi=%s namespace=%r", exposedapi_name, namespace)
            return None
        raise


def summarize_apisix_plugins(plugin_config: dict) -> list[dict]:
    plugins = plugin_config.get("spec", {}).get("plugins", [])
    return [
        {
            "pluginType": p.get("name", ""),
            "name": plugin_config.get("metadata", {}).get("name", ""),
            "namespace": plugin_config.get("metadata", {}).get("namespace", ""),
            "enabled": p.get("enable", True),
            "config": p.get("config", {}),
        }
        for p in plugins
    ]
