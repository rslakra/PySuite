from enum import Enum


class RunState(str, Enum):
    """All possible states that a run (job, task or process) can be in."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    FAILED = "failed"
