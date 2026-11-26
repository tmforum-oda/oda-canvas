from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from auth.middleware import get_current_user
from auth.models import AuthUser
from k8s.resources.operators import list_operators, get_operator
from k8s.resources.pods import get_pod_logs, get_pod_containers, stream_pod_logs

router = APIRouter(prefix="/api/operators", tags=["operators"])


@router.get("")
def get_operators(user: AuthUser = Depends(get_current_user)):
    return list_operators(user)


@router.get("/{namespace}/{name}")
def get_operator_detail(
    namespace: str,
    name: str,
    user: AuthUser = Depends(get_current_user),
):
    return get_operator(name, namespace, user)


@router.get("/{namespace}/{name}/pods/{pod_name}/containers")
def get_operator_pod_containers(
    namespace: str,
    name: str,
    pod_name: str,
    user: AuthUser = Depends(get_current_user),
):
    return {"containers": get_pod_containers(pod_name, namespace, user)}


@router.get(
    "/{namespace}/{name}/pods/{pod_name}/logs",
    response_class=PlainTextResponse,
)
def get_operator_pod_logs(
    namespace: str,
    name: str,
    pod_name: str,
    container: str | None = Query(None, description="Container name"),
    tail: int = Query(500, description="Number of log lines from end"),
    previous: bool = Query(False, description="Return previous container logs"),
    user: AuthUser = Depends(get_current_user),
):
    return get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        user=user,
        container=container,
        tail_lines=tail,
        previous=previous,
    )


@router.get("/{namespace}/{name}/pods/{pod_name}/logs/stream")
def stream_operator_pod_logs(
    namespace: str,
    name: str,
    pod_name: str,
    container: str | None = Query(None, description="Container name"),
    tail: int = Query(100, description="Lines of history to include before live tail"),
    previous: bool = Query(False, description="Stream previous (crashed) instance"),
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
