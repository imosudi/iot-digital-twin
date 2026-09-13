# TwinField Development Guide

## Environment Requirements

- **Python**: 3.11+ (Tested on Python 3.12)
- **Node.js**: 20+
- **Database**: SQLite (local dev default) or PostgreSQL 14+

## Backend Verification & Execution

From the `backend/` directory:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Apply database migrations
alembic upgrade head

# Run automated tests
pytest

# Run linter and formatting checks
ruff check app tests

# Start development API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

### Environment Configuration Variables

The backend supports configuration via environment variables or a `.env` file:

| Variable | Description | Default |
|---|---|---|
| `TWINFIELD_ENV` | Application environment (`development`, `staging`, `production`) | `development` |
| `TWINFIELD_DATABASE_URL` | SQLAlchemy connection URL | `sqlite:///./iot_digital_twin.db` |
| `TWINFIELD_API_HOST` | Host address to bind | `0.0.0.0` |
| `TWINFIELD_API_PORT` | HTTP port to listen on | `9000` |
| `TWINFIELD_CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:5173,...` |
| `TWINFIELD_LOG_LEVEL` | Log verbosity level | `INFO` |
| `TWINFIELD_SECRET_KEY` | Cryptographic secret for signing | Set in production |

## Frontend Studio Verification & Execution

From the `frontend/` directory:

```bash
# Install Node dependencies
npm install

# Run TypeScript check and production bundle build
npm run build

# Run local development studio
npm run dev -- --host 0.0.0.0 --port 5173
```
