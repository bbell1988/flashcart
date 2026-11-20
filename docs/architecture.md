# Architecture

## Overview

```
                         ┌─────────────────────┐
                         │   API Gateway/LB     │
                         │ (Kubernetes Ingress) │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   Order API (FastAPI) │
                         │  - Auth (JWT/RBAC)    │
                         │  - Rate limiting      │
                         │  - Orders/Products API│
                         └──────┬───────┬────────┘
                                │       │
                 writes/reads   │       │ publishes events
                                │       │
                 ┌──────────────▼┐   ┌──▼──────────────────┐
                 │  PostgreSQL    │   │  Message Broker     │
                 │  (orders,      │   │  (RabbitMQ)         │
                 │  inventory,    │   │  topics: order.*    │
                 │  users)        │   └──────────┬──────────┘
                 └───────┬────────┘              │
                         │                        │
                 ┌───────▼────────┐      ┌────────▼─────────────┐
                 │  Redis          │      │  Inventory Worker     │
                 │  (inventory     │      │  (consumes order.*,   │
                 │  cache, rate    │      │   reserves stock,     │
                 │  limit buckets) │      │   idempotent, retries,│
                 └────────────────┘      │   DLQ on failure)      │
                                          └────────┬─────────────┘
                                                   │
                                          ┌────────▼─────────────┐
                                          │  Payment Worker       │
                                          │  (mock provider +     │
                                          │   webhook handler,    │
                                          │   idempotency keys)   │
                                          └───────────────────────┘
```

## Data model (Phase 1)

```
users(id, email, password_hash, role)
products(id, name, price_cents, stock_qty, version)   -- version = optimistic lock column, added Phase 2
orders(id, user_id, status, total_cents, created_at, updated_at)
order_items(id, order_id, product_id, qty, unit_price_cents)
```

Added in later phases:
- `idempotency_keys` — dedupe retried requests/webhooks (Phase 2)
- `outbox` — transactional outbox for reliable event publishing (Phase 3)

## Design decisions log

Record the *why* behind non-obvious choices here as you make them. This doubles as interview
prep material — being able to explain a tradeoff you actually weighed is far stronger than
reciting a pattern name.

| Decision | Options considered | Why |
|---|---|---|
| _(fill in as you go, e.g. "RabbitMQ vs Kafka")_ | | |

## Phases
1. **Core API** — CRUD, Postgres, JWT auth, RBAC, tests, Docker
2. **Concurrency correctness** — optimistic locking, idempotency keys
3. **Event-driven flow** — outbox pattern, RabbitMQ, async workers, DLQ
4. **Performance** — Redis caching, rate limiting, load testing
5. **Platform** — Kubernetes, CI/CD, Prometheus/Grafana
