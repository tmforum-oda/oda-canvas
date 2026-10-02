from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response

from auth.middleware import get_current_user
from auth.models import AuthUser
from conformance.runner import runner
from models.conformance import (
    CanvasConformanceCatalog,
    CanvasConformanceConfig,
    CanvasConformanceRun,
    CanvasConformanceRunList,
    CanvasConformanceRunRequest,
)

router = APIRouter(prefix="/api/conformance", tags=["conformance"])


@router.get("/canvas/config", response_model=CanvasConformanceConfig)
def get_canvas_conformance_config(user: AuthUser = Depends(get_current_user)):
    return runner.get_config()


@router.get("/canvas/catalog", response_model=CanvasConformanceCatalog)
def get_canvas_conformance_catalog(
    refresh: bool = Query(False, description="Force re-fetch from GitHub instead of using cached catalog"),
    user: AuthUser = Depends(get_current_user),
):
    try:
        return runner.get_catalog(refresh=refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/canvas/runs", response_model=CanvasConformanceRunList)
def list_canvas_conformance_runs(
    limit: int = Query(20, ge=1, le=100),
    user: AuthUser = Depends(get_current_user),
):
    return runner.list_runs(limit=limit)


@router.post("/canvas/runs", response_model=CanvasConformanceRun, status_code=status.HTTP_202_ACCEPTED)
def start_canvas_conformance_run(
    payload: CanvasConformanceRunRequest,
    user: AuthUser = Depends(get_current_user),
):
    try:
        return runner.start_run(payload, user)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/canvas/runs/{run_id}", response_model=CanvasConformanceRun)
def get_canvas_conformance_run(run_id: str, user: AuthUser = Depends(get_current_user)):
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Conformance run not found")
    return run


@router.get("/canvas/runs/{run_id}/logs")
def get_canvas_conformance_logs(
    run_id: str,
    tail: int = Query(500, ge=1, le=5000),
    user: AuthUser = Depends(get_current_user),
):
    logs = runner.get_logs(run_id, tail=tail)
    if logs is None:
        raise HTTPException(status_code=404, detail="Conformance run not found")
    return {"id": run_id, "lines": logs}


@router.get("/canvas/runs/{run_id}/logs/download")
def download_canvas_conformance_log(
    run_id: str,
    user: AuthUser = Depends(get_current_user),
):
    log_path = runner.get_log_path(run_id)
    if log_path is None:
        raise HTTPException(status_code=404, detail="Log file not found for this run")
    return FileResponse(
        path=str(log_path),
        media_type="text/plain",
        filename=f"canvas-conformance-{run_id}.log",
    )


@router.get("/canvas/runs/{run_id}/cucumber.json/download")
def download_canvas_conformance_cucumber_json(
    run_id: str,
    user: AuthUser = Depends(get_current_user),
):
    json_path = runner.get_cucumber_json_path(run_id)
    if json_path is None:
        raise HTTPException(status_code=404, detail="Cucumber JSON not found for this run")
    return FileResponse(
        path=str(json_path),
        media_type="application/json",
        filename=f"canvas-conformance-{run_id}.cucumber.json",
    )


@router.get("/canvas/runs/{run_id}/report.html/download")
def download_canvas_conformance_report_html(
    run_id: str,
    user: AuthUser = Depends(get_current_user),
):
    html_path = runner.get_report_html_path(run_id)
    if html_path is None:
        raise HTTPException(status_code=404, detail="HTML report not available for this run")
    return FileResponse(
        path=str(html_path),
        media_type="text/html",
        filename=f"canvas-conformance-{run_id}.report.html",
    )


@router.delete("/canvas/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_canvas_conformance_run(
    run_id: str,
    user: AuthUser = Depends(get_current_user),
):
    try:
        deleted = runner.delete_run(run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="Conformance run not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
