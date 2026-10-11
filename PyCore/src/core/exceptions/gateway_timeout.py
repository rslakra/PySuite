from core.exceptions.server import ServerException


class GatewayTimeoutException(ServerException):
    """504 Gateway Timeout — gateway timed out waiting for upstream."""

    status_code = 504

    @classmethod
    def default_message(cls) -> str:
        return (
            "Gateway Timeout: The proxy or gateway server timed out waiting for the "
            "upstream application server to process and return data."
        )
