import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)


def _container_statuses(pod_status: dict) -> list[dict]:
    return pod_status.get("container_statuses", []) or pod_status.get("containerStatuses", []) or []


def _pod_ready(pod: dict) -> bool:
    for c in pod.get("status", {}).get("conditions", []):
        if c.get("type") == "Ready":
            return c.get("status") == "True"
    return False


def _container_ready(container_name: str, pod_status: dict) -> bool:
    for cs in _container_statuses(pod_status):
        if cs.get("name") == container_name:
            return cs.get("ready", False)
    return False


def _container_restarts(container_name: str, pod_status: dict) -> int:
    for cs in _container_statuses(pod_status):
        if cs.get("name") == container_name:
            return cs.get("restart_count", cs.get("restartCount", 0))
    return 0


def _container_state(container_name: str, pod_status: dict) -> str:
    for cs in _container_statuses(pod_status):
        if cs.get("name") != container_name:
            continue

        state = cs.get("state", {}) or {}
        if state.get("running") is not None:
            return "running"
        if state.get("waiting") is not None:
            return state.get("waiting", {}).get("reason", "waiting")
        if state.get("terminated") is not None:
            return state.get("terminated", {}).get("reason", "terminated")
        return "unknown"
    return "unknown"


def _pod_summary(pod: dict) -> dict:
    metadata   = pod.get("metadata", {})
    spec       = pod.get("spec", {})
    status     = pod.get("status", {})

    containers = [
        {
            "name":     c.get("name", ""),
            "image":    c.get("image", ""),
            "ready":    _container_ready(c.get("name", ""), status),
            "restarts": _container_restarts(c.get("name", ""), status),
            "state":    _container_state(c.get("name", ""), status),
        }
        for c in spec.get("containers", [])
    ]

    created_at = metadata.get("creation_timestamp") or metadata.get("creationTimestamp") or status.get("start_time") or status.get("startTime")

    return {
        "name":       metadata.get("name", ""),
        "namespace":  metadata.get("namespace", ""),
        "phase":      status.get("phase", "Unknown"),
        "ready":      _pod_ready(pod),
        "node":       spec.get("node_name", spec.get("nodeName", "")),
        "createdAt":  str(created_at) if created_at else "",
        "startTime":  str(status.get("start_time", status.get("startTime", ""))),
        "podIP":      status.get("pod_ip", status.get("podIP", "")),
        "restarts":   sum(container.get("restarts", 0) for container in containers),
        "image":      containers[0].get("image", "") if containers else "",
        "containers": containers,
        "labels":     metadata.get("labels", {}),
    }


def list_pods_for_component(
    component_name: str,
    namespace: str,
    user: AuthUser,
) -> list[dict]:
    api_client = get_impersonated_client(user)
    core_api   = client.CoreV1Api(api_client)

    label_selectors = [
        f"oda.tmforum.org/componentName={component_name}",
        f"impl={component_name}",
        f"oda.tmforum.org/component={component_name}",
        f"app={component_name}",
        f"app.kubernetes.io/instance={component_name}",
    ]

    for selector in label_selectors:
        try:
            response = core_api.list_namespaced_pod(
                namespace,
                label_selector=selector,
            )
            if response.items:
                return [_pod_summary(p.to_dict()) for p in response.items]
        except client.exceptions.ApiException as e:
            if e.status == 403:
                logger.warning("No access to list pods in %s", namespace)
                return []
            raise

    return []


def list_pods_in_namespace(namespace: str, user: AuthUser) -> list[dict]:
    api_client = get_impersonated_client(user)
    core_api   = client.CoreV1Api(api_client)
    response   = core_api.list_namespaced_pod(namespace)
    return [_pod_summary(p.to_dict()) for p in response.items]


def get_pod_logs(
    pod_name: str,
    namespace: str,
    user: AuthUser,
    container: str = None,
    tail_lines: int = 500,
    previous: bool = False,
) -> str:
    api_client = get_impersonated_client(user)
    core_api   = client.CoreV1Api(api_client)

    kwargs = dict(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines,
        previous=previous,
        timestamps=True,
    )
    if container:
        kwargs["container"] = container

    try:
        return core_api.read_namespaced_pod_log(**kwargs)
    except client.exceptions.ApiException as e:
        if e.status == 400 and not container:
            first = _first_container(pod_name, namespace, core_api)
            if first:
                kwargs["container"] = first
                return core_api.read_namespaced_pod_log(**kwargs)
        raise


def stream_pod_logs(
    pod_name: str,
    namespace: str,
    user: AuthUser,
    container: str = None,
    tail_lines: int = 100,
    previous: bool = False,
):
    api_client = get_impersonated_client(user)
    core_api = client.CoreV1Api(api_client)

    kwargs = dict(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines,
        previous=previous,
        timestamps=True,
        follow=True,
        _preload_content=False,
    )
    if container:
        kwargs["container"] = container

    try:
        resp = core_api.read_namespaced_pod_log(**kwargs)
    except client.exceptions.ApiException as e:
        if e.status == 400 and not container:
            first = _first_container(pod_name, namespace, core_api)
            if first:
                kwargs["container"] = first
                resp = core_api.read_namespaced_pod_log(**kwargs)
            else:
                raise
        else:
            raise

    try:
        for chunk in resp.stream(amt=4096, decode_content=False):
            if chunk:
                yield chunk
    finally:
        try:
            resp.release_conn()
        except Exception:
            pass
        try:
            resp.close()
        except Exception:
            pass


def _first_container(pod_name: str, namespace: str, core_api) -> str | None:
    try:
        pod  = core_api.read_namespaced_pod(pod_name, namespace)
        spec = pod.to_dict().get("spec", {})
        containers = spec.get("containers", [])
        if containers:
            return containers[0].get("name")
    except Exception:
        pass
    return None


def get_pod_containers(pod_name: str, namespace: str, user: AuthUser) -> list[str]:
    api_client = get_impersonated_client(user)
    core_api   = client.CoreV1Api(api_client)

    try:
        pod  = core_api.read_namespaced_pod(pod_name, namespace)
        spec = pod.to_dict().get("spec", {})
        return [c["name"] for c in spec.get("containers", [])]
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return []
        raise
