import kopf
import kubernetes.client
import yaml
import logging
from kubernetes.client.rest import ApiException
import os
 
logging_level = os.environ.get('LOGGING',20)
print('Logging set to ',logging_level)
logger = logging.getLogger()
logger.setLevel(int(logging_level)) #Logging level default = INFO


# @kopf.on.resume('oda.tmforum.org', 'v1alpha2', 'components')
@kopf.on.create('oda.tmforum.org', 'v1alpha2', 'components') # called by kopf framework when a component is created
@kopf.on.update('oda.tmforum.org', 'v1alpha2', 'components') # or updated
def securityRoles(meta, spec, status, body, namespace, labels, name, **kwargs):
    logging.info(f"oda.tmforum.org component {name} created/updated with spec: {spec}")
    statusValue = {'identityProvider': 'Keycloak'}
    return statusValue # the return value is added to the status field of the k8s object under securityRoles parameter (corresponds to function name)

@kopf.on.delete('oda.tmforum.org', 'v1alpha2', 'components') # called by kopf framework when a component is deleted
def securityRolesDelete(meta, spec, status, body, namespace, labels, name, **kwargs):
    logging.info(f"oda.tmforum.org component {name} deleted")
    statusValue = {'identityProvider': 'Keycloak'}
