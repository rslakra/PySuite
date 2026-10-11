# Circuit Breaker Pattern

## Intent

Prevent cascading failures by **wrapping calls to unreliable dependencies** with a breaker that opens after repeated errors, rejects calls while open, and probes in half-open state before closing again.

This demo wraps a flaky payment gateway; after three failures the breaker opens and fast-fails until recovery timeout.

## Class Diagram

```mermaid
classDiagram
    class State {
        <<enumeration>>
        CLOSED
        OPEN
        HALF_OPEN
    }
    class CircuitBreaker {
        +failure_threshold: int
        +recovery_timeout: float
        +failures: int
        +state: State
        +call(operation) str
    }
    class FlakyPaymentGateway {
        +charge() str
    }
    CircuitBreaker --> State
    CircuitBreaker ..> FlakyPaymentGateway : protects
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant App
    participant CB as CircuitBreaker
    participant GW as PaymentGateway

    App->>CB: call(charge)
    CB->>GW: charge()
    GW-->>CB: timeout (failure++)
    Note over CB: failures >= threshold
    CB->>CB: state = OPEN
    App->>CB: call(charge)
    CB-->>App: rejected (fast fail)
    Note over CB: recovery timeout elapsed
    CB->>CB: state = HALF-OPEN
    App->>CB: call(charge)
    CB->>GW: probe
    GW-->>CB: success
    CB->>CB: state = CLOSED
```

## Flowchart

```mermaid
flowchart TD
    A[Call downstream] --> B{Breaker state?}
    B -->|CLOSED| C[Invoke service]
    C --> D{Success?}
    D -->|Yes| E[Reset failure count]
    D -->|No| F[Increment failures]
    F --> G{Threshold reached?}
    G -->|Yes| H[OPEN — reject calls]
    G -->|No| A
    B -->|OPEN| I{Timeout elapsed?}
    I -->|No| J[Fast fail]
    I -->|Yes| K[HALF-OPEN — allow probe]
    K --> C
    B -->|HALF-OPEN| K
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/circuit_breaker/demo.py
```

Expected output shows failures incrementing, breaker opening, then half-open probe and close on success.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Stops hammering failing services | Tuning thresholds is workload-specific |
| Fails fast — frees threads and connections | Open breaker may reject valid calls during recovery |
| Gives downstream time to heal | Needs fallback or degraded-mode UX |

## Distributed Environments

Circuit breakers are **mandatory at service mesh boundaries**:

- **Istio / Envoy / resilience4j / Polly**: per-route failure budgets and automatic open/close.
- **Bulkhead pattern (companion)**: isolate thread pools so one dependency cannot exhaust all resources.
- **Health checks + load balancers**: remove unhealthy instances before breakers trip fleet-wide.

Log state transitions, expose breaker metrics to dashboards, and combine with retries only in closed state.

## References

- [Circuit Breaker — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
