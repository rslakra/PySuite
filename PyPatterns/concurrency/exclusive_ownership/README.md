# Exclusive Ownership Pattern

## Intent

Eliminate data races by ensuring only one thread owns a mutable object at any time. Ownership transfers through queues — workers never read or write shared state concurrently.

This demo pipes `WorkItem` objects through two pipeline stages; each stage exclusively owns an item while transforming it, then hands it off via a queue.

## Class Diagram

```mermaid
classDiagram
    class WorkItem {
        +item_id: int
        +value: int
    }
    class PipelineStage {
        +inbox: Queue
        +outbox: Queue
        +run(transform)
    }
    PipelineStage ..> WorkItem : exclusive owner
    PipelineStage ..> Queue : transfer ownership
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Main
    participant Q1 as stage1_in
    participant A as stage-a
    participant Q2 as stage2_in
    participant B as stage-b

    Main->>Q1: put WorkItem
    A->>Q1: get (owns item)
    A->>A: value += 10
    A->>Q2: put (transfer ownership)
    B->>Q2: get (owns item)
    B->>B: value *= 2
    Main->>Q2: collect result
```

## Flowchart

```mermaid
flowchart TD
    A[Producer enqueues object] --> B[Single consumer takes ownership]
    B --> C[Mutate while exclusively owned]
    C --> D{Another stage?}
    D -->|Yes| E[Enqueue to next stage — transfer ownership]
    E --> B
    D -->|No| F[Done — no concurrent access ever occurred]
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/exclusive_ownership/demo.py
```

Expected output shows each stage logging sole ownership, then five items with final values `(id+10)*2` — e.g. item 0 → 20, item 1 → 22.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| No locks on shared mutable state | Ownership transfer adds queue latency |
| Easier to reason about invariants | Object must not be referenced elsewhere |
| Scales to pipeline / actor architectures | Deep copies may be needed if aliases exist |

## Distributed Environments

Exclusive ownership is the foundation of **message-passing concurrency**:

- **Kafka partition consumption** — one consumer group member owns a partition at a time.
- **Actor models** (Erlang, Akka) — messages transfer state; actors never share memory.
- **S3 object workflows** — lambdas receive an object key, process, write a new key (immutable hand-off).

Prefer queues and immutable messages over shared databases with row locks when crossing service boundaries. See also [atomic_operation](../atomic_operation/README.md) for when shared counters require explicit synchronization instead.

## References

- [Ownership semantics — Rust book (concept)](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
- [Message passing — Wikipedia](https://en.wikipedia.org/wiki/Message_passing)
- [Python queue — thread-safe transfers](https://docs.python.org/3/library/queue.html)
