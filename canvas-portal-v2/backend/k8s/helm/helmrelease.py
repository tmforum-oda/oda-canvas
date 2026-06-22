from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

FLUX_GROUP = "helm.toolkit.fluxcd.io"
FLUX_VERSION = "v2beta1"
HR_PLURAL = "helmreleases"


def create_helmrelease(user: AuthUser, release_name: str, chart_name: str, chart_version: str, source_ref_name: str, namespace: str, values: dict = None) -> dict:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    body = {
        "apiVersion": f"{FLUX_GROUP}/{FLUX_VERSION}", "kind": "HelmRelease",
        "metadata": {"name": release_name, "namespace": namespace},
        "spec": {
            "interval": "5m",
            "chart": {"spec": {"chart": chart_name, "version": chart_version, "sourceRef": {"kind": "HelmRepository", "name": source_ref_name, "namespace": namespace}}},
            "values": values or {},
        },
    }
    return custom_api.create_namespaced_custom_object(group=FLUX_GROUP, version=FLUX_VERSION, namespace=namespace, plural=HR_PLURAL, body=body)


def delete_helmrelease(user: AuthUser, release_name: str, namespace: str) -> None:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    custom_api.delete_namespaced_custom_object(group=FLUX_GROUP, version=FLUX_VERSION, namespace=namespace, plural=HR_PLURAL, name=release_name)


def list_helmreleases(user: AuthUser, namespace: str = None) -> list[dict]:
    api_client = get_impersonated_client(user)
    custom_api = client.CustomObjectsApi(api_client)
    if namespace:
        response = custom_api.list_namespaced_custom_object(group=FLUX_GROUP, version=FLUX_VERSION, namespace=namespace, plural=HR_PLURAL)
    else:
        response = custom_api.list_cluster_custom_object(group=FLUX_GROUP, version=FLUX_VERSION, plural=HR_PLURAL)
    return response.get("items", [])
