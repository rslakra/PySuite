from pycrux.exceptions.server import ServerException


class BadGatewayException(ServerException):
    """502 Bad Gateway — gateway received an invalid response from upstream."""

    status_code = 502

    @classmethod
    def default_message(cls) -> str:
        return (
            "Bad Gateway: The API gateway or proxy server received an invalid response "
            "from the upstream backend service."
        )
