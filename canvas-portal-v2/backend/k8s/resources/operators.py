import logging
from kubernetes import client
from auth.models import AuthUser
from k8s.impersonation import get_impersonated_client

logger = logging.getLogger(__name__)

OPERATOR_SIGNATURES = {
    "component-operator": (
        "component-operator",
    ),
    "identityconfig-operator-keycloak": (
        "identityconfig-operator-keycloak",
        "identity-config-operator-keycloak",
        "identity-config-operator",
        "identityconfig-operator",
    ),
    "secretsmanagement-operator": (
        "secretsmanagement-operator",
        "secrets-management-operator",
    ),
    "observability-operator": (
        "observability-operator",
    ),
    "modelgateway-ai-gateway-operator": (
        "modelgateway-ai-gateway-operator",
    ),
    "ai-gateway-operator": (
        "ai-gateway-ai-gateway-operator",
        "ai-gateway-operator",
    ),
    "pdb-management-operator": (
        "pdb-management-operator",
    ),
    "mcp-gateway-operator": (
        "mcp-gateway-operator",
        "contextforge-mcp-operator",
        "contextforge-mcp-gateway-operator",
    ),
    "api-operator-istio": (
        "api-operator-istio",
        "istio-operator",
    ),
    "api-operator-kong": (
        "api-operator-kong",
        "kong-operator",
    ),
    "api-operator-apisix": (
        "api-operator-apisix",
        "apisix-operator",
    ),
}

TMF_OPERATOR_IDS: dict[str, tuple[str, str]] = {
    "component-operator":               ("TMFOP001", "Component Management Operator"),
    "api-operator-istio":               ("TMFOP002", "API Management Operator"),
    "api-operator-kong":                ("TMFOP002", "API Management Operator"),
    "api-operator-apisix":              ("TMFOP002", "API Management Operator"),
    "identityconfig-operator-keycloak": ("TMFOP003", "Identity Configuration Operator"),
    "secretsmanagement-operator":       ("TMFOP007", "Secrets Management Operator"),
    "modelgateway-ai-gateway-operator": ("TMFOP009", "Model-as-a-Service Operator"),
    "ai-gateway-operator":              ("TMFOP009", "Model-as-a-Service Operator"),
    "pdb-management-operator":          ("TMFOP010", "Disruption Budget Management Operator"),
}

TMF_OPERATOR_LABEL_ID = "oda.tmforum.org/operatorId"
TMF_OPERATOR_LABEL_NAME = "oda.tmforum.org/operatorName"

CANVAS_OPERATOR_NAMESPACES = [
    "canvas",
    "canvas-system",
    "components",
    "istio-ingress",
    "istio-system",
    "apisix",
    "apisix-system",
    "kong",
    "kong-system",
    "ingress-apisix",
    "ingress-kong",
    "api-gateway",
    "api-exposure",
]


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


def _match_operator_name(text: str) -> str | None:
    normalized = text.lower()
    for operator_name, patterns in OPERATOR_SIGNATURES.items():
        if any(pattern in normalized for pattern in patterns):
            return operator_name
    return None


def _deployment_containers(deploy: dict) -> list[dict]:
    return (
        deploy.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [])
    )


def _pick_container_for_operator(containers: list[dict], operator_name: str) -> dict:
    patterns = OPERATOR_SIGNATURES.get(operator_name, ())
    for container in containers:
        searchable = " ".join(
            [
                str(container.get("name", "")),
                str(container.get("image", "")),
            ]
        ).lower()
        if any(pattern in searchable for pattern in patterns):
            return container
    return containers[0] if containers else {}


def _discover_logical_operators(deploy: dict) -> list[dict]:
    deployment_name = deploy.get("metadata", {}).get("name", "")
    containers = _deployment_containers(deploy)
    matches: dict[str, dict] = {}

    for container in containers:
        operator_name = _match_operator_name(
            " ".join(
                [
                    str(container.get("name", "")),
                    str(container.get("image", "")),
                ]
            )
        )
        if not operator_name:
            continue
        matches[operator_name] = {
            "name": operator_name,
            "containerName": container.get("name", ""),
            "image": container.get("image", ""),
        }

    deployment_match = _match_operator_name(deployment_name)
    if deployment_match and deployment_match not in matches:
        container = _pick_container_for_operator(containers, deployment_match)
        matches[deployment_match] = {
            "name": deployment_match,
            "containerName": container.get("name", ""),
            "image": container.get("image", ""),
        }

    return list(matches.values())


