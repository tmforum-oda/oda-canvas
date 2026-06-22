import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from auth.middleware import get_current_user
from auth.models import AuthUser
from config import get_settings
from k8s.helm.installer import install_chart, uninstall_chart, list_releases, get_chart_values, get_release_history, get_release_values
from k8s.helm.repositories import add_repository, list_repositories, list_repository_charts, remove_repository, sync_repository
from models.helm import (
    HelmChartVersion,
    HelmInstallRequest,
    HelmReleaseStatus,
    HelmRepositoryChart,
    HelmRepositoryCreateRequest,
    HelmRepositorySummary,
    HelmUninstallRequest,
)

router = APIRouter(prefix="/api/helm", tags=["helm"])

logger = logging.getLogger(__name__)


def _ensure_namespace_allowed(namespace: str, user: AuthUser, action: str) -> None:
    allowed = get_settings().install_target_namespaces
    if allowed and namespace not in allowed:
        logger.warning(
            "Helm %s denied: user=%s requested namespace %r which is not in the "
            "allowed namespaces %s",
            action, user.username, namespace, allowed,
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Namespace '{namespace}' is not allowed for {action}. "
                f"Allowed namespaces: {', '.join(allowed)}."
            ),
        )


def _ensure_chart_source_allowed(source: str | None, user: AuthUser, action: str) -> None:
    if not source:
        return
    allowed = get_settings().allowed_chart_sources
    if not allowed:
        return
    src = source.strip().rstrip("/")
    for entry in allowed:
        base = entry.strip().rstrip("/")
        if base and (src == base or src.startswith(base + "/")):
            return
    logger.warning(
        "Helm %s denied: user=%s used chart source %r which is not in the "
        "approved sources %s",
        action, user.username, source, allowed,
    )
    raise HTTPException(
        status_code=403,
        detail=(
            f"Chart source '{source}' is not an approved repository. "
            "Please contact your administrator to allow this source."
        ),
    )


def format_helm_operation_error(raw_message: str) -> str:
    message = raw_message.strip()
    if 'cannot create resource "namespaces"' in message:
        return (
            f'{message} '
            'Hint: disable "Create namespace if it does not exist" for existing namespaces, '
            'or ask a cluster admin to create the namespace first.'
        )
    if 'cannot patch resource "components"' in message and 'api group "oda.tmforum.org"' in message:
        return (
            f'{message} '
            'Hint: the target namespace role needs patch/update access to ODA Component resources. '
            'Upgrade the Canvas Portal chart so the admin RoleBinding includes the ODA custom-resource extension.'
        )
    return message


def helm_failure_prefix(raw_message: str) -> str:
    message = raw_message.strip().upper()
    if "UPGRADE FAILED" in message:
        return "Helm upgrade failed"
    if "INSTALLATION FAILED" in message:
        return "Helm install failed"
    return "Helm operation failed"


@router.get("/releases", response_model=list[HelmReleaseStatus])
def get_releases(namespace: str | None = Query(None), user: AuthUser = Depends(get_current_user)):
    try:
        releases = list_releases(user=user, namespace=namespace)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return [HelmReleaseStatus(name=r.get("name", ""), namespace=r.get("namespace", ""), chart=r.get("chart", ""), app_version=r.get("app_version"), status=r.get("status", ""), updated=r.get("updated")) for r in releases]


@router.get("/internal/repos-with-charts")
def get_repos_with_charts_internal(user: AuthUser = Depends(get_current_user)):
    from k8s.helm.repositories import _read_catalog
    try:
        catalog = _read_catalog()
        repos = catalog.get("repositories", [])
        result = []
        for repo in repos:
            charts = []
            for c in repo.get("charts", []):
                charts.append({
                    "name": c.get("name", ""),
                    "full_name": c.get("full_name", ""),
                    "repo_name": c.get("repo_name", ""),
                    "repo_url": c.get("repo_url", ""),
                    "description": c.get("description", ""),
                    "latest_version": c.get("latest_version", ""),
                })
            result.append({
                "name": repo.get("name", ""),
                "url": repo.get("url", ""),
                "status": repo.get("status", ""),
                "chart_count": len(charts),
                "charts": charts,
            })
        return result
    except Exception as exc:
        return []


