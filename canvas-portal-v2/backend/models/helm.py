from pydantic import BaseModel, Field


class HelmInstallRequest(BaseModel):
    release_name: str
    chart: str
    namespace: str
    repo_name: str | None = None
    version: str | None = None
    repo_url: str | None = None
    create_namespace: bool = False
    values: dict = Field(default_factory=dict)
    values_yaml: str | None = None
    timeout_minutes: int = Field(default=5, ge=1, le=60)


class HelmUninstallRequest(BaseModel):
    release_name: str
    namespace: str


class HelmReleaseStatus(BaseModel):
    name: str
    namespace: str
    chart: str
    app_version: str | None = None
    status: str
    updated: str | None = None


class HelmRepositoryCreateRequest(BaseModel):
    name: str
    url: str


class HelmRepositorySummary(BaseModel):
    name: str
    url: str
    status: str
    error: str | None = None
    chart_count: int = 0
    last_synced_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class HelmChartVersion(BaseModel):
    version: str
    app_version: str | None = None


class HelmRepositoryChart(BaseModel):
    name: str
    full_name: str
    repo_name: str
    repo_url: str
    description: str = ""
    latest_version: str = ""
    latest_app_version: str | None = None
    versions: list[HelmChartVersion] = Field(default_factory=list)
