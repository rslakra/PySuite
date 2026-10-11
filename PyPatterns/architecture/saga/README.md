# Saga Pattern

## Intent

Coordinate a **long-running business transaction** across multiple services without a distributed two-phase commit. Each step has a **compensating action**; if a later step fails, prior steps are undone in reverse order.

This demo books a hotel, fails on flight reservation, and compensates by cancelling the hotel.

## Class Diagram

```mermaid
classDiagram
    class SagaOrchestrator {
        +steps: list
        -_completed: list
        +add(name, execute, compensate)
        +run()
        -_rollback()
    }
    class Step {
        +name: str
        +execute()
        +compensate()
    }
    SagaOrchestrator o-- Step
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant H as Hotel Service
    participant F as Flight Service

    O->>H: reserve-hotel
    H-->>O: ok
    O->>F: reserve-flight
    F-->>O: error (no seats)
    O->>O: rollback
    O->>H: compensate (cancel hotel)
    H-->>O: cancelled
```

## Flowchart

```mermaid
flowchart TD
    A[Start saga] --> B[Execute step N]
    B --> C{Success?}
    C -->|Yes| D[Record compensation handler]
    D --> E{More steps?}
    E -->|Yes| B
    E -->|No| F[Commit — saga complete]
    C -->|No| G[Run compensations in reverse]
    G --> H[Saga aborted]
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/saga/demo.py
```

Expected output shows hotel booked, flight failing, hotel cancelled, and final state with no reservations.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Avoids locking resources across services (no 2PC) | Compensations are hard to design — not true undo |
| Fits microservices and eventual consistency | Orchestrator is a single coordination point (or complex choreography) |
| Each service owns its local transaction | Temporary inconsistent state visible between steps |
| Industry-proven for orders, travel, payments | Idempotent compensate handlers required |

## Distributed Environments

Sagas are essential in **microservice workflows**:

- **Orchestration**: central coordinator (Temporal, Camunda, AWS Step Functions) drives steps.
- **Choreography**: each service listens for events and reacts (`OrderCreated` → `PaymentCaptured` → …).
- **Travel booking**, **e-commerce checkout**, **loan approval** — multi-step flows with rollback.
- **Temporal / Cadence** provide durable saga state and automatic retries.

Prefer **outbox pattern** to publish saga events atomically with local DB commits.

## References

- [Saga pattern — microservices.io](https://microservices.io/patterns/data/saga.html)
- [Saga — Wikipedia (long-running transaction)](https://en.wikipedia.org/wiki/Saga_(software))
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
