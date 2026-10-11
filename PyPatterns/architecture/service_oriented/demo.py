"""Service-oriented architecture — discoverable services via a central registry."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ServiceDescriptor:
    name: str
    endpoint: str
    version: str


class ServiceRegistry:
    """Enterprise service bus directory — services register and lookup by name."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceDescriptor] = {}

    def register(self, descriptor: ServiceDescriptor) -> None:
        self._services[descriptor.name] = descriptor
        print(f"[Registry] registered {descriptor.name} @ {descriptor.endpoint}")

    def lookup(self, name: str) -> ServiceDescriptor:
        svc = self._services.get(name)
        if svc is None:
            raise LookupError(f"service not found: {name}")
        return svc


@dataclass
class CustomerService:
    registry: ServiceRegistry
    endpoint: str = "soa://customer/v1"

    def register(self) -> None:
        self.registry.register(ServiceDescriptor("CustomerService", self.endpoint, "1.0"))

    def get_profile(self, customer_id: str) -> dict:
        return {"id": customer_id, "name": "Alice", "tier": "gold"}


@dataclass
class OrderService:
    registry: ServiceRegistry
    customer: CustomerService
    endpoint: str = "soa://orders/v1"

    def register(self) -> None:
        self.registry.register(ServiceDescriptor("OrderService", self.endpoint, "1.0"))

    def create(self, customer_id: str) -> str:
        desc = self.registry.lookup("CustomerService")
        profile = self.customer.get_profile(customer_id)
        order_id = f"SOA-{customer_id}"
        print(f"[OrderService] via {desc.endpoint} → order for {profile['name']}")
        return order_id


def main() -> None:
    registry = ServiceRegistry()
    customers = CustomerService(registry)
    orders = OrderService(registry, customers)

    customers.register()
    orders.register()
    orders.create("C-100")
    print("Services are loosely coupled through registry-based discovery")


if __name__ == "__main__":
    main()
