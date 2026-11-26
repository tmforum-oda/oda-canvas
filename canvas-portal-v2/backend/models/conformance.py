from typing import Literal

from pydantic import BaseModel, Field


ConformanceRunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
ConformanceRunMode = Literal["tags", "features"]


class CanvasConformanceConfig(BaseModel):
    repo_url: str
    branch: str
    default_tags: str = ""
    keycloak_base_url: str
    keycloak_realm: str


class CanvasConformanceRunRequest(BaseModel):
    mode: ConformanceRunMode = "tags"
    tags: str | None = None
    features: list[str] = Field(default_factory=list)


class CanvasConformanceResultSummary(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0


class CanvasConformanceRun(BaseModel):
    id: str
    suite: Literal["canvas"] = "canvas"
    status: ConformanceRunStatus
    mode: ConformanceRunMode
    repo_url: str
    branch: str
    tags: str = ""
    features: list[str] = Field(default_factory=list)
    created_by: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    phase: str = "queued"
    progress: int = 0
    message: str = ""
    exit_code: int | None = None
    result: CanvasConformanceResultSummary = Field(default_factory=CanvasConformanceResultSummary)
    log_tail: list[str] = Field(default_factory=list)
    log_path: str | None = None
    cucumber_json_path: str | None = None


class CanvasConformanceRunList(BaseModel):
    runs: list[CanvasConformanceRun]
    active_run: CanvasConformanceRun | None = None


class CanvasConformanceCatalog(BaseModel):
    repo: str
    branch: str
    path: str
    features: list[str] = Field(default_factory=list)
    use_case_tags: list[str] = Field(default_factory=list)
    feature_tags: list[str] = Field(default_factory=list)
