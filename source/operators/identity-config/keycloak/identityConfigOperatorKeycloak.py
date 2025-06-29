import kopf
import logging
import os
import requests
from keycloakUtils import Keycloak
from log_wrapper import LogWrapper, logwrapper
from kubernetes.client.rest import ApiException
import kubernetes.client
import datetime

# HTTP status codes
HTTP_NOT_FOUND = 404

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

def register_listener(url: str, api_type: str = "Unknown") -> None:
    """
    Register the listener URL with API hub for role/permission updates

    Args:
        url: The hub URL to register with
        api_type: Type of API (e.g., "partyRoleAPI", "permissionSpecificationSetAPI") for logging

    Returns nothing, or raises an exception for the caller to catch
    """
    callback_url = "http://idlistkey.canvas:5000/listener"
    payload = {"callback": callback_url, "@type": "Hub"}
    
    logger.info(f"Registering listener for {api_type} - Hub URL: {url}")
    logger.debug(f"Registration payload: {payload}")

    try:  # to register the listener
        # pylint: disable=try-except-raise
        # Disabled because we raise immediately deliberately. We want
        # Kopf to handle this and only this error until we come across
        # more errors
        r = requests.post(url, json=payload)
        r.raise_for_status()
        
        logger.info(f"Successfully registered listener for {api_type} at {url}")
        logger.debug(f"Hub registration response status: {r.status_code}, response: {r.text}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to register listener for {api_type} at {url}: {str(e)}")
        raise RuntimeError(f"Hub registration failed for {api_type}: {str(e)}")
    except RuntimeError:
        logger.error(f"RuntimeError during listener registration for {api_type} at {url}")
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


# Global registry to track all registered listeners
registered_listeners = {}

def add_to_listener_registry(component_name: str, api_type: str, url: str):
    """
    Add a listener to the global registry for tracking
    
    Args:
        component_name: Name of the component
        api_type: Type of API (partyRoleAPI or permissionSpecificationSetAPI)
        url: The hub URL
    """
    if component_name not in registered_listeners:
        registered_listeners[component_name] = {}
    
    registered_listeners[component_name][api_type] = {
        "url": url,
        "registered_at": datetime.datetime.now().isoformat()
    }
    
    logger.info(f"Added {api_type} listener for component {component_name} to registry")
    logger.info(f"Current registered listeners: {list(registered_listeners.keys())}")
    logger.debug(f"Full listener registry: {registered_listeners}")


def remove_from_listener_registry(component_name: str):
    """
    Remove a component's listeners from the registry
    
    Args:
        component_name: Name of the component to remove
    """
    if component_name in registered_listeners:
        removed_listeners = registered_listeners.pop(component_name)
        logger.info(f"Removed component {component_name} from listener registry")
        logger.debug(f"Removed listeners: {removed_listeners}")
    else:
        logger.warning(f"Component {component_name} not found in listener registry")
    
    logger.info(f"Remaining registered listeners: {list(registered_listeners.keys())}")


def log_all_registered_listeners():
    """
    Log all currently registered listeners
    """
    if registered_listeners:
        logger.info(f"Currently registered listeners for {len(registered_listeners)} components:")
        for component, listeners in registered_listeners.items():
            for api_type, details in listeners.items():
                logger.info(f"  - Component: {component}, API: {api_type}, URL: {details['url']}, Registered: {details['registered_at']}")
    else:
        logger.info("No listeners currently registered")


# Script setup --------------

username = os.environ.get("KEYCLOAK_USER")
password = os.environ.get("KEYCLOAK_PASSWORD")
kcBaseURL = os.environ.get("KEYCLOAK_BASE")
kcRealm = os.environ.get("KEYCLOAK_REALM")

canvassystem_client = "canvassystem"

kc = Keycloak(kcBaseURL)

GROUP = "oda.tmforum.org"
VERSION = "v1"
COMPONENTS_PLURAL = "components"

IDENTITYCONFIG_GROUP = "oda.tmforum.org"
IDENTITYCONFIG_VERSION = "v1"
IDENTITYCONFIG_PLURAL = "identityconfigs"
IDENTITYCONFIG_KIND = "IdentityConfig"


# Kopf handlers -------------

