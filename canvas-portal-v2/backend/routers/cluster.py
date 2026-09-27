import logging
from fastapi import APIRouter, Depends
from kubernetes import client as k8s_client
from auth.middleware import get_current_user
from auth.models import AuthUser
from config import get_settings
from k8s.client import get_base_api_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cluster", tags=["cluster"])


def parse_cpu(cpu_str: str) -> float:
    if not cpu_str:
        return 0.0
    if cpu_str.endswith("m"):
        return int(cpu_str[:-1]) / 1000
    return float(cpu_str)


def parse_memory_bytes(mem_str: str) -> int:
    if not mem_str:
        return 0
    units = {
        "Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4,
        "K": 1000, "M": 1000**2, "G": 1000**3, "T": 1000**4,
    }
    for suffix, factor in units.items():
        if mem_str.endswith(suffix):
            return int(mem_str[: -len(suffix)]) * factor
    return int(mem_str)


@router.get("/overview")
def get_cluster_overview(user: AuthUser = Depends(get_current_user)):
    api_client = get_base_api_client()
    core_api = k8s_client.CoreV1Api(api_client)
    apps_api = k8s_client.AppsV1Api(api_client)

    result = {
        "nodes": {"total": 0, "ready": 0, "notReady": 0},
        "pods": {"total": 0, "running": 0, "pending": 0, "failed": 0, "allocatable": 0},
        "deployments": {"total": 0, "available": 0},
        "services": 0,
        "capacity": {"cpuCores": 0.0, "cpuUsed": 0.0, "memoryBytes": 0, "memoryUsed": 0},
        "version": "",
        "provider": "",
        "componentNamespaces": [],
        "componentNamespaceCount": 0,
    }

    try:
        nodes = core_api.list_node()
        result["nodes"]["total"] = len(nodes.items)
        for node in nodes.items:
            d = node.to_dict()
            allocatable = d.get("status", {}).get("allocatable", {}) or {}
            result["capacity"]["cpuCores"] += parse_cpu(allocatable.get("cpu", "0"))
            result["capacity"]["memoryBytes"] += parse_memory_bytes(allocatable.get("memory", "0"))
            result["pods"]["allocatable"] = result["pods"].get("allocatable", 0) + int(allocatable.get("pods", 0))

            for cond in (d.get("status", {}).get("conditions", []) or []):
                if cond.get("type") == "Ready":
                    if cond.get("status") == "True":
                        result["nodes"]["ready"] += 1
                    else:
                        result["nodes"]["notReady"] += 1
                    break
    except k8s_client.exceptions.ApiException as exc:
        logger.warning("Cannot list nodes: %s", exc)

    try:
        pods = core_api.list_pod_for_all_namespaces()
        result["pods"]["total"] = len(pods.items)
        cpu_used = 0.0
        mem_used = 0
        for pod in pods.items:
            d = pod.to_dict()
            phase = (d.get("status", {}).get("phase", "") or "").lower()
            if phase == "running":
                result["pods"]["running"] += 1
            elif phase == "pending":
                result["pods"]["pending"] += 1
            elif phase in ("failed", "unknown"):
                result["pods"]["failed"] += 1
            for container in (d.get("spec", {}).get("containers", []) or []):
                req = (container.get("resources") or {}).get("requests") or {}
                cpu_used += parse_cpu(req.get("cpu", "0"))
                mem_used += parse_memory_bytes(req.get("memory", "0"))
        result["capacity"]["cpuUsed"] = round(cpu_used, 2)
        result["capacity"]["memoryUsed"] = mem_used
    except k8s_client.exceptions.ApiException as exc:
        logger.warning("Cannot list pods: %s", exc)

    try:
        deployments = apps_api.list_deployment_for_all_namespaces()
        result["deployments"]["total"] = len(deployments.items)
        for dep in deployments.items:
            d = dep.to_dict()
            available = (d.get("status", {}).get("available_replicas") or
                         d.get("status", {}).get("availableReplicas") or 0)
            desired = (d.get("spec", {}).get("replicas") or 1)
            if available >= desired:
                result["deployments"]["available"] += 1
    except k8s_client.exceptions.ApiException as exc:
        logger.warning("Cannot list deployments: %s", exc)

    try:
        services = core_api.list_service_for_all_namespaces()
        result["services"] = len(services.items)
    except k8s_client.exceptions.ApiException as exc:
        logger.warning("Cannot list services: %s", exc)


    settings = get_settings()
    install_namespaces = settings.install_target_namespaces
    result["installNamespaces"] = install_namespaces

    try:
        ns_items = core_api.list_namespace()
        comp_ns = [
            ns.metadata.name
            for ns in ns_items.items
            if ns.metadata.name == "components" or ns.metadata.name.startswith("odacompns-")
        ]
        result["componentNamespaces"] = comp_ns
        result["componentNamespaceCount"] = len(comp_ns)
    except k8s_client.exceptions.ApiException as exc:
        logger.warning("Cannot list namespaces: %s", exc)

    try:
        ver_api = k8s_client.VersionApi(api_client)
        ver = ver_api.get_code()
        git_version = ver.git_version
        result["version"] = git_version
        v_lower = git_version.lower()
        if "gke" in v_lower:
            result["provider"] = "Google"
        elif "eks" in v_lower:
            result["provider"] = "Amazon"
        elif "aks" in v_lower:
            result["provider"] = "Azure"
        else:
            result["provider"] = ""
    except Exception:
        pass

    return result
