import kopf
import logging
import os


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
logger.info('Logging set to %s', logging_level)
logger.debug('debug logging is on')


CICD_BUILD_TIME = os.getenv('CICD_BUILD_TIME')
GIT_COMMIT_SHA = os.getenv('GIT_COMMIT_SHA')
if CICD_BUILD_TIME:
    logger.info(f'CICD_BUILD_TIME=%s', CICD_BUILD_TIME)
if GIT_COMMIT_SHA:
    logger.info(f'GIT_COMMIT_SHA=%s', GIT_COMMIT_SHA)



@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.peering.priority = 110
    settings.peering.name = "dependentapi"
    settings.watching.server_timeout = 1 * 60



# triggered when an oda.tmforum.org dependentapi resource is created or updated 
@kopf.on.resume(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.create(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
@kopf.on.update(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiCreate(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.info( f"Create/Update  called with name {name} in namespace {namespace}")
    logger.debug(f"Create/Update  called with body: {body}")

    
 
# when an oda.tmforum.org api resource is deleted
@kopf.on.delete(DEPAPI_GROUP, DEPAPI_VERSION, DEPAPI_PLURAL, retries=5)
async def dependentApiDelete(meta, spec, status, body, namespace, labels, name, **kwargs):

    logger.info( f"Delete         called with name {name} in namespace {namespace}")
    logger.debug(f"Delete         called with body: {body}")

