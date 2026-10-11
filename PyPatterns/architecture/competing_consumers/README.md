# Competing Consumers Pattern

## Intent

Enable **horizontal scaling** by running multiple consumer instances against **one shared queue**. Each message is processed by exactly one consumer — whichever worker is idle first claims the job.

This demo enqueues nine tasks; three consumers race to drain the queue.

## Class Diagram

```mermaid
classDiagram
    class Job {
        +job_id: int
        +task: str
    }
    class WorkQueue {
        -_queue: Queue
        -_assignments: list
        +enqueue(job)
        +run(jobs, consumers) list
        -_consumer(name)
    }
    WorkQueue o-- Job
    WorkQueue o-- Thread : N consumers
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Prod as Producer
    participant Q as Shared Queue
    participant C0 as consumer-0
    participant C1 as consumer-1
    participant C2 as consumer-2

    Prod->>Q: enqueue task-0..8
    par Competing
        C0->>Q: get task-0
        C1->>Q: get task-1
        C2->>Q: get task-2
    end
    C0->>C0: process
    C0->>Q: get task-3
```

## Flowchart

```mermaid
flowchart TD
    A[Messages enqueued] --> B[Shared queue]
    B --> C{Idle consumer?}
    C -->|consumer-0| D[Dequeue message]
    C -->|consumer-1| D
    C -->|consumer-2| D
    D --> E[Process exactly once]
    E --> B
    F[Add consumers] --> C
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/competing_consumers/demo.py
```

Expected output shows nine tasks distributed across three consumers (interleaved assignment lines).

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Scale throughput by adding workers | Messages not globally ordered across consumers |
| Built-in load balancing via queue | Poison messages can block one consumer |
| Simple deployment model | Duplicate processing if visibility timeout expires |

## Distributed Environments

Competing consumers power **worker fleets everywhere**:

- **Amazon SQS + auto-scaling groups**: CloudWatch queue depth triggers new EC2 instances.
- **Celery workers**: `--concurrency=N` processes pull from Redis/RabbitMQ.
- **Kubernetes HPA**: scale Deployments based on queue lag metrics.

Use FIFO queues only when strict ordering per partition is required; otherwise standard queues maximize parallelism.

## References

- [Competing Consumers — Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