# try to recover from broken watchers https://github.com/nolar/kopf/issues/1036 
@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.server_timeout = 1 * 60


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
def identityConfig(
    meta, spec, status, body, namespace, labels, name, old, new, **kwargs
):
    """
    Handler for component create/update
    """
    # del unused-arguments for linting
    del status, labels, kwargs

    logw = LogWrapper(
        handler_name="security_client_add", function_name="security_client_add"
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),  # f"POD/{get_pod_name(body)}",
    )
    rooturl = ""

    logw.debugInfo("security_client_add called", body)

    try:  # to authenticate and get a token
        token = kc.get_token(username, password)
    except RuntimeError as e:
        logw.error("secCon could not GET Keycloak token", str(e))

    try:  # to create the client in Keycloak
        logw.debugInfo(
            "Creating client in Keycloak",
            f"name: {name}, rooturl: {rooturl}, token: {token}, kcRealm: {kcRealm}",
        )
        kc.create_client(name, rooturl, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f"identityConfigOperator could not POST new client {name} in realm {kcRealm}",
            str(e),
        )
        raise kopf.TemporaryError(
            "Could not add component to Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Client {name} created")

    try:  # to get the list of existing clients and the client object for this component
        client_list = kc.get_client_list(token, kcRealm)
    except RuntimeError as e:
        logw.error(f"security-APIListener could not GET clients for {kcRealm}", str(e))
        raise kopf.TemporaryError(
            "Could not get the client from Keycloak. Will retry.", delay=10
        )
    else:
        client = client_list[name]
        canvassystem_client_id = client_list[canvassystem_client]
        logw.info(f"Client {name} retrieved")

    try:  # to create the bootstrap role and add it to the canvassystem client
        canvassystem_role = spec["canvasSystemRole"]
        kc.add_role(canvassystem_role, client, token, kcRealm)
    except RuntimeError as e:
        logw.error(f"Keycloak add_role failed for {canvassystem_role}", str(e))
        raise kopf.TemporaryError(
            "Could not add the canvassystem role to Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Keycloak role {canvassystem_role} created")

    try:  # to assign the role to the canvassystem client
        kc.add_role(canvassystem_role, canvassystem_client_id, token, kcRealm)
    except RuntimeError as e:
        logw.error(f"Keycloak add role failed for {canvassystem_role} to {canvassystem_client} client", str(e))
        raise kopf.TemporaryError(
            "Could not add the canvassystem role to canvassystem client in Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Keycloak role {canvassystem_role} assigned to {canvassystem_client} client")

    if "componentRole" in spec and len(spec["componentRole"]):
        try:  # to add list of static roles exposed in component
            # TODO find securityFunction.componentRole and add_role in {name}
            # 1) GET securityFunction.componentRole from the component
            # 2) Run for loop through list of roles present in securityFunction.componentRole
            # 3) and execute add_role against component in every iteration

            for role in spec["componentRole"]:
                kc.add_role(role["name"], client, token, kcRealm)
                logw.info(f'Keycloak role {role["name"]} created')
        except RuntimeError as e:
            logw.error(
                f"Keycloak add_role failed for roles present in componentRole for component {name}",
                str(e),
            )
            raise kopf.TemporaryError(
                "Could not add list of static roles to Keycloak. Will retry.", delay=10
            )

    # check if the partyRoleManagement API is exposed by the component
    # if it is present, add a listener to the partyRoleManagement API
    listener_registered = False
    if "partyRoleAPI" in spec:
        partyRoleAPI = spec["partyRoleAPI"]

        try:  # to register with the partyRoleManagement API
            rooturl = (
                "http://"
                + partyRoleAPI["implementation"]
                + "."
                + namespace
                + ".svc.cluster.local:"
                + str(partyRoleAPI["port"])
                + partyRoleAPI["path"]
            )
            logw.info(f"register_listener for partyRoleAPI url {rooturl}")
            register_listener(rooturl + "/hub", "partyRoleAPI")
            add_to_listener_registry(name, "partyRoleAPI", rooturl + "/hub")
            listener_registered = True

        except RuntimeError as e:
            logw.error(f"register_listener failed for partyRoleAPI url {rooturl}", str(e))
            raise kopf.TemporaryError(
                "Could not register listener for partyRoleAPI. Will retry.", delay=10
            )

    # check if the permissionSpecificationSetAPI is exposed by the component
    # if it is present, add a listener to the permissionSpecificationSetAPI
    if "permissionSpecificationSetAPI" in spec:
        permissionSpecificationSetAPI = spec["permissionSpecificationSetAPI"]

        try:  # to register with the permissionSpecificationSetAPI
            rooturl = (
                "http://"
                + permissionSpecificationSetAPI["implementation"]
                + "."
                + namespace
                + ".svc.cluster.local:"
                + str(permissionSpecificationSetAPI["port"])
                + permissionSpecificationSetAPI["path"]
            )
            logw.info(f"register_listener for permissionSpecificationSetAPI url {rooturl}")
            register_listener(rooturl + "/hub", "permissionSpecificationSetAPI")
            add_to_listener_registry(name, "permissionSpecificationSetAPI", rooturl + "/hub")
            listener_registered = True

        except RuntimeError as e:
            logw.error(f"register_listener failed for permissionSpecificationSetAPI url {rooturl}", str(e))
            raise kopf.TemporaryError(
                "Could not register listener for permissionSpecificationSetAPI. Will retry.", delay=10
            )

    status_value = {"identityProvider": "Keycloak", "listenerRegistered": listener_registered}

    # Log all currently registered listeners
    log_all_registered_listeners()

    # update the status value to the parent component object
    if "ownerReferences" in meta.keys():
        # str | the custom object's name
        parent_component_name = meta["ownerReferences"][0]["name"]

        try:
            custom_objects_api = kubernetes.client.CustomObjectsApi()
            parent_component = custom_objects_api.get_namespaced_custom_object(
                GROUP,
                VERSION,
                namespace,
                COMPONENTS_PLURAL,
                parent_component_name,
            )
        except ApiException as e:
            # Cant find parent component (if component in same chart as other kubernetes resources it may not be created yet)
            if e.status == HTTP_NOT_FOUND:
                raise kopf.TemporaryError(
                    "Cannot find parent component " + parent_component_name
                )
            else:
                logw.error(
                    f"Exception when calling custom_objects_api.get_namespaced_custom_object: {e}"
                )

        parent_component["status"]["identityConfig"] = status_value

        try:
            api_response = custom_objects_api.patch_namespaced_custom_object(
                GROUP,
                VERSION,
                namespace,
                COMPONENTS_PLURAL,
                parent_component_name,
                parent_component,
            )
            logw.debug(f"patchComponent: {api_response}")
        except ApiException as e:
            logw.warning(
                f"Exception when calling api_instance.patch_namespaced_custom_object for component {name}"
            )
            raise kopf.TemporaryError(
                "Exception when calling api_instance.patch_namespaced_custom_object for component "
                + name
            )

    # the return value is added to the status field of the k8s object
    # under securityRoles parameter (corresponds to function name)
    return status_value


