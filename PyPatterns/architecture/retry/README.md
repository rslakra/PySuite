# Retry Pattern

## Intent

Automatically **re-attempt failed operations** when errors are transient (timeouts, 503s, network blips). Combine retries with **exponential backoff** and jitter to avoid overwhelming a recovering dependency.

This demo uses a `RetryPolicy` that succeeds on the fourth attempt after backing off between failures.

## Class Diagram

```mermaid
classDiagram
    class RetryPolicy {
        +max_attempts: int
        +base_delay: float
        +max_delay: float
        +run(operation) T
    }
    class FlakyClient {
        +fetch() str
    }
    RetryPolicy --> FlakyClient : wraps call
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant R as RetryPolicy
    participant U as Upstream

    C->>R: run(fetch)
    R->>U: attempt 1
    U-->>R: timeout
    R->>R: sleep(backoff)
    R->>U: attempt 2
    U-->>R: timeout
    R->>R: sleep(2x backoff)
    R->>U: attempt 3
    U-->>R: timeout
    R->>U: attempt 4
    U-->>R: success
    R-->>C: result
```

## Flowchart

```mermaid
flowchart TD
    A[Invoke operation] --> B{Success?}
    B -->|Yes| C[Return result]
    B -->|No| D{Retryable error?}
    D -->|No| E[Fail fast]
    D -->|Yes| F{Attempts left?}
    F -->|No| G[Raise / circuit open]
    F -->|Yes| H[Wait exponential backoff + jitter]
    H --> A
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/retry/demo.py
```

Expected output shows three failed attempts, then success on attempt four.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Masks transient failures from callers | Can amplify load during outages (retry storms) |
| Improves perceived reliability | Non-idempotent ops may duplicate side effects |
| Backoff + jitter protects recovering services | Hides systemic problems if retries always succeed eventually |
| Configurable per dependency | Total latency grows with attempt count |

## Distributed Environments

Retries appear at **every network boundary**:

- **HTTP clients**: `urllib3.Retry`, AWS SDK built-in retry modes.
- **gRPC**: retry policy in service config; idempotency keys for POST.
- **Message consumers**: visibility timeout + redelivery (SQS, RabbitMQ).
- **Kubernetes**: `restartPolicy` and probe failure thresholds.
- **Circuit breaker** (Hystrix, resilience4j) often sits beside retry to stop infinite loops.

Always retry **idempotent** reads and writes with deduplication keys; use **dead-letter queues** after max attempts.

## References

- [Exponential backoff — Wikipedia](https://en.wikipedia.org/wiki/Exponential_backoff)
- [Idempotence — Wikipedia](https://en.wikipedia.org/wiki/Idempotence)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
