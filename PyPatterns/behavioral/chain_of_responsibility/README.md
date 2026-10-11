# Chain of Responsibility

## Intent

Avoid coupling the sender of a request to its receiver by giving multiple objects a chance to handle the request. Chain the receiving objects and pass the request along the chain until an object handles it.

This demo models a **support ticket escalation chain**: Level 1 handles low-severity issues, Level 2 handles medium, and Level 3 handles critical outages.

## Run

```bash
python3 behavioral/chain_of_responsibility/demo.py
```

## Class Diagram

```mermaid
classDiagram
    class SupportTicket {
        +int id
        +str description
        +int severity
    }
    class SupportHandler {
        <<abstract>>
        +int level
        +str name
        +SupportHandler _next
        +set_next(handler) SupportHandler
        +handle(ticket) str
    }
    class Level1Support {
        +handle(ticket) str
    }
    class Level2Support {
        +handle(ticket) str
    }
    class Level3Support {
        +handle(ticket) str
    }
    SupportHandler <|-- Level1Support
    SupportHandler <|-- Level2Support
    SupportHandler <|-- Level3Support
    SupportHandler --> SupportHandler : next
    SupportHandler ..> SupportTicket : uses
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant L1 as Level1Support
    participant L2 as Level2Support
    participant L3 as Level3Support

    Client->>L1: handle(critical ticket)
    L1->>L1: severity > level?
    L1->>L2: handle(ticket)
    L2->>L2: severity > level?
    L2->>L3: handle(ticket)
    L3->>L3: resolve ticket
    L3-->>Client: resolution message
```

## Flowchart

```mermaid
flowchart TD
    A[Receive ticket] --> B{Can this handler resolve it?}
    B -->|Yes| C[Resolve and return]
    B -->|No| D{Next handler exists?}
    D -->|Yes| E[Forward to next handler]
    E --> B
    D -->|No| F[Return unhandled message]
```

## Pros and Cons

| Pros | Cons |
| ---- | ---- |
| Reduces coupling between sender and receivers | No guarantee the request will be handled |
| Add or reorder handlers at runtime | Can be hard to debug long chains |
| Single Responsibility — each handler focuses on one level | May introduce latency as requests traverse the chain |

## Distributed Environments

In microservices, a chain of responsibility often maps to **middleware pipelines** or **API gateway filters** (auth → rate limit → routing). Each node decides whether to handle the request or pass it downstream.

- **HTTP middleware** (FastAPI, Starlette, Express) chains handlers in order.
- **Message queues** can route events through topic subscriptions where each consumer either processes or re-publishes.
- **Service meshes** (Istio, Linkerd) apply sidecar filters that mirror chain-of-responsibility semantics at the network layer.

Watch for **lost requests** when no handler claims responsibility — add explicit dead-letter queues or fallback endpoints in distributed setups.

## References

- [Chain of Responsibility — Refactoring.Guru](https://refactoring.guru/design-patterns/chain-of-responsibility)
- [Chain-of-responsibility pattern — Wikipedia](https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern)
