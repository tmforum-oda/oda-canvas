import logging
import subprocess
import shutil
import json
import tempfile
import os
import base64
from dataclasses import dataclass
from auth.models import AuthUser
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INCLUSTER_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
INCLUSTER_CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


@dataclass
class HelmInstallResult:
    success: bool
    release_name: str
    namespace: str
    message: str


def _load_cluster_connection() -> tuple[dict, list[str]]:
    cleanup_paths: list[str] = []

    if settings.K8S_MODE == "incluster":
        host = os.getenv("KUBERNETES_SERVICE_HOST", "").strip()
        port = os.getenv("KUBERNETES_SERVICE_PORT_HTTPS", "").strip() or os.getenv("KUBERNETES_SERVICE_PORT", "").strip()
        if not host or not port:
            raise RuntimeError("Kubernetes in-cluster API host/port environment variables are missing")
        if not os.path.exists(INCLUSTER_TOKEN_PATH):
            raise RuntimeError("Kubernetes in-cluster service account token not found")
        with open(INCLUSTER_TOKEN_PATH, "r", encoding="utf-8") as token_file:
            token = token_file.read().strip()
        if not token:
            raise RuntimeError("Kubernetes in-cluster service account token is empty")

        cluster: dict[str, object] = {"server": f"https://{host}:{port}"}
        if os.path.exists(INCLUSTER_CA_PATH):
            cluster["certificate-authority"] = INCLUSTER_CA_PATH
        else:
            cluster["insecure-skip-tls-verify"] = True
        return {"cluster": cluster, "token": token}, cleanup_paths

    if not settings.K8S_REMOTE_API_URL:
        raise RuntimeError("K8S_REMOTE_API_URL required when K8S_MODE=outofcluster")
    if not settings.K8S_REMOTE_SA_TOKEN:
        raise RuntimeError("K8S_REMOTE_SA_TOKEN required when K8S_MODE=outofcluster")

    cluster = {"server": settings.K8S_REMOTE_API_URL}
    if settings.K8S_REMOTE_CA_CERT:
        ca_cert_data = base64.b64decode(settings.K8S_REMOTE_CA_CERT)
        ca_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".crt", delete=False)
        ca_file.write(ca_cert_data)
        ca_file.close()
        cleanup_paths.append(ca_file.name)
        cluster["certificate-authority"] = ca_file.name
    else:
        cluster["insecure-skip-tls-verify"] = True

    return {"cluster": cluster, "token": settings.K8S_REMOTE_SA_TOKEN}, cleanup_paths


def _write_kubeconfig() -> tuple[str, list[str]]:
    connection, cleanup_paths = _load_cluster_connection()
    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "canvas-cluster",
                "cluster": connection["cluster"],
            }
        ],
        "users": [
            {
                "name": "canvas-service-account",
                "user": {
                    "token": connection["token"],
                },
            }
        ],
        "contexts": [
            {
                "name": "canvas-context",
                "context": {
                    "cluster": "canvas-cluster",
                    "user": "canvas-service-account",
                },
            }
        ],
        "current-context": "canvas-context",
    }

    kubeconfig_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(kubeconfig, kubeconfig_file)
    kubeconfig_file.close()
    cleanup_paths.append(kubeconfig_file.name)
    return kubeconfig_file.name, cleanup_paths


def _cleanup_paths(paths: list[str]) -> None:
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def _helm_cmd(user: AuthUser | None, *args: str) -> tuple[list[str], list[str]]:
    kubeconfig_path, cleanup_paths = _write_kubeconfig()
    cmd = ["helm", "--kubeconfig", kubeconfig_path]
    cmd += list(args)
    return cmd, cleanup_paths


def _helm_available() -> bool:
    return shutil.which("helm") is not None


def _ensure_helm_available() -> None:
    if not _helm_available():
        raise RuntimeError("helm binary not found in PATH")


