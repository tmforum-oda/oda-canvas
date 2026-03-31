"""
TMFOP005 Dependency Management — Keycloak Authorization operator.

This operator resolves API dependencies between ODA Components using Keycloak
as the authorization policy enforcement point.  When a component's service
account is granted a client role in Keycloak (a CLIENT_ROLE_MAPPING event),
the operator:

  1. Resolves the *user-component* (whose service account receives the role)
     and the *target-component* (which owns the role's client) from the
     Keycloak Admin Events API.
  2. Lists all DependentAPI resources owned by the user-component.
  3. For each DependentAPI, searches for a matching ready ExposedAPI on the
     target-component (matched by specification URL and apiType 'openapi').
  4. On a match, patches the DependentAPI status (url, implementation.ready)
     and creates or updates the corresponding Service Inventory entry.

The polling loop is implemented as a @kopf.daemon() anchored to the operator's
own ConfigMap, giving a single continuous background loop that is independent
of any application-level CRD objects.

Keycloak compatibility notes:
  - Tested against Keycloak 20.  AdminEventRepresentation has no 'id' field;
    deduplication uses a composite key (time, operationType, resourcePath).
  - 'dateFrom' accepts date granularity only (yyyy-MM-dd), so today's events
    always re-appear on every poll.  The composite-key set eliminates replays.
  - resourcePath format: users/{user-uuid}/role-mappings/clients/{client-uuid}

Code structure:
  Configuration          — constants and environment variable defaults
  Kubernetes helpers     — K8s client setup, list/patch CRD resources
  Keycloak helpers       — UUID → component name resolution with caching
  Service Inventory      — create/update canvas-info-service entries
  DependentAPI status    — patch DependentAPI ready status
  Component status       — propagate DependentAPI ready/url back to parent Component
  Event processing       — reduce, deduplicate, log, and act on events
  Kopf handlers          — startup, liveness probe, and polling daemon

Environment variables (supplied via ConfigMap and Secret):
  KEYCLOAK_BASE         - Keycloak base URL
                          e.g. http://canvas-keycloak-headless.canvas:8083/auth
  KEYCLOAK_REALM        - Realm to monitor (default: odari)
  KEYCLOAK_USER         - Keycloak admin username
  KEYCLOAK_PASSWORD     - Keycloak admin password
  POLL_INTERVAL_SECONDS - Polling interval in seconds (default: 5)
  POD_NAMESPACE         - Namespace the operator is deployed in
  LOGGING               - Python log level as an integer string (default: 20)
  CANVAS_INFO_ENDPOINT  - Canvas Info Service base URL
                          (default: http://info.canvas.svc.cluster.local)
"""

import asyncio
import json
import logging
import os
import re
import time

import kopf
import kubernetes
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException

from keycloakUtils import Keycloak
from log_wrapper import LogWrapper
from service_inventory_client import ServiceInventoryAPI
from utils import safe_get

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPERATOR_CONFIGMAP_NAME = "dependency-management-keycloak-authz-configmap"
"""Name of the ConfigMap the daemon attaches to.  Must match the Helm template."""

CANVAS_INFO_ENDPOINT: str = os.environ.get(
    "CANVAS_INFO_ENDPOINT", "http://info.canvas.svc.cluster.local"
)
"""Canvas Info Service endpoint for updating the Service Inventory."""

POLL_INTERVAL_SECONDS: int = int(os.environ.get("POLL_INTERVAL_SECONDS", "5"))
"""How often (in seconds) to query Keycloak for new admin events."""

RESOURCE_TYPES = ["CLIENT_ROLE_MAPPING"]
"""Keycloak admin-event resourceTypes to monitor."""

OPERATION_TYPES = ["CREATE", "UPDATE", "DELETE"]
"""Keycloak admin-event operationTypes to monitor."""

DEPAPI_GROUP = "oda.tmforum.org"
DEPAPI_VERSION = "v1"
DEPAPI_PLURAL = "dependentapis"
EXPAPI_PLURAL = "exposedapis"
COMPONENTS_PLURAL = "components"
HTTP_NOT_FOUND = 404
COMPONENT_NAME_LABEL = "oda.tmforum.org/componentName"
"""Label used on DependentAPI and ExposedAPI resources to identify their parent component."""

