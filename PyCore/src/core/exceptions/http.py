from core.exceptions.base import BaseException


class HTTPException(BaseException):
    """Base class for HTTP-style API exceptions."""

    status_code: int = 0

    def __init__(
        self,
        message: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message or self.default_message(), cause=cause)

    @classmethod
    def default_message(cls) -> str:
        return f"HTTP {cls.status_code} error"
