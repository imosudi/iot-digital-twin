from datetime import datetime, timezone
from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DataQuality
from app.domain.state import Provenance


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TelemetryReading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    twin_id: str
    component_id: str | None = None
    sensor_id: str | None = None
    metric: str
    value: Union[float, int, str, bool]
    unit: str | None = None
    quality: DataQuality = DataQuality.VALID
    event_time: datetime
    ingestion_time: datetime = Field(default_factory=utc_now)
    processing_time: datetime | None = None
    provenance: Provenance | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
