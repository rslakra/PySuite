"""Client–server — request/response over a simple TCP connection."""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    path: str


@dataclass(frozen=True)
class Response:
    status: int
    body: str


class EchoServer:
    """Single-threaded server: one request in, one response out."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self._host = host
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, port))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]

    def serve_once(self) -> Response:
        conn, _addr = self._sock.accept()
        with conn:
            data = conn.recv(1024).decode()
            body = f"echo:{data}"
            conn.sendall(body.encode())
            return Response(status=200, body=body)

    def close(self) -> None:
        self._sock.close()


class HttpLikeClient:
    """Client opens connection, sends request, waits for response."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

    def get(self, path: str) -> Response:
        with socket.create_connection((self._host, self._port), timeout=1.0) as conn:
            conn.sendall(path.encode())
            body = conn.recv(1024).decode()
            return Response(status=200, body=body)


def main() -> None:
    server = EchoServer()
    client = HttpLikeClient("127.0.0.1", server.port)

    worker = threading.Thread(target=server.serve_once, daemon=True)
    worker.start()

    response = client.get("/hello")
    print(f"Client sent: /hello")
    print(f"Server responded: {response.body}")
    print("Classic client–server: client initiates, server processes, connection closes")

    worker.join(timeout=1.0)
    server.close()


if __name__ == "__main__":
    main()
