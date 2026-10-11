from pycrux.exceptions.client import ClientException


class TooManyRequestsException(ClientException):
    """429 Too Many Requests — client exceeded rate limit or quota."""

    status_code = 429

    @classmethod
    def default_message(cls) -> str:
        return (
            "Too Many Requests: The client has exceeded their allowed rate limit "
            "or quota within a given timeframe."
        )
