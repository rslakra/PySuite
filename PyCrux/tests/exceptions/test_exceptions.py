"""Tests for ``pycrux.exceptions`` — base class, HTTP hierarchy, lookup helpers."""

import pytest

import pycrux.exceptions as exceptions
from pycrux.exceptions import (
    CLIENT_EXCEPTIONS,
    HTTP_EXCEPTIONS,
    SERVER_EXCEPTIONS,
    STATUS_CODE_TO_EXCEPTION,
    BadGatewayException,
    BadRequestException,
    ClientException,
    ConflictException,
    ForbiddenException,
    GatewayTimeoutException,
    HTTPException,
    InternalServerException,
    MethodNotAllowedException,
    NotFoundException,
    ServerException,
    ServiceUnavailableException,
    TooManyRequestsException,
    UnauthorizedException,
    UnprocessableEntityException,
    UnsupportedMediaTypeException,
    exception_for_status,
)
from pycrux.exceptions import BaseException as PyCruxBaseException

CLIENT_CASES = [
    (BadRequestException, 400),
    (UnauthorizedException, 401),
    (ForbiddenException, 403),
    (NotFoundException, 404),
    (MethodNotAllowedException, 405),
    (ConflictException, 409),
    (UnsupportedMediaTypeException, 415),
    (UnprocessableEntityException, 422),
    (TooManyRequestsException, 429),
]
SERVER_CASES = [
    (InternalServerException, 500),
    (BadGatewayException, 502),
    (ServiceUnavailableException, 503),
    (GatewayTimeoutException, 504),
]
ALL_CASES = CLIENT_CASES + SERVER_CASES


# --- BaseException ---------------------------------------------------------------


def test_base_exception_keeps_message_and_cause() -> None:
    cause = ValueError("root")
    exc = PyCruxBaseException("boom", cause=cause)
    assert exc.cause is cause
    assert exc.args == ("boom",)
    assert isinstance(exc, Exception)


def test_base_exception_without_cause() -> None:
    exc = PyCruxBaseException("boom")
    assert exc.cause is None
    assert str(exc) == "boom"


def test_base_exception_str_appends_cause_on_same_line() -> None:
    exc = PyCruxBaseException("boom", cause=ValueError("root"))
    assert str(exc) == "boom (caused by root)"


def test_base_exception_str_puts_cause_on_new_line_for_multiline_message() -> None:
    exc = PyCruxBaseException("line1\nline2", cause=ValueError("root"))
    assert str(exc) == "line1\nline2\n(caused by root)"


# --- HTTPException -----------------------------------------------------------------


def test_http_exception_defaults() -> None:
    assert HTTPException.status_code == 0
    assert HTTPException.default_message() == "HTTP 0 error"
    assert str(HTTPException()) == "HTTP 0 error"
    assert issubclass(HTTPException, PyCruxBaseException)


def test_http_exception_custom_message_and_cause() -> None:
    cause = RuntimeError("db down")
    exc = HTTPException("custom", cause=cause)
    assert exc.cause is cause
    assert str(exc) == "custom (caused by db down)"


def test_http_exception_empty_message_falls_back_to_default() -> None:
    assert str(HTTPException("")) == "HTTP 0 error"
    assert str(HTTPException(None)) == "HTTP 0 error"


def test_client_and_server_exceptions_are_http_exceptions() -> None:
    assert issubclass(ClientException, HTTPException)
    assert issubclass(ServerException, HTTPException)
    assert not issubclass(ClientException, ServerException)
    assert not issubclass(ServerException, ClientException)


# --- every concrete status exception -----------------------------------------------


@pytest.mark.parametrize(("cls", "code"), ALL_CASES)
def test_status_code(cls: type[HTTPException], code: int) -> None:
    assert cls.status_code == code


@pytest.mark.parametrize(("cls", "code"), CLIENT_CASES)
def test_client_exceptions_hierarchy(cls: type[HTTPException], code: int) -> None:
    assert issubclass(cls, ClientException)
    assert 400 <= code < 500


@pytest.mark.parametrize(("cls", "code"), SERVER_CASES)
def test_server_exceptions_hierarchy(cls: type[HTTPException], code: int) -> None:
    assert issubclass(cls, ServerException)
    assert 500 <= code < 600


@pytest.mark.parametrize(("cls", "code"), ALL_CASES)
def test_default_message_is_specific(cls: type[HTTPException], code: int) -> None:
    message = cls.default_message()
    assert message
    assert message != HTTPException.default_message()
    assert str(cls()) == message


@pytest.mark.parametrize(("cls", "code"), ALL_CASES)
def test_custom_message_and_cause(cls: type[HTTPException], code: int) -> None:
    cause = KeyError("k")
    exc = cls("custom", cause=cause)
    assert exc.cause is cause
    assert str(exc).startswith("custom (caused by ")


@pytest.mark.parametrize(("cls", "code"), ALL_CASES)
def test_can_be_raised_and_caught_as_http_exception(
    cls: type[HTTPException], code: int
) -> None:
    with pytest.raises(HTTPException) as info:
        raise cls()
    assert info.value.status_code == code


# --- registries and lookup ----------------------------------------------------------


def test_registry_tuples() -> None:
    assert CLIENT_EXCEPTIONS == tuple(cls for cls, _ in CLIENT_CASES)
    assert SERVER_EXCEPTIONS == tuple(cls for cls, _ in SERVER_CASES)
    assert HTTP_EXCEPTIONS == CLIENT_EXCEPTIONS + SERVER_EXCEPTIONS
    assert len(HTTP_EXCEPTIONS) == 13


def test_status_code_map_covers_every_exception() -> None:
    assert STATUS_CODE_TO_EXCEPTION == {code: cls for cls, code in ALL_CASES}
    assert len(STATUS_CODE_TO_EXCEPTION) == len(HTTP_EXCEPTIONS)


@pytest.mark.parametrize(("cls", "code"), ALL_CASES)
def test_exception_for_status_known_codes(cls: type[HTTPException], code: int) -> None:
    exc = exception_for_status(code)
    assert type(exc) is cls
    assert str(exc) == cls.default_message()


def test_exception_for_status_passes_message_and_cause() -> None:
    cause = OSError("disk")
    exc = exception_for_status(404, "user 42 missing", cause=cause)
    assert isinstance(exc, NotFoundException)
    assert exc.cause is cause
    assert str(exc) == "user 42 missing (caused by disk)"


@pytest.mark.parametrize("code", [0, 200, 418, 499, 599, -1])
def test_exception_for_status_unknown_code_is_internal_server_error(code: int) -> None:
    assert type(exception_for_status(code)) is InternalServerException


def test_all_exports_resolve() -> None:
    for name in exceptions.__all__:
        assert hasattr(exceptions, name), name
