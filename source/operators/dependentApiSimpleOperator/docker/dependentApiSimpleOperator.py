import kopf
import logging
import os
import time
import json
import sys
from http.client import HTTPConnection
import base64
import kubernetes
from kubernetes.client.rest import ApiException
from typing import AsyncIterator


DEPAPI_GROUP = 'oda.tmforum.org'
DEPAPI_VERSION = 'v1beta3'
DEPAPI_PLURAL = 'dependentapis'

# https://kopf.readthedocs.io/en/stable/install/

# Setup logging
logging_level = os.environ.get('LOGGING', logging.DEBUG)
kopf_logger = logging.getLogger()
kopf_logger.setLevel(logging.INFO)
logger = logging.getLogger('DependentApiSimpleOperator')
logger.setLevel(int(logging_level))
logger.info(f'Logging set to %s', logging_level)


CICD_BUILD_TIME = os.getenv('CICD_BUILD_TIME')
GIT_COMMIT_SHA = os.getenv('GIT_COMMIT_SHA')
if CICD_BUILD_TIME:
    logger.info(f'CICD_BUILD_TIME=%s', CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f'GIT_COMMIT_SHA=%s', GIT_COMMIT_SHA)

webhook_service_name = os.getenv('WEBHOOK_SERVICE_NAME', 'dummyservicename') 
webhook_service_namespace = os.getenv('WEBHOOK_SERVICE_NAMESPACE', 'dummyservicenamespace') 
webhook_service_port = int(os.getenv('WEBHOOK_SERVICE_PORT', '443'))


# Inheritance: https://github.com/nolar/kopf/blob/main/docs/admission.rst#custom-serverstunnels
# https://github.com/nolar/kopf/issues/785#issuecomment-859931945


class ServiceTunnel:
    async def __call__(
        self, fn: kopf.WebhookFn
    ) -> AsyncIterator[kopf.WebhookClientConfig]:
        container_port = 9443
        server = kopf.WebhookServer(port=container_port, host=f"{webhook_service_name}.{webhook_service_namespace}.svc")
        async for client_config in server(fn):
            client_config["url"] = None
            client_config["service"] = kopf.WebhookClientConfigService(
                name=webhook_service_name, namespace=webhook_service_namespace, port=webhook_service_port
            )
            yield client_config


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.peering.priority = 110
    settings.peering.name = "dependentapi"
    settings.admission.server = ServiceTunnel()
    settings.admission.managed = 'depapi.mutate.kopf'
    settings.watching.server_timeout = 1 * 60



# triggered when an oda.tmforum.org dependentapi resource is created or updated 
@kopf.on.resume(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.create(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.update(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info( f"Create/Update  called with name {name} in namespace {namespace}")
    logging.debug(f"Create/Update  called with body: {body}")

    
 
# when an oda.tmforum.org api resource is deleted
@kopf.on.delete(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logging.info( f"Delete         called with name {name} in namespace {namespace}")
    logging.debug(f"Delete         called with body: {body}")



