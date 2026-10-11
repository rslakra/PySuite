"""Binding properties — two model objects keep name/value in sync via binding."""

from __future__ import annotations

from typing import Callable


class ObservableProperty[T]:
    """Property that notifies listeners when its value changes."""

    def __init__(self, value: T) -> None:
        self._value = value
        self._listeners: list[Callable[[T], None]] = []
        self._blocked = False

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if new_value == self._value:
            return
        self._value = new_value
        if self._blocked:
            return
        self._blocked = True
        try:
            for listener in self._listeners:
                listener(new_value)
        finally:
            self._blocked = False

    def bind(self, other: ObservableProperty[T]) -> None:
        """Two-way binding: changes propagate in both directions."""

        def sync_from_self(value: T) -> None:
            other.value = value

        def sync_from_other(value: T) -> None:
            self.value = value

        self._listeners.append(sync_from_self)
        other._listeners.append(sync_from_other)


class UserModel:
    def __init__(self, name: str) -> None:
        self.name = ObservableProperty(name)


class ProfileModel:
    def __init__(self, display_name: str) -> None:
        self.display_name = ObservableProperty(display_name)


def main() -> None:
    user = UserModel("Ada")
    profile = ProfileModel("Ada Lovelace")
    user.name.bind(profile.display_name)

    print(f"Initial — user: {user.name.value}, profile: {profile.display_name.value}")

    user.name.value = "Augusta Ada"
    print(f"After user update — profile: {profile.display_name.value}")

    profile.display_name.value = "Ada L."
    print(f"After profile update — user: {user.name.value}")


if __name__ == "__main__":
    main()
