"""Rule-Based pattern — forward-chaining rules engine over facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


RuleAction = Callable[[dict[str, Any]], bool]


@dataclass
class RulesEngine:
    """Evaluate rules against a fact base; fired rules may mutate facts."""

    rules: list[tuple[str, RuleAction]] = field(default_factory=list)
    fired: list[str] = field(default_factory=list)

    def add(self, name: str, action: RuleAction) -> None:
        self.rules.append((name, action))

    def run(self, facts: dict[str, Any], max_cycles: int = 10) -> dict[str, Any]:
        for _ in range(max_cycles):
            changed = False
            for name, action in self.rules:
                if name in self.fired:
                    continue
                if action(facts):
                    self.fired.append(name)
                    changed = True
                    print(f"  fired: {name}")
            if not changed:
                break
        return facts


def main() -> None:
    facts: dict[str, Any] = {"cart_total": 120.0, "member": True, "discount": 0.0}

    engine = RulesEngine()

    def free_shipping(f: dict[str, Any]) -> bool:
        if f["cart_total"] >= 100 and not f.get("free_shipping"):
            f["free_shipping"] = True
            return True
        return False

    def member_discount(f: dict[str, Any]) -> bool:
        if f["member"] and f["discount"] == 0.0:
            f["discount"] = 0.10
            return True
        return False

    engine.add("free-shipping", free_shipping)
    engine.add("member-discount", member_discount)

    result = engine.run(facts)
    print(
        f"Final facts: total={result['cart_total']}, discount={result['discount']}, "
        f"free_shipping={result.get('free_shipping')}"
    )
    print("Business policies live as declarative rules — not scattered if/else chains")


if __name__ == "__main__":
    main()
