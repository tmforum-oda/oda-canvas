from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):

    APP_ENV: Literal["development", "production"] = "production"
    LOG_LEVEL: str = "info"
    HEALTH_RATE_LIMIT_PER_MINUTE: int = 120

    IDM_PROVIDER: Literal["keycloak", "entraid"] = "keycloak"

    KEYCLOAK_URL: str = ""
    KEYCLOAK_REALM: str = "canvas"
    KEYCLOAK_CLIENT_ID: str = "canvas-portal"
    KEYCLOAK_ADMIN_CLIENT_ID: str = "canvas-portal-admin"
    KEYCLOAK_ADMIN_CLIENT_SECRET: str = ""

    AUTH_REFRESH_COOKIE_NAME: str = "canvas_portal_refresh"
    AUTH_COOKIE_SECURE: bool = True
    AUTH_COOKIE_SAMESITE: Literal["strict", "lax", "none"] = "strict"

    ENTRAID_TENANT_ID: str = ""
    ENTRAID_CLIENT_ID: str = ""
    ENTRAID_CLIENT_SECRET: str = ""

    K8S_MODE: Literal["incluster", "outofcluster"] = "incluster"
    K8S_REMOTE_API_URL: str = ""
    K8S_REMOTE_SA_TOKEN: str = ""
    K8S_REMOTE_CA_CERT: str = ""

    CONFORMANCE_REPO_URL: str = "https://github.com/tmforum-oda/oda-canvas.git"
    CONFORMANCE_REPO_BRANCH: str = "main"
    CONFORMANCE_DEFAULT_TAGS: str = ""
    CONFORMANCE_TIMEOUT_MINUTES: int = 60
    CONFORMANCE_RUN_STORE_PATH: str = "/app/data/conformance-runs.json"
    CONFORMANCE_WORK_DIR: str = "/app/data/conformance-work"
    CONFORMANCE_SCRATCH_DIR: str = "/var/conformance-scratch"
    CONFORMANCE_KEYCLOAK_USER: str = "admin"
    CONFORMANCE_KEYCLOAK_PASSWORD: str = ""
    CONFORMANCE_KEYCLOAK_BASE_URL: str = ""
    CONFORMANCE_KEYCLOAK_REALM: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    INSTALL_TARGET_NAMESPACES_JSON: str = "[]"

    ALLOWED_CHART_SOURCES_JSON: str = "[]"

    @property
    def allowed_chart_sources(self) -> list[str]:
        import json
        try:
            value = json.loads(self.ALLOWED_CHART_SOURCES_JSON)
        except (json.JSONDecodeError, TypeError):
            return []
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]

    @property
    def install_target_namespaces(self) -> list[str]:
        import json
        try:
            value = json.loads(self.INSTALL_TARGET_NAMESPACES_JSON)
        except (json.JSONDecodeError, TypeError):
            return []
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str) and item]

    @property
    def keycloak_issuer_url(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer_url}/protocol/openid-connect/certs"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_issuer_url}/protocol/openid-connect/token"

    @property
    def keycloak_admin_base_url(self) -> str:
        return f"{self.KEYCLOAK_URL}/admin/realms/{self.KEYCLOAK_REALM}"

    @property
    def conformance_keycloak_base_url(self) -> str:
        base_url = self.CONFORMANCE_KEYCLOAK_BASE_URL or self.KEYCLOAK_URL
        return base_url.rstrip("/") + "/" if base_url else ""

    @property
    def conformance_keycloak_realm(self) -> str:
        return self.CONFORMANCE_KEYCLOAK_REALM or self.KEYCLOAK_REALM

    @property
    def entraid_issuer_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.ENTRAID_TENANT_ID}/v2.0"

    @property
    def entraid_jwks_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.ENTRAID_TENANT_ID}/discovery/v2.0/keys"

    @property
    def entraid_token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.ENTRAID_TENANT_ID}/oauth2/v2.0/token"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
