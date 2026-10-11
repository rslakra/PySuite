from pycrux.exceptions.http import HTTPException


class ServerException(HTTPException):
    """Base class for 5xx server-side HTTP errors."""
