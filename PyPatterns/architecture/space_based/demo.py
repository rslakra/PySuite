"""Space-based architecture — processing units coordinate via a shared tuple space."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TupleSpace:
    """Shared in-memory space — producers write tuples, consumers read and take."""

    _space: dict[str, list[tuple[Any, ...]]] = field(default_factory=dict)

    def write(self, template: str, *values: Any) -> None:
        self._space.setdefault(template, []).append(values)
        print(f"[Space] write {template}{values}")

    def take(self, template: str) -> tuple[Any, ...] | None:
        queue = self._space.get(template)
        if queue:
            item = queue.pop(0)
            print(f"[Space] take {template}{item}")
            return item
        return None

    def read(self, template: str) -> tuple[Any, ...] | None:
        queue = self._space.get(template)
        if queue:
            item = queue[0]
            print(f"[Space] read {template}{item}")
            return item
        return None


@dataclass
class OrderProcessor:
    """Processing unit — picks work from shared space."""

    name: str
    space: TupleSpace

    def poll(self) -> None:
        job = self.space.take("order")
        if job:
            order_id, amount = job
            result = (order_id, amount * 1.08)
            self.space.write("receipt", *result)
            print(f"[{self.name}] processed {order_id} → total ${result[1]:.2f}")


@dataclass
class ReceiptAggregator:
    """Processing unit — reads completed receipts from shared space."""

    space: TupleSpace

    def summarize(self) -> None:
        receipts: list[tuple[Any, ...]] = []
        while True:
            item = self.space.take("receipt")
            if item is None:
                break
            receipts.append(item)
        total = sum(r[1] for r in receipts)
        print(f"[Aggregator] {len(receipts)} receipts, combined total ${total:.2f}")


def main() -> None:
    space = TupleSpace()
    processor_a = OrderProcessor("Unit-A", space)
    processor_b = OrderProcessor("Unit-B", space)
    aggregator = ReceiptAggregator(space)

    space.write("order", "SP-001", 50.0)
    space.write("order", "SP-002", 75.0)

    processor_a.poll()
    processor_b.poll()
    aggregator.summarize()
    print("Units scale independently — coordination happens through shared space")


if __name__ == "__main__":
    main()
