"""Pipes and filters — data flows through a chain of processing stages."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Filter(ABC):
    """Single processing stage in the pipeline."""

    @abstractmethod
    def process(self, data: str) -> str:
        ...


class TrimFilter(Filter):
    def process(self, data: str) -> str:
        return data.strip()


class LowercaseFilter(Filter):
    def process(self, data: str) -> str:
        return data.lower()


class RemovePunctuationFilter(Filter):
    def process(self, data: str) -> str:
        return "".join(ch for ch in data if ch.isalnum() or ch.isspace())


class TokenizeFilter(Filter):
    def process(self, data: str) -> str:
        return " | ".join(data.split())


class Pipeline:
    """Connects filters with pipes — output of one feeds the next."""

    def __init__(self, *filters: Filter) -> None:
        self._filters = filters

    def run(self, data: str) -> str:
        current = data
        for stage, filt in enumerate(self._filters, start=1):
            current = filt.process(current)
            print(f"[Stage {stage}: {filt.__class__.__name__}] → {current!r}")
        return current


def main() -> None:
    pipeline = Pipeline(
        TrimFilter(),
        LowercaseFilter(),
        RemovePunctuationFilter(),
        TokenizeFilter(),
    )
    raw = "  Hello, Pipes & Filters!  "
    print(f"Input: {raw!r}")
    result = pipeline.run(raw)
    print(f"Output: {result}")


if __name__ == "__main__":
    main()
