from pydantic import BaseModel, Field


def first_value(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


class ComponentStatus(BaseModel):
    phase: str | None = None
    summary: str | None = None


class ComponentResponse(BaseModel):
    name: str
    namespace: str
    version: str | None = None
    description: str | None = None
    canvasType: str | None = None
    functionalBlock: str | None = None
    phase: str | None = None
    status: ComponentStatus = Field(default_factory=ComponentStatus)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    createdAt: str | None = None

    @classmethod
    def from_k8s(cls, raw: dict) -> "ComponentResponse":
        metadata = raw.get("metadata", {})
        spec = raw.get("spec", {})
        status = raw.get("status", {})
        summary = status.get("summary", {})
        labels = metadata.get("labels", {}) or {}

        summary_status = status.get("summary/status", {}) or {}
        phase = first_value(
            summary_status.get("deployment_status"),
            summary.get("deployment_status"),
            summary.get("phase"),
            status.get("phase"),
        )
        canvas_type = first_value(
            spec.get("canvasType"),
            spec.get("canvasRole"),
            spec.get("type"),
            labels.get("oda.tmforum.org/type"),
            labels.get("oda.tmforum.org/canvasType"),
            labels.get("oda.tmforum.org/canvas-type"),
        )

        component_metadata = spec.get("componentMetadata", {})
        functional_block = component_metadata.get("functionalBlock") or spec.get("functionalBlock")

        return cls(
            name=metadata.get("name", ""),
            namespace=metadata.get("namespace", ""),
            version=spec.get("version") or component_metadata.get("version"),
            description=spec.get("description") or component_metadata.get("description"),
            canvasType=canvas_type,
            functionalBlock=functional_block,
            phase=phase,
            status=ComponentStatus(
                phase=phase,
                summary=summary.get("message"),
            ),
            labels=labels,
            annotations=metadata.get("annotations", {}) or {},
            createdAt=first_value(
                metadata.get("creationTimestamp"),
                metadata.get("creation_timestamp"),
            ),
        )
