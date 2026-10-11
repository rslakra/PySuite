from core.exceptions.server import ServerException


class ServiceUnavailableException(ServerException):
    """503 Service Unavailable — server temporarily unable to handle the request."""

    status_code = 503

    @classmethod
    def default_message(cls) -> str:
        return (
            "Service Unavailable: The server is temporarily unable to handle the request, "
            "usually due to active maintenance, severe overload, or a down dependency."
        )
