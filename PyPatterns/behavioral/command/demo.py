"""Command — light switch with undo stack."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Light:
    def __init__(self) -> None:
        self._on = False

    def turn_on(self) -> None:
        self._on = True

    def turn_off(self) -> None:
        self._on = False

    @property
    def is_on(self) -> bool:
        return self._on


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


class TurnOnCommand(Command):
    def __init__(self, light: Light) -> None:
        self._light = light

    def execute(self) -> None:
        self._light.turn_on()

    def undo(self) -> None:
        self._light.turn_off()


class TurnOffCommand(Command):
    def __init__(self, light: Light) -> None:
        self._light = light

    def execute(self) -> None:
        self._light.turn_off()

    def undo(self) -> None:
        self._light.turn_on()


class RemoteControl:
    def __init__(self) -> None:
        self._history: list[Command] = []

    def submit(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> None:
        if not self._history:
            print("Nothing to undo")
            return
        self._history.pop().undo()


def main() -> None:
    light = Light()
    remote = RemoteControl()

    remote.submit(TurnOnCommand(light))
    print(f"Light on: {light.is_on}")

    remote.submit(TurnOffCommand(light))
    print(f"Light on: {light.is_on}")

    remote.undo_last()
    print(f"After undo, light on: {light.is_on}")


if __name__ == "__main__":
    main()
