# Development

Run backend checks from `backend/`:

```bash
pip install -e '.[dev]'
alembic upgrade head
pytest
ruff check app tests
```

Run the frontend from `frontend/`:

```bash
npm install
npm run build
```

The project currently requires Python 3.11+ and Node.js 20+.

The local default database is `backend/iot_digital_twin.db`. Set `DATABASE_URL` to a PostgreSQL URL for a shared deployment, then run `alembic upgrade head` before starting the API.