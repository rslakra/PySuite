from pycrux.exceptions.client import ClientException


class MethodNotAllowedException(ClientException):
    """405 Method Not Allowed — HTTP verb is not supported for this endpoint."""

    status_code = 405

    @classmethod
    def default_message(cls) -> str:
        return (
            "Method Not Allowed: The endpoint exists, but the HTTP verb used "
            "(e.g., POST instead of GET) is not supported by that route."
        )
