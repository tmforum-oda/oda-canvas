from datetime import date, datetime
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


def normalize_yaml_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize_yaml_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_yaml_value(item) for key, item in value.items()}
    return value


class ModelGatewayServiceSpecPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    spec: dict[str, Any] | None = None
    spec_yaml: str | None = Field(default=None, alias="specYaml")

    def resolved_spec(self) -> dict[str, Any]:
        if self.spec is not None:
            return self.spec
        if self.spec_yaml is None:
            raise ValueError("Provide either spec or specYaml")

        try:
            loaded = yaml.safe_load(self.spec_yaml)
        except yaml.YAMLError as exc:
            raise ValueError(f"Spec YAML is invalid: {exc}") from exc

        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            raise ValueError("Spec YAML must define an object")
        return normalize_yaml_value(loaded)


class ModelGatewayServiceCreate(ModelGatewayServiceSpecPayload):
    name: str = Field(..., min_length=1)
    namespace: str = Field(..., min_length=1)


class ModelGatewayServiceUpdate(ModelGatewayServiceSpecPayload):
    pass


class ModelGatewayServiceValidate(ModelGatewayServiceCreate):
    mode: Literal["create", "update"] = "create"
