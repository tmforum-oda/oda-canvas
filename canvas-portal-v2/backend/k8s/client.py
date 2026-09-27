import base64
import logging
import tempfile
from functools import lru_cache
from kubernetes import client, config
from kubernetes.client import ApiClient, Configuration
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def build_base_api_client() -> ApiClient:
    if settings.K8S_MODE == "incluster":
        config.load_incluster_config()
        logger.info("K8s client: in-cluster mode")
        return ApiClient()
    else:
        if not settings.K8S_REMOTE_API_URL:
            raise ValueError("K8S_REMOTE_API_URL required when K8S_MODE=outofcluster")
        configuration = Configuration()
        configuration.host = settings.K8S_REMOTE_API_URL
        configuration.api_key["authorization"] = settings.K8S_REMOTE_SA_TOKEN
        configuration.api_key_prefix["authorization"] = "Bearer"
        if settings.K8S_REMOTE_CA_CERT:
            ca_cert_data = base64.b64decode(settings.K8S_REMOTE_CA_CERT)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".crt")
            tmp.write(ca_cert_data)
            tmp.close()
            configuration.ssl_ca_cert = tmp.name
        else:
            logger.warning("K8S_REMOTE_CA_CERT not set - disabling TLS verification")
            configuration.verify_ssl = False
        logger.info("K8s client: out-of-cluster -> %s", settings.K8S_REMOTE_API_URL)
        return ApiClient(configuration)


@lru_cache()
def get_base_api_client() -> ApiClient:
    return build_base_api_client()