@kopf.on.delete(GROUP, IDENTITYCONFIG_VERSION, IDENTITYCONFIG_PLURAL, retries=5)
def security_client_delete(meta, spec, status, body, namespace, labels, name, **kwargs):
    """
    Handler to delete component from Keycloak
    """

    # del unused-arguments for linting
    del meta, spec, status, namespace, labels, kwargs

    logw = LogWrapper(
        handler_name="security_client_delete", function_name="security_client_delete"
    )
    logw.set(
        component_name=quick_get_comp_name(body),
        resource_name=quick_get_comp_name(body),  # f"POD/{get_pod_name(body)}",
    )

    try:  # to authenticate and get a token
        token = kc.get_token(username, password)
    except Exception as e:
        logw.error("IDConfop could not GET Keycloak token", str(e))
        raise kopf.TemporaryError(
            "Could not authenticate to Keycloak. Will retry.", delay=10
        )

    try:  # to delete the client from Keycloak
        kc.del_client(name, token, kcRealm)
    except RuntimeError as e:
        logw.error(
            f"IDConfop could not DELETE client {name} in realm {kcRealm}", str(e)
        )
        raise kopf.TemporaryError(
            "Could not delete component from Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Client {name} deleted from Keycloak")
        remove_from_listener_registry(name)


@kopf.on.timer('oda.tmforum.org', 'v1', 'identityconfigs', interval=300.0)  # Log every 5 minutes
def periodic_listener_summary(**kwargs):
    """
    Periodically log a summary of all registered listeners for monitoring
    """
    logger.info("=== PERIODIC LISTENER REGISTRY SUMMARY ===")
    log_all_registered_listeners()
    logger.info("=== END PERIODIC SUMMARY ===")


# Health check handler
@kopf.on.probe(id='identity-listener-health')
def health_check(**kwargs):
    """
    Health check probe for the identity config operator
    """
    return {"status": "healthy", "registered_listeners": len(registered_listeners)}
