from core.exceptions.client import ClientException


class NotFoundException(ClientException):
    """404 Not Found — resource URL, endpoint, or identifier does not exist."""

    status_code = 404

    @classmethod
    def default_message(cls) -> str:
        return (
            "Not Found: The requested resource URL, endpoint, or specific identifier "
            "(like a user ID) does not exist on the server."
        )
