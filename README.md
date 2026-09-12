# IoT Digital Twin

Configurable IoT digital twin and telemetry platform. The initial implementation is intentionally small: it establishes the generic entity contract and a runnable API/UI boundary before adding persistence, telemetry adapters, simulation, and operations workflows.

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; OpenAPI is at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Repository map

- `backend/`: FastAPI service and domain contracts
- `frontend/`: React/Vite studio shell
- `entity-definitions/`: versioned, schema-driven entity templates
- `docs/architecture/`: repository and architecture decisions

See [ARCHITECTURE.md](ARCHITECTURE.md), [DEVELOPMENT.md](DEVELOPMENT.md), and [ROADMAP.md](ROADMAP.md) for the current boundary and next steps.