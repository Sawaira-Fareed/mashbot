# Mashbot Engineering Record

## Current Status

The approved scope is implemented as a runnable React/FastAPI/PostgreSQL application. Docker, migration, API workflow, frontend build, and backend test evidence has been observed. SonarQube and Jira results will be recorded only after they are actually observed.

## Selected Scope

The selected requirements are: account management, authentication, role-based access, campaign/content management, scheduling, approval workflow, external-service boundary, TLS, backup, and configurable session timeout.

## Architecture

React communicates with FastAPI over JSON. The frontend provides Dashboard, Create, Schedule, Explore, Profile, and People & roles pages. FastAPI contains authentication, authorization, dashboard summary, campaign, approval, scheduling, keyword-alert, and service-account boundaries. PostgreSQL stores application data. Alembic owns schema changes. Docker Compose runs frontend, backend, and database as separate services.

## API Surface

The backend exposes authentication, profile, user-role management, campaign lifecycle, dashboard summary, schedule feed, service accounts, and keyword-alert endpoints. OpenAPI documentation is available at `/docs` when the backend is running.

## Known Limitation

The external-service integration currently stores service-account associations and exposes a provider boundary. It does not claim live Facebook, Twitter, blog, or other third-party publishing/search results without a real provider adapter and credentials. This limitation is intentional and must remain visible in the SQE evidence.

## Evidence Rules

Planned, implemented, executed, observed, and verified are separate states. No test, SonarQube result, or Jira defect will be reported until evidence exists.
