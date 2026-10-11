# Service Handler Pattern

## Intent

Handle each incoming request on its own thread. A server accepts tasks and spawns a dedicated handler thread per request, isolating work without a shared worker pool.

This demo models a small task server that dispatches five requests, each processed by a separately named handler thread.

## Class Diagram

```mermaid
classDiagram
    class Request {
        +request_id: int
        +payload: str
    }
    class ServiceHandler {
        -_requests: Queue
        -_handlers: list
        +submit(request: Request)
        +dispatch(request: Request) Thread
        +drain()
        +join_all()
        -_handle(request: Request)
    }
    ServiceHandler ..> Request : accepts
    ServiceHandler ..> Thread : spawns per request
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Server as ServiceHandler
    participant Q as Request Queue
    participant T1 as handler-0
    participant T2 as handler-1

    Client->>Server: submit(requests)
    Client->>Server: drain()
    Server->>Q: get request 0
    Server->>T1: start thread
    Server->>Q: get request 1
    Server->>T2: start thread
    T1->>T1: process payload
    T2->>T2: process payload
    Client->>Server: join_all()
```

## Flowchart

```mermaid
flowchart TD
    A[Client submits request] --> B[Request queued]
    B --> C[Server accepts request]
    C --> D[Spawn new handler thread]
    D --> E[Handler processes request]
    E --> F{More queued?}
    F -->|Yes| C
    F -->|No| G[join_all completes]
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/service_handler/demo.py
```

Expected output shows five requests each handled by a distinct `handler-N` thread.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Simple mental model — one thread per unit of work | Thread creation overhead at high request rates |
| Fault isolation between requests | Unbounded threads can exhaust memory under load |
| No pool sizing or queue backpressure logic | Context switching cost grows with concurrency |

## Distributed Environments

Thread-per-request maps to **process-per-request** or **container-per-invocation** models in distributed systems:

- **Serverless functions** (AWS Lambda, Cloud Functions) spin up an isolated execution environment per invocation.
- **CGI / early Apache modules** forked or threaded per HTTP request before pools became standard.
- **Sidecar handlers** in service meshes can dedicate a worker to a single RPC stream.

At scale, teams usually migrate to **thread pools**, **async event loops**, or **worker queues** (see [thread_pool](../thread_pool/README.md)) to cap resource use while keeping the same request/handler separation at the API boundary.

## References

- [Thread-per-request — Wikipedia (concurrency patterns)](https://en.wikipedia.org/wiki/Software_design_pattern#Concurrency)
- [Python threading](https://docs.python.org/3/library/threading.html)