def _deployment_selector(deploy: dict) -> dict:
    return deploy.get("spec", {}).get("selector", {}).get("match_labels", {})


def _deployment_pods(selector: dict, pods: list[dict]) -> list[dict]:
    if not selector:
        return []
    return [
        pod
        for pod in pods
        if all(
            pod.get("metadata", {}).get("labels", {}).get(key) == value
            for key, value in selector.items()
        )
    ]


def _pod_has_container(container_name: str, pod_spec: dict) -> bool:
    return any(container.get("name") == container_name for container in pod_spec.get("containers", []))


def _operator_counts(container_name: str, own_pods: list[dict], dep_status: dict) -> tuple[int, int, int, int]:
    desired = dep_status.get("replicas", 0) or 0
    if not container_name:
        return (
            desired,
            dep_status.get("ready_replicas", 0) or 0,
            dep_status.get("available_replicas", 0) or 0,
            dep_status.get("updated_replicas", 0) or 0,
        )

    ready = sum(
        1
        for pod in own_pods
        if _container_ready(container_name, pod.get("status", {}))
    )
    available = sum(
        1
        for pod in own_pods
        if _pod_ready(pod) and _container_ready(container_name, pod.get("status", {}))
    )
    present = sum(
        1
        for pod in own_pods
        if _pod_has_container(container_name, pod.get("spec", {}))
    )
    updated = min(dep_status.get("updated_replicas", 0) or 0, present or desired)
    return desired or present, ready, available, updated


def _operator_status(desired: int, ready: int, available: int) -> str:
    if desired == 0 or ready == 0:
        return "down"
    if ready < desired or available < desired:
        return "degraded"
    return "running"


def _pod_summary(pod: dict, preferred_container_name: str) -> dict:
    pmeta = pod.get("metadata", {})
    pstatus = pod.get("status", {})
    pspec = pod.get("spec", {})
    containers = [
        {
            "name":     container.get("name", ""),
            "image":    container.get("image", ""),
            "ready":    _container_ready(container.get("name", ""), pstatus),
            "restarts": _container_restarts(container.get("name", ""), pstatus),
            "state":    _container_state(container.get("name", ""), pstatus),
        }
        for container in pspec.get("containers", [])
    ]
    created_at = (
        pmeta.get("creation_timestamp")
        or pmeta.get("creationTimestamp")
        or pstatus.get("start_time")
        or pstatus.get("startTime")
    )
    preferred_container = next(
        (container for container in containers if container.get("name") == preferred_container_name),
        None,
    )
    pod_image = containers[0].get("image", "") if containers else ""
    if preferred_container:
        pod_image = preferred_container.get("image", "") or pod_image

    return {
        "name":       pmeta.get("name", ""),
        "namespace":  pmeta.get("namespace", ""),
        "phase":      pstatus.get("phase", "Unknown"),
        "ready":      _pod_ready(pod),
        "node":       pspec.get("node_name", pspec.get("nodeName", "")),
        "createdAt":  str(created_at) if created_at else "",
        "startTime":  str(pstatus.get("start_time", pstatus.get("startTime", ""))),
        "podIP":      pstatus.get("pod_ip", pstatus.get("podIP", "")),
        "restarts":   sum(container.get("restarts", 0) for container in containers),
        "image":      pod_image,
        "containers": containers,
    }


def _resolve_tmf_identity(operator_name: str, labels: dict) -> tuple[str | None, str | None]:
    label_id = labels.get(TMF_OPERATOR_LABEL_ID)
    label_name = labels.get(TMF_OPERATOR_LABEL_NAME)
    if label_id:
        return label_id, label_name
    static = TMF_OPERATOR_IDS.get(operator_name)
    if static:
        return static[0], static[1]
    return None, None


