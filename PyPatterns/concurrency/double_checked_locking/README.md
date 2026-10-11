# Double-Checked Locking Pattern

## Intent

Reduce the overhead of acquiring a lock by testing the locking criterion (the "lock hint") before synchronizing. Lock only when the guarded resource might not yet be initialized — a common technique for thread-safe lazy initialization.

This demo implements **LazyConfig.instance()**: the fast path reads `_instance` without a lock; the slow path acquires the lock and initializes once.

## Class Diagram

```mermaid
classDiagram
    class LazyConfig {
        -LazyConfig _instance$
        -Lock _lock$
        +dict settings
        +instance()$ LazyConfig
    }
    class WorkerThread {
        +run()
    }
    WorkerThread ..> LazyConfig : instance()
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant T1 as Thread 1
    participant T2 as Thread 2
    participant Lock
    participant Config as LazyConfig

    T1->>Config: instance()
    Config->>Config: _instance is None?
    T1->>Lock: acquire
    T2->>Config: instance()
    T2->>Config: _instance is None?
    T2->>Lock: wait (blocked)
    T1->>Config: create LazyConfig
    T1->>Lock: release
    T2->>Lock: acquire
    T2->>Config: _instance already set
    T2->>Lock: release
    T2-->>T2: return existing instance
```

## Flowchart

```mermaid
flowchart TD
    A[Request instance] --> B{_instance set?}
    B -->|Yes| C[Return instance — fast path]
    B -->|No| D[Acquire lock]
    D --> E{_instance still None?}
    E -->|No| F[Release lock, return instance]
    E -->|Yes| G[Create and assign instance]
    G --> F
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/double_checked_locking/demo.py
```

Expected output confirms all threads see the same object id and shared settings.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Avoids lock contention after initialization | Historically buggy on some language/memory-model combinations |
| Fast read path for hot singleton access | Easy to implement incorrectly without proper memory barriers |
| Standard idiom for lazy one-time setup | Python's GIL makes simpler patterns often sufficient |

## Distributed Environments

Double-checked locking has distributed analogues for **one-time initialization under contention**:

- **Distributed locks (Redis Redlock, etcd)** guard first-time resource creation (schema migration, cache warm-up).
- **Compare-and-swap (CAS)** in DynamoDB or Consul avoids full locks when creating a key if-not-exists.
- **Kubernetes init containers** ensure setup runs once before the main pod starts serving traffic.

In Python 3.12, prefer `threading.Lock` with a simple check or `functools.cache` for process-local singletons. For cross-process singletons, use file locks or a coordination service rather than in-memory double-checked locking.

## References

- [Double-checked locking — Wikipedia](https://en.wikipedia.org/wiki/Double-checked_locking)