_RESOURCE_PATH_RE = re.compile(r"users/([^/]+)/role-mappings/clients/([^/]+)")
"""Captures (user_uuid, role_source_client_uuid) from a CLIENT_ROLE_MAPPING resourcePath."""

_SERVICE_ACCOUNT_PREFIX = "service-account-"
"""Keycloak service-account username prefix; strip it to get the component name."""


# ---------------------------------------------------------------------------
# Kubernetes helpers
# ---------------------------------------------------------------------------


def _load_k8s_client() -> kubernetes.client.CustomObjectsApi:
    """Load in-cluster or local kubeconfig and return a CustomObjectsApi client."""
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        kubernetes.config.load_kube_config()
    return kubernetes.client.CustomObjectsApi()


def _list_dependent_apis(
    component_name: str,
    k8s_custom: kubernetes.client.CustomObjectsApi,
    logw: LogWrapper,
) -> list:
    """List all DependentAPI resources owned by component_name."""
    try:
        result = k8s_custom.list_cluster_custom_object(
            group=DEPAPI_GROUP,
            version=DEPAPI_VERSION,
            plural=DEPAPI_PLURAL,
            label_selector=f"{COMPONENT_NAME_LABEL}={component_name}",
        )
        return result.get("items", [])
    except Exception as e:
        logw.warning(
            "Could not list DependentAPIs for component",
            f"component={component_name} error={e}",
        )
        return []


def _extract_spec_url(spec: dict) -> str | None:
    """Extract the specification URL from a DependentAPI or ExposedAPI spec dict."""
    specification = spec.get("specification")
    if isinstance(specification, dict):
        return specification.get("url")
    if isinstance(specification, list) and specification:
        first = specification[0]
        return first.get("url") if isinstance(first, dict) else None
    return None


def _is_matching_exposed_api(exp_api: dict, depapi_spec_url: str) -> bool:
    """Return True if an ExposedAPI matches the given spec URL and is ready."""
    spec = exp_api.get("spec", {})
    if "specification" not in spec or spec.get("apiType") != "openapi":
        return False
    exp_url = (
        spec["specification"].get("url")
        if isinstance(spec["specification"], dict)
        else None
    )
    if exp_url != depapi_spec_url:
        return False
    return exp_api.get("status", {}).get("implementation", {}).get("ready") is True


def _find_matching_exposed_api(
    depapi_spec: dict,
    target_component: str,
    k8s_custom: kubernetes.client.CustomObjectsApi,
    logw: LogWrapper,
) -> dict | None:
    """Find an ExposedAPI owned by target_component that matches the DependentAPI.

    Matches on specification URL, apiType 'openapi', and implementation ready=True.
    Uses the same matching logic as get_depapi_url in dependentApiSimpleOperator.
    Returns the matching ExposedAPI resource dict, or None if not found.
    """
    depapi_spec_url = _extract_spec_url(depapi_spec)
    if not depapi_spec_url:
        return None

    try:
        result = k8s_custom.list_cluster_custom_object(
            group=DEPAPI_GROUP,
            version=DEPAPI_VERSION,
            plural=EXPAPI_PLURAL,
            label_selector=f"{COMPONENT_NAME_LABEL}={target_component}",
        )
    except Exception as e:
        logw.warning(
            "Could not list ExposedAPIs for target-component",
            f"target-component={target_component} error={e}",
        )
        return None

    return next(
        (
            api
            for api in result.get("items", [])
            if _is_matching_exposed_api(api, depapi_spec_url)
        ),
        None,
    )


def _patch_dependent_api(
    k8s_custom: kubernetes.client.CustomObjectsApi,
    namespace: str,
    name: str,
    patch_body: dict,
    logw: LogWrapper,
) -> None:
    """Apply a status patch to a DependentAPI resource."""
    try:
        k8s_custom.patch_namespaced_custom_object(
            group=DEPAPI_GROUP,
            version=DEPAPI_VERSION,
            namespace=namespace,
            plural=DEPAPI_PLURAL,
            name=name,
            body=patch_body,
        )
        logw.info("DependentAPI status patched", f"depapi={name} namespace={namespace}")
    except Exception as e:
        logw.warning(
            "Could not patch DependentAPI status",
            f"depapi={name} namespace={namespace} error={e}",
        )


