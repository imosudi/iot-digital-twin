from enum import StrEnum


class TwinLifecycleStatus(StrEnum):
    """Lifecycle states for physical asset digital twins."""

    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    COMMISSIONED = "COMMISSIONED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class AssetClass(StrEnum):
    """Asset classification for renewable energy and infrastructure."""

    SOLAR_PV = "SOLAR_PV"
    WIND = "WIND"
    BESS = "BESS"
    HYBRID = "HYBRID"
    SUBSTATION = "SUBSTATION"
    WEATHER_STATION = "WEATHER_STATION"
    GATEWAY = "GATEWAY"
    OTHER = "OTHER"


class DataQuality(StrEnum):
    """Telemetry data quality indicator."""

    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    ESTIMATED = "ESTIMATED"
    SIMULATED = "SIMULATED"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    UNKNOWN = "UNKNOWN"


class HealthDerivationMethod(StrEnum):
    """Method by which a digital twin health/performance metric was derived."""

    MEASURED = "MEASURED"
    CALCULATED = "CALCULATED"
    RULE_DERIVED = "RULE_DERIVED"
    AI_DERIVED = "AI_DERIVED"
    PREDICTED = "PREDICTED"


class TwinEventType(StrEnum):
    """Core operational and lifecycle event types."""

    ASSET_REGISTERED = "asset_registered"
    ASSET_COMMISSIONED = "asset_commissioned"
    STATE_CHANGED = "state_changed"
    TELEMETRY_RECEIVED = "telemetry_received"
    TELEMETRY_QUALITY_CHANGED = "telemetry_quality_changed"
    COMMUNICATION_LOST = "communication_lost"
    COMMUNICATION_RESTORED = "communication_restored"
    ANOMALY_DETECTED = "anomaly_detected"
    MAINTENANCE_STARTED = "maintenance_started"
    MAINTENANCE_COMPLETED = "maintenance_completed"
    CONFIGURATION_CHANGED = "configuration_changed"
    TWIN_SYNCHRONISED = "twin_synchronised"
