# Batch Request Pattern

## Intent

**Combine multiple operations into a single request** to reduce network round trips and database queries. Especially valuable when a page needs N related records — batching avoids the N+1 problem.

This demo fetches five user names: naive mode uses five round trips; batch mode uses one.

## Class Diagram

```mermaid
classDiagram
    class UserRecord {
        +user_id: int
        +name: str
    }
    class UserStore {
        +get_one(user_id) UserRecord
        +get_many(user_ids) list
    }
    class NaiveClient {
        +round_trips: int
        +fetch_names(ids) list
    }
    class BatchClient {
        +round_trips: int
        +fetch_names(ids) list
    }
    NaiveClient --> UserStore
    BatchClient --> UserStore
    UserStore ..> UserRecord
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant App
    participant Store as UserStore

    Note over App,Store: Naive — 5 round trips
    loop Each user_id
        App->>Store: get_one(id)
        Store-->>App: UserRecord
    end

    Note over App,Store: Batch — 1 round trip
    App->>Store: get_many([1..5])
    Store-->>App: 5 UserRecords
```

## Flowchart

```mermaid
flowchart TD
    A[Need N related records] --> B{Batch API available?}
    B -->|No| C[N sequential requests]
    B -->|Yes| D[Collect IDs]
    D --> E[Single batch request]
    E --> F[Split results client-side]
    C --> G[High latency / load]
    F --> H[One round trip]
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/batch_request/demo.py
```

Expected output compares 5 round trips (naive) vs 1 round trip (batch) with identical name lists.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Dramatically fewer network hops | Batch endpoints more complex to design |
| Lower DB connection pressure | Large batches can timeout or hit payload limits |
| Better cache efficiency | Partial failures need explicit handling |

## Distributed Environments

Batching is essential at **service and data layers**:

- **GraphQL DataLoader**: coalesces per-key fetches into one query per tick.
- **gRPC batch RPCs** and **Facebook Graph API** `?ids=1,2,3` style endpoints.
- **SQL `WHERE id IN (...)`** instead of N point lookups.

Cap batch size, paginate mega-batches, and return per-item errors so one bad ID does not fail the entire request.

## References

- [Batch Request — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/batch-request)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