def _patch_component(
    namespace: str,
    name: str,
    component: dict,
    handler_name: str,
    logw: LogWrapper,
) -> None:
    """Apply a patch to the parent Component resource."""
    try:
        k8s_custom = kubernetes.client.CustomObjectsApi()
        k8s_custom.patch_namespaced_custom_object(
            group=DEPAPI_GROUP,
            version=DEPAPI_VERSION,
            namespace=namespace,
            plural=COMPONENTS_PLURAL,
            name=name,
            body=component,
        )
        logw.info(
            "Component status patched",
            f"component={name} namespace={namespace} handler={handler_name}",
        )
    except ApiException as e:
        logw.warning(
            "Could not patch Component status",
            f"component={name} namespace={namespace} error={e}",
        )


# ---------------------------------------------------------------------------
# Keycloak resolution helpers
# ---------------------------------------------------------------------------


def _resolve_user_component(
    user_uuid: str,
    token: str,
    kc: Keycloak,
    realm: str,
    cache: dict,
    logw: LogWrapper,
) -> str | None:
    """Resolve a Keycloak user UUID to an ODA component name.

    Keycloak service accounts use the username 'service-account-{componentName}'.
    Strips the prefix to derive the component name.  Result is cached.
    """
    if user_uuid in cache:
        return cache[user_uuid]
    try:
        user_rep = kc.get_user_by_uuid(token, realm, user_uuid)
        username: str = user_rep.get("username", "")
        cache[user_uuid] = (
            username[len(_SERVICE_ACCOUNT_PREFIX) :]
            if username.startswith(_SERVICE_ACCOUNT_PREFIX)
            else None
        )
    except Exception as e:
        logw.warning(
            "Could not resolve Keycloak user UUID", f"uuid={user_uuid} error={e}"
        )
        cache[user_uuid] = None
    return cache[user_uuid]


def _resolve_target_component(
    client_uuid: str,
    token: str,
    kc: Keycloak,
    realm: str,
    cache: dict,
    logw: LogWrapper,
) -> str | None:
    """Resolve a Keycloak client UUID to an ODA component name via its clientId.

    Result is cached to avoid repeated Keycloak API calls for the same client.
    """
    if client_uuid in cache:
        return cache[client_uuid]
    try:
        client_rep = kc.get_client_by_uuid(token, realm, client_uuid)
        cache[client_uuid] = client_rep.get("clientId")
    except Exception as e:
        logw.warning(
            "Could not resolve Keycloak client UUID", f"uuid={client_uuid} error={e}"
        )
        cache[client_uuid] = None
    return cache[client_uuid]


def _resolve_event_components(
    event: dict,
    token: str,
    kc: Keycloak,
    realm: str,
    k8s_custom: kubernetes.client.CustomObjectsApi,
    cache: dict,
    logw: LogWrapper,
) -> tuple[str | None, str | None, list]:
    """Resolve a CLIENT_ROLE_MAPPING event to ODA component names and DependentAPIs.

    resourcePath format: users/{user-uuid}/role-mappings/clients/{client-uuid}

    Returns:
        (user_component, target_component, dependent_apis)
        - user_component:  component whose service account receives the role
        - target_component: component that owns the role being assigned
        - dependent_apis:  DependentAPI resources owned by user_component
    """
    resource_path: str = event.get("resourcePath", "")
    match = _RESOURCE_PATH_RE.search(resource_path)
    if not match:
        return None, None, []

    user_uuid, client_uuid = match.group(1), match.group(2)
    user_component = _resolve_user_component(user_uuid, token, kc, realm, cache, logw)
    target_component = _resolve_target_component(
        client_uuid, token, kc, realm, cache, logw
    )
    dependent_apis = (
        _list_dependent_apis(user_component, k8s_custom, logw) if user_component else []
    )
    return user_component, target_component, dependent_apis


# ---------------------------------------------------------------------------
# Service Inventory helpers
# ---------------------------------------------------------------------------

_CANVAS_INFO_INSTANCE: ServiceInventoryAPI | None = None


def _canvas_info_instance() -> ServiceInventoryAPI:
    """Singleton accessor for the Canvas Info (Service Inventory) API client."""
    global _CANVAS_INFO_INSTANCE
    if _CANVAS_INFO_INSTANCE is None:
        _CANVAS_INFO_INSTANCE = ServiceInventoryAPI(CANVAS_INFO_ENDPOINT)
    return _CANVAS_INFO_INSTANCE


