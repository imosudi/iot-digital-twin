from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DataType(StrEnum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"


class TelemetryQuality(StrEnum):
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    MISSING = "MISSING"
    SIMULATED = "SIMULATED"


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: DataType
    unit: str | None = None
    description: str | None = None
    required: bool = False


class TelemetryDefinition(FieldDefinition):
    sampling_interval_seconds: float | None = Field(default=None, gt=0)
    engineering_range: tuple[float, float] | None = None


class EntityTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(pattern=r"^\d+\.\d+$")
    display_name: str
    description: str | None = None
    properties: dict[str, FieldDefinition] = Field(default_factory=dict)
    telemetry: dict[str, TelemetryDefinition] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)


class DigitalEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    site_id: str | None = None
    type: str
    name: str = Field(min_length=1)
    template: str
    version: str
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityCreate(BaseModel):
    site_id: str | None = None
    type: str
    name: str = Field(min_length=1)
    template: str
    version: str
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SiteCreate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Site(BaseModel):
    id: str
    name: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipCreate(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
