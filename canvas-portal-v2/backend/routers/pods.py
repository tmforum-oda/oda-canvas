from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.pods import (
    get_pod_logs,
    get_pod_containers,
    list_pods_in_namespace,
    stream_pod_logs,
)

router = APIRouter(prefix="/api/pods", tags=["pods"])


@router.get("/{namespace}")
def get_pods(
    namespace: str,
    user: AuthUser = Depends(get_current_user),
):
    return list_pods_in_namespace(namespace, user)


@router.get("/{namespace}/{pod_name}/containers")
def get_containers(
    namespace: str,
    pod_name: str,
    user: AuthUser = Depends(get_current_user),
):
    return {"containers": get_pod_containers(pod_name, namespace, user)}


@router.get(
    "/{namespace}/{pod_name}/logs",
    response_class=PlainTextResponse,
)
def download_pod_logs(
    namespace: str,
    pod_name: str,
    container: str | None = Query(None, description="Container name (optional)"),
    tail: int = Query(500, description="Lines from end of log"),
    previous: bool = Query(False, description="Previous container instance logs"),
    user: AuthUser = Depends(get_current_user),
):
    logs = get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        user=user,
        container=container,
        tail_lines=tail,
        previous=previous,
    )
    return Response(
        content=logs,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{pod_name}.log"'
        },
    )


@router.get("/{namespace}/{pod_name}/logs/stream")
def stream_logs(
    namespace: str,
    pod_name: str,
    container: str | None = Query(None, description="Container name (optional)"),
    tail: int = Query(100, description="Lines of history to include before live tail"),
    previous: bool = Query(False, description="Stream from the previous (crashed) instance"),
    user: AuthUser = Depends(get_current_user),
):
    return StreamingResponse(
        stream_pod_logs(
            pod_name=pod_name,
            namespace=namespace,
            user=user,
            container=container,
            tail_lines=tail,
            previous=previous,
        ),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
        },
    )
