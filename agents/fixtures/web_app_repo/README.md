# Web App Repo

A simple FastAPI application with a health check and items CRUD API.
The `/health` endpoint has a known bug — it references an undefined variable.

## Dependencies

Requires `fastapi` and `httpx` (for the test client).

## Running tests

```bash
python -m pytest test_app.py -v
```
