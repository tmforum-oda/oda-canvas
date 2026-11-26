import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


class CanvasPortalError(Exception):

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CanvasDetectionError(CanvasPortalError):
    def __init__(self):
        super().__init__("Unable to detect canvas type from cluster CRDs", 503)


class K8sResourceNotFound(CanvasPortalError):
    def __init__(self, kind: str, name: str):
        super().__init__(f"{kind} '{name}' not found", 404)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(CanvasPortalError)
    async def canvas_portal_error_handler(request: Request, exc: CanvasPortalError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(ApiException)
    async def k8s_api_exception_handler(request: Request, exc: ApiException):
        status_code = exc.status if isinstance(exc.status, int) else 500
        return JSONResponse(status_code=status_code, content={"detail": exc.reason or "Kubernetes API error"})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", str(exc))
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})
