from pycrux.exceptions.client import ClientException


class ForbiddenException(ClientException):
    """403 Forbidden — authenticated but lacking permissions or scopes."""

    status_code = 403

    @classmethod
    def default_message(cls) -> str:
        return (
            "Forbidden: The client is authenticated but does not have the necessary "
            "permissions or scopes to access the specific resource."
        )
