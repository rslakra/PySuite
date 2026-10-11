"""Batch request — combine many lookups into one round trip."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserRecord:
    user_id: int
    name: str


class UserStore:
    """Simulated datastore — single fetch is cheap, many round trips are not."""

    _DATA = {
        1: "Alice",
        2: "Bob",
        3: "Carol",
        4: "Dan",
        5: "Eve",
    }

    def get_one(self, user_id: int) -> UserRecord:
        return UserRecord(user_id, self._DATA[user_id])

    def get_many(self, user_ids: list[int]) -> list[UserRecord]:
        return [UserRecord(uid, self._DATA[uid]) for uid in user_ids]


class NaiveClient:
    def __init__(self, store: UserStore) -> None:
        self._store = store
        self.round_trips = 0

    def fetch_names(self, user_ids: list[int]) -> list[str]:
        names: list[str] = []
        for uid in user_ids:
            self.round_trips += 1
            names.append(self._store.get_one(uid).name)
        return names


class BatchClient:
    def __init__(self, store: UserStore) -> None:
        self._store = store
        self.round_trips = 0

    def fetch_names(self, user_ids: list[int]) -> list[str]:
        self.round_trips += 1
        return [record.name for record in self._store.get_many(user_ids)]


def main() -> None:
    store = UserStore()
    ids = [1, 2, 3, 4, 5]

    naive = NaiveClient(store)
    batch = BatchClient(store)

    naive_names = naive.fetch_names(ids)
    batch_names = batch.fetch_names(ids)

    print(f"Naive: {naive.round_trips} round trips → {naive_names}")
    print(f"Batch: {batch.round_trips} round trip  → {batch_names}")
    print("Same result, fewer network hops — critical for N+1 query problems")


if __name__ == "__main__":
    main()
