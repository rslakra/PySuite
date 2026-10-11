# Service-Oriented Architecture (SOA)

## Intent

Structure an enterprise as a set of **coarse-grained, discoverable services** that communicate through an **enterprise service bus (ESB)** or **service registry**. SOA emphasizes reusable business capabilities, standardized contracts, and centralized governance — a precursor to microservices with larger service boundaries.

This demo registers Customer and Order services in a `ServiceRegistry`, then creates an order by discovering and calling the customer service at runtime.

## Class Diagram

```mermaid
classDiagram
    class ServiceRegistry {
        -_services: dict
        +register(descriptor)
        +lookup(name) ServiceDescriptor
    }
    class ServiceDescriptor {
        +name: str
        +endpoint: str
        +version: str
    }
    class CustomerService {
        -registry: ServiceRegistry
        +register()
        +get_profile(customer_id) dict
    }
    class OrderService {
        -registry: ServiceRegistry
        -customer: CustomerService
        +register()
        +create(customer_id) str
    }
    CustomerService --> ServiceRegistry
    OrderService --> ServiceRegistry
    OrderService --> CustomerService : uses via registry
    ServiceRegistry ..> ServiceDescriptor
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Order as OrderService
    participant Reg as ServiceRegistry
    participant Cust as CustomerService

    Order->>Reg: lookup("CustomerService")
    Reg-->>Order: ServiceDescriptor
    Order->>Cust: get_profile("C-100")
    Cust-->>Order: profile
    Order->>Order: create order
    Order-->>Order: order_id
```

## Flowchart

```mermaid
flowchart TD
    A[Service startup] --> B[Register with ServiceRegistry]
    B --> C[Client needs capability]
    C --> D[Lookup service by name]
    D --> E{Service found?}
    E -->|Yes| F[Invoke via endpoint]
    F --> G[Return result]
    E -->|No| H[Service unavailable error]
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/service_oriented/demo.py
```

Expected output shows services registering themselves and an order created via registry-based discovery.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Promotes reusable enterprise business services | ESB can become a bottleneck and single point of failure |
| Centralized governance, contracts, and security policies | Heavyweight XML/SOAP stacks add complexity and latency |
| Services are discoverable and loosely coupled | Large services can still be monoliths in disguise |

## Distributed Environments

SOA shaped enterprise integration before microservices dominated:

- **Enterprise Service Buses** (MuleSoft, IBM Integration Bus) route, transform, and orchestrate SOAP/REST messages between services.
- **UDDI/WSDL registries** (largely superseded) provided formal service discovery; today **Consul**, **Eureka**, and **Kubernetes DNS** fill a similar role.
- **BPM engines** orchestrate long-running business processes across SOA services.

A bank's SOA layer exposes Customer, Account, and Payment as governed services behind an API gateway — each with SLA-backed contracts, centralized authentication, and audit logging enforced by the bus rather than individual teams.

## References

- [Service-oriented architecture — Wikipedia](https://en.wikipedia.org/wiki/Service-oriented_architecture)
- [SOA design pattern — Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/soa)
