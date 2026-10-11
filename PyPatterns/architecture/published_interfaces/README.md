# Published Interface Pattern

## Intent

Expose a **stable, versioned public API** while allowing internal services to evolve freely. External integrators depend only on the published contract; internal field renames and schema changes are mapped at the boundary.

This demo hides internal `loyalty_tier` and maps `given_name`/`family_name` to a semver-guaranteed `PublishedCustomerV1`.

## Class Diagram

```mermaid
classDiagram
    class InternalCustomer {
        +id: int
        +given_name: str
        +family_name: str
        +email_address: str
        +loyalty_tier: str
    }
    class PublishedCustomerV1 {
        +customer_id: str
        +full_name: str
        +contact_email: str
    }
    class CustomerServiceInternal {
        +fetch(id) InternalCustomer
    }
    class PublishedCustomerAPI {
        +version: str
        +get_customer(id) PublishedCustomerV1
    }
    PublishedCustomerAPI --> CustomerServiceInternal
    PublishedCustomerAPI ..> PublishedCustomerV1 : exposes
    CustomerServiceInternal ..> InternalCustomer
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Partner as External Integrator
    participant Pub as PublishedCustomerAPI
    participant Int as CustomerServiceInternal

    Partner->>Pub: GET /v1/customers/42
    Pub->>Int: fetch(42)
    Int-->>Pub: InternalCustomer
    Pub->>Pub: map to PublishedCustomerV1
    Pub-->>Partner: stable JSON schema
```

## Flowchart

```mermaid
flowchart TD
    A[External request] --> B[Published API layer]
    B --> C[Validate against public schema]
    C --> D[Call internal service]
    D --> E[Internal model may differ]
    E --> F[Map to published DTO]
    F --> G[Return versioned response]
    H[Internal refactor] --> D
    H -.->|does not break| G
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/published_interfaces/demo.py
```

Expected output shows `PublishedCustomerV1` with `full_name` and `contact_email`, with internal-only fields omitted.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Internal agility without breaking partners | Mapping layer to build and test |
| Clear semver contract for integrators | Multiple published versions may coexist |
| Hides implementation details | Published surface can lag new features |

## Distributed Environments

Published interfaces define **integration boundaries**:

- **OpenAPI / AsyncAPI specs** checked into a registry; breaking changes require major version bumps.
- **API gateways** enforce published routes while routing to internal microservices.
- **Consumer-driven contracts** (Pact): partners test against the published schema, not internal stubs.

Document deprecation timelines; never remove a published field without a migration path.

## References

- [Published Language — Domain-Driven Design](https://www.domainlanguage.com/ddd/reference/)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
