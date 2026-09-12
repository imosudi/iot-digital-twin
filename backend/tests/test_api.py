from fastapi.testclient import TestClient

from app.main import app, registry

client = TestClient(app)


def setup_function() -> None:
    registry._templates.clear()
    registry._entities.clear()


def test_health_and_readiness() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_registered_template_creates_generic_entity() -> None:
    template = {
        "type": "hydrogen_storage_tank",
        "version": "1.0",
        "display_name": "Hydrogen Storage Tank",
        "properties": {"pressure": {"type": "number", "unit": "bar", "required": True}},
        "telemetry": {"temperature": {"type": "number", "unit": "C"}},
    }
    assert client.post("/api/v1/templates", json=template).status_code == 201

    response = client.post(
        "/api/v1/entities",
        json={
            "type": "hydrogen_storage_tank",
            "name": "Tank 01",
            "template": "hydrogen_storage_tank",
            "version": "1.0",
            "properties": {"pressure": 12.5},
        },
    )
    assert response.status_code == 201
    assert response.json()["type"] == "hydrogen_storage_tank"


def test_required_template_property_is_validated() -> None:
    client.post(
        "/api/v1/templates",
        json={
            "type": "sensor",
            "version": "1.0",
            "display_name": "Sensor",
            "properties": {"location": {"type": "string", "required": True}},
        },
    )
    response = client.post(
        "/api/v1/entities",
        json={"type": "sensor", "name": "Sensor 01", "template": "sensor", "version": "1.0"},
    )
    assert response.status_code == 422