def _update_service_inventory(
    logw: LogWrapper,
    component_name: str,
    dependency_name: str,
    specification,
    url: str,
) -> str | None:
    """Create or update the Service Inventory entry for a resolved dependency.

    Returns the service inventory ID, or None if the update failed.
    """
    try:
        svc_info = _canvas_info_instance()
        existing = svc_info.list_services(
            component_name=component_name, dependency_name=dependency_name, state=None
        )
        assert len(existing) <= 1
        if not existing:
            svc = svc_info.create_service(
                componentName=component_name,
                dependencyName=dependency_name,
                url=url,
                specification=specification,
                state="active",
            )
            logw.info(
                "Service Inventory entry created",
                f"component={component_name} dependency={dependency_name} id={svc['id']}",
            )
        else:
            svc = svc_info.update_service(
                id=existing[0]["id"],
                componentName=component_name,
                dependencyName=dependency_name,
                url=url,
                specification=specification,
                state="active",
            )
            logw.info(
                "Service Inventory entry updated",
                f"component={component_name} dependency={dependency_name} id={svc['id']}",
            )
        return svc["id"]
    except Exception as e:
        logw.warning(
            "Could not update Service Inventory",
            f"component={component_name} dependency={dependency_name} error={e}",
        )
        return None


def _delete_service_inventory(
    logw: LogWrapper,
    component_name: str,
    dependency_name: str,
    svc_inv_id: str,
) -> None:
    """Delete the Service Inventory entry for a dependency by its ID.

    Silently ignores the case where the entry no longer exists (404).
    """
    try:
        svc_info = _canvas_info_instance()
        deleted = svc_info.delete_service(svc_inv_id, ignore_not_found=True)
        if deleted:
            logw.info(
                "Service Inventory entry deleted",
                f"component={component_name} dependency={dependency_name} id={svc_inv_id}",
            )
        else:
            logw.info(
                "Service Inventory entry not found — skipping delete",
                f"component={component_name} dependency={dependency_name} id={svc_inv_id}",
            )
    except Exception as e:
        logw.warning(
            "Could not delete Service Inventory entry",
            f"component={component_name} dependency={dependency_name} id={svc_inv_id} error={e}",
        )


# ---------------------------------------------------------------------------
# DependentAPI status management
# ---------------------------------------------------------------------------


def _set_dependent_api_ready(
    logw: LogWrapper,
    depapi: dict,
    url: str,
    k8s_custom: kubernetes.client.CustomObjectsApi,
) -> None:
    """Patch the DependentAPI status to mark it ready with the resolved URL.

    Skips the patch if the DependentAPI is already marked ready, to avoid
    redundant writes.  Also creates or updates the Service Inventory entry.
    """
    meta = depapi.get("metadata", {})
    spec = depapi.get("spec", {})
    namespace = meta.get("namespace", "components")
    name = meta.get("name", "")
    component_name = safe_get(None, depapi, "metadata", "labels", COMPONENT_NAME_LABEL)
    dependency_name = spec.get("name", name)
    specification = spec.get("specification")

    if safe_get(None, depapi, "status", "implementation", "ready") is True:
        logw.info(
            "DependentAPI already ready — skipping patch",
            f"depapi={name} namespace={namespace}",
        )
        return

    logw.info(
        "Setting DependentAPI implementation ready",
        f"depapi={name} namespace={namespace} url={url}",
    )

    svc_id = _update_service_inventory(
        logw, component_name, dependency_name, specification, url
    )

    patch_body = depapi.copy()
    patch_body.setdefault("status", {})
    patch_body["status"].setdefault("depapiStatus", {})
    patch_body["status"]["depapiStatus"]["url"] = url
    patch_body["status"]["implementation"] = {"ready": True}
    if svc_id:
        patch_body["status"]["depapiStatus"]["svcInvID"] = svc_id

    _patch_dependent_api(k8s_custom, namespace, name, patch_body, logw)
    _propagate_depapi_to_component(
        logw, depapi, {"url": url, "ready": True}, "_set_dependent_api_ready"
    )


