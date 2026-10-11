"""State — vending machine with distinct operational states."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VendingMachineState(ABC):
    def __init__(self, machine: VendingMachine) -> None:
        self._machine = machine

    @abstractmethod
    def insert_coin(self) -> None:
        ...

    @abstractmethod
    def dispense(self) -> None:
        ...


class IdleState(VendingMachineState):
    def insert_coin(self) -> None:
        print("Coin inserted")
        self._machine.state = HasCoinState(self._machine)

    def dispense(self) -> None:
        print("Insert a coin first")


class HasCoinState(VendingMachineState):
    def insert_coin(self) -> None:
        print("Coin already inserted")

    def dispense(self) -> None:
        print("Dispensing item")
        self._machine.state = IdleState(self._machine)


class VendingMachine:
    def __init__(self) -> None:
        self.state: VendingMachineState = IdleState(self)

    def insert_coin(self) -> None:
        self.state.insert_coin()

    def dispense(self) -> None:
        self.state.dispense()


def main() -> None:
    machine = VendingMachine()
    machine.dispense()
    machine.insert_coin()
    machine.dispense()


if __name__ == "__main__":
    main()
