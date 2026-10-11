from pycrux.exceptions.client import ClientException


class UnauthorizedException(ClientException):
    """401 Unauthorized — missing, expired, or invalid authentication credentials."""

    status_code = 401

    @classmethod
    def default_message(cls) -> str:
        return (
            "Unauthorized: The client has not provided valid authentication credentials "
            "(e.g., missing, expired, or invalid API tokens)."
        )