def _set_dependent_api_not_ready(
    logw: LogWrapper,
    depapi: dict,
    k8s_custom: kubernetes.client.CustomObjectsApi,
) -> None:
    """Patch the DependentAPI status to mark it not ready and clear the resolved URL
    and service inventory ID.

    Called when a CLIENT_ROLE_MAPPING DELETE event is received, indicating the
    user-component's service account has lost access to the target-component's API.
    Skips the patch if the DependentAPI is already not ready, to avoid redundant writes.
    """
    meta = depapi.get("metadata", {})
    spec = depapi.get("spec", {})
    namespace = meta.get("namespace", "components")
    name = meta.get("name", "")

    if safe_get(None, depapi, "status", "implementation", "ready") is not True:
        logw.info(
            "DependentAPI already not ready — skipping patch",
            f"depapi={name} namespace={namespace}",
        )
        return
    component_name = safe_get(None, depapi, "metadata", "labels", COMPONENT_NAME_LABEL)
    dependency_name = spec.get("name", name)
    svc_inv_id = safe_get(None, depapi, "status", "depapiStatus", "svcInvID")

    logw.info(
        "Clearing DependentAPI implementation ready",
        f"depapi={name} namespace={namespace}",
    )

    if svc_inv_id:
        _delete_service_inventory(logw, component_name, dependency_name, svc_inv_id)

    patch_body = depapi.copy()
    patch_body.setdefault("status", {})
    patch_body["status"].setdefault("depapiStatus", {})
    patch_body["status"]["depapiStatus"]["url"] = None
    patch_body["status"]["depapiStatus"]["svcInvID"] = None
    patch_body["status"]["implementation"] = {"ready": False}

    _patch_dependent_api(k8s_custom, namespace, name, patch_body, logw)
    _propagate_depapi_to_component(
        logw, depapi, {"url": None, "ready": False}, "_set_dependent_api_not_ready"
    )


# ---------------------------------------------------------------------------
# Component status
# ---------------------------------------------------------------------------


def _propagate_depapi_to_component(
    logw: LogWrapper,
    depapi: dict,
    updates: dict,
    handler_name: str,
) -> None:
    """Propagate DependentAPI status changes to the parent Component resource.

    Finds the entry in coreDependentAPIs / managementDependentAPIs /
    securityDependentAPIs matching the DependentAPI uid and applies the
    given updates dict (e.g. ``{'url': url, 'ready': True}``).

    Silently returns if the DependentAPI has no owner reference, or if the
    parent Component cannot be found.

    Args:
        logw:         Shared LogWrapper instance.
        depapi:       Full DependentAPI resource dict (as returned by the K8s API).
        updates:      Key/value pairs to merge into the matching status array entry.
        handler_name: Name of the calling function, used for log messages.
    """
    meta = depapi.get("metadata", {})
    owner_refs = meta.get("ownerReferences", [])
    if not owner_refs:
        return

    parent_component_name = owner_refs[0]["name"]
    dep_api_uid = meta.get("uid")
    namespace = meta.get("namespace", "components")

    try:
        k8s_custom = kubernetes.client.CustomObjectsApi()
        parent_component = k8s_custom.get_namespaced_custom_object(
            group=DEPAPI_GROUP,
            version=DEPAPI_VERSION,
            namespace=namespace,
            plural=COMPONENTS_PLURAL,
            name=parent_component_name,
        )
    except ApiException as e:
        if e.status == HTTP_NOT_FOUND:
            logw.warning(
                "Parent component not found — skipping status propagation",
                f"component={parent_component_name} namespace={namespace}",
            )
            return
        logw.warning("Error fetching parent component", str(e))
        return

    component_status = parent_component.get("status", {})
    for segment_key in (
        "coreDependentAPIs",
        "managementDependentAPIs",
        "securityDependentAPIs",
    ):
        entries = component_status.get(segment_key, [])
        for entry in entries:
            if entry.get("uid") == dep_api_uid:
                entry.update(updates)
                logw.info(
                    "Propagating DependentAPI status to parent component",
                    f"component={parent_component_name} segment={segment_key} "
                    f"updates={updates} handler={handler_name}",
                )
                _patch_component(
                    namespace,
                    parent_component_name,
                    parent_component,
                    handler_name,
                    logw,
                )
                return


# ---------------------------------------------------------------------------
# Event processing
# ---------------------------------------------------------------------------


def _reduce_to_latest_per_path(events: list) -> list:
    """Keep only the most recent event for each resourcePath in a batch.

    Prevents redundant processing when multiple operations occur on the same
    resource within a single poll window.
    """
    latest: dict = {}
    for event in events:
        rp = event.get("resourcePath")
        if latest.get(rp) is None or event.get("time", 0) > latest[rp].get("time", 0):
            latest[rp] = event
    return list(latest.values())


