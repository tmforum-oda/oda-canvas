from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

ODA_GROUP = "oda.tmforum.org"
ODA_VERSION = "v1beta3"
COMPONENTS_PLURAL = "components"


def list_components(user: AuthUser) -> list[dict]:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    response = custom_api.list_cluster_custom_object(group=ODA_GROUP, version=ODA_VERSION, plural=COMPONENTS_PLURAL)
    return response.get("items", [])


def get_component(name: str, namespace: str, user: AuthUser) -> dict:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    return custom_api.get_namespaced_custom_object(group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=COMPONENTS_PLURAL, name=name)


def list_components_in_namespace(namespace: str, user: AuthUser) -> list[dict]:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    response = custom_api.list_namespaced_custom_object(group=ODA_GROUP, version=ODA_VERSION, namespace=namespace, plural=COMPONENTS_PLURAL)
    return response.get("items", [])