@router.get("/repos", response_model=list[HelmRepositorySummary])
def get_repositories(user: AuthUser = Depends(get_current_user)):
    try:
        return [HelmRepositorySummary(**repo) for repo in list_repositories()]
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/repos", response_model=HelmRepositorySummary)
def create_repository(payload: HelmRepositoryCreateRequest, user: AuthUser = Depends(get_current_user)):
    _ensure_chart_source_allowed(payload.url, user, "repository add")
    try:
        return HelmRepositorySummary(**add_repository(name=payload.name, url=payload.url))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/repos/{repo_name}/sync", response_model=HelmRepositorySummary)
def sync_repository_index(repo_name: str, user: AuthUser = Depends(get_current_user)):
    try:
        return HelmRepositorySummary(**sync_repository(repo_name))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/repos/{repo_name}")
def delete_repository(repo_name: str, user: AuthUser = Depends(get_current_user)):
    try:
        remove_repository(repo_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"success": True, "name": repo_name}


@router.get("/repos/{repo_name}/charts", response_model=list[HelmRepositoryChart])
def get_repository_charts(repo_name: str, user: AuthUser = Depends(get_current_user)):
    try:
        charts = list_repository_charts(repo_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    normalized = []
    for chart in charts:
        normalized.append(
            HelmRepositoryChart(
                **{
                    **chart,
                    "versions": [HelmChartVersion(**version) for version in chart.get("versions", [])],
                }
            )
        )
    return normalized


@router.get("/repo-charts", response_model=list[HelmRepositoryChart])
def get_repository_charts_by_query(
    repo_name: str = Query(..., description="Repository name"),
    user: AuthUser = Depends(get_current_user),
):
    try:
        charts = list_repository_charts(repo_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    normalized = []
    for chart in charts:
        normalized.append(
            HelmRepositoryChart(
                **{
                    **chart,
                    "versions": [HelmChartVersion(**version) for version in chart.get("versions", [])],
                }
            )
        )
    return normalized


@router.get("/values")
def fetch_values(
    chart: str | None = Query(None, description="Chart name"),
    repo_url: str | None = Query(None, description="Helm repository URL"),
    version: str | None = Query(None, description="Chart version"),
    user: AuthUser = Depends(get_current_user),
):
    _ensure_chart_source_allowed(repo_url, user, "values fetch")
    if chart and chart.startswith(("oci://", "http://", "https://")):
        _ensure_chart_source_allowed(chart, user, "values fetch")
    try:
        yaml_content = get_chart_values(chart=chart, repo_url=repo_url, version=version)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"values": yaml_content}


@router.post("/install")
def install(payload: HelmInstallRequest, user: AuthUser = Depends(get_current_user)):
    _ensure_namespace_allowed(payload.namespace, user, "install")
    _ensure_chart_source_allowed(payload.repo_url, user, "install")
    if payload.chart and payload.chart.startswith(("oci://", "http://", "https://")):
        _ensure_chart_source_allowed(payload.chart, user, "install")
    try:
        result = install_chart(
            user=user,
            release_name=payload.release_name,
            chart=payload.chart,
            namespace=payload.namespace,
            values=payload.values,
            values_yaml=payload.values_yaml,
            version=payload.version,
            repo_url=payload.repo_url,
            create_namespace=payload.create_namespace,
            timeout_minutes=payload.timeout_minutes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"{helm_failure_prefix(result.message)}: {format_helm_operation_error(result.message)}",
        )
    return {"success": True, "release_name": result.release_name, "namespace": result.namespace, "message": result.message}


@router.delete("/uninstall")
def uninstall(payload: HelmUninstallRequest, user: AuthUser = Depends(get_current_user)):
    _ensure_namespace_allowed(payload.namespace, user, "uninstall")
    try:
        result = uninstall_chart(user=user, release_name=payload.release_name, namespace=payload.namespace)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    if not result.success:
        raise HTTPException(status_code=500, detail=f"Helm uninstall failed: {result.message}")
    return {"success": True, "release_name": result.release_name, "message": result.message}


@router.get("/history")
def get_history(
    release: str = Query(..., description="Helm release name"),
    namespace: str = Query(..., description="Kubernetes namespace"),
    user: AuthUser = Depends(get_current_user),
):
    try:
        history = get_release_history(user=user, release_name=release, namespace=namespace)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return history


@router.get("/releases/values")
def fetch_release_values(
    release: str = Query(..., min_length=1),
    namespace: str = Query(..., min_length=1),
    user: AuthUser = Depends(get_current_user),
):
    try:
        values_yaml = get_release_values(user=user, release_name=release, namespace=namespace)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"values": values_yaml}
