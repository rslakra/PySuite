"""Peer-to-Peer pattern — nodes communicate without a central broker."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PeerNode:
    """A node that routes messages directly to known peers."""

    name: str
    _peers: dict[str, PeerNode] = field(default_factory=dict, repr=False)

    def connect(self, peer: PeerNode) -> None:
        self._peers[peer.name] = peer
        peer._peers[self.name] = self

    def send(self, recipient: str, payload: str) -> str:
        peer = self._peers.get(recipient)
        if peer is None:
            raise ValueError(f"{self.name} has no peer named {recipient!r}")
        return peer.receive(self.name, payload)

    def receive(self, sender: str, payload: str) -> str:
        return f"[{self.name}] from {sender}: {payload}"


def main() -> None:
    alice = PeerNode("alice")
    bob = PeerNode("bob")
    carol = PeerNode("carol")

    alice.connect(bob)
    bob.connect(carol)

    print(alice.send("bob", "sync inventory delta"))
    print(bob.send("carol", "replicate shard-7"))
    print("No central server — each node talks directly to its peers")


if __name__ == "__main__":
    main()
