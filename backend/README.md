# UMD Scheduler Backend

FastAPI backend for the UMD Scheduler API and scraper dependencies.

## Run the API locally

From the repository root:

```bash
cd backend
uv sync
uv run uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at <http://localhost:8000>. Interactive API
documentation is available at <http://localhost:8000/docs>.

Before starting the server, create `backend/.env` from
`backend/.env.example` and set `CORS_ORIGINS` to include the frontend origin:

```dotenv
CORS_ORIGINS=http://localhost:5173
```

The backend requires PostgreSQL data at startup. Set `DATABASE_URL` in
`backend/.env` for a hosted database, or leave it empty to use the default
local connection (`class_api` on `localhost:5432` with the current OS user).

## Run the scraper

The scraper can be run from the backend directory with:

```bash
uv run python -m scraper.scraper
```

## Build the package

Package metadata references this README for wheel builds:

```bash
uv build
```

This README is also used as the package metadata source during wheel builds.
