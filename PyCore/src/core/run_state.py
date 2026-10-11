from enum import Enum


class RunState(str, Enum):
    """
    All possible states that a DagRun can be in.

    These are "shared" with TaskInstanceState in some parts of the code,
    so please ensure that their values always match the ones with the
    same name in TaskInstanceState.
    """

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    FAILED = "failed"

    # def __str__(self) -> str:
    #     return self.value


run_state = RunState.IDLE
print(run_state)
print(run_state.value)
print(run_state.name)

running_states = RunState.__members__.keys()
print(running_states)
