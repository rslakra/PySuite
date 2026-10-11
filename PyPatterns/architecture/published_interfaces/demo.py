"""Published interfaces — stable public contract over evolving internal APIs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InternalCustomer:
    """Internal model — fields change freely between releases."""

    id: int
    given_name: str
    family_name: str
    email_address: str
    loyalty_tier: str


@dataclass(frozen=True)
class PublishedCustomerV1:
    """Published contract — semver-guaranteed for external integrators."""

    customer_id: str
    full_name: str
    contact_email: str


class CustomerServiceInternal:
    """Team-owned service with breaking changes allowed."""

    def fetch(self, customer_id: int) -> InternalCustomer:
        return InternalCustomer(
            id=customer_id,
            given_name="Ada",
            family_name="Lovelace",
            email_address="ada@example.com",
            loyalty_tier="gold",
        )


class PublishedCustomerAPI:
    """Facade exposing only the published surface; maps internal → public."""

    version = "1.0"

    def __init__(self, internal: CustomerServiceInternal) -> None:
        self._internal = internal

    def get_customer(self, customer_id: str) -> PublishedCustomerV1:
        record = self._internal.fetch(int(customer_id))
        return PublishedCustomerV1(
            customer_id=str(record.id),
            full_name=f"{record.given_name} {record.family_name}",
            contact_email=record.email_address,
        )


def main() -> None:
    api = PublishedCustomerAPI(CustomerServiceInternal())
    published = api.get_customer("42")

    print(f"Published API v{api.version}: {published}")
    print("Internal loyalty_tier is hidden — integrators see only the published schema")
    print("Internal renames (email → email_address) do not break external clients")


if __name__ == "__main__":
    main()
