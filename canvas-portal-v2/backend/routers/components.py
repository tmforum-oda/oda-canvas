from fastapi import APIRouter, Depends, Query
from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.components import list_components, get_component, list_components_in_namespace
from k8s.resources.pods import list_pods_for_component
from k8s.resources.events import get_events_for_resource
from models.component import ComponentResponse

router = APIRouter(prefix="/api/components", tags=["components"])


@router.get("", response_model=list[ComponentResponse])
def get_components(namespace: str | None = Query(None), user: AuthUser = Depends(get_current_user)):
    raw = list_components_in_namespace(namespace, user) if namespace else list_components(user)
    return [ComponentResponse.from_k8s(item) for item in raw]


@router.get("/{namespace}/{name}", response_model=ComponentResponse)
def get_component_detail(namespace: str, name: str, user: AuthUser = Depends(get_current_user)):
    return ComponentResponse.from_k8s(get_component(name, namespace, user))


@router.get("/{namespace}/{name}/raw")
def get_component_raw(namespace: str, name: str, user: AuthUser = Depends(get_current_user)):
    return get_component(name, namespace, user)


def first_nonempty(*values):
    for value in values:
        if value:
            return value
    return None


@router.get("/{namespace}/{name}/status")
def get_component_status(
    namespace: str,
    name: str,
    user: AuthUser = Depends(get_current_user),
):
    raw     = get_component(name, namespace, user)
    status  = raw.get("status", {}) or {}
    summary = status.get("summary", {}) or {}
    summary_status = status.get("summary/status", {}) or {}

    phase = first_nonempty(
        summary_status.get("deployment_status"),
        summary.get("deployment_status"),
        summary.get("phase"),
        status.get("phase"),
    ) or "Unknown"

    summary_message = first_nonempty(
        summary.get("message"),
        summary_status.get("message"),
    ) or ""

    return {
        "name":           name,
        "namespace":      namespace,
        "phase":          phase,
        "summaryMessage": summary_message,
        "summary":        {"phase": phase, "message": summary_message},
        "deploymentSummary": summary_status,
        "implementation": status.get("implementation", {}),
        "apiStatus":      status.get("apiStatus", {}),
        "children":       status.get("children", []),
        "conditions":     status.get("conditions", []),
    }


@router.get("/{namespace}/{name}/pods")
def get_component_pods(
    namespace: str,
    name: str,
    user: AuthUser = Depends(get_current_user),
):
    return {
        "component": name,
        "namespace": namespace,
        "pods":      list_pods_for_component(name, namespace, user),
    }


@router.get("/{namespace}/{name}/apis")
def get_component_apis(
    namespace: str,
    name: str,
    user: AuthUser = Depends(get_current_user),
):
    raw = get_component(name, namespace, user)
    spec = raw.get("spec", {})
    status = raw.get("status", {})

    api_status: dict = status.get("apiStatus", {}) or {}

    def extract_apis(function_spec: dict | None) -> list[dict]:
        if not function_spec:
            return []
        apis = []
        for exposed in function_spec.get("exposedAPIs", []):
            api_name = exposed.get("name", "")
            st = api_status.get(api_name, {}) or {}
            ready_val = st.get("ready", exposed.get("ready"))
            if ready_val is None:
                ready_val = st.get("implementation", {}).get("ready") if st.get("implementation") else None
            apis.append({
                "name": api_name,
                "specification": exposed.get("specification", ""),
                "implementation": exposed.get("implementation", ""),
                "path": exposed.get("path", ""),
                "url": st.get("url") or exposed.get("url", ""),
                "developerUI": st.get("developerUI") or exposed.get("developerUI", ""),
                "ready": bool(ready_val) if ready_val is not None else None,
                "port": exposed.get("port"),
            })
        return apis

    return {
        "name": name,
        "namespace": namespace,
        "coreFunction": extract_apis(spec.get("coreFunction")),
        "managementFunction": extract_apis(spec.get("managementFunction")),
        "securityFunction": extract_apis(spec.get("securityFunction")),
    }


@router.get("/{namespace}/{name}/events")
def get_component_events(
    namespace: str,
    name: str,
    user: AuthUser = Depends(get_current_user),
):
    return {
        "component": name,
        "namespace": namespace,
        "events":    get_events_for_resource(name, namespace, "Component", user),
    }
