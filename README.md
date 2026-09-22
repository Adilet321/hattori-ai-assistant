# HATTORI AI Assistant — backend

Initial backend infrastructure for the HATTORI AI assistant. This repository intentionally contains no integrations with GreenAPI, Altegio, OpenAI, and no customer or booking business logic.

## Requirements

- Python 3.12+
- Docker and Docker Compose (for the containerized launch)

## Local launch with Docker Compose

1. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Set a non-default value for `POSTGRES_PASSWORD` in `.env`.

3. Start the API and PostgreSQL:

   ```bash
   docker compose up --build
   ```

4. Check the service:

   ```bash
   curl http://localhost:8000/health
   ```

   Expected response: `{"status":"ok"}`.

## Local Python launch

1. Create and activate a virtual environment, then install the project with development dependencies:

   ```bash
   python -m venv .venv
   .venv/bin/pip install -e ".[dev]"
   ```

   On Windows PowerShell:

   ```powershell
   .\.venv\Scripts\python -m pip install -e ".[dev]"
   ```

2. Start PostgreSQL with Docker Compose:

   ```bash
   docker compose up -d db
   ```

3. Copy `.env.example` to `.env`, set `POSTGRES_PASSWORD`, and set `DATABASE_URL` for localhost as shown in the example file.

4. Run the API:

   ```bash
   uvicorn app.main:app --reload
   ```

## Database migrations

Alembic uses `DATABASE_URL` from the environment. Create a revision after adding ORM models:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Tests

```bash
pytest
```

