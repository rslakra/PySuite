from core.exceptions.http import HTTPException


class ClientException(HTTPException):
    """Base class for 4xx client-side HTTP errors."""
