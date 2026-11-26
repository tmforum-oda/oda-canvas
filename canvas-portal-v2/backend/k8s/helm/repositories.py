import hashlib
import json
import logging
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CATALOG_PATH = (
    os.getenv("HELM_REPOSITORY_CATALOG_PATH", "").strip()
    or str(Path(__file__).resolve().parents[2] / "data" / "helm-repositories.json")
)


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _catalog_path() -> Path:
    return Path(CATALOG_PATH)


def _read_catalog() -> dict:
    path = _catalog_path()
    if not path.exists():
        return {"repositories": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Helm repository catalog is invalid JSON: {path}") from exc


def _write_catalog(catalog: dict) -> None:
    path = _catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _normalize_repo_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-")
    return normalized or "repo"


def _ephemeral_repo_alias(repo_name: str) -> str:
    digest = hashlib.sha1(repo_name.encode("utf-8")).hexdigest()[:8]
    return f"canvas-{_normalize_repo_name(repo_name)[:40]}-{digest}"


def _run_helm_repo(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["helm", "repo", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"helm repo {' '.join(args)} failed")
    return result


def _run_helm_search_repo(repo_name: str) -> list[dict]:
    result = subprocess.run(
        ["helm", "search", "repo", repo_name, "--versions", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "helm search repo failed")
    return json.loads(result.stdout or "[]")


def _group_repo_charts(raw_entries: list[dict], repo_name: str, repo_url: str) -> list[dict]:
    grouped: dict[str, dict] = {}
    for entry in raw_entries:
        full_name = str(entry.get("name", "")).strip()
        chart_name = full_name.split("/", 1)[1] if "/" in full_name else full_name
        if not chart_name:
            continue

        version = str(entry.get("version", "")).strip()
        app_version = str(entry.get("app_version", "") or "").strip() or None
        record = grouped.setdefault(
            chart_name,
            {
                "name": chart_name,
                "full_name": f"{repo_name}/{chart_name}",
                "repo_name": repo_name,
                "repo_url": repo_url,
                "description": str(entry.get("description", "")).strip(),
                "versions": [],
                "latest_version": "",
                "latest_app_version": None,
            },
        )
        if version and version not in {item["version"] for item in record["versions"]}:
            record["versions"].append({"version": version, "app_version": app_version})

    charts = []
    for chart_name in sorted(grouped):
        chart = grouped[chart_name]
        if chart["versions"]:
            chart["latest_version"] = chart["versions"][0]["version"]
            chart["latest_app_version"] = chart["versions"][0]["app_version"]
        charts.append(chart)
    return charts


def list_repo_charts(repo_url: str, repo_name: str = "canvas-repo") -> list[dict]:
    alias = _ephemeral_repo_alias(repo_name)
    try:
        _run_helm_repo("add", alias, repo_url)
        _run_helm_repo("update", alias)
        raw_entries = _run_helm_search_repo(alias)
        return _group_repo_charts(raw_entries, repo_name=repo_name, repo_url=repo_url)
    finally:
        subprocess.run(["helm", "repo", "remove", alias], capture_output=True, timeout=10)


def list_repositories() -> list[dict]:
    catalog = _read_catalog()
    repositories = sorted(catalog.get("repositories", []), key=lambda item: item.get("name", ""))
    output: list[dict] = []
    for repo in repositories:
        charts = repo.get("charts", [])
        output.append(
            {
                "name": repo.get("name", ""),
                "url": repo.get("url", ""),
                "status": repo.get("status", "pending"),
                "error": repo.get("error"),
                "chart_count": len(charts),
                "last_synced_at": repo.get("last_synced_at"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
            }
        )
    return output


def add_repository(name: str, url: str) -> dict:
    repo_name = name.strip()
    repo_url = url.strip()
    if not repo_name or not repo_url:
        raise RuntimeError("Repository name and URL are required")

    catalog = _read_catalog()
    existing = next((item for item in catalog["repositories"] if item.get("name") == repo_name), None)
    if existing:
        raise RuntimeError(f"Helm repository already exists: {repo_name}")

    now = _now_iso()
    repo = {
        "name": repo_name,
        "url": repo_url,
        "status": "pending",
        "error": None,
        "charts": [],
        "created_at": now,
        "updated_at": now,
        "last_synced_at": None,
    }
    catalog["repositories"].append(repo)
    _write_catalog(catalog)
    return sync_repository(repo_name)


def remove_repository(name: str) -> None:
    catalog = _read_catalog()
    remaining = [item for item in catalog.get("repositories", []) if item.get("name") != name]
    if len(remaining) == len(catalog.get("repositories", [])):
        raise RuntimeError(f"Helm repository not found: {name}")
    catalog["repositories"] = remaining
    _write_catalog(catalog)


def sync_repository(name: str) -> dict:
    catalog = _read_catalog()
    repo = next((item for item in catalog.get("repositories", []) if item.get("name") == name), None)
    if not repo:
        raise RuntimeError(f"Helm repository not found: {name}")

    now = _now_iso()
    try:
        charts = list_repo_charts(repo_url=repo["url"], repo_name=repo["name"])
        repo["charts"] = charts
        repo["status"] = "ready"
        repo["error"] = None
        repo["last_synced_at"] = now
        repo["updated_at"] = now
    except Exception as exc:
        repo["status"] = "error"
        repo["error"] = str(exc)
        repo["updated_at"] = now
        _write_catalog(catalog)
        raise RuntimeError(str(exc)) from exc

    _write_catalog(catalog)
    return {
        "name": repo["name"],
        "url": repo["url"],
        "status": repo["status"],
        "error": repo.get("error"),
        "chart_count": len(repo["charts"]),
        "last_synced_at": repo.get("last_synced_at"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
    }


def list_repository_charts(name: str) -> list[dict]:
    catalog = _read_catalog()
    repo = next((item for item in catalog.get("repositories", []) if item.get("name") == name), None)
    if not repo:
        raise RuntimeError(f"Helm repository not found: {name}")
    return sorted(repo.get("charts", []), key=lambda item: item.get("name", ""))
