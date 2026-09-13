import pytest
from fastapi.testclient import TestClient

from app.domain.enums import AssetClass, TwinEventType, TwinLifecycleStatus
from app.main import app
from app.persistence.database import init_db

init_db()
client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_clean_site():
    # Register a standard test site for twin tests
    site_payload = {
        "id": "site-sol-01",
        "name": "Solar Farm Alpha",
        "description": "50MW utility-scale solar PV facility",
        "metadata": {"country": "DE", "commissioned_year": 2023},
    }
    client.post("/api/v1/sites", json=site_payload)


def test_create_twin_success():
    twin_payload = {
        "twin_id": "sol-alpha-inv-01",
        "asset_id": "INV-001",
        "external_id": "SCADA-INV-001",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Central Inverter 01",
        "description": "2.5MW central inverter with integrated MPPT",
        "status": TwinLifecycleStatus.REGISTERED.value,
        "site_id": "site-sol-01",
        "capabilities": ["curtailment", "reactive_power_control"],
        "configuration": {"max_power_kw": 2500.0, "ac_voltage_nominal": 690.0},
        "metadata": {"bay": "BAY-A1"},
    }
    response = client.post("/api/v1/twins", json=twin_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["twin_id"] == "sol-alpha-inv-01"
    assert data["status"] == TwinLifecycleStatus.REGISTERED.value
    assert data["asset_class"] == AssetClass.SOLAR_PV.value
    assert data["capabilities"] == ["curtailment", "reactive_power_control"]

    # Verify initial ASSET_REGISTERED event was logged
    events_resp = client.get("/api/v1/twins/sol-alpha-inv-01/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 1
    assert any(e["event_type"] == TwinEventType.ASSET_REGISTERED.value for e in events)


def test_create_duplicate_twin_fails():
    twin_payload = {
        "twin_id": "sol-alpha-inv-02",
        "asset_id": "INV-002",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Central Inverter 02",
        "site_id": "site-sol-01",
    }
    res1 = client.post("/api/v1/twins", json=twin_payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/twins", json=twin_payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_create_twin_invalid_site_fails():
    twin_payload = {
        "twin_id": "invalid-site-twin",
        "asset_id": "INV-999",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Orphan Inverter",
        "site_id": "nonexistent-site-id",
    }
    response = client.post("/api/v1/twins", json=twin_payload)
    assert response.status_code == 400
    assert "site with id" in response.json()["detail"].lower()


def test_twin_hierarchy_and_cycle_prevention():
    # Parent inverter
    parent_payload = {
        "twin_id": "sol-alpha-inv-03",
        "asset_id": "INV-003",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Central Inverter 03",
        "site_id": "site-sol-01",
    }
    res_p = client.post("/api/v1/twins", json=parent_payload)
    assert res_p.status_code == 201

    # Child combiner box
    child_payload = {
        "twin_id": "sol-alpha-cb-01",
        "asset_id": "CB-001",
        "twin_type": "combiner_box",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Combiner Box 01",
        "site_id": "site-sol-01",
        "parent_twin_id": "sol-alpha-inv-03",
    }
    res_c = client.post("/api/v1/twins", json=child_payload)
    assert res_c.status_code == 201

    # Test children endpoint
    children_resp = client.get("/api/v1/twins/sol-alpha-inv-03/children")
    assert children_resp.status_code == 200
    children = children_resp.json()
    assert len(children) == 1
    assert children[0]["twin_id"] == "sol-alpha-cb-01"

    # Attempting to make a twin its own parent fails
    self_parent_payload = {
        "twin_id": "sol-alpha-self-parent",
        "asset_id": "SELF-01",
        "twin_type": "sensor",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Self Parent Twin",
        "parent_twin_id": "sol-alpha-self-parent",
    }
    res_self = client.post("/api/v1/twins", json=self_parent_payload)
    assert res_self.status_code == 400
    assert "cannot be its own parent" in res_self.json()["detail"].lower()

    # Attempting to introduce a cycle via patch fails
    cycle_patch = client.patch(
        "/api/v1/twins/sol-alpha-inv-03",
        json={"parent_twin_id": "sol-alpha-cb-01"},
    )
    assert cycle_patch.status_code == 400
    assert "creates a cycle" in cycle_patch.json()["detail"].lower()


def test_twin_lifecycle_state_machine():
    twin_payload = {
        "twin_id": "sol-alpha-inv-04",
        "asset_id": "INV-004",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Central Inverter 04",
        "status": TwinLifecycleStatus.REGISTERED.value,
    }
    create_res = client.post("/api/v1/twins", json=twin_payload)
    assert create_res.status_code == 201

    # Valid transition: REGISTERED -> COMMISSIONED
    t1 = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.COMMISSIONED.value,
            "reason": "Commissioning tests passed on-site",
            "operator": "engineer_sarah",
        },
    )
    assert t1.status_code == 200
    assert t1.json()["status"] == TwinLifecycleStatus.COMMISSIONED.value

    # Valid transition: COMMISSIONED -> ACTIVE
    t2 = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.ACTIVE.value,
            "reason": "Commercial operation date reached",
            "operator": "plant_manager_dave",
        },
    )
    assert t2.status_code == 200
    assert t2.json()["status"] == TwinLifecycleStatus.ACTIVE.value

    # Invalid transition: ACTIVE -> REGISTERED (Not allowed!)
    t_invalid = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.REGISTERED.value,
            "reason": "Mistaken rollback",
            "operator": "engineer_sarah",
        },
    )
    assert t_invalid.status_code == 422
    assert "cannot transition twin" in t_invalid.json()["detail"].lower()

    # Valid transition: ACTIVE -> DEGRADED (Warning event)
    t3 = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.DEGRADED.value,
            "reason": "IGBT thermal derating detected",
            "operator": "ai_health_subagent",
        },
    )
    assert t3.status_code == 200
    assert t3.json()["status"] == TwinLifecycleStatus.DEGRADED.value

    # Valid transition: DEGRADED -> MAINTENANCE
    t4 = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.MAINTENANCE.value,
            "reason": "Scheduled inverter module replacement",
            "operator": "technician_bob",
        },
    )
    assert t4.status_code == 200

    # Valid transition: MAINTENANCE -> DECOMMISSIONED
    t5 = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.DECOMMISSIONED.value,
            "reason": "Asset repowering end of lifecycle",
            "operator": "asset_owner",
        },
    )
    assert t5.status_code == 200
    assert t5.json()["status"] == TwinLifecycleStatus.DECOMMISSIONED.value

    # Terminal check: DECOMMISSIONED -> ACTIVE is strictly rejected
    t_terminal = client.post(
        "/api/v1/twins/sol-alpha-inv-04/transition",
        json={
            "target_status": TwinLifecycleStatus.ACTIVE.value,
            "reason": "Illegal reactivation",
            "operator": "operator_x",
        },
    )
    assert t_terminal.status_code == 422


