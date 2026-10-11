"""Builder — assemble a complex HTTP request step by step."""

from dataclasses import dataclass, field


@dataclass
class HttpRequest:
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    def __str__(self) -> str:
        header_lines = "\n".join(f"  {k}: {v}" for k, v in self.headers.items())
        return f"{self.method} {self.url}\n{header_lines}\n\n{self.body or '(empty)'}"


class HttpRequestBuilder:
    def __init__(self) -> None:
        self._request = HttpRequest()

    def method(self, verb: str) -> "HttpRequestBuilder":
        self._request.method = verb.upper()
        return self

    def url(self, url: str) -> "HttpRequestBuilder":
        self._request.url = url
        return self

    def header(self, key: str, value: str) -> "HttpRequestBuilder":
        self._request.headers[key] = value
        return self

    def json_body(self, payload: str) -> "HttpRequestBuilder":
        self._request.body = payload
        self._request.headers.setdefault("Content-Type", "application/json")
        return self

    def build(self) -> HttpRequest:
        if not self._request.url:
            raise ValueError("URL is required")
        return self._request


def main() -> None:
    get_req = (
        HttpRequestBuilder()
        .method("GET")
        .url("https://api.example.com/users")
        .header("Accept", "application/json")
        .build()
    )

    post_req = (
        HttpRequestBuilder()
        .method("POST")
        .url("https://api.example.com/users")
        .header("Authorization", "Bearer token")
        .json_body('{"name": "Ada"}')
        .build()
    )

    print("GET request:\n", get_req, sep="")
    print("\nPOST request:\n", post_req, sep="")


if __name__ == "__main__":
    main()
