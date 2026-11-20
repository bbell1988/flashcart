# FlashCart

An order & inventory backend built to demonstrate production-grade backend engineering:
concurrency control, event-driven processing, auth/RBAC, caching, observability, and CI/CD —
not just CRUD.

## Why this project exists
Most portfolio CRUD apps don't exercise the problems senior backend engineers actually solve
day to day: race conditions under concurrent load, idempotent retries, async workflows with
failure handling, and operating a service under traffic. FlashCart is a small e-commerce-style
domain (place an order against limited stock) chosen specifically because it can't be solved
correctly without those concepts.

## Status
Work in progress, built incrementally and documented phase by phase.

- [ ] Phase 1 — Core API (CRUD, Postgres, JWT auth, RBAC, tests, Docker)
- [ ] Phase 2 — Concurrency correctness (optimistic locking, idempotency keys)
- [ ] Phase 3 — Event-driven flow (outbox pattern, RabbitMQ, async workers, DLQ)
- [ ] Phase 4 — Performance (Redis caching, rate limiting, load testing)
- [ ] Phase 5 — Platform (Kubernetes, CI/CD, Prometheus/Grafana)

## Architecture
See [`docs/architecture.md`](./docs/architecture.md) for the full system design and the
rationale behind each decision (why Postgres optimistic locking over `SELECT ... FOR UPDATE`,
why RabbitMQ over Kafka for this scale, why choreography over a central orchestrator, etc.).

## Local development

```bash
cp .env.example .env     # fill in real values
docker-compose up -d     # starts Postgres
pip install -e ".[dev]"  # install the app + dev/test dependencies
alembic upgrade head      # apply DB migrations (added in Task 4)
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

## Tech stack
FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Alembic · JWT auth · pytest ·
(later phases: Redis, RabbitMQ, Docker, Kubernetes, GitHub Actions, Prometheus/Grafana)
