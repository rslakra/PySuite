from pycrux.exceptions.client import ClientException


class ConflictException(ClientException):
    """409 Conflict — request contradicts current server state (e.g. duplicate unique data)."""

    status_code = 409

    @classmethod
    def default_message(cls) -> str:
        return (
            "Conflict: The request contradicts the current state of the server, "
            "most commonly triggered by duplicate unique data "
            "(e.g., registering an email that already exists)."
        )
