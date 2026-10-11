# Read-Write Lock Pattern

## Intent

Allow **multiple concurrent readers** OR **one exclusive writer** — optimizing read-heavy workloads where shared data is read often but mutated rarely. Readers share access; writers block all readers and other writers.

This demo implements a simple `ReadWriteLock` and uses it in a `SharedCache` where four reader threads run concurrently, then a writer updates exclusively.

## Class Diagram

```mermaid
classDiagram
    class ReadWriteLock {
        -_mutex: Lock
        -_write_lock: Lock
        -_readers: int
        +read() contextmanager
        +write() contextmanager
    }
    class SharedCache {
        -_data: dict
        -_rw: ReadWriteLock
        +read_hits() int
        +increment_hits()
    }
    SharedCache *-- ReadWriteLock
    ReadWriteLock --> threading_Lock : composes two locks
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant R1 as Reader 1
    participant R2 as Reader 2
    participant RW as ReadWriteLock
    participant W as Writer
    participant Data as _data

    R1->>RW: acquire read
    RW->>RW: readers=1, hold write_lock
    R2->>RW: acquire read
    RW->>RW: readers=2
    par Concurrent reads
        R1->>Data: read hits
        R2->>Data: read hits
    end
    R1->>RW: release read
    R2->>RW: release read
    RW->>RW: readers=0, release write_lock
    W->>RW: acquire write
    W->>Data: increment hits
    W->>RW: release write
```

## Flowchart

```mermaid
flowchart TD
    A{Access type?} -->|Read| B[Increment reader count]
    B --> C{First reader?}
    C -->|Yes| D[Acquire write lock shared mode]
    C -->|No| E[Proceed with read]
    D --> E
    E --> F[Read shared data]
    F --> G[Decrement reader count]
    G --> H{Last reader?}
    H -->|Yes| I[Release write lock]
    H -->|No| J[Done]
    I --> J
    A -->|Write| K[Acquire write lock exclusively]
    K --> L[Modify shared data]
    L --> M[Release write lock]
    M --> J
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/read_write_lock/demo.py
```

Expected output shows four readers completing in ~0.02 s each concurrently (total ~0.05 s), then writer increment, final hits = 2.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Higher read throughput than a plain mutex | Writer starvation if readers arrive continuously |
| Fits caches, config snapshots, registries | More complex than a single lock — harder to prove correct |
| Readers do not block each other | Python stdlib has no built-in RW lock (unlike Java) |
| Natural fit for read-heavy service data | Incorrect implementation risks deadlocks or torn reads |

## Distributed Environments

Read-write semantics appear in replicated and cached systems:

- **Database replicas**: primary accepts writes; replicas serve read-only queries (eventual consistency trade-offs).
- **CDN / edge caches**: many edge readers, rare origin writes — invalidation is the "write lock."
- **etcd / Consul**: consistent reads vs transactional writes with revision checks.
- **Copy-on-write structures**: immutable snapshots let readers proceed without locks (functional approach to RW semantics).

For cross-node consistency, pair read replicas with version vectors or lease-based staleness bounds rather than a local RW lock.

## References

- [Readers–writer lock — Wikipedia](https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock)
- [Read-write lock variants — POSIX rwlock](https://en.wikipedia.org/wiki/POSIX_Threads)
- [threading — Python docs](https://docs.python.org/3/library/threading.html)
