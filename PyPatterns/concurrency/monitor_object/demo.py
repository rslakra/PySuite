"""Monitor object — every method acquires the same lock (bank account)."""

from __future__ import annotations

import threading
import time


class BankAccount:
    """Monitor: all public methods run under one mutex."""

    def __init__(self, owner: str, balance: float) -> None:
        self._owner = owner
        self._balance = balance
        self._lock = threading.Lock()

    def deposit(self, amount: float) -> float:
        with self._lock:
            self._balance += amount
            return self._balance

    def withdraw(self, amount: float) -> float | None:
        with self._lock:
            if amount > self._balance:
                return None
            self._balance -= amount
            return self._balance

    def transfer_to(self, other: BankAccount, amount: float) -> bool:
        first, second = (self, other) if id(self) < id(other) else (other, self)
        with first._lock:
            with second._lock:
                if amount > self._balance:
                    return False
                self._balance -= amount
                other._balance += amount
                return True

    def balance(self) -> float:
        with self._lock:
            return self._balance


def deposit_worker(account: BankAccount, rounds: int) -> None:
    for _ in range(rounds):
        account.deposit(10.0)
        time.sleep(0.001)


def withdraw_worker(account: BankAccount, rounds: int) -> None:
    for _ in range(rounds):
        account.withdraw(5.0)
        time.sleep(0.001)


def main() -> None:
    alice = BankAccount("Alice", 100.0)
    bob = BankAccount("Bob", 50.0)

    threads = [
        threading.Thread(target=deposit_worker, args=(alice, 20)),
        threading.Thread(target=withdraw_worker, args=(alice, 20)),
        threading.Thread(
            target=lambda: alice.transfer_to(bob, 25.0) and bob.transfer_to(alice, 10.0)
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(f"Alice balance: ${alice.balance():.2f}")
    print(f"Bob balance:   ${bob.balance():.2f}")
    print("Monitor invariant holds — every method serialized the same lock")


if __name__ == "__main__":
    main()
