from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.models import (
    AssetClass,
    Component,
    DataQuality,
    DigitalTwin,
    HealthDerivationMethod,
    Provenance,
    Sensor,
    StateVector,
    TelemetryReading,
    TwinEvent,
    TwinEventType,
    TwinHealth,
    TwinLifecycleStatus,
    TwinState,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def test_twin_lifecycle_status_values() -> None:
    statuses = [s.value for s in TwinLifecycleStatus]
    expected = [
        "DISCOVERED",
        "REGISTERED",
        "COMMISSIONED",
        "ACTIVE",
        "DEGRADED",
        "MAINTENANCE",
        "DECOMMISSIONED",
    ]
    assert statuses == expected


def test_provenance_confidence_bounds() -> None:
    p_valid = Provenance(source="SCADA_AGENT_01", confidence=0.95)
    assert p_valid.confidence == 0.95

    with pytest.raises(ValidationError):
        Provenance(source="SCADA", confidence=1.5)

    with pytest.raises(ValidationError):
        Provenance(source="SCADA", confidence=-0.1)


def test_separate_four_tier_state_model() -> None:
    now = utc_now()
    prov_reported = Provenance(source="GATEWAY_01", source_type="EDGE_GATEWAY", timestamp=now)
    prov_predicted = Provenance(
        source="AI_DEGRADATION_MODEL", source_type="AI_MODEL", timestamp=now, confidence=0.88
    )

    state = TwinState(
        desired=StateVector(
            values={"curtailment_kw": 0.0, "target_power_factor": 1.0}, timestamp=now
        ),
        reported=StateVector(
            values={"active_power_kw": 850.4, "ambient_temp_c": 32.1},
            timestamp=now,
            provenance=prov_reported,
        ),
        observed=StateVector(
            values={"normalized_efficiency": 0.972, "temperature_delta": 4.2}, timestamp=now
        ),
        predicted=StateVector(
            values={"expected_output_t_plus_1h_kw": 830.0, "degradation_rate_pct": 0.04},
            timestamp=now,
            provenance=prov_predicted,
        ),
    )

    assert state.desired.values["curtailment_kw"] == 0.0
    assert state.reported.values["active_power_kw"] == 850.4
    assert state.observed.values["normalized_efficiency"] == 0.972
    assert state.predicted.values["expected_output_t_plus_1h_kw"] == 830.0
    assert state.predicted.provenance.source == "AI_DEGRADATION_MODEL"
    assert state.predicted.provenance.confidence == 0.88


def test_telemetry_reading_time_semantics_and_quality() -> None:
    t_event = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    t_ingest = datetime(2026, 9, 13, 12, 0, 2, tzinfo=timezone.utc)
    t_process = datetime(2026, 9, 13, 12, 0, 3, tzinfo=timezone.utc)

    reading = TelemetryReading(
        twin_id="TWIN-INV-01",
        component_id="COMP-MPPT-01",
        sensor_id="SENS-DC-VOLT-01",
        metric="dc_voltage_v",
        value=725.4,
        unit="V",
        quality=DataQuality.VALID,
        event_time=t_event,
        ingestion_time=t_ingest,
        processing_time=t_process,
        confidence=0.99,
    )

    assert reading.quality == DataQuality.VALID
    assert reading.event_time < reading.ingestion_time < reading.processing_time
    assert reading.value == 725.4

    # Simulated data quality preserved
    sim_reading = TelemetryReading(
        twin_id="TWIN-BESS-01",
        metric="state_of_charge_pct",
        value=85.0,
        unit="%",
        quality=DataQuality.SIMULATED,
        event_time=t_event,
    )
    assert sim_reading.quality == DataQuality.SIMULATED


def test_component_and_sensor_hierarchy() -> None:
    temp_sensor = Sensor(
        sensor_id="SENS-TEMP-HEATSINK",
        metric="temperature",
        unit="C",
        sampling_interval_seconds=1.0,
        engineering_range=(-20.0, 120.0),
        status="ACTIVE",
    )

    inverter_module = Component(
        component_id="MOD-INV-01",
        name="IGBT Inverter Module 1",
        component_type="INVERTER_MODULE",
        serial_number="SN-IGBT-9921",
        sensors={"temp_heatsink": temp_sensor},
        properties={"rated_current_a": 400.0},
    )

    assert "temp_heatsink" in inverter_module.sensors
    assert inverter_module.sensors["temp_heatsink"].engineering_range == (-20.0, 120.0)


def test_twin_health_and_derivation_method() -> None:
    now = utc_now()
    health = TwinHealth(
        health_state="OPTIMAL",
        health_score=94.5,
        performance_state="NORMAL",
        availability=0.998,
        efficiency=0.981,
        deviation=0.012,
        risk_score=5.5,
        derivation_method=HealthDerivationMethod.AI_DERIVED,
        updated_at=now,
        evidence={"model": "IsolationForest_v2", "outlier_score": 0.02},
    )

    assert health.health_score == 94.5
    assert health.derivation_method == HealthDerivationMethod.AI_DERIVED
    assert health.evidence["model"] == "IsolationForest_v2"


def test_twin_event_structure() -> None:
    event = TwinEvent(
        event_id="EVT-001",
        twin_id="TWIN-SOLAR-01",
        event_type=TwinEventType.ANOMALY_DETECTED,
        severity="WARNING",
        message="Inverter heatsink temperature drift detected.",
        details={"temperature_c": 86.4, "threshold_c": 80.0},
    )

    assert event.event_type == TwinEventType.ANOMALY_DETECTED
    assert event.severity == "WARNING"


def test_canonical_digital_twin_aggregate() -> None:
    now = utc_now()
    twin = DigitalTwin(
        twin_id="TWIN-SOLAR-INV-01",
        asset_id="ASSET-INV-01",
        external_id="EXT-METER-990",
        twin_type="CentralInverterTwin",
        asset_class=AssetClass.SOLAR_PV,
        name="Central Inverter 01 Twin",
        status=TwinLifecycleStatus.ACTIVE,
        tenant_id="ORG-HELIOS-GLOBAL",
        site_id="SITE-MOJAVE-01",
        capabilities=["telemetry", "state_estimation", "thermal_simulation"],
        configuration={"dc_input_channels": 24, "rated_kw": 2500.0},
        state=TwinState(
            reported=StateVector(values={"power_kw": 2480.0}, timestamp=now),
        ),
        health=TwinHealth(
            health_score=96.0,
            derivation_method=HealthDerivationMethod.CALCULATED,
            updated_at=now,
        ),
        created_at=now,
        updated_at=now,
    )

    assert twin.twin_id == "TWIN-SOLAR-INV-01"
    assert twin.asset_class == AssetClass.SOLAR_PV
    assert twin.status == TwinLifecycleStatus.ACTIVE
    assert twin.state.reported.values["power_kw"] == 2480.0
    assert twin.health.health_score == 96.0
