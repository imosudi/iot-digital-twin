from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    source_type: str = "EDGE_GATEWAY"
    source_id: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    method: str | None = None
    transformation: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class StateVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    provenance: Provenance | None = None


class TwinState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    desired: StateVector | None = None
    reported: StateVector | None = None
    observed: StateVector | None = None
    predicted: StateVector | None = None
