# Flash-Sale Inventory Service (FastAPI + PostgreSQL + Redis)
It's Black Friday. Your e-commerce platform has ONE item left in stock. At exactly 12:00:00 PM, 10,000 users simultaneously click "Add to Cart."

## Overview

This dir implements Scenario 1 (Flash Sale Inventory) — a backend service that:

- Handles high concurrent reservation attempts for a limited inventory item.
- Guarantees ACID-like behavior: prevents overselling and ensures at-most-one purchase for the last item.
- Implements reservation TTL (5 minutes) and automatic expiration.
- Provides REST endpoints to reserve, purchase, and check inventory.

Stack:
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Python 3.11

## Features

- Atomic reservation using **database row-level locking** (`SELECT ... FOR UPDATE`) inside an explicit transaction.
- Reservation TTL implemented with Redis keys + background cleanup that reconciles expired reservations and restores inventory.
- Load test script to simulate N concurrent reservations.
- Docker Compose for local setup (Postgres + Redis + API).
- Test concurrency script to test high concurrency inventory safety

## Quick start

1\. Create a `.env` file with the following variables:
```
  DATABASE_URL=postgresql://postgres:{DB_PASSWORD}@postgres:5432/flashsaleinventory
  DATABASE_URL_LOCAL=postgresql://postgres:{DB_PASSWORD}@localhost:5432/flashsaleinventory
  REDIS_URL=redis://{REDIS_HOST}:6379/0
  RESERVATION_TTL_SECONDS=300
  CLEANUP_INTERVAL_SECONDS=1
  POSTGRES_PASSWORD={POSTGRES_PASSWORD}
  API_URL=http://localhost:8000
  CONCURRENCY=10000
```

2\. Install Python dependencies
```
  # Navigate to the root directory and install dependencies from the `requirements.txt` file
  pip install -r requirements.txt
```

3\. Build and start services (requires Docker & docker-compose):
```
  docker-compose up --build
```
API will be available at http://localhost:9000 or http://localhost:8000.


4\. Create the product with initial inventory (100 items):<br />
```
  # enter postgres container
  docker-compose exec postgres psql -U postgres -d flashsale -c "INSERT INTO products (sku, available_qty) VALUES ('BLACK-FRIDAY-ITEM', 100);"
```

5\. Test reserve endpoint:
```
  curl -X POST "http://localhost:8000/reserve" -H "Content-Type: application/json" -d '{"user_id":"<user_id>","sku":"BLACK-FRIDAY-ITEM"}'
```

6\. Test purchase:
```
  curl -X POST "http://localhost:8000/purchase" -H "Content-Type: application/json" -d '{"reservation_id":"<id>","user_id":"<user_id>"}'
```

7\. Check inventory:
```
  curl http://localhost:8000/inventory/BLACK-FRIDAY-ITEM
```

## Running the load test (simulate concurrency)

Modify concurrency via environment variable and provide PURCHASE_IMMEDIATELY if instant purchase is required immediatly after reservation:

```
  CONCURRENCY=10000 API_URL=http://localhost:8000 PURCHASE_IMMEDIATELY=True python scripts/load_test.py
```

## Running the test concurrency
```
  pytest -s tests/test_concurrency.py
```

## Design Decisions

### Database choice & isolation

- PostgreSQL is the source of truth for inventory and reservations.
- I use explicit transactions and ```SELECT ... FOR UPDATE``` to lock the product row for inventory updates — this enforces serializability for inventory changes at row granularity.

### Distributed locking

- To avoid races across multiple API instances, a Redis-based distributed lock is used (simple SET NX PX pattern).
- This is used together with DB transactions — Redis minimizes lock contention across app processes; DB row lock ensures ACID on durability.

## Reservation TTL

- When a reservation is created, i:
  - decrement ```products.available_qty``` inside a DB transaction,
  - insert a reservation record with ```expires_at```,
  - store ```reservation:{id}``` key in Redis with TTL = 5 minutes,
  - add reservation id to ```active_reservations``` Redis SET for cleanup scanning.
- A background cleanup task scans ```active_reservations```, checks expired Redis keys (ttl == -2) and executes ```expire_reservation```, which increments inventory back atomically.

### Trade-offs

- Using Redis to detect expiration is lightweight and efficient. However, TTL-based expiry is eventually consistent — i run a periodic scanner to reconcile state.
- Scheduling via in-memory timers would not survive restarts. Using Redis keys and a background reconciler is more robust for restarts.
- The Redis lock is simple; in production i will consider Redlock with quorum or a robust lock manager.

### Time Complexity

- Reservation: DB SELECT FOR UPDATE (O(1) row lock) + insert: overall O(1) with respect to inventory size.
- Query inventory: O(1).
- Cleanup: scanning Redis set of active reservations — O(n_active) per cleanup tick. For high scale i will use a sharded approach or Redis Streams with consumer groups.

## Security & Observability (notes)

- Input validation via Pydantic.
- Add rate limiting, authentication, and sanitization for production.
- Observability: instrument metrics (Prometheus), structured logs, and tracing (OpenTelemetry) in prod.

## Files of interest

- ```app/``` - main application code
- ```scripts/load_test.py``` - concurrency test
- ```tests/test_concurrency.py```
- ```docker-compose.yml``` - local setup
- ```architecture.md``` - detailed architecture & tradeoffs

## Assumptions

- Single unit reserve per request.
- Single product SKU (Stock Keeping Unit) used for the flash sale example.
- No authentication implemented (out of scope for this test).
