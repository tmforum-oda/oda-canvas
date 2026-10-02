import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)


def get_events_for_resource(
    name: str,
    namespace: str,
    kind: str,
    user: AuthUser,
) -> list[dict]:
    api_client = get_impersonated_client(user)
    core_api   = client.CoreV1Api(api_client)

    field_selector = (
        f"involvedObject.name={name},"
        f"involvedObject.namespace={namespace},"
        f"involvedObject.kind={kind}"
    )

    try:
        response = core_api.list_namespaced_event(
            namespace,
            field_selector=field_selector,
        )
        events = [_event_summary(e.to_dict()) for e in response.items]
        events.sort(
            key=lambda e: e.get("lastTime") or e.get("firstTime") or "",
            reverse=True,
        )
        return events
    except client.exceptions.ApiException as e:
        if e.status == 403:
            logger.warning("No access to events in %s", namespace)
            return []
        raise


def _event_summary(event: dict) -> dict:
    return {
        "reason":         event.get("reason", ""),
        "message":        event.get("message", ""),
        "type":           event.get("type", "Normal"),
        "count":          event.get("count", 1),
        "firstTime":      event.get("first_timestamp", event.get("firstTimestamp", "")),
        "lastTime":       event.get("last_timestamp", event.get("lastTimestamp", "")),
        "source":         event.get("source", {}).get("component", ""),
    }