def test_list_twins_and_filters():
    # Query twins filtered by site_id and asset_class
    resp = client.get("/api/v1/twins", params={"site_id": "site-sol-01"})
    assert resp.status_code == 200
    twins = resp.json()
    assert len(twins) >= 3
    assert all(t["site_id"] == "site-sol-01" for t in twins)

    # Filter by asset class
    resp_class = client.get("/api/v1/twins", params={"asset_class": AssetClass.SOLAR_PV.value})
    assert resp_class.status_code == 200
    assert all(t["asset_class"] == AssetClass.SOLAR_PV.value for t in resp_class.json())


def test_twin_event_logging():
    twin_payload = {
        "twin_id": "sol-alpha-inv-05",
        "asset_id": "INV-005",
        "twin_type": "central_inverter",
        "asset_class": AssetClass.SOLAR_PV.value,
        "name": "Central Inverter 05",
    }
    client.post("/api/v1/twins", json=twin_payload)

    event_payload = {
        "event_type": TwinEventType.ANOMALY_DETECTED.value,
        "severity": "WARNING",
        "message": "MPPT string 3 voltage imbalance of 14.2%",
        "details": {"string_id": "STR-03", "measured_v": 580.0, "expected_v": 675.0},
    }
    ev_resp = client.post("/api/v1/twins/sol-alpha-inv-05/events", json=event_payload)
    assert ev_resp.status_code == 201
    data = ev_resp.json()
    assert data["twin_id"] == "sol-alpha-inv-05"
    assert data["severity"] == "WARNING"
    assert data["event_type"] == TwinEventType.ANOMALY_DETECTED.value


def test_delete_twin():
    twin_payload = {
        "twin_id": "sol-alpha-temp-01",
        "asset_id": "TEMP-001",
        "twin_type": "temp_sensor",
        "asset_class": AssetClass.WEATHER_STATION.value,
        "name": "Temporary Pyranometer",
    }
    client.post("/api/v1/twins", json=twin_payload)

    del_resp = client.delete("/api/v1/twins/sol-alpha-temp-01")
    assert del_resp.status_code == 204

    get_resp = client.get("/api/v1/twins/sol-alpha-temp-01")
    assert get_resp.status_code == 404
