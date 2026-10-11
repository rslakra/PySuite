"""Tests for ``pycrux.enums.run_state.RunState``."""

import importlib

import pytest

import pycrux.enums.run_state as run_state_module
from pycrux.enums import RunState


def test_members_and_values() -> None:
    assert [(m.name, m.value) for m in RunState] == [
        ("IDLE", "idle"),
        ("QUEUED", "queued"),
        ("RUNNING", "running"),
        ("PAUSED", "paused"),
        ("SKIPPED", "skipped"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
    ]


def test_lookup_by_value() -> None:
    assert RunState("running") is RunState.RUNNING
    with pytest.raises(ValueError):
        RunState("exploded")


def test_is_a_str_enum() -> None:
    assert RunState.IDLE == "idle"
    assert isinstance(RunState.FAILED, str)
    assert RunState.COMPLETED.value.upper() == "COMPLETED"


def test_importing_has_no_side_effects(capsys) -> None:
    importlib.reload(run_state_module)
    assert capsys.readouterr().out == ""
