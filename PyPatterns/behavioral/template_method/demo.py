"""Template Method — data mining pipeline with format-specific subclasses."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class DataMiner(ABC):
    def mine(self, path: Path) -> dict[str, int]:
        raw = self._read_file(path)
        records = self._parse(raw)
        return self._analyze(records)

    @abstractmethod
    def _read_file(self, path: Path) -> str:
        ...

    @abstractmethod
    def _parse(self, raw: str) -> list[dict[str, str]]:
        ...

    def _analyze(self, records: list[dict[str, str]]) -> dict[str, int]:
        return {"record_count": len(records)}


class JsonDataMiner(DataMiner):
    def _read_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _parse(self, raw: str) -> list[dict[str, str]]:
        import json

        data = json.loads(raw)
        return data if isinstance(data, list) else [data]


class CsvDataMiner(DataMiner):
    def _read_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _parse(self, raw: str) -> list[dict[str, str]]:
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(raw))
        return list(reader)


def main() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        json_path = base / "data.json"
        csv_path = base / "data.csv"

        json_path.write_text(
            '[{"name": "Alice"}, {"name": "Bob"}]',
            encoding="utf-8",
        )
        csv_path.write_text("name\nAlice\nBob\n", encoding="utf-8")

        json_miner = JsonDataMiner()
        csv_miner = CsvDataMiner()

        print(f"JSON result: {json_miner.mine(json_path)}")
        print(f"CSV result: {csv_miner.mine(csv_path)}")


if __name__ == "__main__":
    main()