def _log_role_mapping_event(
    logw: LogWrapper,
    event: dict,
    realm: str,
    user_component: str | None,
    target_component: str | None,
) -> None:
    """Log the top-level CLIENT_ROLE_MAPPING event at INFO level."""
    op_type: str = event.get("operationType", "UNKNOWN")

    role_info: dict = {}
    raw = event.get("representation")
    if raw:
        try:
            role_info = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            role_info = {"raw": raw}

    parts = [
        f"operationType={op_type}",
        f"resourcePath={event.get('resourcePath', '')}",
        f"eventTime={event.get('time', 0)}",
        f"realm={realm}",
    ]
    if role_info:
        parts.append(f"role={role_info}")
    if event.get("error"):
        parts.append(f"error={event['error']}")
    parts.append(f"user-component={user_component or '<not an ODA component>'}")
    parts.append(f"target-component={target_component or '<unknown>'}")

    logw.info(f"CLIENT_ROLE_MAPPING {op_type}", " ".join(parts))


def _process_depapi_matches(
    logw: LogWrapper,
    op_type: str,
    user_component: str | None,
    target_component: str | None,
    dependent_apis: list,
    k8s_custom: kubernetes.client.CustomObjectsApi,
) -> None:
    """For each DependentAPI of user_component, find a matching ExposedAPI on
    target_component, log the outcome, and patch the DependentAPI on CREATE/UPDATE.
    On DELETE, clears the url, svcInvID, and ready status from any matched DependentAPI.
    """
    for depapi in dependent_apis:
        meta = depapi.get("metadata", {})
        spec = depapi.get("spec", {})
        depapi_name = spec.get("name", meta.get("name", "<unknown>"))
        api_type = spec.get("apitype", spec.get("apiType", ""))
        required = spec.get("required", False)
        specification = spec.get("specification", [])

        matched_url = None
        if target_component:
            matched = _find_matching_exposed_api(
                spec, target_component, k8s_custom, logw
            )
            if matched:
                matched_url = matched.get("status", {}).get("apiStatus", {}).get("url")

        logw.info(
            f"CLIENT_ROLE_MAPPING {op_type} — dependentAPI",
            f"user-component={user_component} target-component={target_component or '<unknown>'} "
            f"dependentAPI={depapi_name} apiType={api_type} required={required} "
            f"specification={specification} "
            f"exposedAPI={'matched url=' + matched_url if matched_url else 'no match'}",
        )

        if matched_url and op_type in ("CREATE", "UPDATE"):
            _set_dependent_api_ready(logw, depapi, matched_url, k8s_custom)
        elif matched_url and op_type == "DELETE":
            _set_dependent_api_not_ready(logw, depapi, k8s_custom)


def _process_event(
    logw: LogWrapper,
    event: dict,
    token: str,
    kc: Keycloak,
    realm: str,
    k8s_custom: kubernetes.client.CustomObjectsApi,
    cache: dict,
) -> None:
    """Handle a single Keycloak CLIENT_ROLE_MAPPING admin event end-to-end.

    Resolves components, logs the event, matches DependentAPIs against
    ExposedAPIs, and patches DependentAPI status when a match is found.
    """
    user_component, target_component, dependent_apis = _resolve_event_components(
        event, token, kc, realm, k8s_custom, cache, logw
    )
    op_type: str = event.get("operationType", "UNKNOWN")
    _log_role_mapping_event(logw, event, realm, user_component, target_component)
    _process_depapi_matches(
        logw, op_type, user_component, target_component, dependent_apis, k8s_custom
    )


# ---------------------------------------------------------------------------
# Kopf handlers — startup, probe, and polling daemon
# ---------------------------------------------------------------------------


