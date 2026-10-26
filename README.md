# Infraconect — Records API (Challenge 1)

Containerized RESTful API (Flask + Gunicorn + PostgreSQL) with local
orchestration via Docker Compose, a CI/CD pipeline on GitHub Actions, and
production-ready Kubernetes manifests.

## Endpoints

| Method | Route       | Description                                                   |
|--------|-------------|---------------------------------------------------------------|
| `GET`  | `/healthz`  | Liveness — basic process health.                              |
| `GET`  | `/readyz`   | Readiness — real connectivity to PostgreSQL.                  |
| `POST` | `/records`  | Creates a record (`{ "name": ..., "email": ... }`).           |
| `GET`  | `/records`  | Lists records with pagination (`?limit=1..100`, `?offset=0`). |

## Prerequisites

- Docker 24+ with BuildKit
- Docker Compose v2

## Bring the environment up with a single command

```bash
cp .env.example .env          # adjust DB_PASSWORD before use
docker compose up --build
```

The API will be available at `http://localhost:5000`. Compose starts, in order:
1. `postgres` (with `pg_isready` healthcheck + `pgdata` volume).
2. `migrate` (applies `src/migrations/*.sql` using the same app image).
3. `api` (only after `postgres` is healthy and `migrate` has succeeded).

## Validate

```bash
curl -s localhost:5000/healthz
curl -s localhost:5000/readyz
curl -s -XPOST localhost:5000/records \
  -H 'content-type: application/json' \
  -d '{"name":"Jane","email":"jane@example.com"}'
curl -s localhost:5000/records
```

## Environment variables

| Var                | Default       | Description                             |
|--------------------|---------------|-----------------------------------------|
| `DB_HOST`          | `postgres`    | PostgreSQL host.                        |
| `DB_PORT`          | `5432`        | PostgreSQL port.                        |
| `DB_NAME`          | `infraconect` | Database name.                          |
| `DB_USER`          | `app`         | Database user.                          |
| `DB_PASSWORD`      | —             | Password (Secret in K8s, `.env` local). |
| `APP_PORT`         | `5000`        | Container port.                         |
| `HOST_PORT`        | `5000`        | Port published on the host by Compose.  |
| `GUNICORN_WORKERS` | `2`           | Number of Gunicorn workers.             |
| `POOL_MIN`         | `1`           | Initial pool connections.               |
| `POOL_MAX`         | `5`           | Maximum pool connections.               |

## Migrations

Files in `src/migrations/NNN_*.sql` are applied by `python -m app.migrate`,
with each run recorded in the `schema_migrations` table (one atomic
transaction per file). In Kubernetes, run them as a `Job`/`InitContainer`
with the same image and env as the app (Factor XII).

## CI/CD

`.github/workflows/ci-cd.yml` runs on pull requests and pushes to `main`:
- `hadolint` on the Dockerfile + `ruff` on the source code.
- Integration tests (`PYTHONPATH=src pytest -q tests`) against an ephemeral
  Postgres (service container); the schema is built by `app.migrate` itself.
- Build + Trivy scan (HIGH/CRITICAL) + push to `ghcr.io` tagged with
  `${{ github.sha }}` and `latest` (only on pushes to `main`).
- `update-manifest` job: pins the build tag (`:<sha>`) into
  `k8s/deployment.yaml` (automatic commit, GitOps-lite CD) — guaranteeing
  rollbacks and traceability.

## Kubernetes

`k8s/`:
- `deployment.yaml`: 2 replicas, `livenessProbe` -> `/healthz`,
  `readinessProbe` -> `/readyz`, strict `requests`/`limits`, `runAsNonRoot`.
- `service.yaml`: ClusterIP, port 80 -> `http` (5000).
- `configmap.yaml`: non-sensitive configuration.
- `secret.yaml`: credentials (in production: SealedSecret/ExternalSecret/SOPS).

PostgreSQL is treated as an **external backing service** (it does not run in
the cluster). The Deployment image is pinned automatically by the
`update-manifest` job (`:<sha>` tag); before `kubectl apply`, set the real
Postgres endpoint in `k8s/configmap.yaml` and fill in the Secret.

## Security / DevSecOps

- Base image `python:3.13-slim` (pinned version; never `latest`).
- Multi-stage: the build toolchain never reaches the runtime image.
- Non-root user with fixed UID/GID 1000; `--chown` on all copies.
- `.dockerignore` covering `.git`, `.env*`, `tests/`, `__pycache__/`, etc.
- Cache cleanup in a single layer (`--no-cache-dir`, BuildKit cache mounts).
- Logs only to `stdout`/`stderr`.
