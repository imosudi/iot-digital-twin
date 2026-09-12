# Architecture Decisions

## ADR-001: Generic contracts before device implementations

Entity types are represented by versioned templates and validated instances. This keeps the digital twin engine independent from the renewable-energy starter library and makes schema-driven extensibility testable.

## ADR-002: Modular monolith for the MVP

The initial system uses one backend process with explicit domain, service, and API boundaries. Separate services are deferred until measured workload or operational requirements justify them.

## ADR-003: In-memory registry in Phase 1

The first executable slice uses an in-memory registry to validate API and contract behavior without introducing an untested database migration layer. PostgreSQL and TimescaleDB are Phase 2/4 concerns.