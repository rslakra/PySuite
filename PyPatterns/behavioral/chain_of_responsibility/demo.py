"""Chain of Responsibility — support ticket escalation (Level 1/2/3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SupportTicket:
    id: int
    description: str
    severity: int  # 1 = low, 2 = medium, 3 = critical


class SupportHandler(ABC):
    def __init__(self, level: int, name: str) -> None:
        self.level = level
        self.name = name
        self._next: SupportHandler | None = None

    def set_next(self, handler: SupportHandler) -> SupportHandler:
        self._next = handler
        return handler

    def handle(self, ticket: SupportTicket) -> str:
        if ticket.severity <= self.level:
            return f"{self.name} resolved ticket #{ticket.id}: {ticket.description}"
        if self._next:
            return self._next.handle(ticket)
        return f"No handler available for ticket #{ticket.id}"


class Level1Support(SupportHandler):
    def __init__(self) -> None:
        super().__init__(level=1, name="Level1Support")


class Level2Support(SupportHandler):
    def __init__(self) -> None:
        super().__init__(level=2, name="Level2Support")


class Level3Support(SupportHandler):
    def __init__(self) -> None:
        super().__init__(level=3, name="Level3Support")


def build_chain() -> SupportHandler:
    level1 = Level1Support()
    level2 = Level2Support()
    level3 = Level3Support()
    level1.set_next(level2).set_next(level3)
    return level1


def main() -> None:
    chain = build_chain()
    tickets = [
        SupportTicket(101, "Password reset", 1),
        SupportTicket(102, "Billing discrepancy", 2),
        SupportTicket(103, "Production outage", 3),
    ]
    for ticket in tickets:
        print(chain.handle(ticket))


if __name__ == "__main__":
    main()
