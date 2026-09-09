# Mashbot

Mashbot is a campaign workspace for creating text campaigns, applying role-based approval, scheduling approved content, exploring keyword alerts, and maintaining a provider-neutral external-service boundary.

## Stack

- React and Vite frontend
- FastAPI backend
- PostgreSQL database
- SQLAlchemy ORM and Alembic migrations
- Docker Compose
- pytest for backend tests

## Interface

After signing in, the React application provides:

- Dashboard: campaign totals, approval pipeline, connected services, and upcoming schedule.
- Create: campaign drafting, service-account association, and approval actions.
- Schedule: approved-campaign scheduling and upcoming calendar feed.
- Explore: persistent keyword-alert management.
- Profile: update display name and password.
- People & roles: administrator-only role management.

## Run

Prerequisite: Docker Desktop with Compose.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the GUI at http://localhost:8080. API documentation is available at http://localhost:8000/docs and health status at http://localhost:8000/health.

The default bootstrap administrator is `admin@mashbot.local` with the password from `.env`. Change it before any shared deployment.

The default roles are contributor, approver, publisher, and admin. Contributors create and submit campaigns, approvers accept or reject submitted campaigns, and publishers schedule approved campaigns.

## Database

The backend runs `alembic upgrade head` when its container starts. PostgreSQL data is stored in the named `postgres_data` volume. `docker compose down` preserves it; `docker compose down -v` removes it.

The current migration head is `0002_keyword_alerts`.

## Troubleshooting

- If a port is occupied, change the host side of `8000:8000` or `8080:80`.
- If the database is not ready, wait for the health check and restart with `docker compose up`.
- If dependencies changed, rebuild with `docker compose up --build`.
- If the database must be reset, use `docker compose down -v` only when destroying local data is acceptable.

## Quality workflow

SonarQube is intentionally separate from the application Compose stack. After the baseline is complete and frozen, scan the complete repository and preserve the observed report. Do not treat a quality rating as a substitute for interpreting the findings.

The Explore page stores keyword alerts and provides the provider boundary. It does not claim live third-party search results until a real provider adapter and credentials are configured.
