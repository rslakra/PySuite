"""Blackboard — knowledge sources collaborate on a shared problem space."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Blackboard:
    """Shared workspace: hypothesis, evidence, and solution slots."""

    hypothesis: str = ""
    evidence: list[str] = field(default_factory=list)
    solution: str | None = None

    def add_evidence(self, fact: str) -> None:
        self.evidence.append(fact)


class HypothesisSource:
    """Proposes an initial guess from partial input."""

    def contribute(self, board: Blackboard, symptoms: list[str]) -> None:
        if "fever" in symptoms and "cough" in symptoms:
            board.hypothesis = "viral respiratory infection"
        else:
            board.hypothesis = "unknown — gather more data"


class LabSource:
    """Adds test results when hypothesis exists."""

    def contribute(self, board: Blackboard) -> None:
        if not board.hypothesis:
            return
        board.add_evidence("PCR: influenza A positive")


class DiagnosisSource:
    """Writes final solution when evidence supports hypothesis."""

    def contribute(self, board: Blackboard) -> None:
        if board.hypothesis and any("influenza" in e for e in board.evidence):
            board.solution = "Treat with rest, fluids; consider antivirals within 48h"


class BlackboardController:
    """Orchestrates sources until the blackboard holds a solution."""

    def __init__(self, sources: list[object]) -> None:
        self._sources = sources

    def solve(self, board: Blackboard, symptoms: list[str]) -> str | None:
        for source in self._sources:
            if hasattr(source, "contribute"):
                if isinstance(source, HypothesisSource):
                    source.contribute(board, symptoms)
                else:
                    source.contribute(board)
            if board.solution:
                break
        return board.solution


def main() -> None:
    board = Blackboard()
    controller = BlackboardController(
        [HypothesisSource(), LabSource(), DiagnosisSource()]
    )

    symptoms = ["fever", "cough", "fatigue"]
    print(f"Symptoms: {symptoms}")
    solution = controller.solve(board, symptoms)

    print(f"Hypothesis: {board.hypothesis}")
    print(f"Evidence:   {board.evidence}")
    print(f"Solution:   {solution}")
    print("Sources read/write the blackboard independently — no direct coupling")


if __name__ == "__main__":
    main()
