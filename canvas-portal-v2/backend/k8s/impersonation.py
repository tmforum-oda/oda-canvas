import logging
from kubernetes.client import ApiClient
from auth.models import AuthUser
from k8s.client import get_base_api_client

logger = logging.getLogger(__name__)


def get_impersonated_client(user: AuthUser) -> ApiClient:
    logger.debug("K8s request authenticated as %s; using backend service account", user.username)
    return get_base_api_client()
