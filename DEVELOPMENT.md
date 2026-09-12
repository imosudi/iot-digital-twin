# Development

Run backend checks from `backend/`:

```bash
pip install -e '.[dev]'
pytest
ruff check app tests
```

Run the frontend from `frontend/`:

```bash
npm install
npm run build
```

The project currently requires Python 3.11+ and Node.js 20+.