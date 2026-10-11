# Thread Pool Pattern

## Intent

Reuse a fixed set of worker threads to process many tasks from a shared queue. Avoids the cost of spawning a thread per request while still parallelizing CPU-bound or blocking work.

This demo runs eight tasks through a pool of three workers that pull from a central task queue until shutdown.

## Class Diagram

```mermaid
classDiagram
    class Task {
        +task_id: int
        +payload: str
    }
    class ThreadPool {
        -_tasks: Queue
        -_workers: list~Thread~
        +start()
        +submit(task: Task)
        +shutdown(wait: bool)
        -_worker()
    }
    ThreadPool ..> Task : processes
    ThreadPool o-- Thread : fixed pool
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Pool as ThreadPool
    participant Q as Task Queue
    participant W1 as worker-0
    participant W2 as worker-1

    Client->>Pool: start()
    Client->>Pool: submit(tasks)
    W1->>Q: get task
    W2->>Q: get task
    W1->>W1: process
    W2->>W2: process
    W1->>Q: get next task
    Client->>Pool: shutdown()
    Pool->>Q: poison pills
    W1-->>Pool: exit
    W2-->>Pool: exit
```

## Flowchart

```mermaid
flowchart TD
    A[Create N worker threads] --> B[Workers wait on task queue]
    C[Client submits task] --> D[Task enqueued]
    D --> B
    B --> E[Idle worker dequeues task]
    E --> F[Worker executes task]
    F --> B
    G[shutdown] --> H[Send None sentinel per worker]
    H --> I[Workers exit]
```

## Run Instructions

```bash
cd PyPatterns
python3 concurrency/thread_pool/demo.py
```

Expected output interleaves task processing across `worker-0`, `worker-1`, and `worker-2`.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Amortizes thread creation cost | Pool size must be tuned to workload |
| Bounds concurrent threads | Queue can grow unbounded if producers outpace workers |
| Natural backpressure hook via queue size limits | Shared queue can become a contention point |

## Distributed Environments

Thread pools have direct analogues in distributed job processing:

- **Celery / RQ workers** — fixed consumer processes pulling from Redis or RabbitMQ.
- **Kubernetes Deployments** — replica count defines parallel pod workers.
- **SQS / Pub/Sub consumers** — long-polling workers with configurable concurrency.

Compare with [service_handler](../service_handler/README.md): pools trade isolation per task for predictable resource ceilings — the standard choice for web servers (Tomcat, gunicorn sync workers) and batch pipelines.

## References

- [Thread pool — Wikipedia](https://en.wikipedia.org/wiki/Thread_pool)
- [concurrent.futures.ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)
- [Python threading](https://docs.python.org/3/library/threading.html)
