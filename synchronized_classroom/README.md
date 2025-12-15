# Synchronized Classroom — Real-Time Comment Synchronization

**Domain:** EdTech & Media Streaming
**Scenario:** The Synchronized Classroom (BONUS)
**Focus:** Real-Time Communication, State Synchronization, Latency Management

## Overview

This project implements the backend infrastructure for a **synchronized virtual classroom**, where multiple students watch the same educational video and exchange timestamp-anchored comments in real time.

Due to varying network latency, buffering, and playback controls (pause/seek), students may be at different video frames at any given moment.
The system guarantees that **comments appear at the correct video timestamp for all viewers**, including:

* Live viewers
* Late joiners
* Users who pause or seek backward/forward

The solution uses **WebSockets for real-time communication**, **Redis Sorted Sets for temporal indexing**, and **server-authoritative time** to maintain deterministic synchronization across clients.

## Key Capabilities

* Real-time bidirectional communication using WebSockets
* Sub-second timestamp anchoring of comments
* Deterministic comment delivery despite network latency
* Comment history synchronization for late joiners
* Correct behavior during pause, resume, and seeking
* Horizontal scalability via Redis Pub/Sub fan-out
* Docker-ready, one-command startup
* Load tested up to **500 concurrent clients**

## Architecture Summary

```
            ┌─────────────┐
            │   Browser   │
            │ <video>     │
            │ WebSocket   │
            └──────▲──────┘
                   │
           WebSocket│
                   │
        ┌──────────┴──────────┐
        │  FastAPI WS Server  │
        │  (Stateless)        │
        └──────────▲──────────┘
                   │
      Pub/Sub + ZSET│
                   │
            ┌──────┴──────┐
            │    Redis    │
            │ Sorted Sets │
            │ Pub/Sub     │
            └─────────────┘
```

> **Important:**
> Video delivery is intentionally handled via the browser `<video>` element (HTTP/CDN).
> WebSockets are used strictly for **synchronization and comments**, not media streaming.

## Technology Stack

| Component        | Technology             |
| ---------------- | ---------------------- |
| Backend          | Python 3.11, FastAPI   |
| Real-time        | WebSockets             |
| Temporal Index   | Redis Sorted Sets      |
| Fan-out          | Redis Pub/Sub          |
| Containerization | Docker, Docker Compose |
| Load Testing     | Locust                 |

## Core Design Decisions

### Server-Authoritative Time

The server is the single source of truth for time.
Clients receive server timestamps and schedule comment rendering relative to their local playback clock.

**Why?**

* Client clocks are unreliable
* Eliminates drift and race conditions
* Enables deterministic replay for late joiners

### Redis Sorted Sets for Temporal Indexing

Each classroom stores comments in a Redis Sorted Set:

```
ZADD classroom:{id}:comments <video_timestamp> <comment_payload>
```

**Benefits**

* Sub-second timestamp precision
* O(log n) insertion and retrieval
* Atomic, thread-safe operations
* Perfect fit for time-indexed data

### Client-Side Scheduling

The server **does not push comments immediately**.
Instead, clients schedule comments locally based on:

* `video.currentTime`
* pause/play state
* seek events

This ensures:

* No comment backlog during pause
* Correct rendering after seek
* Accurate synchronization regardless of buffering

## Synchronization Strategy

### New Viewer Joins Mid-Video

1. Client loads video metadata
2. Client requests comment history from `00:00 → currentTime`
3. Past comments render immediately
4. Future comments are scheduled

### Pause / Resume

* Pause cancels scheduled comment timers
* Resume re-hydrates state from Redis
* No comment accumulation occurs

### Seek Forward / Backward

* Cancel existing timers
* Clear rendered comments
* Request fresh history up to new timestamp
* Reschedule future comments

### Late Network Delivery

* Comments are rendered based on **video timestamp**, not arrival time
* Late packets do not affect correctness

## Redis Pub/Sub Fan-Out

To support horizontal scaling across multiple WebSocket servers:

1. A server publishes new comments to Redis Pub/Sub
2. All server instances receive the event
3. Each server forwards it to its connected clients

This enables:

* Stateless WebSocket servers
* Linear horizontal scaling
* No cross-node coupling

## Load Testing

Load testing was performed using **Locust** to simulate real WebSocket clients.

### Test Parameters

| Scenario      | Users | Result |
| ------------- | ----- | ------ |
| Baseline      | 50    | Stable |
| Expected Peak | 200   | Stable |
| Stress Test   | 500   | Stable |

### Observations

* Message latency remained under **500ms**
* Redis CPU utilization remained stable
* No dropped WebSocket connections
* Fan-out performed correctly across simulated load

## Running the Project (Docker)

### Prerequisites

* Docker
* Docker Compose

### Start the System

```bash
docker compose up --build
```

### Services

* WebSocket Server: `ws://localhost:8000/ws/{user_id}`
* Redis: internal container

### Client Demo

Open in browser:

```
client/index.html
```

Multiple tabs simulate multiple students.

---

## Running Tests

```bash
pytest -s tests/test_redis_index.py
```

or

```bash
locust -f loadtest/locustfile.py 
```

## Time Complexity

| Operation         | Complexity   |
| ----------------- | ------------ |
| Add comment       | O(log n)     |
| Retrieve history  | O(log n + k) |
| Fan-out broadcast | O(c) clients |

Where:

* `n` = number of comments
* `k` = comments returned
* `c` = connected clients per server

## Security Considerations

* Clients do not control authoritative timestamps
* WebSocket message structure is validated
* Redis keys are namespaced per classroom
* No sensitive credentials committed (via `.env`)

## Trade-offs & Alternatives

### Trade-offs

* Redis Pub/Sub does not persist messages (acceptable since comments are stored in ZSETs)
* Client-side scheduling increases frontend complexity

### Alternatives Considered

* Kafka: Overkill for real-time ephemeral events
* Server-side scheduling: Breaks under variable client buffering
* Streaming video via WebSocket: Inefficient and unrealistic

## Assumptions

* Video files are delivered via CDN or HTTP
* Classroom sizes are moderate (50–500 concurrent viewers)
* Redis is available as shared infrastructure

## Walkthrough Video

A short walkthrough video explains:

* Architecture overview
* Synchronization strategy
* Redis Sorted Sets & Pub/Sub usage
* Load testing approach

(See link provided in submission email.)
