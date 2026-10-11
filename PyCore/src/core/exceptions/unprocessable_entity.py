from core.exceptions.client import ClientException


class UnprocessableEntityException(ClientException):
    """422 Unprocessable Entity — valid structure but failed business/semantic validation."""

    status_code = 422

    @classmethod
    def default_message(cls) -> str:
        return (
            "Unprocessable Entity: The request structure is completely valid, but the "
            "internal data fails business logic or semantic validation rules."
        )
