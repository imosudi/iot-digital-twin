from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AssetClass, HealthDerivationMethod, TwinEventType, TwinLifecycleStatus
from app.domain.state import Provenance, TwinState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Sensor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: str
    metric: str
    unit: str | None = None
    sampling_interval_seconds: float | None = Field(default=None, gt=0)
    engineering_range: tuple[float, float] | None = None
    status: str = "ACTIVE"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str
    name: str
    component_type: str
    serial_number: str | None = None
    sensors: dict[str, Sensor] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)
    status: str = "ACTIVE"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TwinHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health_state: str = "OPTIMAL"
    health_score: float = Field(ge=0.0, le=100.0)
    performance_state: str = "NORMAL"
    availability: float = Field(default=1.0, ge=0.0, le=1.0)
    efficiency: float | None = None
    deviation: float | None = None
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    derivation_method: HealthDerivationMethod = HealthDerivationMethod.RULE_DERIVED
    updated_at: datetime = Field(default_factory=utc_now)
    evidence: dict[str, Any] = Field(default_factory=dict)


class TwinEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    twin_id: str
    event_type: TwinEventType
    severity: str = "INFO"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    provenance: Provenance | None = None


class TwinEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: TwinEventType
    severity: str = "INFO"
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance | None = None


class DigitalTwin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    twin_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    asset_id: str = Field(min_length=1)
    external_id: str | None = None
    twin_type: str
    asset_class: AssetClass = AssetClass.SOLAR_PV
    name: str = Field(min_length=1)
    description: str | None = None
    status: TwinLifecycleStatus = TwinLifecycleStatus.REGISTERED
    tenant_id: str | None = None
    portfolio_id: str | None = None
    site_id: str | None = None
    parent_twin_id: str | None = None
    components: dict[str, Component] = Field(default_factory=dict)
    sensors: dict[str, Sensor] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    state: TwinState = Field(default_factory=TwinState)
    health: TwinHealth | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DigitalTwinCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    twin_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    asset_id: str = Field(min_length=1)
    external_id: str | None = None
    twin_type: str
    asset_class: AssetClass = AssetClass.SOLAR_PV
    name: str = Field(min_length=1)
    description: str | None = None
    status: TwinLifecycleStatus = TwinLifecycleStatus.REGISTERED
    tenant_id: str | None = None
    portfolio_id: str | None = None
    site_id: str | None = None
    parent_twin_id: str | None = None
    components: dict[str, Component] = Field(default_factory=dict)
    sensors: dict[str, Sensor] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DigitalTwinUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    external_id: str | None = None
    twin_type: str | None = None
    asset_class: AssetClass | None = None
    tenant_id: str | None = None
    portfolio_id: str | None = None
    site_id: str | None = None
    parent_twin_id: str | None = None
    capabilities: list[str] | None = None
    configuration: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class LifecycleTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_status: TwinLifecycleStatus
    reason: str = Field(min_length=1)
    operator: str = Field(min_length=1)