def install_chart(
    user: AuthUser,
    release_name: str,
    chart: str,
    namespace: str,
    values: dict = None,
    values_yaml: str = None,
    version: str = None,
    repo_url: str = None,
    create_namespace: bool = True,
    timeout_minutes: int = 5,
) -> HelmInstallResult:
    _ensure_helm_available()
    timeout_minutes = max(1, min(int(timeout_minutes or 5), 60))
    cmd, cleanup_paths = _helm_cmd(
        user,
        "upgrade",
        "--install",
        release_name,
        chart,
        "--namespace",
        namespace,
        "--wait",
        "--timeout",
        f"{timeout_minutes}m",
    )
    if create_namespace:
        cmd.append("--create-namespace")
    if version:
        cmd += ["--version", version]
    if repo_url:
        cmd += ["--repo", repo_url]
    tmp_path = None
    try:
        if values_yaml:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
            tmp.write(values_yaml)
            tmp.close()
            tmp_path = tmp.name
            cmd += ["-f", tmp_path]
        elif values:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(values, tmp)
            tmp.close()
            tmp_path = tmp.name
            cmd += ["-f", tmp_path]
        logger.info(
            "Helm install: release=%s chart=%s ns=%s create_namespace=%s user=%s",
            release_name,
            chart,
            namespace,
            create_namespace,
            user.username,
        )
        subprocess_timeout = timeout_minutes * 60 + 60
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=subprocess_timeout)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        _cleanup_paths(cleanup_paths)
    return HelmInstallResult(
        success=result.returncode == 0,
        release_name=release_name,
        namespace=namespace,
        message=result.stdout if result.returncode == 0 else result.stderr,
    )


def get_chart_values(
    chart: str | None = None,
    repo_url: str = None,
    version: str = None,
) -> str:
    _ensure_helm_available()
    if not chart:
        raise RuntimeError("chart is required")
    cmd = ["helm", "show", "values", chart]
    if repo_url:
        cmd += ["--repo", repo_url]
    if version:
        cmd += ["--version", version]
    logger.info("Helm show values: chart=%s repo=%s version=%s", chart, repo_url, version)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "helm show values failed")
    return result.stdout


def uninstall_chart(user: AuthUser, release_name: str, namespace: str) -> HelmInstallResult:
    _ensure_helm_available()
    cmd, cleanup_paths = _helm_cmd(user, "uninstall", release_name, "--namespace", namespace, "--wait")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    finally:
        _cleanup_paths(cleanup_paths)
    return HelmInstallResult(success=result.returncode == 0, release_name=release_name, namespace=namespace, message=result.stdout if result.returncode == 0 else result.stderr)


def list_releases(user: AuthUser, namespace: str = None) -> list[dict]:
    _ensure_helm_available()
    cmd, cleanup_paths = _helm_cmd(user, "list", "--output", "json")
    cmd += (["--namespace", namespace] if namespace else ["--all-namespaces"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    finally:
        _cleanup_paths(cleanup_paths)
    return json.loads(result.stdout or "[]") if result.returncode == 0 else []


def get_release_history(user: AuthUser, release_name: str, namespace: str) -> list[dict]:
    _ensure_helm_available()
    cmd, cleanup_paths = _helm_cmd(
        user, "history", release_name, "--namespace", namespace, "--output", "json"
    )
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    finally:
        _cleanup_paths(cleanup_paths)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "helm history failed")
    return json.loads(result.stdout or "[]")


def get_release_values(user: AuthUser, release_name: str, namespace: str) -> str:
    _ensure_helm_available()
    cmd, cleanup_paths = _helm_cmd(
        user, "get", "values", release_name, "--namespace", namespace, "--output", "yaml"
    )
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    finally:
        _cleanup_paths(cleanup_paths)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "helm get values failed")
    output = (result.stdout or "").strip()
    if output.startswith("USER-SUPPLIED VALUES:"):
        output = output.split("\n", 1)[1] if "\n" in output else ""
    if output.strip() in ("null", "{}", ""):
        return ""
    return output.strip() + "\n"
