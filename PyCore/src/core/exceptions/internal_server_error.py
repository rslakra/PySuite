from core.exceptions.server import ServerException


class InternalServerException(ServerException):
    """500 Internal Server Error — unhandled exception in backend code."""

    status_code = 500

    @classmethod
    def default_message(cls) -> str:
        return (
            "Internal Server Error: A generic catch-all error indicating an unhandled "
            "exception occurred in the backend code (e.g., a null-pointer error or a code crash)."
        )
