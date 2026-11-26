from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client


def list_namespaces(user: AuthUser) -> list[str]:
    api_client = get_impersonated_client(user)
    core_api = client.CoreV1Api(api_client)
    response = core_api.list_namespace()
    return [ns.metadata.name for ns in response.items]
