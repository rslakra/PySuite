from pycrux.exceptions.client import ClientException


class UnsupportedMediaTypeException(ClientException):
    """415 Unsupported Media Type — Content-Type is not accepted."""

    status_code = 415

    @classmethod
    def default_message(cls) -> str:
        return (
            "Unsupported Media Type: The server refuses to accept the request format, "
            "typically because the Content-Type header (like application/xml) is not supported."
        )
