"""HTTP-style client (4xx) and server (5xx) exceptions."""

from pycrux.exceptions.bad_gateway import BadGatewayException
from pycrux.exceptions.bad_request import BadRequestException
from pycrux.exceptions.base import BaseException
from pycrux.exceptions.client import ClientException
from pycrux.exceptions.conflict import ConflictException
from pycrux.exceptions.forbidden import ForbiddenException
from pycrux.exceptions.gateway_timeout import GatewayTimeoutException
from pycrux.exceptions.http import HTTPException
from pycrux.exceptions.internal_server_error import InternalServerException
from pycrux.exceptions.method_not_allowed import MethodNotAllowedException
from pycrux.exceptions.not_found import NotFoundException
from pycrux.exceptions.server import ServerException
from pycrux.exceptions.service_unavailable import ServiceUnavailableException
from pycrux.exceptions.too_many_requests import TooManyRequestsException
from pycrux.exceptions.unauthorized import UnauthorizedException
from pycrux.exceptions.unprocessable_entity import UnprocessableEntityException
from pycrux.exceptions.unsupported_media_type import UnsupportedMediaTypeException

CLIENT_EXCEPTIONS: tuple[type[ClientException], ...] = (
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    MethodNotAllowedException,
    ConflictException,
    UnsupportedMediaTypeException,
    UnprocessableEntityException,
    TooManyRequestsException,
)

SERVER_EXCEPTIONS: tuple[type[ServerException], ...] = (
    InternalServerException,
    BadGatewayException,
    ServiceUnavailableException,
    GatewayTimeoutException,
)

HTTP_EXCEPTIONS: tuple[type[HTTPException], ...] = CLIENT_EXCEPTIONS + SERVER_EXCEPTIONS

STATUS_CODE_TO_EXCEPTION: dict[int, type[HTTPException]] = {
    cls.status_code: cls for cls in HTTP_EXCEPTIONS
}


def exception_for_status(
    status_code: int,
    message: str | None = None,
    cause: Exception | None = None,
) -> HTTPException:
    """Return the matching HTTP exception class instance for a status code."""
    exc_cls = STATUS_CODE_TO_EXCEPTION.get(status_code, InternalServerException)
    return exc_cls(message, cause=cause)


__all__ = [
    "BaseException",
    "HTTPException",
    "ClientException",
    "ServerException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "MethodNotAllowedException",
    "ConflictException",
    "UnsupportedMediaTypeException",
    "UnprocessableEntityException",
    "TooManyRequestsException",
    "InternalServerException",
    "BadGatewayException",
    "ServiceUnavailableException",
    "GatewayTimeoutException",
    "CLIENT_EXCEPTIONS",
    "SERVER_EXCEPTIONS",
    "HTTP_EXCEPTIONS",
    "STATUS_CODE_TO_EXCEPTION",
    "exception_for_status",
]