@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, logger, **kwargs):
    """Configure operator settings and verify Keycloak admin-events are enabled."""
    logw = LogWrapper(logger, function_name="configure", handler_name="startup")

    settings.peering.name = "dependency-mgmt-keycloak"
    settings.peering.priority = 110
    settings.watching.server_timeout = 1 * 60

    keycloak_base = os.environ.get("KEYCLOAK_BASE", "")
    keycloak_realm = os.environ.get("KEYCLOAK_REALM", "odari")

    LogWrapper.set_defaultLogger(logger)
    logw.info(
        "Operator starting",
        f"keycloak_base={keycloak_base} realm={keycloak_realm} "
        f"poll_interval={POLL_INTERVAL_SECONDS}s",
    )

    if not keycloak_base:
        logw.warning("KEYCLOAK_BASE is not set", "admin event polling will fail")
        return

    kc = Keycloak(keycloak_base)
    try:
        token = kc.get_token(
            os.environ.get("KEYCLOAK_USER", ""), os.environ.get("KEYCLOAK_PASSWORD", "")
        )
        events_config = kc.get_realm_events_config(token, keycloak_realm)
        if not events_config.get("adminEventsEnabled", False):
            logw.warning(
                "adminEventsEnabled is False in Keycloak realm config",
                f"realm={keycloak_realm} — enable admin events under "
                "Realm Settings > Events > Admin Events",
            )
        elif not events_config.get("adminEventsDetailsEnabled", False):
            logw.warning(
                "adminEventsDetailsEnabled is False in Keycloak realm config",
                f"realm={keycloak_realm} — enable 'Include Representation' under "
                "Realm Settings > Events > Admin Events",
            )
        else:
            logw.info("Keycloak admin events are enabled", f"realm={keycloak_realm}")
    except Exception as e:
        logw.warning("Could not verify Keycloak admin events configuration", str(e))


@kopf.on.probe(id="keycloak-connection")
async def check_keycloak_connection(**kwargs):
    """Probe that verifies a Keycloak admin token can be acquired."""
    kc = Keycloak(os.environ.get("KEYCLOAK_BASE", ""))
    kc.get_token(
        os.environ.get("KEYCLOAK_USER", ""), os.environ.get("KEYCLOAK_PASSWORD", "")
    )
    return "ok"


@kopf.daemon(
    "",
    "v1",
    "configmaps",
    when=lambda name, **_: name == OPERATOR_CONFIGMAP_NAME,
    cancellation_timeout=1.0,
)
async def keycloak_admin_event_poller(stopped, logger, **kwargs):
    """Single background daemon that polls Keycloak for CLIENT_ROLE_MAPPING admin events.

    Anchored to the operator's own ConfigMap so there is exactly one active polling
    loop regardless of how many application-level CRD objects exist in the cluster.
    """
    logw = LogWrapper(
        logger, function_name="keycloak_admin_event_poller", handler_name="daemon"
    )

    keycloak_base = os.environ.get("KEYCLOAK_BASE", "")
    keycloak_user = os.environ.get("KEYCLOAK_USER", "")
    keycloak_password = os.environ.get("KEYCLOAK_PASSWORD", "")
    keycloak_realm = os.environ.get("KEYCLOAK_REALM", "odari")

    kc = Keycloak(keycloak_base)
    k8s_custom = _load_k8s_client()
    cache: dict = {}  # UUID → component name; shared and grows across polls

    # Initialise watermark to now so only future events are processed.
    last_poll_time: int = int(time.time() * 1000)

    # Keycloak 20 only supports date granularity for dateFrom (yyyy-MM-dd),
    # so today's events always re-appear.  Deduplicate with a composite key.
    seen_events: set = set()

    logw.info(
        "Keycloak admin event poller daemon started",
        f"realm={keycloak_realm} interval={POLL_INTERVAL_SECONDS}s "
        f"resource_types={RESOURCE_TYPES} operation_types={OPERATION_TYPES}",
    )

    while not stopped:
        try:
            poll_started_at: int = int(time.time() * 1000)

            token = kc.get_token(keycloak_user, keycloak_password)
            raw_events: list = kc.get_admin_events(
                token=token,
                realm=keycloak_realm,
                resource_types=RESOURCE_TYPES,
                operation_types=OPERATION_TYPES,
                date_from=last_poll_time,
            )

            events = _reduce_to_latest_per_path(raw_events)

            new_count = 0
            for event in events:
                event_key = (
                    event.get("time"),
                    event.get("operationType"),
                    event.get("resourcePath"),
                )
                if event_key in seen_events:
                    continue
                seen_events.add(event_key)
                _process_event(
                    logw, event, token, kc, keycloak_realm, k8s_custom, cache
                )
                new_count += 1

            if new_count:
                logw.debug(
                    "Poll complete", f"realm={keycloak_realm} new_events={new_count}"
                )

            last_poll_time = poll_started_at

        except Exception as e:
            logw.exception("Error polling Keycloak admin events", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
