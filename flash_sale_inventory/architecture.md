# Architecture Documentation — Flash Sale Inventory

## Goal
Handle a burst of concurrent "Add to cart" requests for the last units of inventory, ensuring no oversell, fairness, and deterministic expiration of reservations (5 minutes).

## Components
- **FastAPI** — HTTP API
- **PostgreSQL** — Source of truth for products and reservations
- **Redis** — Distributed lock and reservation TTL tracking
- **Background cleanup task** — reconciles expired reservations and restores inventory

## Data Model

### `products` table
- `id` (PK)
- `sku` (unique)
- `available_qty` (int)
- `created_at`

### `reservations` table
- `id` (UUID PK)
- `product_id` (FK -> products.id)
- `user_id` (string)
- `status` (enum: reserved|purchased|expired)
- `expires_at` (epoch ms)
- `created_at` (epoch ms)

**Storage approach**: PostgreSQL stores canonical inventory and reservation history (audit).

## Core Algorithms

### Reserve flow (atomic)
1. Acquire Redis lock for the SKU (`SET NX PX`).
2. Begin DB transaction.
3. SELECT product row FOR UPDATE.
4. IF `available_qty > 0`:
   - decrement `available_qty`
   - insert reservation row with `expires_at`
   - commit
5. Create Redis key `reservation:{id}` with TTL = 5 minutes and add `id` to `active_reservations` SET.
6. Release Redis lock.

**ACID**: The DB step ensures atomicity & durability; the Redis step tracks TTL for expiry.

### Purchase flow (atomic)
1. Acquire lock on reservation (Redis).
2. Begin DB transaction.
3. SELECT reservation row FOR UPDATE.
4. IF owner matches and status is `reserved`, set to `purchased` and commit.
5. Delete Redis reservation key to prevent expiry.

### Expiration
- A periodic background task scans `active_reservations`. For each id:
  - check `ttl reservation:{id}`:
    - if TTL indicates missing (`-2`): call `expire_reservation`:
      - SELECT reservation FOR UPDATE; if status `reserved`:
        - set to `expired`
        - increment `products.available_qty` atomically
- Remove id from `active_reservations`.

## Concurrency Strategy
- **DB row-level locks** (SELECT FOR UPDATE) guarantee serialization of inventory changes per product row.
- **Redis distributed lock** prevents multiple app instances from initiating overlapping DB transactions that might compete with each other momentarily (defense-in-depth).
- This combination eliminates overselling: either Redis lock or DB row lock will ensure atomic decrement and reservation creation.

## Handling Edge Cases
- **10k simultaneous requests**: Redis lock serializes entry to the DB block; DB ensures atomic decrement. Excess requests get "out_of_stock".
- **User completes at exactly 5:00 mark**: If purchase arrives before cleanup marks expired, `complete_purchase` will succeed; if cleanup already expired reservation and incremented inventory, purchase will fail; race resolved deterministically by DB locks ordering; fairness is preserved by ordering of lock acquisition.
- **Reservation never completed**: TTL expiry & cleanup returns item to inventory.

## Scalability Considerations
- **Horizontal scaling**: App instances can be scaled behind load balancer; Redis + DB remain central.
- **Locks**: Redis lock latency small; I will consider using consistent hashing per product or partition products for lock sharding.
- **Cleanup**: As active reservations grow, scanning may be costly. I will Use sharded sets or a job queue (Redis Streams / Kafka) to handle expiry events more efficiently.
- **Bottlenecks**: DB is the single source of truth; heavy write throughput can be supported by partitioning or using replicas for reads.

For horizontal scaling across multiple database shards or regions, Redis-based distributed locking or inventory counters could be introduced. For this prototype, PostgreSQL row-level locks provide stronger consistency with lower operational complexity.

## Trade-offs and Alternatives
- **Alternative: Event-driven with message queue** — more scalable but complex to implement for this assessment.
- **Alternative: purely Redis-based inventory** — very fast (INCR/DECR + Lua) but loses durable audit history if not synced to DB.
- **Chosen approach** strikes a balance: durable audit in Postgres + Redis for low-latency locking & TTL.

## Security Concerns & Mitigations
- Add authentication / authorization to endpoints.
- Add rate-limiting to avoid spam.
- Validate and sanitize inputs.
- Monitor Redis & Postgres metrics (latency, slow queries).
