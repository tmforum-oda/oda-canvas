"""
TMFOP005 Dependency Management — Keycloak Authorization implementation.

This operator polls the Keycloak Admin Events API for CLIENT_ROLE_MAPPING
changes in the configured realm and logs each create, update, or delete event.

The polling loop is implemented as a @kopf.daemon() attached to the operator's
own ConfigMap. This gives a single, continuous background loop that is
independent of any application-level CRD objects.

Environment variables (supplied via ConfigMap and Secret):
  KEYCLOAK_BASE       - Keycloak base URL, e.g. http://canvas-keycloak-headless.canvas:8083/auth
  KEYCLOAK_REALM      - Realm to monitor, e.g. odari
  KEYCLOAK_USER       - Keycloak admin username
  KEYCLOAK_PASSWORD   - Keycloak admin password
  POLL_INTERVAL_SECONDS - Polling interval in seconds (default: 5)
  POD_NAMESPACE       - Namespace the operator is deployed in
  LOGGING             - Python log level as an integer string (default: 20)
"""

import asyncio
import json
import logging
import os
import time

import kopf

from keycloakUtils import Keycloak
from log_wrapper import LogWrapper

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPERATOR_CONFIGMAP_NAME = "dependency-management-keycloak-authz-configmap"
"""Name of the ConfigMap the daemon attaches to.  Must match the Helm template."""

POLL_INTERVAL_SECONDS: int = int(os.environ.get("POLL_INTERVAL_SECONDS", "5"))
"""How often (in seconds) to query Keycloak for new admin events."""

RESOURCE_TYPES = ["CLIENT_ROLE_MAPPING"]
"""Keycloak admin-event resourceTypes to monitor."""

OPERATION_TYPES = ["CREATE", "UPDATE", "DELETE"]
"""Keycloak admin-event operationTypes to monitor."""


# ---------------------------------------------------------------------------
# Startup handler — configure operator settings and verify Keycloak access
# ---------------------------------------------------------------------------

@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, logger, **kwargs):
    """Configure operator settings and verify Keycloak admin-events are enabled."""
    logw = LogWrapper(
        logger,
        function_name="configure",
        handler_name="startup",
    )

    settings.peering.name = "dependency-mgmt-keycloak"
    settings.peering.priority = 110
    settings.watching.server_timeout = 1 * 60

    keycloak_base = os.environ.get("KEYCLOAK_BASE", "")
    keycloak_user = os.environ.get("KEYCLOAK_USER", "")
    keycloak_password = os.environ.get("KEYCLOAK_PASSWORD", "")
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
        token = kc.get_token(keycloak_user, keycloak_password)
        events_config = kc.get_realm_events_config(token, keycloak_realm)
        if not events_config.get("adminEventsEnabled", False):
            logw.warning(
                "adminEventsEnabled is False in Keycloak realm config",
                f"realm={keycloak_realm} — enable admin events in the Keycloak "
                "admin console under Realm Settings > Events > Admin Events",
            )
        elif not events_config.get("adminEventsDetailsEnabled", False):
            logw.warning(
                "adminEventsDetailsEnabled is False in Keycloak realm config",
                f"realm={keycloak_realm} — role representation JSON will not be "
                "included in events; enable 'Include Representation' under "
                "Realm Settings > Events > Admin Events",
            )
        else:
            logw.info(
                "Keycloak admin events are enabled",
                f"realm={keycloak_realm}",
            )
    except Exception as e:
        logw.warning(
            "Could not verify Keycloak admin events configuration",
            str(e),
        )


# ---------------------------------------------------------------------------
# Liveness probe — verify Keycloak token acquisition
# ---------------------------------------------------------------------------

@kopf.on.probe(id="keycloak-connection")
async def check_keycloak_connection(**kwargs):
    """Probe that verifies a Keycloak admin token can be acquired."""
    kc = Keycloak(os.environ.get("KEYCLOAK_BASE", ""))
    kc.get_token(
        os.environ.get("KEYCLOAK_USER", ""),
        os.environ.get("KEYCLOAK_PASSWORD", ""),
    )
    return "ok"


