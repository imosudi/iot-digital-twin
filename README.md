# TwinField — REGENOVA Digital Twin Sub-API

**TwinField** is the dedicated Digital Twin representation, synchronization, and interaction sub-API for the **REGENOVA** (Renewable Energy Asset Intelligence & Management Framework).

Target deployment: `https://twinfield.regenova.cloud/`

## Architecture & Boundary

TwinField maintains high-fidelity digital representations of heterogeneous renewable-energy assets (Solar PV, BESS, Wind Turbines, Inverters, Weather Stations, Grid Interconnects).

- **Backend**: FastAPI 0.115+, SQLAlchemy 2.0, Alembic, Pydantic v2.
- **Frontend**: React, Vite, Bootstrap 5.3.x (light control room studio shell).
- **Persistence**: SQLite (development default) / PostgreSQL + TimescaleDB (production).
- **Template System**: Versioned, schema-driven entity templates (`entity-definitions/`).

## Quick Start

### Backend (Default Port: 9000)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

The API will be available at `http://localhost:9000`; interactive OpenAPI documentation is at `http://localhost:9000/docs`.

### Frontend Studio (Default Port: 5173)

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Repository Structure

- `backend/`: FastAPI application, domain contracts, persistence models, and tests.
- `frontend/`: React/Vite/Bootstrap 5.3 studio shell.
- `entity-definitions/`: Canonical schema definitions for renewable entities (e.g. `solar_pv`, `battery`).
- `docs/`: Architectural decision records, roadmap, and forensic audit reports.

See `ARCHITECTURE.md`, `DEVELOPMENT.md`, and `ROADMAP.md` for technical specifications.
