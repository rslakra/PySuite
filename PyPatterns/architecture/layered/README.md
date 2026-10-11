# Layered Architecture

## Intent

Organize an application into horizontal **tiers** with strict top-down dependencies: **presentation** (UI/API), **business** (domain logic), and **data** (persistence). Each layer exposes services to the layer above and calls services in the layer below — never skipping layers or calling upward.

This demo routes order requests from a presentation layer through business pricing rules to a data layer that simulates persistence.

## Class Diagram

```mermaid
classDiagram
    class PresentationLayer {
        -_business: BusinessLayer
        +place_order(sku, quantity)
    }
    class BusinessLayer {
        -_data: DataLayer
        +calculate_order(sku, quantity)
    }
    class DataLayer {
        -_catalog: dict
        +find_by_sku(sku) ProductRecord
        +save_order(sku, qty, total) str
    }
    class ProductRecord {
        +sku: str
        +name: str
        +price: float
    }
    PresentationLayer --> BusinessLayer
    BusinessLayer --> DataLayer
    DataLayer ..> ProductRecord
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant UI as PresentationLayer
    participant Biz as BusinessLayer
    participant DB as DataLayer

    UI->>Biz: calculate_order("SKU-001", 2)
    Biz->>DB: find_by_sku("SKU-001")
    DB-->>Biz: ProductRecord
    Biz->>Biz: apply discount rules
    Biz->>DB: save_order(sku, qty, total)
    DB-->>Biz: order_id
    Biz-->>UI: order_id, total
    UI-->>UI: format and display
```

## Flowchart

```mermaid
flowchart TD
    A[User action] --> B[Presentation layer]
    B --> C[Business layer]
    C --> D{Valid SKU and quantity?}
    D -->|No| E[Return error to UI]
    D -->|Yes| F[Data layer lookup]
    F --> G[Apply business rules]
    G --> H[Data layer persist]
    H --> I[Return result up the stack]
    I --> J[UI renders confirmation]
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/layered/demo.py
```

Expected output shows two orders flowing through presentation → business → data layers with a bulk discount applied.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Simple mental model familiar to most developers | Can degrade into a "big ball of mud" if layers leak |
| Clear separation of UI, logic, and persistence | Performance bottlenecks when every call traverses all tiers |
| Easy onboarding for CRUD-centric applications | Hard to split into independent deployable units later |

## Distributed Environments

Classic layered architecture often appears in **n-tier enterprise deployments**:

- **Presentation tier** runs as a web farm (React SPA + API gateway).
- **Business tier** hosts application servers (Java EE, .NET) behind load balancers.
- **Data tier** is a managed RDBMS cluster (PostgreSQL, SQL Server) with read replicas.

In cloud migrations, teams sometimes **extract the data layer first** (database-per-service) while keeping a monolithic business tier — a stepping stone toward microservices without rewriting every layer at once.

## References

- [Multitier architecture — Wikipedia](https://en.wikipedia.org/wiki/Multitier_architecture)
- [Layered architecture pattern — Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/layered)
