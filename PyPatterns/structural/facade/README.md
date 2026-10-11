# Facade Pattern

## Intent

Provide a unified interface to a set of interfaces in a subsystem. Facade defines a higher-level interface that makes the subsystem easier to use.

This demo's **HomeTheaterFacade** coordinates **Amplifier**, **DvdPlayer**, and **Projector** so the client calls a single `watch_movie()` instead of six individual startup steps.

## Class Diagram

```mermaid
classDiagram
    class Amplifier {
        +on() str
        +set_volume(level) str
    }
    class DvdPlayer {
        +on() str
        +play(movie) str
    }
    class Projector {
        +on() str
        +wide_screen() str
    }
    class HomeTheaterFacade {
        -amp: Amplifier
        -dvd: DvdPlayer
        -projector: Projector
        +watch_movie(movie) list
    }
    HomeTheaterFacade o-- Amplifier
    HomeTheaterFacade o-- DvdPlayer
    HomeTheaterFacade o-- Projector
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Facade as HomeTheaterFacade
    participant Amp as Amplifier
    participant Proj as Projector
    participant DVD as DvdPlayer

    Client->>Facade: watch_movie("Design Patterns")
    Facade->>Amp: on()
    Facade->>Amp: set_volume(5)
    Facade->>Proj: on()
    Facade->>Proj: wide_screen()
    Facade->>DVD: on()
    Facade->>DVD: play("Design Patterns")
    Facade-->>Client: list of steps
```

## Flowchart

```mermaid
flowchart TD
    A[Client: watch_movie] --> B[Facade receives request]
    B --> C[Turn on amplifier]
    C --> D[Set volume]
    D --> E[Turn on projector]
    E --> F[Enable wide-screen]
    F --> G[Turn on DVD player]
    G --> H[Play movie]
    H --> I[Return consolidated result]
    I --> J[Client never touches subsystems directly]
```

## Run Instructions

```bash
cd PyPatterns
python3 structural/facade/demo.py
```

Prints the ordered startup sequence for a home theater movie session from one facade call.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Simplifies client code dramatically | Facade can become a "god object" if it grows unchecked |
| Decouples clients from subsystem churn | Does not prevent direct subsystem access |
| Promotes layered architecture | Extra indirection for power users who need fine control |

## Distributed Environments

Facades are the backbone of **API simplification** in distributed systems:

- **BFF (Backend for Frontend)** — one facade per client platform aggregating calls to many microservices.
- **GraphQL gateways** — a single schema hides dozens of REST/gRPC backends.
- **Cloud SDK high-level clients** — `boto3.client()` vs resource-oriented facades that wrap S3, DynamoDB, and SQS setup.

When onboarding a mobile app to twelve internal services, a facade service orchestrates auth, catalog, cart, and payment in one `checkout()` RPC — reducing round trips, retries, and error-handling burden on the client.

## References

- [Facade — Refactoring.Guru](https://refactoring.guru/design-patterns/facade)
- [Facade pattern — Wikipedia](https://en.wikipedia.org/wiki/Facade_pattern)
