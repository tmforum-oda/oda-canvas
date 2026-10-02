import json
import logging
import os
import re
import shutil
import subprocess
import threading
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from auth.models import AuthUser
from config import get_settings
from k8s.helm.installer import _cleanup_paths, _write_kubeconfig
from models.conformance import (
    CanvasConformanceCatalog,
    CanvasConformanceConfig,
    CanvasConformanceResultSummary,
    CanvasConformanceRun,
    CanvasConformanceRunList,
    CanvasConformanceRunRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()

RUNNING_STATUSES = {"queued", "running"}
LOG_TAIL_LIMIT = 250
KIT_FEATURES_PATH = "feature-definition-and-test-kit/features"
FEATURE_TAG_RE = re.compile(r"^(UC\d+-F\d+)")
USE_CASE_TAG_RE = re.compile(r"^(UC\d+)")


def repo_owner_and_name(repo_url: str) -> tuple[str, str]:
    cleaned = repo_url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    for prefix in ("https://github.com/", "http://github.com/", "git@github.com:"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    parts = cleaned.split("/")
    if len(parts) < 2:
        raise RuntimeError(f"Unsupported repository URL for catalog: {repo_url}")
    return parts[-2], parts[-1]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def duration_seconds(started_at: str | None, finished_at: str | None) -> float | None:
    start = parse_timestamp(started_at)
    finish = parse_timestamp(finished_at)
    if not start or not finish:
        return None
    return round((finish - start).total_seconds(), 2)


def safe_line(value: str) -> str:
    return value.rstrip("\r\n")


def normalize_feature_name(feature: str) -> str:
    clean = feature.strip().replace("\\", "/")
    if clean.startswith("features/"):
        clean = clean[len("features/") :]
    clean = Path(clean).name
    return clean


def html_escape(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def step_status(step: dict) -> str:
    return ((step.get("result") or {}).get("status") or "").lower()


HTML_STATUS_COLORS = {
    "passed": "#16a34a",
    "failed": "#dc2626",
    "skipped": "#737373",
    "ambiguous": "#dc2626",
    "undefined": "#dc2626",
    "pending": "#ca8a04",
}


def render_cucumber_html(cucumber_json_path: Path, run_id: str) -> str:
    try:
        data = json.loads(cucumber_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (
            f"<!doctype html><html><body><h1>No cucumber data</h1>"
            f"<p>{html_escape(exc)}</p></body></html>"
        )
    if not isinstance(data, list):
        data = []

    total = 0
    passed = 0
    failed = 0
    skipped = 0
    feature_blocks: list[str] = []
    for feature in data:
        feature_name = html_escape(feature.get("name") or feature.get("uri") or "Feature")
        scenarios_html: list[str] = []
        for scenario in feature.get("elements", []) or []:
            if scenario.get("type") == "background":
                continue
            steps = scenario.get("steps", []) or []
            statuses = [step_status(step) for step in steps if step.get("result")]
            if not statuses:
                continue
            total += 1
            if any(status in {"failed", "ambiguous", "undefined", "pending"} for status in statuses):
                status = "failed"
                failed += 1
            elif all(status == "skipped" for status in statuses):
                status = "skipped"
                skipped += 1
            else:
                status = "passed"
                passed += 1
            color = HTML_STATUS_COLORS.get(status, "#262626")
            step_rows: list[str] = []
            for step in steps:
                step_state = step_status(step)
                step_color = HTML_STATUS_COLORS.get(step_state, "#262626")
                keyword = html_escape(step.get("keyword") or "")
                name = html_escape(step.get("name") or "")
                error_msg = (step.get("result") or {}).get("error_message") or ""
                error_html = (
                    f"<pre style='margin:4px 0 0 24px;color:#dc2626;white-space:pre-wrap'>"
                    f"{html_escape(error_msg)}</pre>"
                    if error_msg
                    else ""
                )
                step_rows.append(
                    f"<li><span style='color:{step_color};font-weight:600'>"
                    f"[{html_escape(step_state or '-')}]</span> "
                    f"{keyword}{name}{error_html}</li>"
                )
            scenarios_html.append(
                "<details style='margin:6px 0;border:1px solid #e5e7eb;border-radius:6px;padding:8px'>"
                f"<summary><span style='display:inline-block;min-width:80px;color:{color};"
                f"font-weight:600'>{status.upper()}</span> "
                f"{html_escape(scenario.get('name') or 'Scenario')}</summary>"
                f"<ul style='margin:8px 0 0 16px;padding:0;list-style:none'>{''.join(step_rows)}</ul>"
                "</details>"
            )
        if scenarios_html:
            feature_blocks.append(
                f"<section style='margin-top:18px'>"
                f"<h3 style='margin:0 0 4px 0'>{feature_name}</h3>"
                f"{''.join(scenarios_html)}</section>"
            )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Canvas Conformance Report {html_escape(run_id)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:24px;color:#262626}}
header{{border-bottom:1px solid #e5e7eb;padding-bottom:12px;margin-bottom:16px}}
.summary span{{display:inline-block;margin-right:12px;padding:4px 10px;border-radius:999px;font-weight:600;font-size:13px}}
.s-total{{background:#f3f4f6;color:#262626}}
.s-passed{{background:#dcfce7;color:#15803d}}
.s-failed{{background:#fee2e2;color:#b91c1c}}
.s-skipped{{background:#e5e7eb;color:#525252}}
summary{{cursor:pointer}}
</style>
</head>
<body>
<header>
  <h1 style="margin:0">Canvas Conformance Report</h1>
  <p style="margin:4px 0 12px 0;color:#525252">Run <code>{html_escape(run_id)}</code></p>
  <div class="summary">
    <span class="s-total">Total {total}</span>
    <span class="s-passed">Passed {passed}</span>
    <span class="s-failed">Failed {failed}</span>
    <span class="s-skipped">Skipped {skipped}</span>
  </div>
</header>
{''.join(feature_blocks) or '<p>No scenarios recorded.</p>'}
</body></html>"""


def summarize_cucumber_json(path: Path) -> CanvasConformanceResultSummary:
    summary = CanvasConformanceResultSummary()
    if not path.exists():
        return summary
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Unable to parse cucumber JSON %s: %s", path, exc)
        return summary

    for feature in data if isinstance(data, list) else []:
        for scenario in feature.get("elements", []) or []:
            if scenario.get("type") == "background":
                continue
            steps = scenario.get("steps", []) or []
            statuses = [
                ((step.get("result") or {}).get("status") or "").lower()
                for step in steps
                if step.get("result")
            ]
            if not statuses:
                continue
            summary.total += 1
            if any(status in {"failed", "ambiguous", "undefined", "pending"} for status in statuses):
                summary.failed += 1
            elif all(status == "skipped" for status in statuses):
                summary.skipped += 1
            else:
                summary.passed += 1
    return summary


class CanvasConformanceRunner:
    RUN_HISTORY_LIMIT = 100

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._threads: dict[str, threading.Thread] = {}
        self._store_path = Path(settings.CONFORMANCE_RUN_STORE_PATH)
        self._work_dir = Path(settings.CONFORMANCE_WORK_DIR)
        self._scratch_dir = Path(settings.CONFORMANCE_SCRATCH_DIR)
        self._runs: list[CanvasConformanceRun] = self.load_runs()
        self.recover_interrupted_runs()
        self.gc_orphan_dirs()
        self._catalog_lock = threading.Lock()
        self._catalog_cache: dict[tuple[str, str], CanvasConformanceCatalog] = {}

    def gc_orphan_dirs(self) -> None:
        known_ids = {run.id for run in self._runs}
        for base in (self._work_dir, self._scratch_dir):
            if not base.exists():
                continue
            try:
                for child in base.iterdir():
                    if child.is_dir() and child.name not in known_ids:
                        shutil.rmtree(child, ignore_errors=True)
            except OSError as exc:
                logger.warning("Conformance GC sweep failed under %s: %s", base, exc)

    def get_catalog(self, refresh: bool = False) -> CanvasConformanceCatalog:
        repo_url = settings.CONFORMANCE_REPO_URL
        branch = settings.CONFORMANCE_REPO_BRANCH
        key = (repo_url, branch)
        if not refresh:
            with self._catalog_lock:
                cached = self._catalog_cache.get(key)
                if cached:
                    return cached

        owner, repo = repo_owner_and_name(repo_url)
        api_url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/"
            f"{KIT_FEATURES_PATH}?ref={branch}"
        )
        request = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "canvas-portal-conformance",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Unable to fetch feature catalog from GitHub: {exc}") from exc

        if not isinstance(payload, list):
            raise RuntimeError("Unexpected GitHub response while listing features")

        features: list[str] = sorted(
            item["name"]
            for item in payload
            if isinstance(item, dict)
            and item.get("type") == "file"
            and isinstance(item.get("name"), str)
            and item["name"].endswith(".feature")
        )

        use_case_tags: set[str] = set()
        feature_tags: set[str] = set()
        for name in features:
            feature_match = FEATURE_TAG_RE.match(name)
            if feature_match:
                feature_tags.add(f"@{feature_match.group(1)}")
            use_case_match = USE_CASE_TAG_RE.match(name)
            if use_case_match:
                use_case_tags.add(f"@{use_case_match.group(1)}")

        catalog = CanvasConformanceCatalog(
            repo=f"{owner}/{repo}",
            branch=branch,
            path=KIT_FEATURES_PATH,
            features=features,
            use_case_tags=sorted(use_case_tags),
            feature_tags=sorted(feature_tags),
        )
        with self._catalog_lock:
            self._catalog_cache[key] = catalog
        return catalog

    def get_config(self) -> CanvasConformanceConfig:
        return CanvasConformanceConfig(
            repo_url=settings.CONFORMANCE_REPO_URL,
            branch=settings.CONFORMANCE_REPO_BRANCH,
            default_tags=settings.CONFORMANCE_DEFAULT_TAGS,
            keycloak_base_url=settings.conformance_keycloak_base_url,
            keycloak_realm=settings.conformance_keycloak_realm,
        )

    def list_runs(self, limit: int = 20) -> CanvasConformanceRunList:
        with self._lock:
            runs = sorted(self._runs, key=lambda run: run.started_at or "", reverse=True)
            active = next((run for run in runs if run.status in RUNNING_STATUSES), None)
            return CanvasConformanceRunList(runs=runs[:limit], active_run=active)

    def get_run(self, run_id: str) -> CanvasConformanceRun | None:
        with self._lock:
            return next((run for run in self._runs if run.id == run_id), None)

    def get_log_path(self, run_id: str) -> Path | None:
        run = self.get_run(run_id)
        if not run or not run.log_path:
            return None
        path = Path(run.log_path)
        return path if path.exists() else None

    def get_cucumber_json_path(self, run_id: str) -> Path | None:
        run = self.get_run(run_id)
        if not run or not run.cucumber_json_path:
            return None
        path = Path(run.cucumber_json_path)
        return path if path.exists() else None

    def get_report_html_path(self, run_id: str) -> Path | None:
        run = self.get_run(run_id)
        if not run:
            return None
        json_path = self.get_cucumber_json_path(run_id)
        if not json_path:
            return None
        html_path = json_path.with_name("report.html")
        if not html_path.exists():
            try:
                html_path.write_text(render_cucumber_html(json_path, run_id), encoding="utf-8")
            except OSError as exc:
                logger.warning("Unable to write report.html for %s: %s", run_id, exc)
                return None
        return html_path

    def delete_run(self, run_id: str) -> bool:
        with self._lock:
            run = next((item for item in self._runs if item.id == run_id), None)
            if not run:
                return False
            if run.status in RUNNING_STATUSES:
                raise RuntimeError(f"Run {run_id} is {run.status} and cannot be deleted")
            self._runs = [item for item in self._runs if item.id != run_id]
            self.save_runs_locked()
        for base in (self._work_dir, self._scratch_dir):
            run_dir = base / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir, ignore_errors=True)
        return True

    def get_logs(self, run_id: str, tail: int = 500) -> list[str] | None:
        run = self.get_run(run_id)
        if not run:
            return None
        log_path = Path(run.log_path) if run.log_path else None
        if not log_path or not log_path.exists():
            return run.log_tail[-tail:]
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-tail:]
        except OSError:
            return run.log_tail[-tail:]

    def start_run(self, payload: CanvasConformanceRunRequest, user: AuthUser) -> CanvasConformanceRun:
        with self._lock:
            active = next((run for run in self._runs if run.status in RUNNING_STATUSES), None)
            if active:
                raise RuntimeError(f"Conformance run {active.id} is already {active.status}")

            run_id = uuid.uuid4().hex[:12]
            repo_url = settings.CONFORMANCE_REPO_URL.strip()
            branch = settings.CONFORMANCE_REPO_BRANCH.strip()
            tags = (payload.tags or settings.CONFORMANCE_DEFAULT_TAGS or "").strip()
            features = [normalize_feature_name(feature) for feature in payload.features if feature.strip()]
            run_dir = self._work_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            run = CanvasConformanceRun(
                id=run_id,
                status="queued",
                mode=payload.mode,
                repo_url=repo_url,
                branch=branch,
                tags=tags,
                features=features,
                created_by=user.username or user.email or user.sub,
                started_at=utc_now(),
                phase="queued",
                progress=0,
                message="Run queued",
                log_path=str(run_dir / "run.log"),
                cucumber_json_path=str(run_dir / "cucumber.json"),
            )
            self._runs.insert(0, run)
            self.save_runs_locked()

            thread = threading.Thread(target=self.run_worker, args=(run_id, run_dir), daemon=True)
            self._threads[run_id] = thread
            thread.start()
            return run

    def load_runs(self) -> list[CanvasConformanceRun]:
        if not self._store_path.exists():
            return []
        try:
            raw = json.loads(self._store_path.read_text(encoding="utf-8"))
            items = raw.get("runs", raw if isinstance(raw, list) else [])
            return [CanvasConformanceRun.model_validate(item) for item in items]
        except Exception as exc:
            logger.warning("Unable to load conformance run store %s: %s", self._store_path, exc)
            return []

    def recover_interrupted_runs(self) -> None:
        changed = False
        with self._lock:
            for run in self._runs:
                if run.status in RUNNING_STATUSES:
                    run.status = "failed"
                    run.phase = "interrupted"
                    run.progress = 100
                    run.finished_at = utc_now()
                    run.duration_seconds = duration_seconds(run.started_at, run.finished_at)
                    run.message = "Run was interrupted because the backend process restarted"
                    changed = True
            if changed:
                self.save_runs_locked()

    def save_runs_locked(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        if len(self._runs) > self.RUN_HISTORY_LIMIT:
            self._runs = self._runs[: self.RUN_HISTORY_LIMIT]
            self.gc_orphan_dirs()
        payload = {
            "runs": [run.model_dump() for run in self._runs],
            "updated_at": utc_now(),
        }
        tmp_path = self._store_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self._store_path)

    def mutate_run(self, run_id: str, mutate: Callable[[CanvasConformanceRun], None]) -> CanvasConformanceRun | None:
        with self._lock:
            run = next((item for item in self._runs if item.id == run_id), None)
            if not run:
                return None
            mutate(run)
            self.save_runs_locked()
            return run

    def set_progress(self, run_id: str, phase: str, progress: int, message: str) -> None:
        def mutate(run: CanvasConformanceRun) -> None:
            run.status = "running"
            run.phase = phase
            run.progress = max(0, min(progress, 99))
            run.message = message

        self.mutate_run(run_id, mutate)

    def append_log(self, run_id: str, line: str) -> None:
        clean = safe_line(line)
        with self._lock:
            run = next((item for item in self._runs if item.id == run_id), None)
            if not run:
                return
            if run.log_path:
                try:
                    Path(run.log_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(run.log_path, "a", encoding="utf-8", errors="replace") as log_file:
                        log_file.write(clean + "\n")
                except OSError as exc:
                    logger.warning("Unable to append conformance log for %s: %s", run_id, exc)
            run.log_tail.append(clean)
            if len(run.log_tail) > LOG_TAIL_LIMIT:
                run.log_tail = run.log_tail[-LOG_TAIL_LIMIT:]
            self.save_runs_locked()

    def run_streamed_command(
        self,
        run_id: str,
        cmd: list[str],
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> int:
        self.append_log(run_id, f"$ {' '.join(cmd)}")
        killed_by_timeout = {"value": False}
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def kill_process() -> None:
            killed_by_timeout["value"] = True
            process.kill()

        timer = threading.Timer(timeout_seconds, kill_process) if timeout_seconds else None
        if timer:
            timer.start()
        try:
            assert process.stdout is not None
            for line in process.stdout:
                self.append_log(run_id, line)
            return_code = process.wait()
        finally:
            if timer:
                timer.cancel()

        if killed_by_timeout["value"]:
            raise TimeoutError(f"Command timed out after {timeout_seconds} seconds: {' '.join(cmd)}")
        return return_code

    def run_worker(self, run_id: str, run_dir: Path) -> None:
        scratch_run_dir = self._scratch_dir / run_id
        scratch_run_dir.mkdir(parents=True, exist_ok=True)
        repo_dir = scratch_run_dir / "repo"
        cleanup_paths: list[str] = []
        try:
            run = self.get_run(run_id)
            if not run:
                return
            self.append_log(run_id, f"Starting Canvas CTK run {run_id}")
            self.append_log(run_id, f"Repository: {run.repo_url} ({run.branch})")

            for binary in ("git", "npm", "helm"):
                if not shutil.which(binary):
                    raise RuntimeError(f"Required binary '{binary}' was not found in PATH")

            self.set_progress(run_id, "cloning", 8, "Cloning CTK repository")
            clone_code = self.run_streamed_command(
                run_id,
                ["git", "clone", "--depth", "1", "--branch", run.branch, run.repo_url, str(repo_dir)],
                timeout_seconds=600,
            )
            if clone_code != 0:
                raise RuntimeError(f"git clone failed with exit code {clone_code}")

            kit_dir = repo_dir / "feature-definition-and-test-kit"
            features_dir = kit_dir / "features"
            if not kit_dir.is_dir() or not features_dir.is_dir():
                raise RuntimeError("feature-definition-and-test-kit/features was not found in the cloned repository")

            if run.mode == "features":
                missing = [feature for feature in run.features if not (features_dir / feature).exists()]
                if missing:
                    raise RuntimeError(f"Feature file(s) not found in the CTK repo: {', '.join(missing)}")

            kubeconfig_path, cleanup_paths = _write_kubeconfig()
            env = {
                **os.environ,
                "KUBECONFIG": kubeconfig_path,
                "KEYCLOAK_USER": settings.CONFORMANCE_KEYCLOAK_USER,
                "KEYCLOAK_PASSWORD": settings.CONFORMANCE_KEYCLOAK_PASSWORD,
                "KEYCLOAK_BASE_URL": settings.conformance_keycloak_base_url,
                "KEYCLOAK_REALM": settings.conformance_keycloak_realm,
                "CUCUMBER_PUBLISH_QUIET": "true",
            }

            package_dirs = sorted(
                path.parent for path in (kit_dir / "utilities").glob("*/package.json")
            )
            package_dirs.append(kit_dir)
            total_installs = len(package_dirs)
            for index, package_dir in enumerate(package_dirs, start=1):
                percent = 15 + int((index - 1) / max(total_installs, 1) * 35)
                rel = package_dir.relative_to(kit_dir)
                self.set_progress(run_id, "installing", percent, f"Installing npm dependencies in {rel}")
                install_code = self.run_streamed_command(
                    run_id,
                    ["npm", "install", "--no-audit", "--no-fund"],
                    cwd=package_dir,
                    env=env,
                    timeout_seconds=900,
                )
                if install_code != 0:
                    raise RuntimeError(f"npm install failed in {rel} with exit code {install_code}")

            cucumber_json = Path(run.cucumber_json_path or run_dir / "cucumber.json")
            cucumber_bin = kit_dir / "node_modules" / ".bin" / "cucumber-js"
            if not cucumber_bin.exists():
                raise RuntimeError("cucumber-js binary was not installed under node_modules/.bin")

            command = [str(cucumber_bin), "--format", f"json:{cucumber_json}"]
            if run.mode == "tags":
                if not run.tags:
                    raise RuntimeError("Tag expression is required when mode is 'tags'")
                command += ["--tags", run.tags]
                selection = run.tags
            elif run.mode == "features":
                if not run.features:
                    raise RuntimeError(f"At least one feature file is required when mode is '{run.mode}'")
                command += [f"features/{feature}" for feature in run.features]
                selection = ", ".join(run.features)
            else:
                raise RuntimeError(f"Unsupported conformance run mode: {run.mode}")

            self.set_progress(run_id, "running", 65, f"Running CTK tests: {selection}")
            timeout_seconds = max(1, settings.CONFORMANCE_TIMEOUT_MINUTES) * 60
            exit_code = self.run_streamed_command(
                run_id,
                command,
                cwd=kit_dir,
                env=env,
                timeout_seconds=timeout_seconds,
            )
            result = summarize_cucumber_json(cucumber_json)
            if cucumber_json.exists():
                try:
                    (cucumber_json.with_name("report.html")).write_text(
                        render_cucumber_html(cucumber_json, run_id), encoding="utf-8"
                    )
                except OSError as exc:
                    logger.warning("Unable to write report.html for %s: %s", run_id, exc)

            def finish_success_or_failure(item: CanvasConformanceRun) -> None:
                item.exit_code = exit_code
                item.result = result
                item.status = "succeeded" if exit_code == 0 else "failed"
                item.phase = "completed" if exit_code == 0 else "failed"
                item.progress = 100
                item.finished_at = utc_now()
                item.duration_seconds = duration_seconds(item.started_at, item.finished_at)
                if exit_code == 0:
                    item.message = "Canvas conformance run completed successfully"
                else:
                    item.message = f"Canvas conformance run failed with exit code {exit_code}"

            self.mutate_run(run_id, finish_success_or_failure)
            self.append_log(run_id, f"Finished with exit code {exit_code}")
        except Exception as exc:
            logger.exception("Canvas conformance run %s failed", run_id)
            self.append_log(run_id, f"ERROR: {exc}")

            def finish_error(item: CanvasConformanceRun) -> None:
                item.status = "failed"
                item.phase = "failed"
                item.progress = 100
                item.finished_at = utc_now()
                item.duration_seconds = duration_seconds(item.started_at, item.finished_at)
                item.message = str(exc)

            self.mutate_run(run_id, finish_error)
        finally:
            _cleanup_paths(cleanup_paths)
            if scratch_run_dir.exists():
                shutil.rmtree(scratch_run_dir, ignore_errors=True)
            with self._lock:
                self._threads.pop(run_id, None)


runner = CanvasConformanceRunner()
