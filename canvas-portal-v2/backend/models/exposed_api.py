from pydantic import BaseModel
from typing import Literal


class GatewayResource(BaseModel):
    kind: str
    name: str
    namespace: str
    group: str


class PolicyResource(BaseModel):
    plugin_type: str
    name: str | None = None
    namespace: str | None = None
    enabled: bool = True
    config: dict = {}


class ExposedAPIResponse(BaseModel):
    name: str
    namespace: str
    url: str | None = None
    status: Literal["ready", "notReady", "unknown"] = "unknown"
    implementation: str | None = None
    canvas_type: Literal["istio", "kong", "apisix"] | None = None
    gateway_resource: GatewayResource | None = None
    policies: list[PolicyResource] = []
    error: str | None = None
