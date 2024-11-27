import kopf
import logging
import os
import requests
from keycloakUtils import Keycloak
from log_wrapper import LogWrapper, logwrapper

# Setup logging
logging_level = os.environ.get("LOGGING", logging.INFO)
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
logger = logging.getLogger("IdentityConfig")
logger.setLevel(int(logging_level))
logger.info("Logging set to %s", logging_level)
logger.debug("debug logging active")
LogWrapper.set_defaultLogger(logger)

componentname_label = os.getenv("COMPONENTNAME_LABEL", "oda.tmforum.org/componentName")
 
# Helper functions ----------

@logwrapper
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
            json = {'callback': 'http://idlistkey.canvas:5000/listener'})
        r.raise_for_status()
    except RuntimeError:
        raise

def safe_get(default_value, dictionary, *paths):
    result = dictionary
    for path in paths:
        if path not in result:
            return default_value
        result = result[path]
    return result

def quick_get_comp_name(body):
    return safe_get(None, body, "metadata", "labels", componentname_label)


# Script setup --------------

username = os.environ.get('KEYCLOAK_USER')
password = os.environ.get('KEYCLOAK_PASSWORD')
kcBaseURL = os.environ.get('KEYCLOAK_BASE')
kcRealm = os.environ.get('KEYCLOAK_REALM')

idconfop_user = 'idconfop'

kc = Keycloak(kcBaseURL)

GROUP = "oda.tmforum.org"
VERSION = "v1beta4"
COMPONENTS_PLURAL = "components"

IDENTITYCONFIG_GROUP = "oda.tmforum.org"
IDENTITYCONFIG_VERSION = "v1beta4"
IDENTITYCONFIG_PLURAL = "identityconfigs"
IDENTITYCONFIG_KIND = "IdentityConfig"


# Kopf handlers -------------

# @kopf.on.update(
#     GROUP,
#     VERSION,
#     COMPONENTS_PLURAL,
#     field='status.summary/status.deployment_status',
#     value='In-Progress-IDConfOp',
#     retries=5
# )
@kopf.on.resume(GROUP, IDENTITYCONFIG_VERSION, IDENTITYCONFIG_PLURAL, retries=5)
@kopf.on.create(GROUP, IDENTITYCONFIG_VERSION, IDENTITYCONFIG_PLURAL, retries=5)
@kopf.on.update(GROUP, IDENTITYCONFIG_VERSION, IDENTITYCONFIG_PLURAL, retries=5)
def security_client_add(meta, spec, status, body, namespace, labels,name, old, new, **kwargs):
    """
    Handler for component create/update
    """
    # del unused-arguments for linting
    del status, meta, labels, kwargs

    logw = LogWrapper(handler_name="security_client_add", function_name="security_client_add")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body) # f"POD/{get_pod_name(body)}",
    )
    rooturl = ""
            
    logw.debugInfo("security_client_add called", body)

    try: # to authenticate and get a token
        token = kc.get_token(username, password)
    except RuntimeError as e:
        logw.error(
            'secCon could not GET Keycloak token',
            str(e)
        )

    try: # to create the client in Keycloak
        logw.debugInfo("Creating client in Keycloak", f"name: {name}, rooturl: {rooturl}, token: {token}, kcRealm: {kcRealm}")
        kc.create_client(name, rooturl, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f'identityConfigOperator could not POST new client {name} in realm {kcRealm}',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not add component to Keycloak. Will retry.',
            delay=10
        )
    else:
        logw.info(
            f'Client {name} created'
        )


    try: # to get the list of existing clients and the client object for this component
        client_list = kc.get_client_list(token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f'security-APIListener could not GET clients for {kcRealm}',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not get the client from Keycloak. Will retry.',
            delay=10
        )
    else:
        client = client_list[name]
        logw.info(
            f'Client {name} retrieved'
        )

    try: # to create the bootstrap role and add it to the idconfop user
        idconfop_role = spec['controllerRole']
        kc.add_role(idconfop_role, client, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f'Keycloak add_role failed for {idconfop_role}',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not add the idconfop role to Keycloak. Will retry.',
            delay=10
        )
    else:
        logw.info(
            f'Keycloak role {idconfop_role} created'
        )
    
    try: # to assign the role to the idconfop user
        kc.add_role_to_user(idconfop_user, idconfop_role, name, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f'Keycloak assign role failed for {idconfop_role} in {name}',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not add the idconfop role to user in Keycloak. Will retry.',
            delay=10
        )
    else:
        logw.info(
            f'Keycloak role {idconfop_role} assigned to user {idconfop_user}'
        )



    if ('componentRole' in spec and len(spec['componentRole'])):
        try:# to add list of static roles exposed in component
            # TODO find securityFunction.componentRole and add_role in {name}
            # 1) GET securityFunction.componentRole from the component
            # 2) Run for loop through list of roles present in securityFunction.componentRole
            # 3) and execute add_role against component in every iteration
            
            for role in spec['componentRole']:
                kc.add_role(role['name'], client, token, kcRealm)
                logw.info(
                    f'Keycloak role {role["name"]} created'
                )
        except RuntimeError as e:
            logw.error(
                f'Keycloak add_role failed for roles present in componentRole for component {name}',
                str(e)
            )
            raise kopf.TemporaryError(
                'Could not add list of static roles to Keycloak. Will retry.',
                delay=10
            ) 

    # check if the partyRoleManagement API is exposed by the component
    # if it is present, add a listener to the partyRoleManagement API
    foundPartyRole = False
    partyRoleAPI = None
    if ('securityFunction' in spec and 'exposedAPIs' in spec):
        for api in spec['exposedAPIs']:
            if ('partyrole' in api['name']):
                partyRoleAPI = api
                foundPartyRole = True
                break

    if (foundPartyRole == True) :
        try: # to register with the partyRoleManagement API
            rooturl = (
                'http://'
                + partyRoleAPI['implementation']
                + '.' + namespace + '.svc.cluster.local:'
                + str(partyRoleAPI['port'])
                + partyRoleAPI['path']
            )
            logw.info(f'register_listener for url {rooturl}')
            register_listener(rooturl + '/hub')    

        except RuntimeError as e:
            logw.error(
                f'register_listener failed for url {rooturl}',
                str(e)
            )
            raise kopf.TemporaryError(
                'Could not register listener. Will retry.', delay=10
            )
        else:
            status_value = { 'identityProvider': 'Keycloak',
                            'listenerRegistered': True }
    else :
        status_value = { 'identityProvider': 'Keycloak',
                        'listenerRegistered': False }

    # the return value is added to the status field of the k8s object
    # under securityRoles parameter (corresponds to function name) 
    return status_value

@kopf.on.delete(GROUP, VERSION, COMPONENTS_PLURAL, retries=5)
def security_client_delete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """

    # del unused-arguments for linting
    del meta, spec, status, namespace, labels, kwargs

    logw = LogWrapper(handler_name="security_client_add", function_name="security_client_add")
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body) # f"POD/{get_pod_name(body)}",
    )

    try: # to authenticate and get a token
        token = kc.get_token(username, password)
    except Exception as e:
        logw.error(
            'IDConfop could not GET Keycloak token',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not authenticate to Keycloak. Will retry.',
            delay=10
        )  
    
    try: # to delete the client from Keycloak
        kc.del_client(name, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f'IDConfop could not DELETE client {name} in realm {kcRealm}',
            str(e)
        )
        raise kopf.TemporaryError(
            'Could not delete component from Keycloak. Will retry.',
            delay=10
        )
    else:
        logw.info(
            f'Client {name} deleted from Keycloak'
        )

