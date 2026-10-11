# Reactor Pattern

## Intent

Handle many concurrent I/O sources on **one thread** by demultiplexing readiness events (via `select`, epoll, kqueue) and dispatching each event to a registered handler. The reactor turns synchronous blocking resources into a structured, non-blocking event loop.

This demo posts typed events to a queue, wakes the loop through a `socketpair` + `select`, and dispatches to order/inventory handlers.

## Class Diagram

```mermaid
classDiagram
    class Reactor {
        -_handlers: dict
        -_events: Queue
        -_read: socket
        -_write: socket
        +register(event_type, handler)
        +post(event_type, payload)
        +run(timeout)
    }
    class EventHandler {
        <<callable>>
        +__call__(payload)
    }
    class Queue {
        +put(item)
        +get_nowait() item
    }
    Reactor *-- Queue
    Reactor o-- EventHandler : dispatches to
    Reactor ..> select : waits on readable fd
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Producer as Producer thread
    participant Reactor
    participant Select as select()
    participant Handler as OrderHandler

    Producer->>Reactor: post("order", "order-101 placed")
    Reactor->>Reactor: enqueue event
    Reactor->>Reactor: write wakeup byte to socketpair
    Reactor->>Select: select([read_fd], [], [], timeout)
    Select-->>Reactor: fd readable
    Reactor->>Reactor: dequeue event
    Reactor->>Handler: handler("order-101 placed")
    Handler-->>Reactor: done
```

## Flowchart

```mermaid
flowchart TD
    A[Event loop start] --> B[select on registered fds]
    B --> C{Fd readable or timeout?}
    C -->|Readable| D[Read wakeup / I/O data]
    D --> E[Dequeue pending events]
    E --> F{Handler registered?}
    F -->|Yes| G[Dispatch to handler]
    F -->|No| H[Drop or log unknown event]
    G --> B
    H --> B
    C -->|Timeout| I{Shutdown?}
    I -->|No| B
    I -->|Yes| J[Exit loop]
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/reactor/demo.py
```

Expected output shows three events dispatched to OrderHandler and InventoryHandler within ~1 s, then a completion line.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Single thread — no locks for handler state | Handler must not block (stalls entire loop) |
| Scales to many idle connections cheaply | Complex error handling and backpressure |
| Foundation of asyncio, Node.js, Nginx event model | CPU-bound work needs thread/process offload |
| Clear registration/dispatch separation | Debugging callback chains can be difficult |

## Distributed Environments

Reactor semantics appear wherever **event demux + dispatch** drives throughput:

- **API gateways & proxies**: Nginx, Envoy, HAProxy — epoll/kqueue on thousands of idle connections.
- **Stream processors**: Kafka consumers poll partitions and dispatch records to handlers.
- **asyncio / Trio**: Python async runtimes are reactor-style loops over sockets and timers.
- **Serverless triggers**: S3 upload → Lambda dispatch; CloudWatch Events → target function.

At scale, combine reactors on each node with message queues for cross-node work; never block the reactor on remote RPC.

## References

- [Reactor pattern — Wikipedia](https://en.wikipedia.org/wiki/Reactor_pattern)
- [Reactor pattern — POSA2](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture)
- [select — Python docs](https://docs.python.org/3/library/select.html)
