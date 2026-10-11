"""Nuclear reaction — fission (one triggers many) and fusion (many trigger one)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class FissionStage:
    """One stage triggers the next wave of workers (chain reaction)."""

    name: str
    next_stage: FissionStage | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def trigger(self, depth: int = 0) -> None:
        print(f"  {'  ' * depth}[fission:{self.name}] triggered")
        if self.next_stage and depth < 2:
            for i in range(2):
                threading.Thread(
                    target=self.next_stage.trigger, args=(depth + 1,), daemon=True
                ).start()


@dataclass
class FusionGate:
    """Waits for N signals before releasing one downstream action."""

    threshold: int
    _count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _done: threading.Event = field(default_factory=threading.Event, repr=False)

    def signal(self, worker: str) -> None:
        with self._lock:
            self._count += 1
            print(f"[fusion] {worker} signaled ({self._count}/{self.threshold})")
            if self._count >= self.threshold:
                self._done.set()

    def wait_and_run(self) -> None:
        self._done.wait()
        print("[fusion] threshold reached — single downstream action runs")


def main() -> None:
    print("=== Fission (one → many chain) ===")
    stage_c = FissionStage("C")
    stage_b = FissionStage("B", next_stage=stage_c)
    stage_a = FissionStage("A", next_stage=stage_b)
    stage_a.trigger()
    time.sleep(0.5)

    print("\n=== Fusion (many → one) ===")
    gate = FusionGate(threshold=3)
    threading.Thread(target=gate.wait_and_run, daemon=True).start()
    for name in ("worker-1", "worker-2", "worker-3"):
        threading.Thread(target=gate.signal, args=(name,), daemon=True).start()
    time.sleep(0.5)
    print("Done.")


if __name__ == "__main__":
    main()
