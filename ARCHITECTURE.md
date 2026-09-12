# Architecture

## Current boundary

The platform is organized around a configurable `DigitalEntity`, not device-specific application code. Entity templates describe properties, telemetry, capabilities, commands, and validation metadata. The core API accepts and returns these contracts without branching on entity type.

The backend now has Phase 2 persistence for templates, sites, entities, and relationships. SQLite is the local default; SQLAlchemy supports PostgreSQL through `DATABASE_URL`. MQTT, time-series storage, rules, commands, and streaming remain staged behind the domain contract.

```text
React studio
    | REST / future WebSocket
FastAPI application
    | generic entity and template contracts
Digital Twin domain
    | future repository and telemetry ports
PostgreSQL / MQTT / simulator
```

## Extension rule

Adding an entity means adding a template under `entity-definitions/` and registering it through the template service. The engine must not gain a new Python class or frontend page for each entity type. The hydrogen storage tank is the planned extensibility test.

## Boundaries

- `app/domain`: framework-independent vocabulary and validation.
- `app/services`: use cases and registry behavior.
- `app/api`: transport adapters only.
- `entity-definitions`: data-driven entity library.
- `frontend`: generic rendering of returned schemas.
- `backend/migrations`: Alembic schema history; production databases are upgraded explicitly.