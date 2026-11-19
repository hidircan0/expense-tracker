# Expense Tracker API

A modular REST API built with FastAPI, SQLAlchemy 2 async, Pydantic v2, and SQLite. PostgreSQL is supported by changing `DATABASE_URL`.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Change SECRET_KEY before deploying
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

OpenAPI docs are at `http://localhost:8000/docs`; health check is `/health`. The seed script creates default categories and a demo account (`demo@example.com` / `demo-password-change-me`); change or remove that credential outside local development.

## Configuration

`DATABASE_URL` defaults to `sqlite+aiosqlite:///./expense_tracker.db`. For PostgreSQL, provide a URL such as `postgresql+asyncpg://user:password@localhost:5432/expenses` (plain `postgresql://` URLs are converted automatically). `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and JSON array `CORS_ORIGINS` are loaded from `.env` or the environment.

## API

All application routes are under `/api/v1`.

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET|POST /categories`, `GET|PATCH|DELETE /categories/{id}`
- `GET|POST /expenses`, `GET|PATCH|DELETE /expenses/{id}`
- `GET /analytics/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Login uses the OAuth2 password form fields `username` (the email address) and `password`, and returns a bearer JWT. Use `Authorization: Bearer <access_token>` for protected routes. Expense amounts use decimal strings and are stored as `NUMERIC(10, 2)`. The analytics response includes category totals, monthly totals within the requested date range, and comparison to the immediately preceding period of equal length.

Default categories are shared and read-only. Custom categories belong to their creating user. Expenses and custom categories are always scoped to the authenticated user.

## Database migrations

Generate revisions with `alembic revision --autogenerate -m "description"`, then apply via `alembic upgrade head`. Migrations load the same configured database URL as the application.

## Tests

```bash
pytest
```

## Docker Compose deployment

Compose runs the frontend, API, and PostgreSQL as separate services on a private bridge network. The frontend is a small static Turkish UI served by Nginx; it reverse-proxies API requests internally, so the browser uses one origin. PostgreSQL has a persistent named volume and is not published to the host. A one-shot migration service waits for the database health check, applies Alembic migrations, then allows the API to start. The initial migration inserts the shared default categories.

```bash
cp .env.docker.example .env
# Edit .env: use unique strong POSTGRES_PASSWORD and SECRET_KEY values.
# DATABASE_URL must use the same DB username/password and point to host `db`.
docker compose up --build -d
```

The frontend is available at `http://localhost:${FRONTEND_PORT:-3000}` and the API directly at `http://localhost:${API_PORT:-8000}`. Check services with `docker compose ps` and logs with `docker compose logs -f api`. To shut down while retaining database data, run `docker compose down`. To also erase the database volume, run `docker compose down -v`.

For a password containing URL-reserved characters, percent-encode it in `DATABASE_URL`. The Postgres port stays private to the Compose network by default. `seed.py` creates a demo account and is intended only for local development; run it manually only when a demo login is desired.

The API is deployed as one modular application service, with PostgreSQL as its own stateful service. Auth, expense, category, and analytics currently share the same ORM and transaction boundary, so splitting them into independently deployable domain services would require API and data ownership changes beyond containerizing this application.