# ---------------------------------------------------------------------------
# Daemon — single polling loop for Keycloak CLIENT_ROLE_MAPPING admin events
# ---------------------------------------------------------------------------

@kopf.daemon(
    "",
    "v1",
    "configmaps",
    when=lambda name, **_: name == OPERATOR_CONFIGMAP_NAME,
    cancellation_timeout=1.0,
)
async def keycloak_admin_event_poller(stopped, logger, **kwargs):
    """
    Single background daemon that polls Keycloak for CLIENT_ROLE_MAPPING
    admin events and logs each one.

    The daemon is anchored to the operator's own ConfigMap so there is
    exactly one active polling loop regardless of how many application-level
    CRD objects exist in the cluster.

    Each poll fetches events that occurred since the previous successful
    poll using the dateFrom query parameter, eliminating duplicate processing.
    """
    logw = LogWrapper(
        logger,
        function_name="keycloak_admin_event_poller",
        handler_name="daemon",
    )

    keycloak_base = os.environ.get("KEYCLOAK_BASE", "")
    keycloak_user = os.environ.get("KEYCLOAK_USER", "")
    keycloak_password = os.environ.get("KEYCLOAK_PASSWORD", "")
    keycloak_realm = os.environ.get("KEYCLOAK_REALM", "odari")

    kc = Keycloak(keycloak_base)

    # Initialise the watermark to now so we only see events going forward.
    last_poll_time: int = int(time.time() * 1000)

    # Keycloak 20 only supports date granularity for dateFrom (yyyy-MM-dd),
    # so multiple polls on the same day return all of today's events.
    # Keycloak 20's AdminEventRepresentation has no id field, so we build a
    # composite key from (time, operationType, resourcePath) to deduplicate.
    seen_event_ids: set = set()

    logw.info(
        "Keycloak admin event poller daemon started",
        f"realm={keycloak_realm} interval={POLL_INTERVAL_SECONDS}s "
        f"resource_types={RESOURCE_TYPES} operation_types={OPERATION_TYPES}",
    )

    while not stopped:
        try:
            poll_started_at: int = int(time.time() * 1000)

            token = kc.get_token(keycloak_user, keycloak_password)
            events: list = kc.get_admin_events(
                token=token,
                realm=keycloak_realm,
                resource_types=RESOURCE_TYPES,
                operation_types=OPERATION_TYPES,
                date_from=last_poll_time,
            )

            new_count = 0
            for event in events:
                event_key = (
                    event.get("time"),
                    event.get("operationType"),
                    event.get("resourcePath"),
                )
                if event_key in seen_event_ids:
                    continue
                seen_event_ids.add(event_key)
                _log_admin_event(logw, event, keycloak_realm)
                new_count += 1

            if new_count:
                logw.debug(
                    "Poll complete",
                    f"realm={keycloak_realm} events_found={new_count}",
                )

            last_poll_time = poll_started_at

        except Exception as e:
            logw.exception("Error polling Keycloak admin events", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_admin_event(logw: LogWrapper, event: dict, realm: str) -> None:
    """Log a single Keycloak AdminEventRepresentation at INFO level."""
    op_type: str = event.get("operationType", "UNKNOWN")
    resource_path: str = event.get("resourcePath", "")
    event_time: int = event.get("time", 0)
    representation_raw: str = event.get("representation")
    error: str = event.get("error", "")

    role_info: dict = {}
    if representation_raw:
        try:
            role_info = json.loads(representation_raw)
        except (json.JSONDecodeError, TypeError):
            role_info = {"raw": representation_raw}

    detail_parts = [
        f"operationType={op_type}",
        f"resourcePath={resource_path}",
        f"eventTime={event_time}",
        f"realm={realm}",
    ]
    if role_info:
        detail_parts.append(f"role={role_info}")
    if error:
        detail_parts.append(f"error={error}")

    logw.info(
        f"CLIENT_ROLE_MAPPING {op_type}",
        " ".join(detail_parts),
    )