def _deployment_to_operators(deploy: dict, pods: list[dict]) -> list[dict]:
    metadata   = deploy.get("metadata", {})
    spec       = deploy.get("spec", {})
    dep_status = deploy.get("status", {})
    selector = _deployment_selector(deploy)
    own_pods = _deployment_pods(selector, pods)
    logical_operators = _discover_logical_operators(deploy)
    if not logical_operators:
        return []

    operators = []
    shared_deployment = len(logical_operators) > 1
    created_at = metadata.get("creation_timestamp") or metadata.get("creationTimestamp")
    deploy_labels = metadata.get("labels", {}) or {}
    for logical_operator in logical_operators:
        container_name = logical_operator.get("containerName", "")
        desired, ready, available, updated = _operator_counts(container_name, own_pods, dep_status)
        operator_name = logical_operator.get("name", metadata.get("name", ""))
        tmf_id, tmf_name = _resolve_tmf_identity(operator_name, deploy_labels)
        operators.append(
            {
                "name":           operator_name,
                "deploymentName": metadata.get("name", ""),
                "containerName":  container_name,
                "sharedDeployment": shared_deployment,
                "namespace":      metadata.get("namespace", ""),
                "status":         _operator_status(desired, ready, available),
                "desired":        desired,
                "ready":          ready,
                "available":      available,
                "updated":        updated,
                "image":          logical_operator.get("image", ""),
                "createdAt":      str(created_at) if created_at else "",
                "selector":       selector,
                "labels":         deploy_labels,
                "strategy":       spec.get("strategy", {}).get("type", "RollingUpdate"),
                "tmfId":          tmf_id,
                "tmfName":        tmf_name,
                "pods":           [_pod_summary(pod, container_name) for pod in own_pods],
            }
        )
    return operators


def _list_known_namespace_resources(
    apps_api: client.AppsV1Api,
    core_api: client.CoreV1Api,
) -> tuple[list[dict], list[dict]]:
    deployments: list[dict] = []
    pods: list[dict] = []

    for namespace in CANVAS_OPERATOR_NAMESPACES:
        try:
            deployments.extend(
                [deployment.to_dict() for deployment in apps_api.list_namespaced_deployment(namespace).items]
            )
        except client.exceptions.ApiException as e:
            if e.status in (404, 403):
                logger.warning("Skipping deployment scan in namespace %s: %s", namespace, e.reason)
            else:
                raise

        try:
            pods.extend([pod.to_dict() for pod in core_api.list_namespaced_pod(namespace).items])
        except client.exceptions.ApiException as e:
            if e.status in (404, 403):
                logger.warning("Skipping pod scan in namespace %s: %s", namespace, e.reason)
            else:
                raise

    return deployments, pods


def _list_operator_resources(
    apps_api: client.AppsV1Api,
    core_api: client.CoreV1Api,
) -> tuple[list[dict], list[dict]]:
    try:
        deployments = [deployment.to_dict() for deployment in apps_api.list_deployment_for_all_namespaces().items]
        pods = [pod.to_dict() for pod in core_api.list_pod_for_all_namespaces().items]
        return deployments, pods
    except client.exceptions.ApiException as e:
        if e.status not in (404, 403):
            raise
        logger.warning("Falling back to known operator namespaces: %s", e.reason)
        return _list_known_namespace_resources(apps_api, core_api)


def list_operators(user: AuthUser) -> list[dict]:
    api_client = get_impersonated_client(user)
    apps_api = client.AppsV1Api(api_client)
    core_api = client.CoreV1Api(api_client)
    deployment_items, pod_items = _list_operator_resources(apps_api, core_api)

    pods_by_namespace: dict[str, list[dict]] = {}
    for pod in pod_items:
        namespace = pod.get("metadata", {}).get("namespace", "")
        pods_by_namespace.setdefault(namespace, []).append(pod)

    results: list[dict] = []
    for deployment in deployment_items:
        namespace = deployment.get("metadata", {}).get("namespace", "")
        results.extend(_deployment_to_operators(deployment, pods_by_namespace.get(namespace, [])))

    operator_order = {name: index for index, name in enumerate(OPERATOR_SIGNATURES)}
    results.sort(
        key=lambda operator: (
            operator.get("namespace", ""),
            operator_order.get(operator.get("name", ""), len(operator_order)),
            operator.get("deploymentName", ""),
            operator.get("name", ""),
        )
    )
    return results


def get_operator(name: str, namespace: str, user: AuthUser) -> dict | None:
    api_client = get_impersonated_client(user)
    apps_api = client.AppsV1Api(api_client)
    core_api = client.CoreV1Api(api_client)

    try:
        deployments = [deployment.to_dict() for deployment in apps_api.list_namespaced_deployment(namespace).items]
        pod_items = [pod.to_dict() for pod in core_api.list_namespaced_pod(namespace).items]
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return None
        raise

    namespace_operators: list[dict] = []
    for deployment in deployments:
        namespace_operators.extend(_deployment_to_operators(deployment, pod_items))

    for operator in namespace_operators:
        if operator.get("name") == name:
            return operator

    for operator in namespace_operators:
        if operator.get("deploymentName") == name:
            return operator

    return None
