import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from k8s.canvas_detector import detect_canvas_type, get_cached_canvas_type
from utils.exceptions import register_exception_handlers
from utils.ratelimit import RateLimiter
from routers import auth, components, conformance, dependent_apis, exposed_apis, gateway, helm, model_gateway, operators, pods, cluster, observability

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Canvas Portal starting up...")
    canvas_type = await detect_canvas_type()
    logger.info("Canvas type: %s | IDM: %s | K8s mode: %s", canvas_type, settings.IDM_PROVIDER, settings.K8S_MODE)
    yield
    logger.info("Canvas Portal shutting down...")


app = FastAPI(
    title="Canvas Portal API",
    description="Management portal for TM Forum ODA Canvas",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(components.router)
app.include_router(exposed_apis.router)
app.include_router(dependent_apis.router)
app.include_router(gateway.router)
app.include_router(helm.router)
app.include_router(conformance.router)
app.include_router(operators.router)
app.include_router(pods.router)
app.include_router(cluster.router)
app.include_router(observability.router)
app.include_router(model_gateway.router)


health_rate_limiter = RateLimiter(max_requests=settings.HEALTH_RATE_LIMIT_PER_MINUTE, window_seconds=60)


@app.get("/health", dependencies=[Depends(health_rate_limiter)])
def health():
    return {"status": "ok", "canvasType": get_cached_canvas_type(), "idmProvider": settings.IDM_PROVIDER}
