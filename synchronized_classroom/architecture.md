# Architecture Documentation

## Synchronized Classroom — Scenario 2 (BONUS)


## Architectural Overview

This system implements a **real-time synchronized classroom** where multiple students watch the same video and exchange comments anchored to precise video timestamps.

The architecture follows a **control-plane vs data-plane separation**:

* **Data Plane:** Video delivery handled by HTTP/CDN via the browser `<video>` element
* **Control Plane:** WebSockets handle synchronization, state changes, and comment delivery

This separation mirrors real-world systems (e.g., YouTube Live, Coursera, Zoom recordings) and avoids inefficient video streaming over WebSockets.


## High-Level System Diagram

```
                   ┌─────────────┐
                   │   Browser   │
                   │ <video>     │
                   │ WebSocket   │
                   └──────▲──────┘
                          │
                  WebSocket│
                          │
        ┌─────────────────┴─────────────────┐
        │       WebSocket Application        │
        │  (FastAPI, Stateless Instances)   │
        └─────────────────▲─────────────────┘
                          │
          Pub/Sub + ZSET   │
                          │
                   ┌──────┴──────┐
                   │    Redis    │
                   │ Sorted Sets │
                   │ Pub/Sub     │
                   └─────────────┘
```

## Core Components

### WebSocket Server

**Responsibilities**

* Manage client connections
* Receive comment submissions
* Broadcast synchronization events
* Fetch comment history from Redis
* Enforce server-authoritative timestamps

**Characteristics**

* Stateless
* Horizontally scalable
* No per-client persistent state


### Redis (Shared State Layer)

Redis serves two distinct roles:

#### a. Temporal Data Store (Sorted Sets)

Stores comments indexed by video timestamp.

```
Key: classroom:{classroom_id}:comments
Type: ZSET
Score: video_timestamp (float, seconds)
Value: JSON-encoded comment payload
```

#### b. Pub/Sub Fan-Out

Used to broadcast new comment events across all WebSocket server instances.

```
Channel: classroom-events
Payload: serialized comment event
```

### Client (Browser)

**Responsibilities**

* Play video using native HTML `<video>`
* Track playback state (play, pause, seek)
* Request comment history from server
* Schedule comment rendering relative to playback time

**Important Design Choice**

* The client controls *when* comments render
* The server controls *what* comments exist and *where* they belong in time


## Data Model

### Comment Entity

| Field           | Type   | Description                                 |
|  |  | - |
| id              | UUID   | Unique identifier                           |
| video_timestamp | float  | Timestamp in seconds (sub-second precision) |
| message         | string | Comment text                                |
| author          | string | User identifier                             |
| created_at      | float  | Server-authoritative creation time          |


## Synchronization Strategy

### Server-Authoritative Time

The server is the **single source of truth** for time.

* Clients never send authoritative timestamps
* Server timestamps all comments
* Prevents clock skew and client manipulation

### Comment Scheduling Model

Comments are **not rendered immediately on arrival**.

Instead:

1. Server sends comment metadata
2. Client schedules rendering based on:

   * `video.currentTime`
   * pause/play state
   * seek position

This avoids:

* Comment flooding during pause
* Rendering drift due to buffering
* Network latency inconsistencies


### State Transitions

| Event        | Action                                 |
|  | -- |
| New join     | Fetch history `00:00 → currentTime`    |
| Pause        | Cancel scheduled comment timers        |
| Resume       | Re-fetch history and reschedule        |
| Seek         | Clear UI, rehydrate state              |
| Late message | Render based on timestamp, not arrival |


## Concurrency Strategy

### Server-Side

* FastAPI WebSocket handlers are asynchronous
* Redis operations are atomic
* No shared in-memory mutable state across requests

### Redis Guarantees

* `ZADD` and `ZRANGEBYSCORE` are atomic
* Pub/Sub guarantees fan-out to all subscribers
* Eliminates race conditions between servers


## Scalability Considerations

### Horizontal Scaling

The system scales horizontally by adding more WebSocket server instances.

* All instances share Redis
* Pub/Sub ensures consistent fan-out
* No session affinity required

### Expected Capacity

| Metric             | Supported               |
|  | -- |
| Concurrent clients | 500+                    |
| Message latency    | < 500ms                 |
| Comment volume     | Thousands per classroom |


## Performance Characteristics

### Time Complexity

| Operation       | Big-O        |
|  |  |
| Insert comment  | O(log n)     |
| Fetch history   | O(log n + k) |
| Broadcast event | O(c)         |

Where:

* `n` = total comments
* `k` = comments returned
* `c` = connected clients per server instance

## Fault Tolerance

### Redis Failure

* Comment persistence unavailable
* WebSocket servers remain functional but degraded
* Can be mitigated with Redis replication

### WebSocket Server Failure

* Clients reconnect to another instance
* No data loss due to Redis persistence


## Security Considerations & Mitigations

| Risk                      | Mitigation                      |
| - | - |
| Client timestamp spoofing | Server-authoritative timestamps |
| Replay attacks            | Comment IDs are unique          |
| State corruption          | Redis atomic operations         |
| Credential leaks          | `.env`-based configuration      |
| Cross-room access         | Namespaced Redis keys           |


## Trade-offs & Design Alternatives

### Trade-offs

* Redis Pub/Sub does not persist messages
  → Acceptable since comments are stored in Sorted Sets

* Client-side scheduling increases frontend complexity
  → Necessary for accurate playback synchronization

### Alternatives Considered

| Alternative               | Reason Rejected                          |
| - | - |
| Kafka                     | Too heavy for real-time ephemeral events |
| Server-side scheduling    | Cannot handle client buffering           |
| WebSocket video streaming | Inefficient and unrealistic              |


## Observability & Testing

* Load tested with **Locust** (50–500 clients)
* Manual browser testing for pause/seek correctness
* Unit tests for Redis indexing logic


## Assumptions

* Video delivery handled via HTTP/CDN
* Redis available as shared infrastructure
* Classroom sizes are moderate
* Authentication is out of scope
