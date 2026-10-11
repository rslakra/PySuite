"""Claim Check pattern — store large payload, pass reference in message."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClaimCheckStore:
    """External store for bulky payloads; messages carry only claim IDs."""

    _vault: dict[str, Any] = field(default_factory=dict)

    def store(self, payload: Any) -> str:
        claim_id = str(uuid.uuid4())
        self._vault[claim_id] = payload
        return claim_id

    def retrieve(self, claim_id: str) -> Any:
        return self._vault[claim_id]


@dataclass
class Message:
    """Lightweight envelope carrying a claim check instead of the payload."""

    topic: str
    claim_id: str


def main() -> None:
    store = ClaimCheckStore()
    large_order = {
        "customer": "acme-corp",
        "lines": [{"sku": f"ITEM-{i}", "qty": i * 10} for i in range(1, 6)],
        "notes": "x" * 200,
    }

    claim_id = store.store(large_order)
    message = Message(topic="orders.created", claim_id=claim_id)

    print(f"Message on bus: {message}  (payload stays in store)")
    restored = store.retrieve(message.claim_id)
    print(f"Consumer fetched {len(restored['lines'])} line items for {restored['customer']}")
    print("Bus traffic stays small — only the claim ID travels between services")


if __name__ == "__main__":
    main()
