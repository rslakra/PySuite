"""Mediator — chat room coordinates user messaging."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Mediator(ABC):
    @abstractmethod
    def send(self, message: str, sender: User) -> None:
        ...


class ChatRoom(Mediator):
    def __init__(self) -> None:
        self._users: list[User] = []

    def register(self, user: User) -> None:
        self._users.append(user)

    def send(self, message: str, sender: User) -> None:
        for user in self._users:
            if user is not sender:
                user.receive(message, sender.name)


class User:
    def __init__(self, name: str, chat_room: ChatRoom) -> None:
        self.name = name
        self._chat_room = chat_room
        chat_room.register(self)

    def send(self, message: str) -> None:
        print(f"{self.name} sends: {message}")
        self._chat_room.send(message, self)

    def receive(self, message: str, sender: str) -> None:
        print(f"{self.name} received from {sender}: {message}")


def main() -> None:
    room = ChatRoom()
    alice = User("Alice", room)
    bob = User("Bob", room)
    carol = User("Carol", room)

    alice.send("Hello everyone!")
    bob.send("Hi Alice!")


if __name__ == "__main__":
    main()
