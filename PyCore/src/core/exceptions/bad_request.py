from core.exceptions.client import ClientException


class BadRequestException(ClientException):
    """400 Bad Request — malformed payload, missing fields, or syntax violations."""

    status_code = 400

    @classmethod
    def default_message(cls) -> str:
        return (
            "Bad Request: The request payload is malformed, missing required fields, "
            "or violates syntax constraints (e.g., sending text to an integer field)."
        )
