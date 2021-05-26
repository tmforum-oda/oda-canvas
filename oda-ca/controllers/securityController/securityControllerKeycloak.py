import kopf
import logging
import os
import requests
import uuid
import datetime
# import secconkeycloak
from secconkeycloak import Keycloak
from cloudevents.http import CloudEvent, to_structured

# Helper functions ----------

def register_listener(url: str) -> None:
    """
    Register the listener URL with partyRoleManagement for role updates

    Returns nothing, or raises an exception for the caller to catch
    """

    try: # to register the listener
        # pylint: disable=try-except-raise
        # Disabled because we raise immediately deliberately. We want
        # Kopf to handle this and only this error until we come across
        # more errors
        r = requests.post(
            url,
            json = {'callback': 'http://seccon.canvas:5000/listener'})
        r.raise_for_status()
    except RuntimeError:
        raise

def format_cloud_event(message: str, subject: str) -> str:
    """
    Returns a correctly formatted CloudEvents compliant event
    """
    attributes = {
        'specversion' : '1.0',
        'type' : 'org.tmforum.for.type.event.an.invented.burton.brian',
        'source' : 'http://seccon.canvas.svc.cluster.local',
        'subject': subject,
        'id' : str(uuid.uuid4()),
        'time' : datetime.datetime.now().isoformat(),
        'datacontenttype' : 'application/json',
    }

    data = {'message': message}

    event = CloudEvent(attributes, data)
    _, body = to_structured(event)

    return body

# Script setup --------------

logging_level = os.environ.get('LOGGING', logging.INFO)
print('Logging set to ', logging_level)
logger = logging.getLogger('SecurityOperator')
logger.setLevel(int(logging_level))

username = os.environ.get('KEYCLOAK_USER')
password = os.environ.get('KEYCLOAK_PASSWORD')
kcBaseURL = os.environ.get('KEYCLOAK_BASE')
kcRealm = os.environ.get('KEYCLOAK_REALM')

seccon_user = 'seccon'

kc = Keycloak(kcBaseURL)


# Kopf handlers -------------

@kopf.on.update(
    'oda.tmforum.org',
    'v1alpha3',
    'components',
    field='status.summary/status.deployment_status',
    value='In-Progress-SecCon'
)
def security_client_add(meta, spec, status, body, namespace, labels,name, old, new, **kwargs):
    """
    Handler for component create/update
    """
    # del unused-arguments for linting
    del meta, status, body, labels, kwargs

    rooturl = (
        'http://'
        + spec['security']['partyrole']['implementation']
        + '.' + namespace + '.svc.cluster.local:'
        + str(spec['security']['partyrole']['port'])
        + spec['security']['partyrole']['path']
    )
    logger.debug('using component root url: %s', rooturl)
    logger.debug('status.deployment_status = %s -> %s', old, new)

    try: # to authenticate and get a token
        token = kc.get_token(username, password)
    except RuntimeError as e:
        logger.error(format_cloud_event(
            str(e),
            'secCon could not GET Keycloak token'
        ))

    try: # to create the client in Keycloak
        kc.create_client(name, rooturl, token, kcRealm)
    except RuntimeError as e:
        logger.error(format_cloud_event(
            str(e),
            f'secCon could not POST new client {name} in realm {kcRealm}'
        ))
        raise kopf.TemporaryError(
            'Could not add component to Keycloak. Will retry.',
            delay=10
        )
    else:
        logger.info(format_cloud_event(
            f'oda.tmforum.org component {name} created',
            'secCon: component created'
        ))

        try: # to get the list of existing clients
            client_list = kc.get_client_list(token, kcRealm)
        except RuntimeError as e:
            logging.error(format_cloud_event(
                str(e),
                f'security-APIListener could not GET clients for {kcRealm}'
            ))
        else:
            client = client_list[name]

    try: # to create the bootstrap role
        # TODO find security.controllerRole and add_role in {name}
        # 1) GET security.controllerRole from the component
        # 2) add_role for security.controllerRole against component
        # 3) write new function for add_role_to_user
        # 4) create user for seccon
        # 5) add_role_to_user for secCon user

        seccon_role = spec['security']['controllerRole']
        kc.add_role(seccon_role, client, token, kcRealm)
    except RuntimeError as e:
        logging.error(format_cloud_event(
            f'Keycloak add_role failed for {seccon_role} in {name}: {e}',
            'secCon: bootstrap add_role failed'
        ))

    try: # to assign the role to the seccon user
        kc.add_role_to_user(seccon_user, seccon_role, name, token, kcRealm)
    except RuntimeError as e:
        logging.error(format_cloud_event(
            f'Keycloak assign role failed for {seccon_role} in {name}: {e}',
            'secCon: bootstrap failed'
        ))
    else:
        try: # to register with the partyRoleManagement API
            register_listener(rooturl + '/hub')
        except RuntimeError as e:
            logger.warning(format_cloud_event(
                str(e),
                'secCon could not register partyRoleManagement listener'
            ))
            status_value = { 'identityProvider': 'Keycloak',
                            'listenerRegistered': False }
            raise kopf.TemporaryError(
                'Could not register listener. Will retry.', delay=10
            )
        else:
            status_value = { 'identityProvider': 'Keycloak',
                            'listenerRegistered': True }

    # the return value is added to the status field of the k8s object
    # under securityRoles parameter (corresponds to function name)
    return status_value

@kopf.on.delete('oda.tmforum.org', 'v1alpha3', 'components', retries=5)
def security_client_delete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """

    # del unused-arguments for linting
    del meta, spec, status, body, namespace, labels, kwargs

    try: # to authenticate and get a token
        token = kc.get_token(username, password)
    except RuntimeError as e:
        logger.error(format_cloud_event(
            str(e),
            'secCon could not GET Keycloak token'
        ))

    try: # to delete the client from Keycloak
        kc.del_client(name, token, kcRealm)
    except RuntimeError as e:
        logger.error(format_cloud_event(
            str(e),
            f'secCon could not DELETE client {name} in realm {kcRealm}'
        ))
        raise kopf.TemporaryError(
            'Could not delete component from Keycloak. Will retry.',
            delay=10
        )
    else:
        logger.info(format_cloud_event(
            f'oda.tmforum.org component {name} deleted',
            'secCon: component deleted'
        ))
