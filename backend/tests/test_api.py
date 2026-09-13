from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import settings
from app.main import app, registry
from app.persistence.database import SessionLocal
from app.persistence.models import EntityRecord, RelationshipRecord, SiteRecord, TemplateRecord

client = TestClient(app)


def setup_function() -> None:
    registry._templates.clear()
    registry._entities.clear()
    with SessionLocal() as session:
        session.execute(delete(RelationshipRecord))
        session.execute(delete(EntityRecord))
        session.execute(delete(SiteRecord))
        session.execute(delete(TemplateRecord))
        session.commit()


def test_health_and_readiness() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_root_metadata_and_headers() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "TwinField" in data["service"]
    assert data["status"] in ("ok", "healthy")
    assert "0." in data["version"]
    assert "X-Process-Time" in response.headers


def test_cors_headers() -> None:
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_config_settings() -> None:
    assert settings.api_port == 9000
    assert "http://localhost:5173" in settings.cors_origins
    assert settings.env == "development"


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


def test_site_entities_and_relationships_are_persisted() -> None:
    template = {
        "type": "inverter",
        "version": "1.0",
        "display_name": "Inverter",
        "properties": {"rated_power": {"type": "number", "unit": "kW", "required": True}},
    }
    assert client.post("/api/v1/templates", json=template).status_code == 201
    assert client.post(
        "/api/v1/sites",
        json={"id": "north-ridge", "name": "North Ridge Energy"},
    ).status_code == 201

    for name, power in (("Inverter 01", 250), ("Inverter 02", 250)):
        response = client.post(
            "/api/v1/entities",
            json={
                "site_id": "north-ridge",
                "type": "inverter",
                "name": name,
                "template": "inverter",
                "version": "1.0",
                "properties": {"rated_power": power},
            },
        )
        assert response.status_code == 201

    relationship = client.post(
        "/api/v1/relationships",
        json={
            "source_entity_id": "inverter-01",
            "target_entity_id": "inverter-02",
            "relationship_type": "connected_to",
        },
    )
    assert relationship.status_code == 201
    assert len(client.get("/api/v1/entities?site_id=north-ridge").json()) == 2
    assert len(client.get("/api/v1/relationships").json()) == 1

    registry._entities.clear()
    persisted = client.get("/api/v1/entities/inverter-01")
    assert persisted.status_code == 200
    assert persisted.json()["site_id"] == "north-ridge"


def test_error_handling_entity_and_site_not_found() -> None:
    assert client.get("/api/v1/entities/non-existent-id").status_code == 404

    # Post entity pointing to invalid site
    template = {
        "type": "meter",
        "version": "1.0",
        "display_name": "Electric Meter",
    }
    client.post("/api/v1/templates", json=template)
    res = client.post(
        "/api/v1/entities",
        json={
            "site_id": "non-existent-site",
            "type": "meter",
            "name": "Meter 01",
            "template": "meter",
            "version": "1.0",
        },
    )
    assert res.status_code == 404
