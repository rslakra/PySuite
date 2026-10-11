# Throttling Pattern

## Intent

**Protect downstream services** by limiting how much load reaches them — typically via concurrency caps, queue depth limits, or deliberate slowdown. Unlike rate limiting (requests per second), throttling focuses on **resource protection** and graceful degradation under pressure.

This demo compares an unthrottled burst (overloading a fragile backend) with a `ThrottleGate` that caps inflight requests at two.

## Class Diagram

```mermaid
classDiagram
    class ThrottleGate {
        +max_inflight: int
        -_semaphore: Semaphore
        +invoke(backend, request_id) str
    }
    class ThrottledBackend {
        +max_safe: int
        -_active: int
        +handle(request_id) str
    }
    class ClientPool {
        +burst(n)
    }
    ClientPool --> ThrottleGate : optional
    ThrottleGate --> ThrottledBackend : guarded access
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant C1 as Client 1
    participant C2 as Client 2
    participant G as ThrottleGate
    participant B as Backend

    C1->>G: acquire slot
    G->>B: handle #1
    C2->>G: acquire slot
    G->>B: handle #2
    Note over G: third client waits
    B-->>G: done #1
    G-->>C1: release slot
    G->>B: handle #3
```

## Flowchart

```mermaid
flowchart TD
    A[Incoming request] --> B{Inflight < max?}
    B -->|Yes| C[Admit to backend]
    B -->|No| D[Queue or reject]
    C --> E[Backend processes]
    E --> F[Release slot]
    D --> G{Queue full?}
    G -->|Yes| H[503 / shed load]
    G -->|No| I[Wait for slot]
    I --> C
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/throttling/demo.py
```

Expected output shows failures without throttling and six successful responses with the gate limiting concurrency to two.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Prevents cascade failures and OOM on backends | Queued requests increase tail latency |
| Semaphore / bulkhead patterns isolate tenants | Tuning max inflight requires load testing |
| Works alongside rate limiting at different layers | Aggressive throttling drops revenue-bearing traffic |
| Enables graceful degradation under spike load | Clients may need retry-after signaling |

## Distributed Environments

Throttling protects **capacity-constrained dependencies**:

- **Bulkhead pattern** (Hystrix thread pools per dependency).
- **Envoy / nginx** `max_concurrent_streams` and connection limits.
- **Database connection pools** cap concurrent queries.
- **Serverless concurrency limits** (Lambda reserved concurrency).
- **Adaptive throttling** (Google SRE) reduces accepted RPS as backend latency rises.

Pair with **load shedding** (return 503 early) and **autoscaling** so throttles are a safety net, not the primary capacity plan.

## References

- [Throttling — Wikipedia (computing)](https://en.wikipedia.org/wiki/Throttle)
- [Bulkhead pattern — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
