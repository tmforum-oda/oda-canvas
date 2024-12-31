import kopf
import logging
import os
import requests
from keycloakUtils import Keycloak
from log_wrapper import LogWrapper, logwrapper
from kubernetes.client.rest import ApiException
import kubernetes.client

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

def register_listener(url: str) -> None:
    """
    Register the listener URL with partyRoleManagement for role updates

    Returns nothing, or raises an exception for the caller to catch
    """

    try:  # to register the listener
        # pylint: disable=try-except-raise
        # Disabled because we raise immediately deliberately. We want
        # Kopf to handle this and only this error until we come across
        # more errors
        r = requests.post(
            url, json={"callback": "http://idlistkey.canvas:5000/listener"}
        )
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

username = os.environ.get("KEYCLOAK_USER")
password = os.environ.get("KEYCLOAK_PASSWORD")
kcBaseURL = os.environ.get("KEYCLOAK_BASE")
kcRealm = os.environ.get("KEYCLOAK_REALM")

canvassystem_user = "canvassystem"

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
        logw.info(f"Client {name} retrieved")

    try:  # to create the bootstrap role and add it to the canvassystem user
        canvassystem_role = spec["canvasSystemRole"]
        kc.add_role(canvassystem_role, client, token, kcRealm)
    except RuntimeError as e:
        logw.error(f"Keycloak add_role failed for {canvassystem_role}", str(e))
        raise kopf.TemporaryError(
            "Could not add the canvassystem role to Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Keycloak role {canvassystem_role} created")

    try:  # to assign the role to the canvassystem user
        kc.add_role_to_user(canvassystem_user, canvassystem_role, name, token, kcRealm)
    except RuntimeError as e:
        logw.error(f"Keycloak assign role failed for {canvassystem_role} in {name}", str(e))
        raise kopf.TemporaryError(
            "Could not add the canvassystem role to user in Keycloak. Will retry.", delay=10
        )
    else:
        logw.info(f"Keycloak role {canvassystem_role} assigned to user {canvassystem_user}")

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
            logw.info(f"register_listener for url {rooturl}")
            register_listener(rooturl + "/hub")

        except RuntimeError as e:
            logw.error(f"register_listener failed for url {rooturl}", str(e))
            raise kopf.TemporaryError(
                "Could not register listener. Will retry.", delay=10
            )
        else:
            status_value = {"identityProvider": "Keycloak", "listenerRegistered": True}
    else:
        status_value = {"identityProvider": "Keycloak", "listenerRegistered": False}

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
