# Request-Response Pattern

## Intent

Model **synchronous interaction** as a paired message exchange: the client sends a request and blocks until a correlated response arrives. This is the messaging analogue of RPC and HTTP call/response semantics.

This demo uses an in-process `RpcBroker` with correlation IDs, a request queue, and per-call reply queues.

## Class Diagram

```mermaid
classDiagram
    class RpcBroker {
        -_requests: Queue
        -_responses: dict
        -_lock: Lock
        +call(method, params) Any
        +serve_once() bool
    }
    class Client {
        +invoke(method, params)
    }
    class Server {
        +handle(request)
    }
    Client --> RpcBroker : call
    Server --> RpcBroker : serve_once
    RpcBroker --> Client : correlated reply
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant B as RpcBroker
    participant S as Server

    C->>B: call("get_balance", params)
    B->>B: assign correlation_id
    B->>S: dequeue request
    S->>S: process
    S->>B: enqueue response(corr_id)
    B->>C: reply_q.get()
    C-->>C: return result
```

## Flowchart

```mermaid
flowchart TD
    A[Client builds request] --> B[Assign correlation ID]
    B --> C[Send to request channel]
    C --> D[Client waits on reply channel]
    D --> E[Server dequeues request]
    E --> F[Server processes]
    F --> G[Server sends reply with same ID]
    G --> H[Client receives matching response]
    D --> I{Timeout?}
    I -->|Yes| J[Fail or retry]
    I -->|No| H
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/request_response/demo.py
```

Expected output shows two RPC calls returning formatted results after the background server handles them.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Familiar semantics — maps cleanly to function calls | Couples client and server in time (blocking) |
| Correlation IDs enable many in-flight calls | Timeouts and orphaned replies need handling |
| Works over queues, sockets, or HTTP | Less resilient than fire-and-forget under load |
| Natural fit for query operations | Not ideal for long-running or streaming work |

## Distributed Environments

Request-response underpins most **synchronous service calls**:

- **HTTP/REST** and **gRPC** are request-response at the transport layer.
- **RabbitMQ RPC** (`reply_to` + `correlation_id` headers).
- **JSON-RPC**, **SOAP**, **GraphQL queries** — all request-reply shaped.
- **Service mesh** retries and circuit breakers wrap synchronous hops.

For long operations, combine with **async callback**, **polling**, or **webhooks** instead of holding the connection open.

## References

- [Request–response — Wikipedia](https://en.wikipedia.org/wiki/Request%E2%80%93response)
- [Remote procedure call — Wikipedia](https://en.wikipedia.org/wiki/Remote_procedure_call)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
